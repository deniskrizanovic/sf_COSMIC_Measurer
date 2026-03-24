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
    expected_path = project_root / "expected" / "cfp_createCRUDLwithRelatedLists.expected.json"
    if not sample.exists() or not expected_path.exists():
        pytest.skip("Sample flow or golden file not found")
    result = measure_file(sample)
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    assert result == expected


def test_measure_flow_includes_screen_entries_and_exits(tmp_path):
    body = """
    <variables>
        <name>selectedAccount</name>
        <dataType>SObject</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Account</objectType>
    </variables>
    <screens>
        <name>ReviewAccount</name>
        <fields>
            <name>acctInput</name>
            <fieldType>InputField</fieldType>
            <fieldText>{!selectedAccount.Name}</fieldText>
        </fields>
        <fields>
            <name>acctDisplay</name>
            <fieldType>DisplayText</fieldType>
            <fieldText>{!selectedAccount.Name}</fieldText>
        </fields>
    </screens>
    """
    xml = make_flow_xml(body=body)
    f = tmp_path / "ScreenFlow.flow-meta.xml"
    f.write_text(xml, encoding="utf-8")

    result = measure_file(f)
    entries = [m for m in result["dataMovements"] if m["movementType"] == "E"]
    exits = [m for m in result["dataMovements"] if m["movementType"] == "X"]
    assert any("Screen input" in e["name"] for e in entries)
    assert any("Screen display" in x["name"] for x in exits)
    assert exits[-1]["name"] == CANONICAL_EXIT_NAME


def test_measure_flow_mixed_preserves_type_order(tmp_path):
    body = """
    <variables>
        <name>selectedAccount</name>
        <dataType>SObject</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Account</objectType>
    </variables>
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
    <screens>
        <name>ReviewData</name>
        <fields>
            <name>acctInput</name>
            <fieldType>InputField</fieldType>
            <fieldText>{!selectedAccount.Name}</fieldText>
        </fields>
        <fields>
            <name>acctDisplay</name>
            <fieldType>DisplayText</fieldType>
            <fieldText>{!selectedAccount.Name}</fieldText>
        </fields>
    </screens>
    """
    xml = make_flow_xml(body=body)
    f = tmp_path / "MixedFlow.flow-meta.xml"
    f.write_text(xml, encoding="utf-8")

    result = measure_file(f)
    types = [m["movementType"] for m in result["dataMovements"]]
    first_r = types.index("R")
    first_w = types.index("W")
    first_x = types.index("X")
    assert first_r > 0
    assert first_w > first_r
    assert first_x > first_w
    assert result["dataMovements"][-1]["name"] == CANONICAL_EXIT_NAME


def test_measure_flow_merges_invocable_apex_from_sample(project_root):
    flow_path = project_root / "samples" / "Program_Validation_Commencement_Process.flow"
    apex_path = project_root / "samples" / "InvokeRunValidation.cls"
    if not flow_path.exists() or not apex_path.exists():
        pytest.skip("Flow/Apex sample files not found")

    result = measure_file(flow_path, apex_search_paths=[project_root / "samples"])
    via_rows = [m for m in result["dataMovements"] if m.get("viaArtifact")]
    assert via_rows, "Expected merged movements from invocable Apex"
    assert any(m["movementType"] in {"E", "R", "X"} for m in via_rows)
    assert all(m["implementationType"] == "apex" for m in via_rows)
    assert "InvokeRunValidation" not in (result.get("invocableApexClassesNotFound") or [])
    assert result["dataMovements"][-1]["name"] == CANONICAL_EXIT_NAME


def test_measure_flow_trigger_entry_precedes_invocable_apex_entries(project_root):
    flow_path = project_root / "samples" / "Program_Validation_Commencement_Process.flow"
    apex_path = project_root / "samples" / "InvokeRunValidation.cls"
    if not flow_path.exists() or not apex_path.exists():
        pytest.skip("Flow/Apex sample files not found")

    result = measure_file(flow_path, apex_search_paths=[project_root / "samples"])
    entries = [m for m in result["dataMovements"] if m["movementType"] == "E"]
    assert entries, "Expected at least one Entry movement"
    assert entries[0]["name"] == "Trigger record (Program__c)"
    assert any(
        m["name"] == "Receive programIds (Program__c)" and m.get("viaArtifact")
        for m in entries[1:]
    )


def test_measure_flow_missing_invocable_apex_class_is_non_fatal(tmp_path):
    xml = make_flow_xml(
        process_type="AutolaunchedFlow",
        body="""
    <actionCalls>
        <name>CallMissing</name>
        <label>Call Missing</label>
        <actionName>ClassThatDoesNotExist</actionName>
        <actionType>apex</actionType>
    </actionCalls>
    """,
    )
    flow_file = tmp_path / "MissingInvocable.flow-meta.xml"
    flow_file.write_text(xml, encoding="utf-8")

    result = measure_file(flow_file, apex_search_paths=[tmp_path])
    assert result["artifact"]["name"] == "MissingInvocable"
    assert result.get("invocableApexClassesNotFound") == ["ClassThatDoesNotExist"]
    assert result["dataMovements"][-1]["name"] == CANONICAL_EXIT_NAME
