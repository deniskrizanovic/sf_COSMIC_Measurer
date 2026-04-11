"""Unit tests for flexipage_parser.py."""

from conftest import make_flexipage_xml
from flexipage_parser import (
    build_path_component_movements,
    build_synthetic_action_entry,
    build_synthetic_page_trigger_entry,
    extract_tab_component_bindings,
    extract_dynamic_related_lists,
    extract_flexipage_metadata,
    extract_highlights_actions,
    extract_path_components,
    extract_record_field_bindings,
    extract_sidebar_component_movements,
    extract_tab_labels,
    extract_tab_bound_component_movements,
    has_highlights_panel,
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


def test_extract_path_components():
    body = """
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentName>runtime_sales_pathassistant:pathAssistant</componentName>
                <identifier>runtime_sales_pathassistant_pathAssistant</identifier>
            </componentInstance>
        </itemInstances>
        <name>header</name>
        <type>Region</type>
    </flexiPageRegions>
    """
    xml = make_flexipage_xml(body=body, sobject_type="WorkOrder")
    root = parse_xml(xml)
    path_components = extract_path_components(root)
    assert len(path_components) == 1
    assert path_components[0].identifier == "runtime_sales_pathassistant_pathAssistant"
    assert path_components[0].region_name == "header"


def test_build_path_component_movements_emits_read_and_display_pair():
    body = """
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentName>runtime_sales_pathassistant:pathAssistant</componentName>
                <identifier>runtime_sales_pathassistant_pathAssistant</identifier>
            </componentInstance>
        </itemInstances>
        <name>header</name>
        <type>Region</type>
    </flexiPageRegions>
    """
    xml = make_flexipage_xml(body=body, sobject_type="WorkOrder")
    root = parse_xml(xml)
    path_components = extract_path_components(root)
    movements = build_path_component_movements("WorkOrder", path_components)
    assert [movement.name for movement in movements] == [
        "Read path state (WorkOrder) (region:header, id:runtime_sales_pathassistant_pathAssistant)",
        "Display path state (WorkOrder) (region:header, id:runtime_sales_pathassistant_pathAssistant)",
    ]
    assert [movement.movement_type for movement in movements] == ["R", "X"]


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


def test_has_highlights_panel():
    body = """
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentName>force:highlightsPanel</componentName>
                <identifier>force_highlightsPanel</identifier>
            </componentInstance>
        </itemInstances>
    </flexiPageRegions>
    """
    xml = make_flexipage_xml(body=body)
    root = parse_xml(xml)
    assert has_highlights_panel(root) is True


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


def test_extract_tab_component_bindings_identifies_lwc_and_aura():
    body = """
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentName>cfp_FunctionalProcessVisualiser</componentName>
                <identifier>c_cfp_FunctionalProcessVisualiser</identifier>
            </componentInstance>
        </itemInstances>
        <name>Facet-visualiser</name>
        <type>Facet</type>
    </flexiPageRegions>
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentName>lst:dynamicRelatedList</componentName>
                <identifier>lst_dynamicRelatedList2</identifier>
            </componentInstance>
        </itemInstances>
        <name>Facet-metadata</name>
        <type>Facet</type>
    </flexiPageRegions>
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>body</name>
                    <value>Facet-visualiser</value>
                </componentInstanceProperties>
                <componentInstanceProperties>
                    <name>title</name>
                    <value>Visualiser</value>
                </componentInstanceProperties>
                <componentName>flexipage:tab</componentName>
                <identifier>flexipage_tab5</identifier>
            </componentInstance>
        </itemInstances>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>body</name>
                    <value>Facet-metadata</value>
                </componentInstanceProperties>
                <componentInstanceProperties>
                    <name>title</name>
                    <value>MetadataView</value>
                </componentInstanceProperties>
                <componentName>flexipage:tab</componentName>
                <identifier>flexipage_tab3</identifier>
            </componentInstance>
        </itemInstances>
    </flexiPageRegions>
    """
    xml = make_flexipage_xml(body=body)
    root = parse_xml(xml)
    bindings = extract_tab_component_bindings(root)

    assert len(bindings) == 2
    visualiser = next(item for item in bindings if item.tab_title == "Visualiser")
    metadata = next(item for item in bindings if item.tab_title == "MetadataView")

    assert visualiser.target_component_name == "cfp_FunctionalProcessVisualiser"
    assert visualiser.target_component_kind == "lwc"
    assert metadata.target_component_name == "lst:dynamicRelatedList"
    assert metadata.target_component_kind == "aura"


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


def test_parse_flexipage_includes_primary_record_edit_entry():
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
                <componentName>force:relatedListSingleContainer</componentName>
                <identifier>force_relatedListSingleContainer</identifier>
            </componentInstance>
        </itemInstances>
    </flexiPageRegions>
    """
    xml = make_flexipage_xml(body=body)
    _, movements, _, _ = parse_flexipage(xml, filename="Sample.flexipage-meta.xml")
    assert any(
        movement.name == "Edit page record (Account)" and movement.movement_type == "E"
        for movement in movements
    )
    assert any(
        movement.name == "Write page record (Account)" and movement.movement_type == "W"
        for movement in movements
    )


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
    assert any(m.name == "Read highlights panel fields (Account)" for m in movements)
    assert any(m.name == "Display highlights panel fields (Account)" for m in movements)


def test_parse_flexipage_includes_path_read_and_display_movements():
    body = """
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentName>runtime_sales_pathassistant:pathAssistant</componentName>
                <identifier>runtime_sales_pathassistant_pathAssistant</identifier>
            </componentInstance>
        </itemInstances>
        <name>header</name>
        <type>Region</type>
    </flexiPageRegions>
    """
    xml = make_flexipage_xml(body=body, sobject_type="WorkOrder")
    _, movements, _, _ = parse_flexipage(xml, filename="WorkOrder.flexipage-meta.xml")
    names_in_order = [movement.name for movement in movements]
    read_name = "Read path state (WorkOrder) (region:header, id:runtime_sales_pathassistant_pathAssistant)"
    display_name = "Display path state (WorkOrder) (region:header, id:runtime_sales_pathassistant_pathAssistant)"
    assert read_name in names_in_order
    assert display_name in names_in_order
    assert names_in_order.index(display_name) == names_in_order.index(read_name) + 1


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


def test_normalize_related_list():
    from flexipage_parser import _normalize_related_list

    # Rule 1: __r -> __c
    name, dg = _normalize_related_list("MyObject__r")
    assert name == "MyObject__c"
    assert dg == "MyObject__c"

    # Rule 2: AttachedContentDocuments -> ContentDocument
    name, dg = _normalize_related_list("AttachedContentDocuments")
    assert name == "ContentDocument"
    assert dg == "ContentDocument"

    # Rule 3: Histories -> parentObjectName_History
    name, dg = _normalize_related_list("Histories", "WorkOrder.Id")
    assert name == "WorkOrder_History"
    assert dg == "WorkOrder_History"

    # Rule 3 fallback: Histories without parent_field_api_name
    name, dg = _normalize_related_list("Histories")
    assert name == "Histories"
    assert dg == "Histories"

    # No rule: standard object
    name, dg = _normalize_related_list("Contacts")
    assert name == "Contacts"
    assert dg == "Contacts"


def test_extract_tab_bound_component_movements_for_supported_components():
    body = """
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>relatedListApiName</name>
                    <value>Contacts</value>
                </componentInstanceProperties>
                <componentName>force:relatedListSingleContainer</componentName>
                <identifier>rlContacts</identifier>
            </componentInstance>
        </itemInstances>
        <name>Facet-list</name>
        <type>Facet</type>
    </flexiPageRegions>
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>flowName</name>
                    <value>SampleFlow</value>
                </componentInstanceProperties>
                <componentName>flowruntime:interview</componentName>
                <identifier>flowInterview</identifier>
            </componentInstance>
        </itemInstances>
        <name>Facet-flow</name>
        <type>Facet</type>
    </flexiPageRegions>
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>lookupFieldName</name>
                    <value>WorkOrder.Id</value>
                </componentInstanceProperties>
                <componentInstanceProperties>
                    <name>titleFieldName</name>
                    <value>Access Issue Details</value>
                </componentInstanceProperties>
                <componentName>console:relatedRecord</componentName>
                <identifier>relatedRecord</identifier>
            </componentInstance>
        </itemInstances>
        <name>Facet-related</name>
        <type>Facet</type>
    </flexiPageRegions>
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties><name>body</name><value>Facet-list</value></componentInstanceProperties>
                <componentInstanceProperties><name>title</name><value>ContactsTab</value></componentInstanceProperties>
                <componentName>flexipage:tab</componentName>
                <identifier>tabContacts</identifier>
            </componentInstance>
        </itemInstances>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties><name>body</name><value>Facet-flow</value></componentInstanceProperties>
                <componentInstanceProperties><name>title</name><value>FlowTab</value></componentInstanceProperties>
                <componentName>flexipage:tab</componentName>
                <identifier>tabFlow</identifier>
            </componentInstance>
        </itemInstances>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties><name>body</name><value>Facet-related</value></componentInstanceProperties>
                <componentInstanceProperties><name>title</name><value>RelatedTab</value></componentInstanceProperties>
                <componentName>flexipage:tab</componentName>
                <identifier>tabRelated</identifier>
            </componentInstance>
        </itemInstances>
    </flexiPageRegions>
    """
    xml = make_flexipage_xml(body=body, sobject_type="WorkOrder")
    root = parse_xml(xml)
    movements, warnings = extract_tab_bound_component_movements(root, "WorkOrder")

    movement_names = [movement.name for movement in movements]
    assert "Read related list Contacts | tab:ContactsTab" in movement_names
    assert "Display related list Contacts | tab:ContactsTab" in movement_names
    assert "Display flow interview SampleFlow | tab:FlowTab" in movement_names
    assert "Read related record Access Issue Details | tab:RelatedTab" in movement_names
    assert "Display related record Access Issue Details | tab:RelatedTab" in movement_names
    assert any("inferred as X only" in warning for warning in warnings)


def test_related_record_movements_are_paired_in_order():
    body = """
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties><name>lookupFieldName</name><value>WorkOrder.Id</value></componentInstanceProperties>
                <componentInstanceProperties><name>titleFieldName</name><value>First Details</value></componentInstanceProperties>
                <componentName>console:relatedRecord</componentName>
                <identifier>relatedRecord1</identifier>
            </componentInstance>
        </itemInstances>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties><name>lookupFieldName</name><value>WorkOrder.Id</value></componentInstanceProperties>
                <componentInstanceProperties><name>titleFieldName</name><value>Second Details</value></componentInstanceProperties>
                <componentName>console:relatedRecord</componentName>
                <identifier>relatedRecord2</identifier>
            </componentInstance>
        </itemInstances>
        <name>Facet-related</name>
        <type>Facet</type>
    </flexiPageRegions>
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties><name>body</name><value>Facet-related</value></componentInstanceProperties>
                <componentInstanceProperties><name>title</name><value>RelatedTab</value></componentInstanceProperties>
                <componentName>flexipage:tab</componentName>
                <identifier>tabRelated</identifier>
            </componentInstance>
        </itemInstances>
    </flexiPageRegions>
    """
    xml = make_flexipage_xml(body=body, sobject_type="WorkOrder")
    root = parse_xml(xml)
    movements, _ = extract_tab_bound_component_movements(root, "WorkOrder")

    names_in_order = [movement.name for movement in movements]
    assert names_in_order == [
        "Read related record First Details | tab:RelatedTab",
        "Display related record First Details | tab:RelatedTab",
        "Read related record Second Details | tab:RelatedTab",
        "Display related record Second Details | tab:RelatedTab",
    ]


def test_extract_sidebar_component_movements_for_related_record():
    body = """
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties><name>lookupFieldName</name><value>Case.Id</value></componentInstanceProperties>
                <componentInstanceProperties><name>titleFieldName</name><value>Request Details</value></componentInstanceProperties>
                <componentName>console:relatedRecord</componentName>
                <identifier>sidebarRelatedRecord</identifier>
            </componentInstance>
        </itemInstances>
        <name>sidebar</name>
        <type>Region</type>
    </flexiPageRegions>
    """
    xml = make_flexipage_xml(body=body, sobject_type="WorkOrder")
    root = parse_xml(xml)
    movements, warnings = extract_sidebar_component_movements(root, "WorkOrder")

    names_in_order = [movement.name for movement in movements]
    assert names_in_order == [
        "Read related record Request Details",
        "Display related record Request Details",
    ]
    assert [movement.data_group_ref for movement in movements] == ["Case", "Case"]
    assert warnings == []


def test_related_record_data_group_uses_lookup_target_object():
    body = """
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties><name>lookupFieldName</name><value>WorkOrder.CaseId</value></componentInstanceProperties>
                <componentInstanceProperties><name>titleFieldName</name><value>Request Details</value></componentInstanceProperties>
                <componentName>console:relatedRecord</componentName>
                <identifier>relatedRecordCase</identifier>
            </componentInstance>
        </itemInstances>
        <name>Facet-related</name>
        <type>Facet</type>
    </flexiPageRegions>
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties><name>body</name><value>Facet-related</value></componentInstanceProperties>
                <componentInstanceProperties><name>title</name><value>RelatedTab</value></componentInstanceProperties>
                <componentName>flexipage:tab</componentName>
                <identifier>tabRelated</identifier>
            </componentInstance>
        </itemInstances>
    </flexiPageRegions>
    """
    xml = make_flexipage_xml(body=body, sobject_type="WorkOrder")
    root = parse_xml(xml)
    movements, _ = extract_tab_bound_component_movements(root, "WorkOrder")
    assert [movement.data_group_ref for movement in movements] == ["Case", "Case"]
