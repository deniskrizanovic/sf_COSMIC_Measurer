"""Unit tests for flow_parser.py XML parsing and movement extraction."""

import pytest

from conftest import make_flow_xml
from flow_parser import (
    InvocableApexCall,
    VariableInfo,
    extract_flow_metadata,
    extract_variables,
    find_entries,
    find_exits,
    find_invocable_apex_calls,
    find_record_lookups,
    find_record_mutations,
    find_screen_movements,
    parse_flow,
    parse_flow_with_invocables,
    parse_xml,
)


# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------

def test_extract_flow_name_from_label():
    xml = make_flow_xml(label="My Screen Flow")
    root = parse_xml(xml)
    meta = extract_flow_metadata(root, filename="MyFlow.flow-meta.xml")
    assert meta.name == "MyFlow"
    assert meta.label == "My Screen Flow"


def test_extract_flow_name_fallback_to_filename():
    xml = make_flow_xml(label="")
    root = parse_xml(xml)
    meta = extract_flow_metadata(root, filename="FallbackFlow.flow-meta.xml")
    assert meta.name == "FallbackFlow"


def test_extract_process_type_screen_flow():
    xml = make_flow_xml(process_type="Flow")
    root = parse_xml(xml)
    meta = extract_flow_metadata(root)
    assert meta.process_type == "Flow"


def test_extract_process_type_autolaunched():
    xml = make_flow_xml(process_type="AutolaunchedFlow")
    root = parse_xml(xml)
    meta = extract_flow_metadata(root)
    assert meta.process_type == "AutolaunchedFlow"


def test_extract_api_version():
    xml = make_flow_xml(api_version="62.0")
    root = parse_xml(xml)
    meta = extract_flow_metadata(root)
    assert meta.api_version == "62.0"


def test_extract_flow_status():
    xml = make_flow_xml(status="Draft")
    root = parse_xml(xml)
    meta = extract_flow_metadata(root)
    assert meta.status == "Draft"


def test_extract_record_triggered_metadata():
    body = """
    <start>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <triggerType>RecordAfterSave</triggerType>
        <object>Account</object>
    </start>
    """
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Flow xmlns="http://soap.sforce.com/2006/04/metadata">\n'
        '    <apiVersion>66.0</apiVersion>\n'
        '    <label>TriggerFlow</label>\n'
        '    <processType>AutolaunchedFlow</processType>\n'
        '    <status>Active</status>\n'
        f'{body}'
        '</Flow>\n'
    )
    root = parse_xml(xml)
    meta = extract_flow_metadata(root)
    assert meta.trigger_type == "RecordAfterSave"
    assert meta.trigger_object == "Account"


# ---------------------------------------------------------------------------
# Reads (recordLookups)
# ---------------------------------------------------------------------------

LOOKUP_BODY = """
    <recordLookups>
        <name>getFunctionalProcess</name>
        <label>getFunctionalProcess</label>
        <object>cfp_FunctionalProcess__c</object>
        <getFirstRecordOnly>true</getFirstRecordOnly>
    </recordLookups>
"""

MULTI_LOOKUP_BODY = """
    <recordLookups>
        <name>getAccounts</name>
        <label>getAccounts</label>
        <object>Account</object>
    </recordLookups>
    <recordLookups>
        <name>getContacts</name>
        <label>getContacts</label>
        <object>Contact</object>
    </recordLookups>
    <recordLookups>
        <name>getAccountsAgain</name>
        <label>getAccountsAgain</label>
        <object>Account</object>
    </recordLookups>
"""


def test_find_reads_single_record_lookup():
    xml = make_flow_xml(body=LOOKUP_BODY)
    root = parse_xml(xml)
    reads = find_record_lookups(root)
    assert len(reads) == 1
    assert reads[0].movement_type == "R"


def test_find_reads_extracts_object_name():
    xml = make_flow_xml(body=LOOKUP_BODY)
    root = parse_xml(xml)
    reads = find_record_lookups(root)
    assert reads[0].data_group_ref == "cfp_FunctionalProcess__c"


def test_find_reads_extracts_label_as_name():
    xml = make_flow_xml(body=LOOKUP_BODY)
    root = parse_xml(xml)
    reads = find_record_lookups(root)
    assert "getFunctionalProcess" in reads[0].name


def test_find_reads_multiple_lookups():
    xml = make_flow_xml(body=MULTI_LOOKUP_BODY)
    root = parse_xml(xml)
    reads = find_record_lookups(root)
    assert len(reads) == 3
    objects = [r.data_group_ref for r in reads]
    assert objects == ["Account", "Contact", "Account"]


def test_find_reads_none_present_returns_empty():
    xml = make_flow_xml(body="")
    root = parse_xml(xml)
    reads = find_record_lookups(root)
    assert reads == []


def test_find_reads_skips_lookup_without_object():
    body = """
    <recordLookups>
        <name>badLookup</name>
        <label>badLookup</label>
    </recordLookups>
    """
    xml = make_flow_xml(body=body)
    root = parse_xml(xml)
    reads = find_record_lookups(root)
    assert reads == []


def test_find_reads_from_sample_flow(project_root):
    sample = project_root / "samples" / "cfp_createCRUDLwithRelatedLists.flow-meta.xml"
    if not sample.exists():
        pytest.skip("Sample flow not found")
    source = sample.read_text(encoding="utf-8")
    root = parse_xml(source)
    reads = find_record_lookups(root)
    objects = {r.data_group_ref for r in reads}
    assert "cfp_FunctionalProcess__c" in objects
    assert "cfp_DataGroups__c" in objects


# ---------------------------------------------------------------------------
# Writes (recordCreates / recordUpdates / recordDeletes)
# ---------------------------------------------------------------------------

CREATE_WITH_OBJECT_BODY = """
    <recordCreates>
        <name>createAccount</name>
        <label>createAccount</label>
        <object>Account</object>
    </recordCreates>
"""

CREATE_WITH_INPUT_REF_BODY = """
    <variables>
        <name>DMsToInsert</name>
        <dataType>SObject</dataType>
        <isCollection>true</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>cfp_Data_Movements__c</objectType>
    </variables>
    <recordCreates>
        <name>createDMs</name>
        <label>createDMs</label>
        <inputReference>DMsToInsert</inputReference>
    </recordCreates>
"""

UPDATE_BODY = """
    <recordUpdates>
        <name>updateCase</name>
        <label>updateCase</label>
        <object>Case</object>
    </recordUpdates>
"""

DELETE_BODY = """
    <recordDeletes>
        <name>deleteOldLogs</name>
        <label>deleteOldLogs</label>
        <object>Log__c</object>
    </recordDeletes>
"""


def test_find_writes_record_create_with_object():
    xml = make_flow_xml(body=CREATE_WITH_OBJECT_BODY)
    root = parse_xml(xml)
    variables = extract_variables(root)
    writes = find_record_mutations(root, variables)
    assert len(writes) == 1
    assert writes[0].data_group_ref == "Account"
    assert writes[0].movement_type == "W"
    assert "Create" in writes[0].name


def test_find_writes_record_create_with_input_reference():
    xml = make_flow_xml(body=CREATE_WITH_INPUT_REF_BODY)
    root = parse_xml(xml)
    variables = extract_variables(root)
    writes = find_record_mutations(root, variables)
    assert len(writes) == 1
    assert writes[0].data_group_ref == "cfp_Data_Movements__c"


def test_find_writes_record_update_with_object():
    xml = make_flow_xml(body=UPDATE_BODY)
    root = parse_xml(xml)
    variables = extract_variables(root)
    writes = find_record_mutations(root, variables)
    assert len(writes) == 1
    assert writes[0].data_group_ref == "Case"
    assert "Update" in writes[0].name


def test_find_writes_record_delete():
    xml = make_flow_xml(body=DELETE_BODY)
    root = parse_xml(xml)
    variables = extract_variables(root)
    writes = find_record_mutations(root, variables)
    assert len(writes) == 1
    assert writes[0].data_group_ref == "Log__c"
    assert "Delete" in writes[0].name


def test_find_writes_none_present_returns_empty():
    xml = make_flow_xml(body="")
    root = parse_xml(xml)
    variables = extract_variables(root)
    writes = find_record_mutations(root, variables)
    assert writes == []


def test_find_writes_unresolvable_input_reference():
    body = """
    <recordCreates>
        <name>createSomething</name>
        <label>createSomething</label>
        <inputReference>nonExistentVar</inputReference>
    </recordCreates>
    """
    xml = make_flow_xml(body=body)
    root = parse_xml(xml)
    variables = extract_variables(root)
    writes = find_record_mutations(root, variables)
    assert len(writes) == 1
    assert writes[0].data_group_ref == "Unknown"


def test_find_writes_from_sample_flow(project_root):
    sample = project_root / "samples" / "cfp_createCRUDLwithRelatedLists.flow-meta.xml"
    if not sample.exists():
        pytest.skip("Sample flow not found")
    source = sample.read_text(encoding="utf-8")
    root = parse_xml(source)
    variables = extract_variables(root)
    writes = find_record_mutations(root, variables)
    objects = {w.data_group_ref for w in writes}
    assert "cfp_Data_Movements__c" in objects


# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------

VARIABLES_BODY = """
    <variables>
        <name>inputRecord</name>
        <dataType>SObject</dataType>
        <isCollection>false</isCollection>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
        <objectType>Account</objectType>
    </variables>
    <variables>
        <name>outputRecord</name>
        <dataType>SObject</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>true</isOutput>
        <objectType>Contact</objectType>
    </variables>
    <variables>
        <name>recordId</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
    <variables>
        <name>internalVar</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
    </variables>
"""


def test_extract_variables_input():
    xml = make_flow_xml(body=VARIABLES_BODY)
    root = parse_xml(xml)
    variables = extract_variables(root)
    assert variables["inputRecord"].is_input is True
    assert variables["inputRecord"].is_output is False


def test_extract_variables_output():
    xml = make_flow_xml(body=VARIABLES_BODY)
    root = parse_xml(xml)
    variables = extract_variables(root)
    assert variables["outputRecord"].is_output is True
    assert variables["outputRecord"].is_input is False


def test_extract_variables_with_object_type():
    xml = make_flow_xml(body=VARIABLES_BODY)
    root = parse_xml(xml)
    variables = extract_variables(root)
    assert variables["inputRecord"].object_type == "Account"
    assert variables["outputRecord"].object_type == "Contact"


def test_extract_variables_primitive_types():
    xml = make_flow_xml(body=VARIABLES_BODY)
    root = parse_xml(xml)
    variables = extract_variables(root)
    assert variables["recordId"].data_type == "String"
    assert variables["recordId"].object_type is None


def test_extract_variables_input_output():
    body = """
    <variables>
        <name>bothWays</name>
        <dataType>SObject</dataType>
        <isCollection>false</isCollection>
        <isInput>true</isInput>
        <isOutput>true</isOutput>
        <objectType>Opportunity</objectType>
    </variables>
    """
    xml = make_flow_xml(body=body)
    root = parse_xml(xml)
    variables = extract_variables(root)
    assert variables["bothWays"].is_input is True
    assert variables["bothWays"].is_output is True


# ---------------------------------------------------------------------------
# Entries
# ---------------------------------------------------------------------------

def test_find_entries_from_input_variables():
    xml = make_flow_xml(body=VARIABLES_BODY)
    root = parse_xml(xml)
    meta = extract_flow_metadata(root)
    variables = extract_variables(root)
    entries = find_entries(root, meta, variables)
    sobject_entries = [e for e in entries if "Account" in e.data_group_ref]
    assert len(sobject_entries) == 1
    assert sobject_entries[0].movement_type == "E"


def test_find_entries_skips_primitive_non_record_id():
    body = """
    <variables>
        <name>someFlag</name>
        <dataType>Boolean</dataType>
        <isCollection>false</isCollection>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
    """
    xml = make_flow_xml(body=body)
    root = parse_xml(xml)
    meta = extract_flow_metadata(root)
    variables = extract_variables(root)
    entries = find_entries(root, meta, variables)
    assert entries == []


def test_find_entries_record_triggered_from_start():
    body = """
    <start>
        <locationX>0</locationX>
        <locationY>0</locationY>
        <triggerType>RecordAfterSave</triggerType>
        <object>Case</object>
    </start>
    """
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Flow xmlns="http://soap.sforce.com/2006/04/metadata">\n'
        '    <apiVersion>66.0</apiVersion>\n'
        '    <label>TriggerFlow</label>\n'
        '    <processType>AutolaunchedFlow</processType>\n'
        '    <status>Active</status>\n'
        f'{body}'
        '</Flow>\n'
    )
    root = parse_xml(xml)
    meta = extract_flow_metadata(root)
    variables = extract_variables(root)
    entries = find_entries(root, meta, variables)
    assert len(entries) == 1
    assert entries[0].data_group_ref == "Case"
    assert entries[0].movement_type == "E"


def test_find_entries_record_id_infers_object():
    body = """
    <variables>
        <name>recordId</name>
        <dataType>String</dataType>
        <isCollection>false</isCollection>
        <isInput>true</isInput>
        <isOutput>false</isOutput>
    </variables>
    <recordLookups>
        <name>getAccount</name>
        <label>getAccount</label>
        <object>Account</object>
        <filterLogic>and</filterLogic>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>recordId</elementReference>
            </value>
        </filters>
    </recordLookups>
    """
    xml = make_flow_xml(body=body)
    root = parse_xml(xml)
    meta = extract_flow_metadata(root)
    variables = extract_variables(root)
    entries = find_entries(root, meta, variables)
    record_id_entries = [e for e in entries if "recordId" in e.name]
    assert len(record_id_entries) == 1
    assert record_id_entries[0].data_group_ref == "Account"


# ---------------------------------------------------------------------------
# Exits
# ---------------------------------------------------------------------------

def test_find_exits_from_output_variables():
    xml = make_flow_xml(body=VARIABLES_BODY)
    root = parse_xml(xml)
    variables = extract_variables(root)
    exits = find_exits(variables)
    assert len(exits) == 1
    assert exits[0].data_group_ref == "Contact"
    assert exits[0].movement_type == "X"


def test_find_exits_empty_when_no_outputs():
    xml = make_flow_xml(body="")
    root = parse_xml(xml)
    variables = extract_variables(root)
    exits = find_exits(variables)
    assert exits == []


# ---------------------------------------------------------------------------
# Screens (Entry/Exit from screen interactions)
# ---------------------------------------------------------------------------

def test_find_screen_entries_per_data_group():
    body = """
    <variables>
        <name>selectedAccount</name>
        <dataType>SObject</dataType>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Account</objectType>
    </variables>
    <screens>
        <name>AccountScreen</name>
        <fields>
            <name>accountInput</name>
            <fieldType>InputField</fieldType>
            <fieldText>&lt;p&gt;{!selectedAccount.Name}&lt;/p&gt;</fieldText>
        </fields>
    </screens>
    """
    xml = make_flow_xml(body=body)
    root = parse_xml(xml)
    variables = extract_variables(root)
    screen_entries, _ = find_screen_movements(root, variables)
    assert len(screen_entries) == 1
    assert screen_entries[0].movement_type == "E"
    assert screen_entries[0].data_group_ref == "Account"


def test_find_screen_exits_per_data_group():
    body = """
    <recordLookups>
        <name>getAccounts</name>
        <object>Account</object>
    </recordLookups>
    <recordLookups>
        <name>getContacts</name>
        <object>Contact</object>
    </recordLookups>
    <screens>
        <name>ReviewData</name>
        <fields>
            <name>accountsTable</name>
            <fieldType>ComponentInstance</fieldType>
            <inputParameters>
                <name>tableData</name>
                <value>
                    <elementReference>getAccounts</elementReference>
                </value>
            </inputParameters>
        </fields>
        <fields>
            <name>contactsTable</name>
            <fieldType>ComponentInstance</fieldType>
            <inputParameters>
                <name>tableData</name>
                <value>
                    <elementReference>getContacts</elementReference>
                </value>
            </inputParameters>
        </fields>
    </screens>
    """
    xml = make_flow_xml(body=body)
    root = parse_xml(xml)
    variables = extract_variables(root)
    _, screen_exits = find_screen_movements(root, variables)
    assert {m.data_group_ref for m in screen_exits} == {"Account", "Contact"}


def test_display_only_screen_counts_as_exit():
    body = """
    <variables>
        <name>selectedAccount</name>
        <dataType>SObject</dataType>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Account</objectType>
    </variables>
    <screens>
        <name>ConfirmScreen</name>
        <fields>
            <name>summaryText</name>
            <fieldType>DisplayText</fieldType>
            <fieldText>&lt;p&gt;Selected: {!selectedAccount.Name}&lt;/p&gt;</fieldText>
        </fields>
    </screens>
    """
    xml = make_flow_xml(body=body)
    root = parse_xml(xml)
    variables = extract_variables(root)
    screen_entries, screen_exits = find_screen_movements(root, variables)
    assert screen_entries == []
    assert len(screen_exits) == 1
    assert screen_exits[0].data_group_ref == "Account"


def test_screen_dedups_same_data_group_within_screen():
    body = """
    <variables>
        <name>selectedAccount</name>
        <dataType>SObject</dataType>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Account</objectType>
    </variables>
    <screens>
        <name>AccountScreen</name>
        <fields>
            <name>summary1</name>
            <fieldType>DisplayText</fieldType>
            <fieldText>{!selectedAccount.Name}</fieldText>
        </fields>
        <fields>
            <name>summary2</name>
            <fieldType>DisplayText</fieldType>
            <fieldText>{!selectedAccount.Id}</fieldText>
        </fields>
    </screens>
    """
    xml = make_flow_xml(body=body)
    root = parse_xml(xml)
    variables = extract_variables(root)
    _, screen_exits = find_screen_movements(root, variables)
    assert len(screen_exits) == 1
    assert screen_exits[0].data_group_ref == "Account"


def test_screen_skips_unresolved_primitive_refs():
    body = """
    <variables>
        <name>plainText</name>
        <dataType>String</dataType>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
    </variables>
    <screens>
        <name>PrimitiveOnlyScreen</name>
        <fields>
            <name>summary</name>
            <fieldType>DisplayText</fieldType>
            <fieldText>{!plainText}</fieldText>
        </fields>
    </screens>
    """
    xml = make_flow_xml(body=body)
    root = parse_xml(xml)
    variables = extract_variables(root)
    screen_entries, screen_exits = find_screen_movements(root, variables)
    assert screen_entries == []
    assert screen_exits == []


def test_screen_handles_multiple_screens_accumulation():
    body = """
    <variables>
        <name>selectedAccount</name>
        <dataType>SObject</dataType>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Account</objectType>
    </variables>
    <variables>
        <name>selectedContact</name>
        <dataType>SObject</dataType>
        <isInput>false</isInput>
        <isOutput>false</isOutput>
        <objectType>Contact</objectType>
    </variables>
    <screens>
        <name>ScreenA</name>
        <fields>
            <name>a1</name>
            <fieldType>DisplayText</fieldType>
            <fieldText>{!selectedAccount.Name}</fieldText>
        </fields>
    </screens>
    <screens>
        <name>ScreenB</name>
        <fields>
            <name>b1</name>
            <fieldType>DisplayText</fieldType>
            <fieldText>{!selectedContact.Name}</fieldText>
        </fields>
    </screens>
    """
    xml = make_flow_xml(body=body)
    root = parse_xml(xml)
    variables = extract_variables(root)
    _, screen_exits = find_screen_movements(root, variables)
    assert {m.data_group_ref for m in screen_exits} == {"Account", "Contact"}


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_parse_empty_xml_raises():
    with pytest.raises(ValueError, match="Invalid XML"):
        parse_xml("")


def test_parse_invalid_xml_raises():
    with pytest.raises(ValueError, match="Invalid XML"):
        parse_xml("<not-closed>")


# ---------------------------------------------------------------------------
# Full parse_flow
# ---------------------------------------------------------------------------

def test_parse_flow_minimal():
    body = LOOKUP_BODY + CREATE_WITH_OBJECT_BODY
    xml = make_flow_xml(body=body)
    meta, movements = parse_flow(xml, filename="Test.flow-meta.xml")
    assert meta.name == "Test"
    types = [m.movement_type for m in movements]
    assert "R" in types
    assert "W" in types


def test_parse_flow_empty_returns_no_movements():
    xml = make_flow_xml(body="")
    meta, movements = parse_flow(xml)
    assert movements == []


def test_find_invocable_apex_calls_detects_action_call():
    body = """
    <actionCalls>
        <name>CallValidation</name>
        <label>Call Validation</label>
        <actionName>InvokeRunValidation</actionName>
        <actionType>apex</actionType>
    </actionCalls>
    """
    xml = make_flow_xml(body=body)
    root = parse_xml(xml)
    calls = find_invocable_apex_calls(root)
    assert len(calls) == 1
    call = calls[0]
    assert isinstance(call, InvocableApexCall)
    assert call.action_name == "InvokeRunValidation"
    assert call.element_name == "CallValidation"


def test_parse_flow_with_invocables_returns_calls():
    body = """
    <actionCalls>
        <name>CallValidation</name>
        <label>Call Validation</label>
        <actionName>InvokeRunValidation</actionName>
        <actionType>apex</actionType>
    </actionCalls>
    <recordLookups>
        <name>getAccount</name>
        <label>getAccount</label>
        <object>Account</object>
    </recordLookups>
    """
    xml = make_flow_xml(body=body)
    meta, movements, calls = parse_flow_with_invocables(xml, filename="MyFlow.flow-meta.xml")
    assert meta.name == "MyFlow"
    assert any(m.movement_type == "R" for m in movements)
    assert len(calls) == 1
    assert calls[0].action_name == "InvokeRunValidation"
