"""CLI tests for measure_flow.py (in-process main() for coverage)."""

import json
import sys

import measure_flow
from conftest import make_flow_xml


BASIC_BODY = """
    <recordLookups>
        <name>getAccount</name>
        <label>getAccount</label>
        <object>Account</object>
    </recordLookups>
    <recordCreates>
        <name>createContact</name>
        <label>createContact</label>
        <object>Contact</object>
    </recordCreates>
"""


def _write_flow(tmp_path, name="Test.flow-meta.xml", body=BASIC_BODY):
    xml = make_flow_xml(body=body)
    f = tmp_path / name
    f.write_text(xml, encoding="utf-8")
    return f


def test_cli_json_stdout(monkeypatch, capsys, tmp_path):
    f = _write_flow(tmp_path)
    monkeypatch.setattr(sys, "argv", ["measure_flow", str(f), "--json"])
    assert measure_flow.main() == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "dataMovements" in data
    assert data["artifact"]["type"] == "Flow"


def test_cli_table_stdout(monkeypatch, capsys, tmp_path):
    f = _write_flow(tmp_path)
    monkeypatch.setattr(sys, "argv", ["measure_flow", str(f)])
    assert measure_flow.main() == 0
    out = capsys.readouterr().out
    assert "| Order |" in out or "Functional size" in out


def test_cli_output_file(monkeypatch, capsys, tmp_path):
    f = _write_flow(tmp_path)
    out_file = tmp_path / "out.json"
    monkeypatch.setattr(sys, "argv", ["measure_flow", str(f), "-o", str(out_file)])
    assert measure_flow.main() == 0
    assert out_file.is_file()
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert "dataMovements" in data
    assert "Functional size" in capsys.readouterr().out


def test_cli_fp_id(monkeypatch, capsys, tmp_path):
    f = _write_flow(tmp_path)
    monkeypatch.setattr(
        sys, "argv", ["measure_flow", str(f), "--json", "--fp-id", "FP-42"]
    )
    assert measure_flow.main() == 0
    data = json.loads(capsys.readouterr().out)
    assert data["functionalProcessId"] == "FP-42"


def test_cli_missing_file(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["measure_flow", "/no/such/file.flow-meta.xml"])
    assert measure_flow.main() == 1
    assert "not found" in capsys.readouterr().err


def test_cli_non_xml_warning(monkeypatch, capsys, tmp_path):
    f = tmp_path / "readme.txt"
    f.write_text("<Flow></Flow>", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["measure_flow", str(f), "--json"])
    assert measure_flow.main() == 0
    assert "may not be a Flow" in capsys.readouterr().err


def test_cli_invalid_xml_error(monkeypatch, capsys, tmp_path):
    f = tmp_path / "Bad.flow-meta.xml"
    f.write_text("<not-closed>", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["measure_flow", str(f), "--json"])
    assert measure_flow.main() == 1
    assert "Invalid XML" in capsys.readouterr().err


def test_cli_multiple_files(monkeypatch, capsys, tmp_path):
    f1 = _write_flow(tmp_path, name="A.flow-meta.xml")
    f2 = _write_flow(tmp_path, name="B.flow-meta.xml", body="")
    monkeypatch.setattr(sys, "argv", ["measure_flow", str(f1), str(f2), "--json"])
    assert measure_flow.main() == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert len(data) == 2


def test_cli_multiple_files_output(monkeypatch, tmp_path):
    f1 = _write_flow(tmp_path, name="A.flow-meta.xml")
    f2 = _write_flow(tmp_path, name="B.flow-meta.xml", body="")
    out_file = tmp_path / "multi.json"
    monkeypatch.setattr(
        sys, "argv", ["measure_flow", str(f1), str(f2), "-o", str(out_file)]
    )
    assert measure_flow.main() == 0
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 2


def test_cli_sample_flow(monkeypatch, capsys, project_root):
    sample = project_root / "samples" / "cfp_createCRUDLwithRelatedLists.flow-meta.xml"
    if not sample.exists():
        return
    monkeypatch.setattr(sys, "argv", ["measure_flow", str(sample), "--json"])
    assert measure_flow.main() == 0
    data = json.loads(capsys.readouterr().out)
    assert data["artifact"]["type"] == "Flow"
    assert len(data["dataMovements"]) >= 4
