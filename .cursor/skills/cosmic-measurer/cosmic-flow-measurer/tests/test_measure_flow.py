"""Integration tests for measure_flow.py."""

import json

import pytest

from conftest import make_flow_xml
from measure_flow import measure_file
from shared.output import CANONICAL_EXIT_DATA_GROUP_REF, CANONICAL_EXIT_NAME


LOOKUP_BODY = """
    <recordLookups>
        <name>getAccount</name>
        <label>getAccount</label>
        <object>Account</object>
    </recordLookups>
"""

CREATE_BODY = """
    <recordCreates>
        <name>createContact</name>
        <label>createContact</label>
        <object>Contact</object>
    </recordCreates>
"""


def test_measure_sample_flow_reads_detected(project_root):
    sample = project_root / "samples" / "cfp_createCRUDLwithRelatedLists.flow-meta.xml"
    if not sample.exists():
        pytest.skip("Sample flow not found")
    result = measure_file(sample)
    reads = [m for m in result["dataMovements"] if m["movementType"] == "R"]
    objects = {r["dataGroupRef"] for r in reads}
    assert "cfp_FunctionalProcess__c" in objects
    assert "cfp_DataGroups__c" in objects


def test_measure_sample_flow_writes_detected(project_root):
    sample = project_root / "samples" / "cfp_createCRUDLwithRelatedLists.flow-meta.xml"
    if not sample.exists():
        pytest.skip("Sample flow not found")
    result = measure_file(sample)
    writes = [m for m in result["dataMovements"] if m["movementType"] == "W"]
    objects = {w["dataGroupRef"] for w in writes}
    assert "cfp_Data_Movements__c" in objects


def test_measure_sample_flow_entry_detected(project_root):
    sample = project_root / "samples" / "cfp_createCRUDLwithRelatedLists.flow-meta.xml"
    if not sample.exists():
        pytest.skip("Sample flow not found")
    result = measure_file(sample)
    entries = [m for m in result["dataMovements"] if m["movementType"] == "E"]
    assert len(entries) >= 1
    assert any("recordId" in e["name"] for e in entries)


def test_measure_sample_flow_canonical_exit_is_final(project_root):
    sample = project_root / "samples" / "cfp_createCRUDLwithRelatedLists.flow-meta.xml"
    if not sample.exists():
        pytest.skip("Sample flow not found")
    result = measure_file(sample)
    dm = result["dataMovements"]
    assert dm[-1]["name"] == CANONICAL_EXIT_NAME
    assert dm[-1]["dataGroupRef"] == CANONICAL_EXIT_DATA_GROUP_REF


def test_measure_minimal_flow(tmp_path):
    body = LOOKUP_BODY + CREATE_BODY
    xml = make_flow_xml(body=body)
    f = tmp_path / "MinimalFlow.flow-meta.xml"
    f.write_text(xml, encoding="utf-8")
    result = measure_file(f)
    assert result["artifact"]["type"] == "Flow"
    assert result["artifact"]["name"] == "MinimalFlow"
    types = [m["movementType"] for m in result["dataMovements"]]
    assert "R" in types
    assert "W" in types
    assert types[-1] == "X"


def test_measure_empty_flow_only_canonical_exit(tmp_path):
    xml = make_flow_xml(body="")
    f = tmp_path / "EmptyFlow.flow-meta.xml"
    f.write_text(xml, encoding="utf-8")
    result = measure_file(f)
    dm = result["dataMovements"]
    assert len(dm) == 1
    assert dm[0]["name"] == CANONICAL_EXIT_NAME


def test_measure_flow_with_dedup(tmp_path):
    body = """
    <recordCreates>
        <name>createAccount</name>
        <label>createAccount</label>
        <object>Account</object>
    </recordCreates>
    <recordUpdates>
        <name>updateAccount</name>
        <label>updateAccount</label>
        <object>Account</object>
    </recordUpdates>
    """
    xml = make_flow_xml(body=body)
    f = tmp_path / "DedupFlow.flow-meta.xml"
    f.write_text(xml, encoding="utf-8")
    result = measure_file(f)
    writes = [m for m in result["dataMovements"] if m["movementType"] == "W"]
    assert len(writes) == 1
    assert writes[0]["dataGroupRef"] == "Account"


def test_measure_sample_flow_artifact_type(project_root):
    sample = project_root / "samples" / "cfp_createCRUDLwithRelatedLists.flow-meta.xml"
    if not sample.exists():
        pytest.skip("Sample flow not found")
    result = measure_file(sample)
    assert result["artifact"]["type"] == "Flow"


def test_measure_sample_flow_golden_file(project_root):
    """Regression test: full output must match golden expected JSON."""
    sample = project_root / "samples" / "cfp_createCRUDLwithRelatedLists.flow-meta.xml"
    expected_path = project_root / "samples" / "expected" / "cfp_createCRUDLwithRelatedLists.expected.json"
    if not sample.exists() or not expected_path.exists():
        pytest.skip("Sample flow or golden file not found")
    result = measure_file(sample)
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    assert result == expected
