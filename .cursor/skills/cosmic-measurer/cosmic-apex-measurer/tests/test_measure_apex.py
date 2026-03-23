"""Regression tests for COSMIC Apex measurer."""

import json

from measure_apex import measure_file
from movements import CANONICAL_EXIT_DATA_GROUP_REF, CANONICAL_EXIT_NAME


def test_cfp_getDataMovements_matches_golden(project_root):
    """Output should match expected JSON (semantic equivalence)."""
    sample = project_root / "samples" / "cfp_getDataMovements.cls"
    expected = project_root / "samples" / "expected" / "cfp_getDataMovements.expected.json"

    result = measure_file(sample)
    with open(expected) as f:
        golden = json.load(f)

    assert result["artifact"]["name"] == golden["artifact"]["name"]
    assert result["artifact"]["type"] == golden["artifact"]["type"]
    assert len(result["dataMovements"]) == len(golden["dataMovements"])

    for got, exp in zip(result["dataMovements"], golden["dataMovements"]):
        assert got["movementType"] == exp["movementType"]
        assert got["dataGroupRef"] == exp["dataGroupRef"]
        assert got["name"] == exp["name"]
        assert got["order"] == exp["order"]


def test_canonical_exit_is_final_row(project_root):
    """Every FP ends with one X: Errors/notifications (User)."""
    sample = project_root / "samples" / "cfp_getDataMovements.cls"
    result = measure_file(sample)
    dm = result["dataMovements"]
    assert dm[-1]["movementType"] == "X"
    assert dm[-1]["name"] == CANONICAL_EXIT_NAME
    assert dm[-1]["dataGroupRef"] == CANONICAL_EXIT_DATA_GROUP_REF


def test_BulkSurveyActionsBatch_has_entry_read_write(project_root):
    """Batch class should have E, R, W for Survey__c."""
    sample = project_root / "samples" / "BulkSurveyActionsBatch.cls"
    if not sample.exists():
        return

    result = measure_file(sample)
    types = [m["movementType"] for m in result["dataMovements"]]

    assert "E" in types
    assert "R" in types
    assert "W" in types
    assert result["artifact"]["name"] == "BulkSurveyActionsBatch"
