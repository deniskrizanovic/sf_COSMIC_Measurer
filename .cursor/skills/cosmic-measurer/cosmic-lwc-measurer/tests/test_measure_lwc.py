"""Tests for standalone LWC measurement API."""

from pathlib import Path

import pytest

from measure_lwc import (
    _apex_rows_to_raw_movements,
    _is_canonical_exit_row,
    measure_lwc,
    measure_lwc_bundle,
    resolve_lwc_candidate,
    validate_required_movement_types,
)


def test_measure_lwc_bundle_sample(project_root: Path):
    bundle_dir = project_root / "samples" / "lwc" / "cfp_FunctionalProcessVisualiser"
    result = measure_lwc_bundle(bundle_dir, functional_process_id="FP-1")
    assert result["functionalProcessId"] == "FP-1"
    assert result["artifact"]["type"] == "LWC"
    assert result["artifact"]["name"] == "cfp_FunctionalProcessVisualiser"
    assert result["dataMovements"][-1]["name"] == "Errors/notifications"
    assert result["dataMovements"][-1]["movementType"] == "X"
    assert result["dataMovements"][-1]["dataGroupRef"] == "status/errors/etc"


def test_measure_lwc_required_types_validation(project_root: Path):
    bundle_dir = project_root / "samples" / "lwc" / "cfp_FunctionalProcessVisualiser"
    result = measure_lwc_bundle(
        bundle_dir,
        required_movement_types=["W"],
        apex_search_paths=[project_root / "samples" / "classes"],
    )
    assert result["requiredMovementTypes"] == ["W"]
    assert result["satisfiesRequiredMovementTypes"] is False
    assert result["missingRequiredMovementTypes"] == ["W"]


def test_measure_lwc_apex_merge_has_via_artifact(project_root: Path):
    bundle_dir = project_root / "samples" / "lwc" / "cfp_FunctionalProcessVisualiser"
    result = measure_lwc_bundle(
        bundle_dir,
        apex_search_paths=[project_root / "samples" / "classes"],
    )
    via_rows = [row for row in result["dataMovements"] if row.get("viaArtifact")]
    assert via_rows
    assert any(row.get("implementationType") == "apex" for row in via_rows)
    display_rows = [
        row
        for row in result["dataMovements"]
        if row.get("name") == "Display LWC output to user"
    ]
    assert display_rows
    assert display_rows[0].get("dataGroupRef") == "cfp_Data_Movements__c"


def test_measure_lwc_missing_apex_non_fatal(tmp_path: Path):
    bundle_dir = tmp_path / "c" / "missingApex"
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "missingApex.js").write_text(
        "import runThing from '@salesforce/apex/MissingClass.runThing';\n",
        encoding="utf-8",
    )
    (bundle_dir / "missingApex.html").write_text("<template></template>", encoding="utf-8")
    (bundle_dir / "missingApex.js-meta.xml").write_text(
        "<LightningComponentBundle xmlns=\"http://soap.sforce.com/2006/04/metadata\"></LightningComponentBundle>",
        encoding="utf-8",
    )
    result = measure_lwc_bundle(bundle_dir)
    warnings = result.get("traversalWarnings") or []
    assert any("MissingClass" in warning for warning in warnings)


def test_measure_lwc_request_passthrough_context(project_root: Path):
    bundle_dir = project_root / "samples" / "lwc" / "cfp_FunctionalProcessVisualiser"
    result = measure_lwc(
        {
            "lwc_bundle_dir": str(bundle_dir),
            "source_artifact": {"type": "FlexiPage", "name": "Any"},
            "tab_context": {"identifier": "tab1", "title": "Visualiser"},
        }
    )
    assert result["sourceArtifact"]["type"] == "FlexiPage"
    assert result["tabContext"]["identifier"] == "tab1"


def test_measure_lwc_sample_matches_golden(project_root: Path):
    bundle_dir = project_root / "samples" / "lwc" / "cfp_FunctionalProcessVisualiser"
    expected_path = (
        project_root
        / "expected"
        / "cfp_FunctionalProcessVisualiser.lwc.expected.json"
    )
    assert expected_path.exists()
    result = measure_lwc_bundle(
        bundle_dir,
        apex_search_paths=[project_root / "samples" / "classes"],
        required_movement_types=["W"],
    )
    import json

    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    assert result == expected


def test_measure_lwc_bundle_raises_for_non_directory(tmp_path: Path):
    not_a_directory = tmp_path / "component.js"
    not_a_directory.write_text("export default class X {}", encoding="utf-8")
    with pytest.raises(ValueError, match="is not a directory"):
        measure_lwc_bundle(not_a_directory)


def test_measure_lwc_bundle_raises_for_missing_files_with_override(tmp_path: Path):
    bundle_dir = tmp_path / "actualBundle"
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "actualBundle.js").write_text("export default class X {}", encoding="utf-8")
    (bundle_dir / "actualBundle.html").write_text("<template></template>", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing overriddenName.js or overriddenName.html"):
        measure_lwc_bundle(bundle_dir, lwc_name="overriddenName")


def test_is_canonical_exit_row_true_and_false():
    canonical = {
        "movementType": "X",
        "name": "Errors/notifications",
        "dataGroupRef": "status/errors/etc",
    }
    non_canonical = {
        "movementType": "X",
        "name": "Display LWC output to user",
        "dataGroupRef": "User",
    }
    assert _is_canonical_exit_row(canonical) is True
    assert _is_canonical_exit_row(non_canonical) is False


def test_apex_rows_to_raw_movements_skips_invalid_and_exit_rows():
    rows = [
        {"movementType": "X", "name": "AnyExit", "dataGroupRef": "User"},
        {
            "movementType": "X",
            "name": "Errors/notifications",
            "dataGroupRef": "status/errors/etc",
        },
        {"movementType": "R", "name": "MissingGroup"},
        {"movementType": "W", "dataGroupRef": "AnyGroup"},
        {"name": "MissingType", "dataGroupRef": "AnyGroup"},
        {
            "movementType": "R",
            "name": "Valid read",
            "dataGroupRef": "Account",
            "sourceLine": 22,
        },
    ]
    raw = _apex_rows_to_raw_movements(rows, via_artifact="MyClass", order_hint_start=1000)
    assert len(raw) == 1
    assert raw[0].movement_type == "R"
    assert raw[0].name == "Valid read"
    assert raw[0].data_group_ref == "Account"
    assert raw[0].order_hint == 1001
    assert raw[0].via_artifact == "MyClass"
    assert raw[0].source_line == 22


def test_validate_required_movement_types_handles_missing_and_all_present():
    movements = [{"movementType": "E"}, {"movementType": "R"}]
    satisfies, missing = validate_required_movement_types(movements, ["E", "X"])
    assert satisfies is False
    assert missing == ["X"]

    satisfies_all, missing_all = validate_required_movement_types(movements, ["E", "R"])
    assert satisfies_all is True
    assert missing_all == []


def test_resolve_lwc_candidate_passthrough(monkeypatch):
    captured = {}

    def fake_measure_lwc(request):
        captured["request"] = request
        return {"artifact": {"type": "LWC", "name": "myCmp"}}

    monkeypatch.setattr("measure_lwc.measure_lwc", fake_measure_lwc)
    candidate = {
        "artifact": {"name": "myCmp"},
        "functionalProcessId": "FP-77",
        "requiredMovementTypes": ["W"],
        "sourceArtifact": {"type": "FlexiPage", "name": "WorkOrder"},
        "tabContext": {"identifier": "tab-1", "title": "Details"},
    }
    result = resolve_lwc_candidate(candidate, apex_search_paths=["samples/classes"])
    assert result["artifact"]["name"] == "myCmp"
    assert captured["request"]["lwc_name"] == "myCmp"
    assert captured["request"]["lwc_bundle_dir"] == "myCmp"
    assert captured["request"]["functional_process_id"] == "FP-77"
    assert captured["request"]["apex_search_paths"] == ["samples/classes"]
    assert captured["request"]["required_movement_types"] == ["W"]
    assert captured["request"]["source_artifact"]["type"] == "FlexiPage"
    assert captured["request"]["tab_context"]["identifier"] == "tab-1"


def test_measure_lwc_bundle_apex_import_dedup_and_group_inference(tmp_path: Path, monkeypatch):
    bundle_dir = tmp_path / "myCmp"
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "myCmp.js").write_text(
        (
            "import one from '@salesforce/apex/MyClass.load';\n"
            "import dup from '@salesforce/apex/MyClass.load';\n"
            "import two from '@salesforce/apex/OtherClass.run';\n"
        ),
        encoding="utf-8",
    )
    (bundle_dir / "myCmp.html").write_text(
        "<template><div>{value}</div></template>",
        encoding="utf-8",
    )

    class_calls = []

    def fake_find_class_file(class_name, _search_paths):
        class_calls.append(class_name)
        return Path(f"/tmp/{class_name}.cls")

    def fake_measure_apex_file(class_file, _fp_id, search_paths, traverse):
        assert search_paths
        assert traverse is True
        class_name = Path(class_file).stem
        if class_name == "MyClass":
            return {
                "dataMovements": [
                    {
                        "movementType": "R",
                        "name": "Read account",
                        "dataGroupRef": "Account",
                        "sourceLine": 10,
                    },
                    {
                        "movementType": "X",
                        "name": "Display LWC output to user",
                        "dataGroupRef": "cfp_Data_Movements__c",
                    },
                    {
                        "movementType": "X",
                        "name": "Errors/notifications",
                        "dataGroupRef": "status/errors/etc",
                    },
                    {
                        "movementType": "W",
                        "dataGroupRef": "NoName",
                    },
                ]
            }
        return {"dataMovements": [{"movementType": "W", "name": "Write", "dataGroupRef": "Case"}]}

    monkeypatch.setattr(
        "measure_lwc._load_apex_measurer_helpers",
        lambda: (fake_find_class_file, fake_measure_apex_file),
    )

    result = measure_lwc_bundle(bundle_dir, apex_search_paths=[tmp_path / "classes"])
    assert class_calls.count("MyClass") == 1
    assert class_calls.count("OtherClass") == 1
    display_rows = [
        row
        for row in result["dataMovements"]
        if row.get("name") == "Display LWC output to user" and row.get("implementationType") == "lwc"
    ]
    assert display_rows
    assert display_rows[0]["dataGroupRef"] == "cfp_Data_Movements__c"
    apex_rows = [row for row in result["dataMovements"] if row.get("implementationType") == "apex"]
    assert any(row.get("name") == "Read account" for row in apex_rows)
    assert any(row.get("name") == "Write" for row in apex_rows)
    assert not any(row.get("name") == "Errors/notifications" and row.get("implementationType") == "apex" for row in apex_rows)
