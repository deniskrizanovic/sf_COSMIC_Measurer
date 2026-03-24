"""CLI and traversal tests for measure_apex.py (in-process main() for coverage)."""

import json
import shutil
import sys
from pathlib import Path

import measure_apex
from measure_apex import _traverse_callees, find_class_file, measure_file
from parser import get_entry_points


CALLER_SRC = """
public class TraverseCaller {
    public static void run() {
        TraverseHelper.doWork();
        MissingCallee.ping();
    }
}
"""

HELPER_SRC = """
public class TraverseHelper {
    public static void doWork() {
        List<Thing__c> rows = [SELECT Id FROM Thing__c WHERE Id != null];
        insert rows;
    }
}
"""

BATCH_CALLER_SRC = """
public class BatchCaller {
    public static void run() {
        Id jobId = Database.executeBatch(new AsyncBatchWorker());
    }
}
"""

ASYNC_BATCH_WORKER_SRC = """
public class AsyncBatchWorker implements Database.Batchable<SObject> {
    public Database.QueryLocator start(Database.BatchableContext bc) {
        return Database.getQueryLocator([SELECT Id FROM Account WHERE Id != null]);
    }
    public void execute(Database.BatchableContext bc, List<SObject> scope) {
        List<Contact> rows = new List<Contact>();
        update rows;
    }
    public void finish(Database.BatchableContext bc) {
    }
}
"""

QUEUEABLE_CALLER_SRC = """
public class QueueableCaller {
    public static void run() {
        Id jobId = System.enqueueJob(new AsyncQueueableWorker());
    }
}
"""

ASYNC_QUEUEABLE_WORKER_SRC = """
public class AsyncQueueableWorker implements Queueable {
    public void execute(QueueableContext context) {
        List<Account> rows = [SELECT Id FROM Account WHERE Id != null];
        update rows;
    }
}
"""

SCHEDULE_CALLER_SRC = """
public class ScheduleCaller {
    public static void run() {
        String id = System.schedule('Nightly', '0 0 2 * * ?', new AsyncSchedulableWorker());
    }
}
"""

ASYNC_SCHEDULABLE_WORKER_SRC = """
public class AsyncSchedulableWorker implements Schedulable {
    public void execute(SchedulableContext context) {
        List<Contact> rows = [SELECT Id FROM Contact WHERE Id != null];
        update rows;
    }
}
"""

SELF_LOOP_SRC = """
public class SelfLoop {
    public static void run() {
        SelfLoop.noop();
    }
    public static void noop() {
    }
}
"""

CYCLE_A_SRC = """
public class CycleA {
    public static void run() {
        CycleB.run();
    }
}
"""

CYCLE_B_SRC = """
public class CycleB {
    public static void run() {
        CycleA.run();
    }
}
"""

MULTI_HOP_CALLER_SRC = """
public class MultiHopCaller {
    public static void run() {
        LevelOne.run(new List<Account>());
    }
}
"""

LEVEL_ONE_SRC = """
public class LevelOne {
    public static List<Account> run(List<Account> accounts) {
        LevelTwo.touch(accounts);
        return accounts;
    }
}
"""

LEVEL_TWO_SRC = """
public class LevelTwo {
    public static void touch(List<Account> accounts) {
        List<Account> rows = [SELECT Id FROM Account WHERE Id != null];
        update accounts;
        MissingDeep.ping();
    }
}
"""


def test_find_class_file_skips_missing_base_and_finds_match(tmp_path):
    missing = tmp_path / "nope"
    helper_dir = tmp_path / "sub"
    helper_dir.mkdir()
    (helper_dir / "TraverseHelper.cls").write_text(HELPER_SRC, encoding="utf-8")

    assert find_class_file("TraverseHelper", [missing, helper_dir]) == helper_dir / "TraverseHelper.cls"


def test_measure_file_traverses_helper_via_artifact(tmp_path):
    (tmp_path / "TraverseCaller.cls").write_text(CALLER_SRC, encoding="utf-8")
    (tmp_path / "TraverseHelper.cls").write_text(HELPER_SRC, encoding="utf-8")

    out = measure_file(tmp_path / "TraverseCaller.cls", search_paths=[tmp_path])
    assert "MissingCallee" in (out.get("calledClassesNotFound") or [])
    via = [m for m in out["dataMovements"] if m.get("viaArtifact") == "TraverseHelper"]
    assert any(m["movementType"] == "R" for m in via)
    assert any(m["movementType"] == "W" for m in via)


def test_measure_file_traverses_execute_batch_as_async(tmp_path):
    (tmp_path / "BatchCaller.cls").write_text(BATCH_CALLER_SRC, encoding="utf-8")
    (tmp_path / "AsyncBatchWorker.cls").write_text(ASYNC_BATCH_WORKER_SRC, encoding="utf-8")

    out = measure_file(tmp_path / "BatchCaller.cls", search_paths=[tmp_path])
    via = [m for m in out["dataMovements"] if m.get("viaArtifact") == "AsyncBatchWorker"]
    assert via
    assert all(m.get("isAsync") is True for m in via)


def test_measure_file_traverses_enqueue_job_as_async(tmp_path):
    (tmp_path / "QueueableCaller.cls").write_text(QUEUEABLE_CALLER_SRC, encoding="utf-8")
    (tmp_path / "AsyncQueueableWorker.cls").write_text(
        ASYNC_QUEUEABLE_WORKER_SRC, encoding="utf-8"
    )

    out = measure_file(tmp_path / "QueueableCaller.cls", search_paths=[tmp_path])
    via = [m for m in out["dataMovements"] if m.get("viaArtifact") == "AsyncQueueableWorker"]
    assert via
    assert all(m.get("isAsync") is True for m in via)


def test_measure_file_traverses_system_schedule_as_async(tmp_path):
    (tmp_path / "ScheduleCaller.cls").write_text(SCHEDULE_CALLER_SRC, encoding="utf-8")
    (tmp_path / "AsyncSchedulableWorker.cls").write_text(
        ASYNC_SCHEDULABLE_WORKER_SRC, encoding="utf-8"
    )

    out = measure_file(tmp_path / "ScheduleCaller.cls", search_paths=[tmp_path])
    via = [
        m for m in out["dataMovements"] if m.get("viaArtifact") == "AsyncSchedulableWorker"
    ]
    assert via
    assert all(m.get("isAsync") is True for m in via)


def test_measure_file_skips_self_static_call(tmp_path):
    (tmp_path / "SelfLoop.cls").write_text(SELF_LOOP_SRC, encoding="utf-8")
    out = measure_file(tmp_path / "SelfLoop.cls", search_paths=[tmp_path])
    assert "SelfLoop" not in (out.get("calledClassesNotFound") or [])


def test_measure_file_skips_cycle_between_classes(tmp_path):
    (tmp_path / "CycleA.cls").write_text(CYCLE_A_SRC, encoding="utf-8")
    (tmp_path / "CycleB.cls").write_text(CYCLE_B_SRC, encoding="utf-8")
    measure_file(tmp_path / "CycleA.cls", search_paths=[tmp_path])


def test_measure_file_traverses_multi_hop_and_merges_rw_only(tmp_path):
    (tmp_path / "MultiHopCaller.cls").write_text(MULTI_HOP_CALLER_SRC, encoding="utf-8")
    (tmp_path / "LevelOne.cls").write_text(LEVEL_ONE_SRC, encoding="utf-8")
    (tmp_path / "LevelTwo.cls").write_text(LEVEL_TWO_SRC, encoding="utf-8")

    out = measure_file(tmp_path / "MultiHopCaller.cls", search_paths=[tmp_path])
    via_level_one = [m for m in out["dataMovements"] if m.get("viaArtifact") == "LevelOne"]
    via_level_two = [m for m in out["dataMovements"] if m.get("viaArtifact") == "LevelTwo"]

    assert not any(m["movementType"] == "E" for m in via_level_one)
    assert not any(m["movementType"] == "X" for m in via_level_one)
    assert any(m["movementType"] == "R" for m in via_level_two)
    assert any(m["movementType"] == "W" for m in via_level_two)
    assert "MissingDeep" in (out.get("calledClassesNotFound") or [])


def test_traverse_skips_class_already_in_visited(tmp_path):
    (tmp_path / "TraverseCaller.cls").write_text(CALLER_SRC, encoding="utf-8")
    (tmp_path / "TraverseHelper.cls").write_text(HELPER_SRC, encoding="utf-8")
    source = (tmp_path / "TraverseCaller.cls").read_text(encoding="utf-8")
    movements, not_found = _traverse_callees(
        source,
        [],
        [tmp_path],
        {"TraverseHelper"},
        "TraverseCaller",
    )
    assert not any(getattr(m, "via_artifact", None) == "TraverseHelper" for m in movements)
    assert "MissingCallee" in not_found


def test_measure_file_relative_search_paths_resolved(project_root, tmp_path):
    rel_name = "_pytest_traverse_search"
    search_dir = project_root / rel_name
    search_dir.mkdir(exist_ok=True)
    try:
        (search_dir / "TraverseHelper.cls").write_text(HELPER_SRC, encoding="utf-8")
        (tmp_path / "TraverseCaller.cls").write_text(CALLER_SRC, encoding="utf-8")
        out = measure_file(
            tmp_path / "TraverseCaller.cls",
            search_paths=[Path(rel_name)],
        )
        assert any(m.get("viaArtifact") == "TraverseHelper" for m in out["dataMovements"])
    finally:
        shutil.rmtree(search_dir, ignore_errors=True)


def test_measure_file_no_traverse_hides_not_found(tmp_path):
    (tmp_path / "TraverseCaller.cls").write_text(CALLER_SRC, encoding="utf-8")
    out = measure_file(
        tmp_path / "TraverseCaller.cls",
        search_paths=[tmp_path],
        traverse=False,
    )
    assert out.get("calledClassesNotFound") is None


def test_main_json_stdout(monkeypatch, capsys, project_root):
    sample = project_root / "samples" / "classes" / "cfp_getDataMovements.cls"
    monkeypatch.setattr(sys, "argv", ["measure_apex", str(sample), "--json"])
    assert measure_apex.main() == 0
    assert "dataMovements" in capsys.readouterr().out


def test_main_table_stdout(monkeypatch, capsys, project_root):
    sample = project_root / "samples" / "classes" / "cfp_getDataMovements.cls"
    monkeypatch.setattr(sys, "argv", ["measure_apex", str(sample)])
    assert measure_apex.main() == 0
    out = capsys.readouterr().out
    assert "Functional size" in out or "| Order |" in out


def test_main_output_file(monkeypatch, capsys, project_root, tmp_path):
    sample = project_root / "samples" / "classes" / "cfp_getDataMovements.cls"
    out_file = tmp_path / "out.json"
    monkeypatch.setattr(sys, "argv", ["measure_apex", str(sample), "-o", str(out_file)])
    assert measure_apex.main() == 0
    assert out_file.is_file()
    assert "dataMovements" in out_file.read_text(encoding="utf-8")
    assert "Functional size" in capsys.readouterr().out


def test_main_fp_id(monkeypatch, capsys, project_root):
    sample = project_root / "samples" / "classes" / "cfp_getDataMovements.cls"
    monkeypatch.setattr(
        sys, "argv", ["measure_apex", str(sample), "--json", "--fp-id", "FP-99"]
    )
    assert measure_apex.main() == 0
    assert json.loads(capsys.readouterr().out)["functionalProcessId"] == "FP-99"


def test_main_multiple_files_json_array(monkeypatch, capsys, project_root, tmp_path):
    s1 = project_root / "samples" / "classes" / "cfp_getDataMovements.cls"
    s2 = tmp_path / "Tiny.cls"
    s2.write_text("public class Tiny { public static void x() {} }", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["measure_apex", str(s1), str(s2), "--json"])
    assert measure_apex.main() == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert len(data) == 2


def test_main_multiple_files_output_writes_array(monkeypatch, project_root, tmp_path):
    s1 = project_root / "samples" / "classes" / "cfp_getDataMovements.cls"
    s2 = tmp_path / "Tiny.cls"
    s2.write_text("public class Tiny { public static void x() {} }", encoding="utf-8")
    out_file = tmp_path / "multi.json"
    monkeypatch.setattr(
        sys, "argv", ["measure_apex", str(s1), str(s2), "-o", str(out_file)]
    )
    assert measure_apex.main() == 0
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 2


def test_main_list_entry_points(monkeypatch, capsys, project_root):
    sample = project_root / "samples" / "classes" / "cfp_getDataMovements.cls"
    monkeypatch.setattr(sys, "argv", ["measure_apex", str(sample), "--list-entry-points"])
    assert measure_apex.main() == 0
    assert "entryPoints" in json.loads(capsys.readouterr().out)


def test_main_list_entry_points_requires_single_file(monkeypatch, capsys, project_root):
    s1 = project_root / "samples" / "classes" / "cfp_getDataMovements.cls"
    s2 = project_root / "samples" / "classes" / "BulkSurveyActionsBatch.cls"
    monkeypatch.setattr(sys, "argv", ["measure_apex", str(s1), str(s2), "--list-entry-points"])
    assert measure_apex.main() == 1
    assert "exactly one file" in capsys.readouterr().err


def test_main_missing_file(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["measure_apex", "/no/such/file.cls"])
    assert measure_apex.main() == 1
    assert "not found" in capsys.readouterr().err


def test_main_list_entry_points_missing_file(monkeypatch, capsys):
    monkeypatch.setattr(
        sys, "argv", ["measure_apex", "/no/such/file.cls", "--list-entry-points"]
    )
    assert measure_apex.main() == 1


def test_main_invalid_entry_point(monkeypatch, capsys, project_root):
    sample = project_root / "samples" / "classes" / "cfp_getDataMovements.cls"
    monkeypatch.setattr(
        sys,
        "argv",
        ["measure_apex", str(sample), "--entry-point", "notARealParamEver", "--json"],
    )
    assert measure_apex.main() == 1
    assert "not found" in capsys.readouterr().err


def test_main_valid_entry_point(monkeypatch, capsys, project_root):
    sample = project_root / "samples" / "classes" / "cfp_getDataMovements.cls"
    eps = get_entry_points(sample.read_text(encoding="utf-8"))
    assert eps
    param = eps[0]["param"]
    monkeypatch.setattr(
        sys, "argv", ["measure_apex", str(sample), "--entry-point", param, "--json"]
    )
    assert measure_apex.main() == 0
    assert "dataMovements" in capsys.readouterr().out


def test_main_non_cls_warning(monkeypatch, capsys, tmp_path):
    f = tmp_path / "readme.txt"
    f.write_text("x", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["measure_apex", str(f), "--json"])
    assert measure_apex.main() == 0
    assert "may not be Apex" in capsys.readouterr().err


def test_main_no_traverse(monkeypatch, capsys, tmp_path):
    (tmp_path / "TraverseCaller.cls").write_text(CALLER_SRC, encoding="utf-8")
    (tmp_path / "TraverseHelper.cls").write_text(HELPER_SRC, encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "measure_apex",
            str(tmp_path / "TraverseCaller.cls"),
            "--no-traverse",
            "--search-paths",
            str(tmp_path),
            "--json",
        ],
    )
    assert measure_apex.main() == 0
    data = json.loads(capsys.readouterr().out)
    assert not any(m.get("viaArtifact") == "TraverseHelper" for m in data["dataMovements"])
