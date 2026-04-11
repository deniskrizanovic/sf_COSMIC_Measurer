"""CLI tests for measure_flexipage.py."""

import json
import sys

import measure_flexipage
from conftest import make_flexipage_xml


def _write_flexipage(tmp_path, name="Test.flexipage-meta.xml", body=""):
    xml = make_flexipage_xml(body=body)
    path = tmp_path / name
    path.write_text(xml, encoding="utf-8")
    return path


def test_cli_json_stdout(monkeypatch, capsys, tmp_path):
    body = """
    <flexiPageRegions>
        <itemInstances><fieldInstance><fieldItem>Record.Name</fieldItem></fieldInstance></itemInstances>
    </flexiPageRegions>
    """
    page_file = _write_flexipage(tmp_path, body=body)
    monkeypatch.setattr(sys, "argv", ["measure_flexipage", str(page_file), "--json"])
    assert measure_flexipage.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["artifact"]["type"] == "FlexiPage"
    assert payload["dataMovements"]
    assert payload["dataMovements"][0]["movementType"] == "E"


def test_cli_output_file(monkeypatch, capsys, tmp_path):
    page_file = _write_flexipage(tmp_path)
    output_path = tmp_path / "out.json"
    monkeypatch.setattr(sys, "argv", ["measure_flexipage", str(page_file), "-o", str(output_path)])
    assert measure_flexipage.main() == 0
    assert output_path.exists()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["artifact"]["type"] == "FlexiPage"
    assert "Functional size" in capsys.readouterr().out


def test_cli_missing_file(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["measure_flexipage", "/no/such/file.flexipage-meta.xml"])
    assert measure_flexipage.main() == 1
    assert "not found" in capsys.readouterr().err


def test_cli_invalid_xml(monkeypatch, capsys, tmp_path):
    page_file = tmp_path / "Bad.flexipage-meta.xml"
    page_file.write_text("<broken>", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["measure_flexipage", str(page_file), "--json"])
    assert measure_flexipage.main() == 1
    assert "Invalid XML" in capsys.readouterr().err


def test_cli_sample_flexipage(monkeypatch, capsys, project_root):
    sample = project_root / "samples" / "flexipages" / "cfp_FunctionalProcess_Record_Page.flexipage-meta.xml"
    if not sample.exists():
        return
    monkeypatch.setattr(sys, "argv", ["measure_flexipage", str(sample), "--json"])
    assert measure_flexipage.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["artifact"]["type"] == "FlexiPage"
    assert len(payload["dataMovements"]) >= 4
    assert payload["dataMovements"][0]["name"].startswith("Open record page")
    warnings = payload.get("traversalWarnings") or []
    assert any("Tab-aware notes:" in item for item in warnings)
    assert any(
        "Visualiser -> lwc(cfp_FunctionalProcessVisualiser)" in item
        for item in warnings
    )
    assert any(
        "Delegate tab-bound LWCs to lwc-measurer" in item
        for item in warnings
    )
    assert "lwcCandidateMeasurements" not in payload


def test_cli_sample_flexipage_matches_golden(monkeypatch, capsys, project_root):
    sample = project_root / "samples" / "flexipages" / "cfp_FunctionalProcess_Record_Page.flexipage-meta.xml"
    expected_path = (
        project_root
        / "expected"
        / "expected"
        / "cfp_FunctionalProcess_Record_Page.flexipage.expected.json"
    )
    if not sample.exists() or not expected_path.exists():
        return
    monkeypatch.setattr(sys, "argv", ["measure_flexipage", str(sample), "--json"])
    assert measure_flexipage.main() == 0
    payload = json.loads(capsys.readouterr().out)
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    assert payload["artifact"] == expected["artifact"]
    assert payload["dataMovements"][-1]["name"] == "Errors/notifications"
    assert len(payload["dataMovements"]) >= len(expected["dataMovements"])


def test_cli_disable_synthetic_trigger_e(monkeypatch, capsys, tmp_path):
    body = """
    <flexiPageRegions>
        <itemInstances><fieldInstance><fieldItem>Record.Name</fieldItem></fieldInstance></itemInstances>
    </flexiPageRegions>
    """
    page_file = _write_flexipage(tmp_path, body=body)
    monkeypatch.setattr(
        sys,
        "argv",
        ["measure_flexipage", str(page_file), "--json", "--no-synthetic-trigger-e"],
    )
    assert measure_flexipage.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert [row["name"] for row in payload["dataMovements"][:3]] == [
        "Read page record (Account)",
        "Display page record (Account)",
        "Edit page record (Account)",
    ]
    assert payload["dataMovements"][2]["movementType"] == "E"
    assert payload["dataMovements"][3]["name"] == "Write page record (Account)"
    assert payload["dataMovements"][3]["movementType"] == "W"


def test_cli_include_action_candidates(monkeypatch, capsys, tmp_path):
    body = """
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>actionNames</name>
                    <valueList>
                        <valueListItems><value>Delete</value></valueListItems>
                        <valueListItems><value>Account.Create_Something</value></valueListItems>
                    </valueList>
                </componentInstanceProperties>
                <componentName>force:highlightsPanel</componentName>
                <identifier>force_highlightsPanel</identifier>
            </componentInstance>
        </itemInstances>
    </flexiPageRegions>
    """
    page_file = _write_flexipage(tmp_path, body=body)
    monkeypatch.setattr(
        sys,
        "argv",
        ["measure_flexipage", str(page_file), "--json", "--include-action-candidates"],
    )
    assert measure_flexipage.main() == 0
    payload = json.loads(capsys.readouterr().out)
    candidates = payload.get("actionCandidateMeasurements") or []
    assert len(candidates) == 2
    assert candidates[0]["artifact"]["type"] == "FlexiPageAction"


def test_cli_counts_highlights_panel_as_explicit_read_and_display(monkeypatch, capsys, tmp_path):
    body = """
    <flexiPageRegions>
        <itemInstances><fieldInstance><fieldItem>Record.Name</fieldItem></fieldInstance></itemInstances>
        <itemInstances>
            <componentInstance>
                <componentName>force:highlightsPanel</componentName>
                <identifier>force_highlightsPanel</identifier>
            </componentInstance>
        </itemInstances>
    </flexiPageRegions>
    """
    page_file = _write_flexipage(tmp_path, body=body)
    monkeypatch.setattr(
        sys,
        "argv",
        ["measure_flexipage", str(page_file), "--json", "--no-synthetic-trigger-e"],
    )
    assert measure_flexipage.main() == 0
    payload = json.loads(capsys.readouterr().out)
    movement_names = [row["name"] for row in payload.get("dataMovements") or []]
    assert "Read highlights panel fields (Account)" in movement_names
    assert "Display highlights panel fields (Account)" in movement_names


def test_cli_places_highlights_rows_directly_after_primary_four(monkeypatch, capsys, tmp_path):
    body = """
    <flexiPageRegions>
        <itemInstances><fieldInstance><fieldItem>Record.Name</fieldItem></fieldInstance></itemInstances>
        <itemInstances>
            <componentInstance>
                <componentName>force:highlightsPanel</componentName>
                <identifier>force_highlightsPanel</identifier>
            </componentInstance>
        </itemInstances>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>relatedListApiName</name>
                    <value>Contacts</value>
                </componentInstanceProperties>
                <componentName>force:relatedListSingleContainer</componentName>
                <identifier>force_relatedListSingleContainer</identifier>
            </componentInstance>
        </itemInstances>
    </flexiPageRegions>
    """
    page_file = _write_flexipage(tmp_path, body=body)
    monkeypatch.setattr(sys, "argv", ["measure_flexipage", str(page_file), "--json"])
    assert measure_flexipage.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert [row["name"] for row in payload["dataMovements"][:9]] == [
        "Open record page (Account)",
        "Read page record (Account)",
        "Display page record (Account)",
        "Edit page record (Account)",
        "Write page record (Account)",
        "Read highlights panel fields (Account)",
        "Display highlights panel fields (Account)",
        "Read related list Contacts",
        "Display related list Contacts",
    ]


def test_cli_places_primary_record_r_x_e_at_top(monkeypatch, capsys, tmp_path):
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
    page_file = _write_flexipage(tmp_path, body=body)
    monkeypatch.setattr(sys, "argv", ["measure_flexipage", str(page_file), "--json"])
    assert measure_flexipage.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert [row["name"] for row in payload["dataMovements"][:7]] == [
        "Open record page (Account)",
        "Read page record (Account)",
        "Display page record (Account)",
        "Edit page record (Account)",
        "Write page record (Account)",
        "Read related list Contacts",
        "Display related list Contacts",
    ]


def test_cli_tab_aware_notes(monkeypatch, capsys, tmp_path):
    body = """
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>title</name>
                    <value>Visualiser</value>
                </componentInstanceProperties>
                <componentName>flexipage:tab</componentName>
                <identifier>tabVisualiser</identifier>
            </componentInstance>
        </itemInstances>
    </flexiPageRegions>
    """
    page_file = _write_flexipage(tmp_path, body=body)
    monkeypatch.setattr(sys, "argv", ["measure_flexipage", str(page_file), "--json"])
    assert measure_flexipage.main() == 0
    payload = json.loads(capsys.readouterr().out)
    warnings = payload.get("traversalWarnings") or []
    assert any("Tab-aware notes: page contains tabs = Visualiser" in item for item in warnings)


def test_cli_tab_component_binding_warning(monkeypatch, capsys, tmp_path):
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
                <componentInstanceProperties>
                    <name>body</name>
                    <value>Facet-visualiser</value>
                </componentInstanceProperties>
                <componentInstanceProperties>
                    <name>title</name>
                    <value>Visualiser</value>
                </componentInstanceProperties>
                <componentName>flexipage:tab</componentName>
                <identifier>tabVisualiser</identifier>
            </componentInstance>
        </itemInstances>
    </flexiPageRegions>
    """
    page_file = _write_flexipage(tmp_path, body=body)
    monkeypatch.setattr(sys, "argv", ["measure_flexipage", str(page_file), "--json"])
    assert measure_flexipage.main() == 0
    payload = json.loads(capsys.readouterr().out)
    warnings = payload.get("traversalWarnings") or []
    assert any(
        "Tab-component bindings: Visualiser -> lwc(cfp_FunctionalProcessVisualiser)" in item
        for item in warnings
    )
    assert any(
        "Delegate tab-bound LWCs to lwc-measurer with additional write movement handling: "
        "cfp_FunctionalProcessVisualiser" in item
        for item in warnings
    )
    assert "lwcCandidateMeasurements" not in payload


def test_cli_tab_component_binding_infers_write_requirement(monkeypatch, capsys, tmp_path):
    body = """
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentName>cfp_FunctionalProcessEditor</componentName>
                <identifier>c_cfp_FunctionalProcessEditor</identifier>
            </componentInstance>
        </itemInstances>
        <name>Facet-editor</name>
        <type>Facet</type>
    </flexiPageRegions>
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>body</name>
                    <value>Facet-editor</value>
                </componentInstanceProperties>
                <componentInstanceProperties>
                    <name>title</name>
                    <value>Edit Details</value>
                </componentInstanceProperties>
                <componentName>flexipage:tab</componentName>
                <identifier>tabEditor</identifier>
            </componentInstance>
        </itemInstances>
    </flexiPageRegions>
    """
    page_file = _write_flexipage(tmp_path, body=body)
    monkeypatch.setattr(sys, "argv", ["measure_flexipage", str(page_file), "--json"])
    assert measure_flexipage.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert "lwcCandidateMeasurements" not in payload


def test_cli_emits_tbc_dm_row_for_each_lwc_candidate(monkeypatch, capsys, tmp_path):
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
                <componentName>cfp_FunctionalProcessEditor</componentName>
                <identifier>c_cfp_FunctionalProcessEditor</identifier>
            </componentInstance>
        </itemInstances>
        <name>Facet-editor</name>
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
                <identifier>tabVisualiser</identifier>
            </componentInstance>
        </itemInstances>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>body</name>
                    <value>Facet-editor</value>
                </componentInstanceProperties>
                <componentInstanceProperties>
                    <name>title</name>
                    <value>Edit Details</value>
                </componentInstanceProperties>
                <componentName>flexipage:tab</componentName>
                <identifier>tabEditor</identifier>
            </componentInstance>
        </itemInstances>
    </flexiPageRegions>
    """
    page_file = _write_flexipage(tmp_path, body=body)
    monkeypatch.setattr(
        sys, "argv", ["measure_flexipage", str(page_file), "--json", "--no-resolve-lwc-candidates"]
    )
    assert measure_flexipage.main() == 0
    payload = json.loads(capsys.readouterr().out)
    dm_rows = payload.get("dataMovements") or []
    tbc_lwc_rows = [
        row for row in dm_rows if row.get("dataGroupRef") == "tbc" and "Inspect LWC" in row.get("name", "")
    ]
    assert len(tbc_lwc_rows) == 2
    assert any("cfp_FunctionalProcessVisualiser" in row["name"] for row in tbc_lwc_rows)
    assert any("cfp_FunctionalProcessEditor" in row["name"] for row in tbc_lwc_rows)


def test_cli_inlines_non_lwc_tab_component_movements(monkeypatch, capsys, tmp_path):
    body = """
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>relatedListApiName</name>
                    <value>Contacts</value>
                </componentInstanceProperties>
                <componentName>force:relatedListSingleContainer</componentName>
                <identifier>force_relatedListSingleContainer</identifier>
            </componentInstance>
        </itemInstances>
        <name>Facet-contacts</name>
        <type>Facet</type>
    </flexiPageRegions>
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>body</name>
                    <value>Facet-contacts</value>
                </componentInstanceProperties>
                <componentInstanceProperties>
                    <name>title</name>
                    <value>Contacts Tab</value>
                </componentInstanceProperties>
                <componentName>flexipage:tab</componentName>
                <identifier>tabContacts</identifier>
            </componentInstance>
        </itemInstances>
    </flexiPageRegions>
    """
    page_file = _write_flexipage(tmp_path, body=body)
    monkeypatch.setattr(
        sys, "argv", ["measure_flexipage", str(page_file), "--json", "--no-dedupe-movements"]
    )
    assert measure_flexipage.main() == 0
    payload = json.loads(capsys.readouterr().out)
    movement_names = [row["name"] for row in payload.get("dataMovements") or []]
    assert "Read related list Contacts | tab:Contacts Tab" in movement_names
    assert "Display related list Contacts | tab:Contacts Tab" in movement_names


def test_cli_places_related_record_read_display_pairs_adjacent(monkeypatch, capsys, tmp_path):
    body = """
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties><name>lookupFieldName</name><value>WorkOrder.Id</value></componentInstanceProperties>
                <componentInstanceProperties><name>titleFieldName</name><value>Access Issue Details</value></componentInstanceProperties>
                <componentName>console:relatedRecord</componentName>
                <identifier>relatedRecord1</identifier>
            </componentInstance>
        </itemInstances>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties><name>lookupFieldName</name><value>WorkOrder.Id</value></componentInstanceProperties>
                <componentInstanceProperties><name>titleFieldName</name><value>NCAT Details</value></componentInstanceProperties>
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
    page_file = _write_flexipage(tmp_path, body=body)
    monkeypatch.setattr(sys, "argv", ["measure_flexipage", str(page_file), "--json"])
    assert measure_flexipage.main() == 0
    payload = json.loads(capsys.readouterr().out)
    movement_names = [row["name"] for row in payload.get("dataMovements") or []]

    first_read_index = movement_names.index("Read related record Access Issue Details | tab:RelatedTab")
    first_display_index = movement_names.index(
        "Display related record Access Issue Details | tab:RelatedTab"
    )
    second_read_index = movement_names.index("Read related record NCAT Details | tab:RelatedTab")
    second_display_index = movement_names.index("Display related record NCAT Details | tab:RelatedTab")

    assert first_display_index == first_read_index + 1
    assert second_display_index == second_read_index + 1


def test_cli_dedupes_tab_suffix_duplicates(monkeypatch, capsys, tmp_path):
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
        <name>Facet-contacts</name>
        <type>Facet</type>
    </flexiPageRegions>
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>body</name>
                    <value>Facet-contacts</value>
                </componentInstanceProperties>
                <componentInstanceProperties>
                    <name>title</name>
                    <value>Contacts Tab</value>
                </componentInstanceProperties>
                <componentName>flexipage:tab</componentName>
                <identifier>tabContacts</identifier>
            </componentInstance>
        </itemInstances>
    </flexiPageRegions>
    """
    page_file = _write_flexipage(tmp_path, body=body)
    monkeypatch.setattr(sys, "argv", ["measure_flexipage", str(page_file), "--json"])
    assert measure_flexipage.main() == 0
    payload = json.loads(capsys.readouterr().out)
    movement_names = [row["name"] for row in payload.get("dataMovements") or []]
    assert movement_names.count("Read related list Contacts") == 1
    assert movement_names.count("Display related list Contacts") == 1
    assert "Read related list Contacts | tab:Contacts Tab" not in movement_names
    assert "Display related list Contacts | tab:Contacts Tab" not in movement_names


def test_cli_resolves_lwc_candidates_by_default(monkeypatch, capsys, project_root):
    sample = project_root / "samples" / "flexipages" / "cfp_FunctionalProcess_Record_Page.flexipage-meta.xml"
    if not sample.exists():
        return
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "measure_flexipage",
            str(sample),
            "--json",
            "--lwc-search-paths",
            str(project_root / "samples" / "lwc"),
            "--apex-search-paths",
            str(project_root / "samples" / "classes"),
            "--include-resolution-details",
        ],
    )
    assert measure_flexipage.main() == 0
    payload = json.loads(capsys.readouterr().out)
    resolved = payload.get("resolvedLwcMeasurements") or []
    assert len(resolved) == 1
    assert resolved[0]["artifact"]["type"] == "LWC"
    assert resolved[0]["artifact"]["name"] == "cfp_FunctionalProcessVisualiser.lwc"
    movement_names = [row["name"] for row in payload.get("dataMovements") or []]
    assert any(name.endswith("| tab:Visualiser") for name in movement_names)
    assert "Potential write via imperative Apex call | tab:Visualiser" not in movement_names
    assert movement_names[-1] == "Errors/notifications"


def test_cli_no_resolve_lwc_candidates_opt_out(monkeypatch, capsys, project_root):
    sample = project_root / "samples" / "flexipages" / "cfp_FunctionalProcess_Record_Page.flexipage-meta.xml"
    if not sample.exists():
        return
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "measure_flexipage",
            str(sample),
            "--json",
            "--no-resolve-lwc-candidates",
        ],
    )
    assert measure_flexipage.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert "resolvedLwcMeasurements" not in payload
    movement_names = [row["name"] for row in payload.get("dataMovements") or []]
    assert all(not name.endswith("| tab:Visualiser") for name in movement_names)


def test_cli_resolves_flow_candidates_by_default(monkeypatch, capsys, project_root, tmp_path):
    body = """
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>flowName</name>
                    <value>cfp_createCRUDLwithRelatedLists</value>
                </componentInstanceProperties>
                <componentName>flowruntime:interview</componentName>
                <identifier>flowruntime_interview</identifier>
            </componentInstance>
        </itemInstances>
        <name>Facet-flow</name>
        <type>Facet</type>
    </flexiPageRegions>
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>body</name>
                    <value>Facet-flow</value>
                </componentInstanceProperties>
                <componentInstanceProperties>
                    <name>title</name>
                    <value>Flow Tab</value>
                </componentInstanceProperties>
                <componentName>flexipage:tab</componentName>
                <identifier>tabFlow</identifier>
            </componentInstance>
        </itemInstances>
    </flexiPageRegions>
    """
    page_file = _write_flexipage(tmp_path, body=body)
    flow_sample_dir = project_root / "samples" / "flows"
    if not flow_sample_dir.exists():
        return
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "measure_flexipage",
            str(page_file),
            "--json",
            "--flow-search-paths",
            str(flow_sample_dir),
            "--include-resolution-details",
        ],
    )
    assert measure_flexipage.main() == 0
    payload = json.loads(capsys.readouterr().out)
    flow_candidates = payload.get("flowCandidateMeasurements") or []
    assert len(flow_candidates) == 1
    assert flow_candidates[0]["artifact"]["name"] == "cfp_createCRUDLwithRelatedLists"
    resolved = payload.get("resolvedFlowMeasurements") or []
    assert len(resolved) == 1
    movement_names = [row["name"] for row in payload.get("dataMovements") or []]
    assert any(name.endswith("| tab:Flow Tab") for name in movement_names)
    assert movement_names[-1] == "Errors/notifications"


def test_cli_no_resolve_flow_candidates_opt_out(monkeypatch, capsys, tmp_path):
    body = """
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>flowName</name>
                    <value>SomeFlow</value>
                </componentInstanceProperties>
                <componentName>flowruntime:interview</componentName>
                <identifier>flowruntime_interview</identifier>
            </componentInstance>
        </itemInstances>
        <name>Facet-flow</name>
        <type>Facet</type>
    </flexiPageRegions>
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>body</name>
                    <value>Facet-flow</value>
                </componentInstanceProperties>
                <componentInstanceProperties>
                    <name>title</name>
                    <value>Flow Tab</value>
                </componentInstanceProperties>
                <componentName>flexipage:tab</componentName>
                <identifier>tabFlow</identifier>
            </componentInstance>
        </itemInstances>
    </flexiPageRegions>
    """
    page_file = _write_flexipage(tmp_path, body=body)
    monkeypatch.setattr(
        sys,
        "argv",
        ["measure_flexipage", str(page_file), "--json", "--no-resolve-flow-candidates"],
    )
    assert measure_flexipage.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert "flowCandidateMeasurements" not in payload
    assert "resolvedFlowMeasurements" not in payload


def test_cli_includes_sidebar_related_record_movements(monkeypatch, capsys, tmp_path):
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
    page_file = _write_flexipage(tmp_path, body=body)
    monkeypatch.setattr(sys, "argv", ["measure_flexipage", str(page_file), "--json"])
    assert measure_flexipage.main() == 0
    payload = json.loads(capsys.readouterr().out)
    movement_names = [row["name"] for row in payload.get("dataMovements") or []]
    assert "Read related record Request Details" in movement_names
    assert "Display related record Request Details" in movement_names
    read_row = next(
        row
        for row in payload.get("dataMovements") or []
        if row.get("name") == "Read related record Request Details"
    )
    assert read_row["dataGroupRef"] == "Case"


def test_cli_includes_path_component_read_and_display_rows(monkeypatch, capsys, tmp_path):
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
    page_file = _write_flexipage(tmp_path, body=body)
    monkeypatch.setattr(sys, "argv", ["measure_flexipage", str(page_file), "--json"])
    assert measure_flexipage.main() == 0
    payload = json.loads(capsys.readouterr().out)
    path_rows = [
        row
        for row in payload.get("dataMovements") or []
        if row.get("name", "").startswith("Read path state (Account)")
        or row.get("name", "").startswith("Display path state (Account)")
    ]
    assert len(path_rows) == 2
    assert [row["movementType"] for row in path_rows] == ["R", "X"]


def test_cli_caps_all_emitted_movement_names_at_80(monkeypatch, capsys, project_root, tmp_path):
    page_file = project_root / "samples" / "flexipages" / "WorkOrder.flexipage"
    flow_search = project_root / "samples" / "flows"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "measure_flexipage",
            str(page_file),
            "--json",
            "--flow-search-paths",
            str(flow_search),
        ],
    )
    assert measure_flexipage.main() == 0
    payload = json.loads(capsys.readouterr().out)
    over_limit = [
        row.get("name", "")
        for row in (payload.get("dataMovements") or [])
        if len(str(row.get("name") or "")) > 80
    ]
    assert over_limit == []
