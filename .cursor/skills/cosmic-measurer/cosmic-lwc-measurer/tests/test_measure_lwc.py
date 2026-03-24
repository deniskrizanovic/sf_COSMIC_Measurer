"""Tests for standalone LWC measurement API."""

from pathlib import Path

from measure_lwc import measure_lwc, measure_lwc_bundle


def test_measure_lwc_bundle_sample(project_root: Path):
    bundle_dir = project_root / "samples" / "cfp_FunctionalProcessVisualiser"
    result = measure_lwc_bundle(bundle_dir, functional_process_id="FP-1")
    assert result["functionalProcessId"] == "FP-1"
    assert result["artifact"]["type"] == "LWC"
    assert result["artifact"]["name"] == "cfp_FunctionalProcessVisualiser"
    assert result["dataMovements"][-1]["name"] == "Errors/notifications"
    assert result["dataMovements"][-1]["movementType"] == "X"
    assert result["dataMovements"][-1]["dataGroupRef"] == "User"


def test_measure_lwc_required_types_validation(project_root: Path):
    bundle_dir = project_root / "samples" / "cfp_FunctionalProcessVisualiser"
    result = measure_lwc_bundle(
        bundle_dir,
        required_movement_types=["W"],
        apex_search_paths=[project_root / "samples"],
    )
    assert result["requiredMovementTypes"] == ["W"]
    assert result["satisfiesRequiredMovementTypes"] is False
    assert result["missingRequiredMovementTypes"] == ["W"]


def test_measure_lwc_apex_merge_has_via_artifact(project_root: Path):
    bundle_dir = project_root / "samples" / "cfp_FunctionalProcessVisualiser"
    result = measure_lwc_bundle(
        bundle_dir,
        apex_search_paths=[project_root / "samples"],
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
    bundle_dir = project_root / "samples" / "cfp_FunctionalProcessVisualiser"
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
    bundle_dir = project_root / "samples" / "cfp_FunctionalProcessVisualiser"
    expected_path = (
        project_root
        / "samples"
        / "expected"
        / "cfp_FunctionalProcessVisualiser.lwc.expected.json"
    )
    assert expected_path.exists()
    result = measure_lwc_bundle(
        bundle_dir,
        apex_search_paths=[project_root / "samples"],
        required_movement_types=["W"],
    )
    import json

    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    assert result == expected
