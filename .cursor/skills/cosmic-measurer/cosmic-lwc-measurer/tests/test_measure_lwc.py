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


# ---------------------------------------------------------------------------
# Step 3 RED: tier assignment
# ---------------------------------------------------------------------------

def test_wire_r_movements_get_init_tier(tmp_path: Path, monkeypatch):
    bundle_dir = tmp_path / "cmp"
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "cmp.js").write_text(
        "import { wire } from 'lwc'; import { CurrentPageReference } from 'lightning/navigation';\n"
        "@wire(CurrentPageReference) pageRef;",
        encoding="utf-8",
    )
    (bundle_dir / "cmp.html").write_text("<template><p>{pageRef}</p></template>", encoding="utf-8")

    result = measure_lwc_bundle(bundle_dir)
    r_rows = [row for row in result["dataMovements"] if row.get("movementType") == "R"]
    assert r_rows, "Expected at least one R movement"
    for row in r_rows:
        assert row.get("tier") == 1, f"Expected tier=1 for wire R, got {row.get('tier')} on {row}"
        assert row.get("tierLabel") == "Init"


def test_interaction_linked_apex_r_gets_interactions_tier(tmp_path: Path, monkeypatch):
    bundle_dir = tmp_path / "cmp"
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "cmp.js").write_text(
        "import loadSORs from '@salesforce/apex/SORController.loadSORs';\n"
        "export default class Cmp extends LightningElement {\n"
        "  handleFilter() { loadSORs({ filter: this.filter }); }\n"
        "}\n",
        encoding="utf-8",
    )
    (bundle_dir / "cmp.html").write_text(
        "<template>"
        "<div><c-lookup oncustomlookupupdateevent={handleFilter}></c-lookup></div>"
        "<p>{result}</p>"
        "</template>",
        encoding="utf-8",
    )

    def fake_find_class_file(class_name, _paths):
        from pathlib import Path as P
        return P(f"/tmp/{class_name}.cls")

    def fake_measure_apex(cls_file, _fp, search_paths, traverse):
        return {"dataMovements": [
            {"movementType": "R", "name": "Read SOR list", "dataGroupRef": "SOR__c", "sourceLine": 10},
            {"movementType": "X", "name": "Errors/notifications", "dataGroupRef": "status/errors/etc"},
        ]}

    monkeypatch.setattr("measure_lwc._load_apex_measurer_helpers", lambda: (fake_find_class_file, fake_measure_apex))
    result = measure_lwc_bundle(bundle_dir, apex_search_paths=[tmp_path / "classes"])

    sor_rows = [r for r in result["dataMovements"] if r.get("dataGroupRef") == "SOR__c"]
    assert sor_rows, "Expected SOR__c R row"
    assert sor_rows[0].get("tier") == 2, f"Expected tier=2 for interaction-linked R, got {sor_rows[0].get('tier')}"
    assert sor_rows[0].get("tierLabel") == "Interactions"
    assert sor_rows[0].get("triggeringBlock") == "filter"


def test_w_movements_get_terminal_tier(tmp_path: Path, monkeypatch):
    bundle_dir = tmp_path / "cmp"
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "cmp.js").write_text(
        "import saveRec from '@salesforce/apex/SaveController.save';\n"
        "export default class Cmp extends LightningElement {\n"
        "  handleSave() { saveRec({ rec: this.record }); }\n"
        "}\n",
        encoding="utf-8",
    )
    (bundle_dir / "cmp.html").write_text(
        "<template>"
        "<div><lightning-button label=\"Save\" onclick={handleSave}></lightning-button></div>"
        "<p>{result}</p>"
        "</template>",
        encoding="utf-8",
    )

    def fake_find_class_file(class_name, _paths):
        from pathlib import Path as P
        return P(f"/tmp/{class_name}.cls")

    def fake_measure_apex(cls_file, _fp, search_paths, traverse):
        return {"dataMovements": [
            {"movementType": "W", "name": "Update Record", "dataGroupRef": "Record__c", "sourceLine": 5},
            {"movementType": "X", "name": "Errors/notifications", "dataGroupRef": "status/errors/etc"},
        ]}

    monkeypatch.setattr("measure_lwc._load_apex_measurer_helpers", lambda: (fake_find_class_file, fake_measure_apex))
    result = measure_lwc_bundle(bundle_dir, apex_search_paths=[tmp_path / "classes"])

    w_rows = [r for r in result["dataMovements"] if r.get("movementType") == "W"]
    assert w_rows, "Expected W row"
    for row in w_rows:
        assert row.get("tier") == 3, f"Expected tier=3 for W, got {row.get('tier')}"
        assert row.get("tierLabel") == "Terminal"


def test_canonical_x_is_terminal_tier(tmp_path: Path):
    bundle_dir = tmp_path / "cmp"
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "cmp.js").write_text("", encoding="utf-8")
    (bundle_dir / "cmp.html").write_text("<template><p>{value}</p></template>", encoding="utf-8")

    result = measure_lwc_bundle(bundle_dir)
    canonical = [r for r in result["dataMovements"] if r.get("name") == "Errors/notifications"]
    assert canonical, "Expected canonical X"
    assert canonical[0].get("tier") == 3
    assert canonical[0].get("tierLabel") == "Terminal"


def test_display_x_follows_first_interaction_cluster_with_r(tmp_path: Path, monkeypatch):
    bundle_dir = tmp_path / "cmp"
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "cmp.js").write_text(
        "import loadData from '@salesforce/apex/DataController.load';\n"
        "export default class Cmp extends LightningElement {\n"
        "  handleFilter() { loadData({ filter: this.f }); }\n"
        "}\n",
        encoding="utf-8",
    )
    (bundle_dir / "cmp.html").write_text(
        "<template>"
        "<div><c-lookup oncustomlookupupdateevent={handleFilter}></c-lookup></div>"
        "<p>{result}</p>"
        "</template>",
        encoding="utf-8",
    )

    def fake_find(cn, _p):
        from pathlib import Path as P
        return P(f"/tmp/{cn}.cls")

    def fake_measure(f, _fp, search_paths, traverse):
        return {"dataMovements": [
            {"movementType": "R", "name": "Read Data", "dataGroupRef": "Data__c", "sourceLine": 5},
            {"movementType": "X", "name": "Errors/notifications", "dataGroupRef": "status/errors/etc"},
        ]}

    monkeypatch.setattr("measure_lwc._load_apex_measurer_helpers", lambda: (fake_find, fake_measure))
    result = measure_lwc_bundle(bundle_dir, apex_search_paths=[tmp_path / "classes"])

    display_x = [r for r in result["dataMovements"] if r.get("name") == "Display LWC output to user"]
    assert display_x, "Expected display X"
    assert display_x[0].get("tier") == 2, "Display X should be in Interactions tier when filter has linked R"
    assert display_x[0].get("tierLabel") == "Interactions"


# ── Step 4 RED: 3-tier ordering ────────────────────────────────────────────


def _make_bundle_with_filter_and_save(tmp_path: Path, monkeypatch) -> list[dict]:
    """Helper: LWC with a filter E (tier 2) and a save W (tier 3); wire R (tier 1)."""
    bundle_dir = tmp_path / "cmp"
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "cmp.js").write_text(
        "import { wire } from 'lwc'; import { CurrentPageReference } from 'lightning/navigation';\n"
        "import saveRec from '@salesforce/apex/SaveCtrl.save';\n"
        "import loadData from '@salesforce/apex/LoadCtrl.load';\n"
        "export default class Cmp extends LightningElement {\n"
        "  @wire(CurrentPageReference) pageRef;\n"
        "  handleFilter() { loadData({ f: this.f }); }\n"
        "  handleSave() { saveRec({ r: this.r }); }\n"
        "}\n",
        encoding="utf-8",
    )
    (bundle_dir / "cmp.html").write_text(
        "<template>"
        "<div><c-lookup oncustomlookupupdateevent={handleFilter}></c-lookup></div>"
        "<div><lightning-button label='Save' onclick={handleSave}></lightning-button></div>"
        "<p>{result}</p>"
        "</template>",
        encoding="utf-8",
    )

    call_count = [0]

    def fake_find(cn, _p):
        from pathlib import Path as P
        return P(f"/tmp/{cn}.cls")

    def fake_measure(f, _fp, search_paths, traverse):
        call_count[0] += 1
        name = str(f)
        if "LoadCtrl" in name:
            return {"dataMovements": [
                {"movementType": "R", "name": "Read Data", "dataGroupRef": "Data__c", "sourceLine": 5},
            ]}
        return {"dataMovements": [
            {"movementType": "W", "name": "Write Record", "dataGroupRef": "Record__c", "sourceLine": 10},
        ]}

    monkeypatch.setattr("measure_lwc._load_apex_measurer_helpers", lambda: (fake_find, fake_measure))
    result = measure_lwc_bundle(bundle_dir, apex_search_paths=[tmp_path / "classes"])
    return result["dataMovements"]


def test_tier_ordering_init_before_interactions_before_terminal(tmp_path: Path, monkeypatch):
    rows = _make_bundle_with_filter_and_save(tmp_path, monkeypatch)
    tiers = [r.get("tier") for r in rows if r.get("tier") is not None]
    assert tiers == sorted(tiers), f"Rows not in ascending tier order: {tiers}"


def test_tier_ordering_w_before_canonical_x(tmp_path: Path, monkeypatch):
    rows = _make_bundle_with_filter_and_save(tmp_path, monkeypatch)
    tier3 = [r for r in rows if r.get("tier") == 3]
    types = [r["movementType"] for r in tier3]
    w_idx = next((i for i, t in enumerate(types) if t == "W"), None)
    x_idx = next((i for i, t in enumerate(types) if t == "X"), None)
    assert w_idx is not None and x_idx is not None
    assert w_idx < x_idx, f"W should precede canonical X in terminal tier: {types}"


def test_tier_ordering_e_before_r_within_interactions_tier(tmp_path: Path, monkeypatch):
    rows = _make_bundle_with_filter_and_save(tmp_path, monkeypatch)
    tier2 = [r for r in rows if r.get("tier") == 2]
    types = [r["movementType"] for r in tier2]
    if "E" in types and "R" in types:
        e_idx = types.index("E")
        r_idx = types.index("R")
        assert e_idx < r_idx, f"E should precede R in Interactions tier: {types}"


# ── Step 5 RED: to_table() tier-grouped output ─────────────────────────────


def test_to_table_includes_tier_section_headers(tmp_path: Path, monkeypatch):
    from shared.output import to_table

    rows = _make_bundle_with_filter_and_save(tmp_path, monkeypatch)
    dummy_output = {
        "functionalProcessId": "<Id>",
        "artifact": {"type": "LWC", "name": "cmp"},
        "dataMovements": rows,
    }
    table = to_table(dummy_output)
    assert "## Init" in table, "Expected '## Init' section header in table"
    assert "## Interactions" in table, "Expected '## Interactions' section header in table"
    assert "## Terminal" in table, "Expected '## Terminal' section header in table"
