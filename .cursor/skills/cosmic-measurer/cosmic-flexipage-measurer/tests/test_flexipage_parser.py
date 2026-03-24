"""Unit tests for flexipage_parser.py."""

from conftest import make_flexipage_xml
from flexipage_parser import (
    build_synthetic_action_entry,
    build_synthetic_page_trigger_entry,
    extract_dynamic_related_lists,
    extract_flexipage_metadata,
    extract_highlights_actions,
    extract_record_field_bindings,
    extract_tab_labels,
    find_exits_from_page,
    find_reads_from_page,
    parse_flexipage,
    parse_xml,
)


def test_extract_metadata():
    xml = make_flexipage_xml(master_label="My Page", sobject_type="cfp_FunctionalProcess__c")
    root = parse_xml(xml)
    metadata = extract_flexipage_metadata(root, filename="MyPage.flexipage-meta.xml")
    assert metadata.name == "MyPage"
    assert metadata.master_label == "My Page"
    assert metadata.sobject_type == "cfp_FunctionalProcess__c"
    assert metadata.page_type == "RecordPage"


def test_extract_record_field_bindings():
    body = """
    <flexiPageRegions>
        <itemInstances>
            <fieldInstance>
                <fieldItem>Record.Name</fieldItem>
            </fieldInstance>
        </itemInstances>
        <itemInstances>
            <fieldInstance>
                <fieldItem>Record.Custom__c</fieldItem>
            </fieldInstance>
        </itemInstances>
    </flexiPageRegions>
    """
    xml = make_flexipage_xml(body=body)
    root = parse_xml(xml)
    fields = extract_record_field_bindings(root)
    assert fields == ["Record.Name", "Record.Custom__c"]


def test_extract_dynamic_related_lists():
    body = """
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>relatedListApiName</name>
                    <value>Contacts</value>
                </componentInstanceProperties>
                <componentInstanceProperties>
                    <name>parentFieldApiName</name>
                    <value>Account.Id</value>
                </componentInstanceProperties>
                <componentName>lst:dynamicRelatedList</componentName>
                <identifier>lst_dynamicRelatedList</identifier>
            </componentInstance>
        </itemInstances>
    </flexiPageRegions>
    """
    xml = make_flexipage_xml(body=body)
    root = parse_xml(xml)
    related_lists = extract_dynamic_related_lists(root)
    assert len(related_lists) == 1
    assert related_lists[0].related_list_api_name == "Contacts"
    assert related_lists[0].parent_field_api_name == "Account.Id"


def test_extract_highlights_actions():
    body = """
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>actionNames</name>
                    <valueList>
                        <valueListItems><value>New</value></valueListItems>
                        <valueListItems><value>Account.Create_Something</value></valueListItems>
                    </valueList>
                </componentInstanceProperties>
                <componentName>force:highlightsPanel</componentName>
                <identifier>force_highlightsPanel</identifier>
            </componentInstance>
        </itemInstances>
    </flexiPageRegions>
    """
    xml = make_flexipage_xml(body=body)
    root = parse_xml(xml)
    actions = extract_highlights_actions(root)
    assert actions == ["New", "Account.Create_Something"]


def test_extract_tab_labels():
    body = """
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>title</name>
                    <value>Listview</value>
                </componentInstanceProperties>
                <componentName>flexipage:tab</componentName>
                <identifier>tab1</identifier>
            </componentInstance>
        </itemInstances>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>title</name>
                    <value>MetadataView</value>
                </componentInstanceProperties>
                <componentName>flexipage:tab</componentName>
                <identifier>tab2</identifier>
            </componentInstance>
        </itemInstances>
    </flexiPageRegions>
    """
    xml = make_flexipage_xml(body=body)
    root = parse_xml(xml)
    labels = extract_tab_labels(root)
    assert labels == ["Listview", "MetadataView"]


def test_find_reads_and_exits_from_page():
    reads = find_reads_from_page(
        "Account",
        ["Record.Name"],
        [],
    )
    exits = find_exits_from_page(
        "Account",
        ["Record.Name"],
        [],
    )
    assert len(reads) == 1
    assert len(exits) == 1
    assert reads[0].movement_type == "R"
    assert exits[0].movement_type == "X"


def test_parse_flexipage():
    body = """
    <flexiPageRegions>
        <itemInstances>
            <fieldInstance>
                <fieldItem>Record.Name</fieldItem>
            </fieldInstance>
        </itemInstances>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>actionNames</name>
                    <valueList>
                        <valueListItems><value>New</value></valueListItems>
                    </valueList>
                </componentInstanceProperties>
                <componentName>force:highlightsPanel</componentName>
                <identifier>force_highlightsPanel</identifier>
            </componentInstance>
        </itemInstances>
    </flexiPageRegions>
    """
    xml = make_flexipage_xml(body=body)
    metadata, movements, actions, tab_labels = parse_flexipage(
        xml, filename="Sample.flexipage-meta.xml"
    )
    assert metadata.name == "Sample"
    assert actions == ["New"]
    assert tab_labels == []
    assert any(m.movement_type == "R" for m in movements)
    assert any(m.movement_type == "X" for m in movements)


def test_build_synthetic_page_trigger_entry():
    entry = build_synthetic_page_trigger_entry("Account")
    assert entry.movement_type == "E"
    assert entry.data_group_ref == "Account"
    assert entry.name == "Open record page (Account)"


def test_build_synthetic_action_entry():
    entry = build_synthetic_action_entry("Delete", "Account")
    assert entry.movement_type == "E"
    assert entry.data_group_ref == "Account"
    assert entry.name == "Trigger action Delete"
