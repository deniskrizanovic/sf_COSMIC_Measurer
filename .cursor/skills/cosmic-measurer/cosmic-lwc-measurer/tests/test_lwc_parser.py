"""Unit tests for lwc_parser helpers."""

from shared.models import RawMovement
from lwc_parser import (
    detect_apex_imports,
    extract_handler_apex_calls,
    infer_bundle_name,
    parse_lwc_native_movements,
)


# ---------------------------------------------------------------------------
# Step 1 RED: RawMovement new fields
# ---------------------------------------------------------------------------

def test_raw_movement_has_tier_fields():
    m = RawMovement(movement_type="E", data_group_ref="User", name="Test", order_hint=1)
    assert m.tier is None
    assert m.tier_label is None
    assert m.block_label is None
    assert m.triggering_block is None


def test_raw_movement_tier_fields_accept_values():
    m = RawMovement(
        movement_type="R",
        data_group_ref="Account",
        name="Read Account",
        order_hint=2,
        tier=1,
        tier_label="Init",
        block_label=None,
        triggering_block=None,
    )
    assert m.tier == 1
    assert m.tier_label == "Init"


def test_raw_movement_interactions_tier_fields():
    m = RawMovement(
        movement_type="E",
        data_group_ref="FilterCriteria",
        name="Receive filter criteria",
        order_hint=10,
        tier=2,
        tier_label="Interactions",
        block_label="filter",
        triggering_block=None,
    )
    assert m.tier == 2
    assert m.block_label == "filter"


def test_raw_movement_triggering_block_field():
    m = RawMovement(
        movement_type="R",
        data_group_ref="Service_Catalogue__c",
        name="Read Service_Catalogue__c list",
        order_hint=11,
        tier=2,
        tier_label="Interactions",
        triggering_block="filter",
    )
    assert m.triggering_block == "filter"


def test_detect_apex_imports_deduplicates_pairs():
    js_source = """
import loadA from '@salesforce/apex/SomeClass.load';
import loadARepeat from '@salesforce/apex/SomeClass.load';
import saveA from '@salesforce/apex/SomeClass.save';
import runB from '@salesforce/apex/OtherClass.run';
"""
    imports = detect_apex_imports(js_source)
    assert imports == [
        ("SomeClass", "load"),
        ("SomeClass", "save"),
        ("OtherClass", "run"),
    ]


def test_detect_apex_imports_returns_empty_when_no_apex_imports():
    js_source = "import { LightningElement } from 'lwc';"
    assert detect_apex_imports(js_source) == []


def test_parse_lwc_native_movements_detects_all_types():
    js_source = """
import { LightningElement, wire } from 'lwc';
import { getRecord, updateRecord } from 'lightning/uiRecordApi';
export default class Example extends LightningElement {
  @wire(getRecord, { recordId: '$recordId' }) wiredRecord;
  save() { return updateRecord({}); }
}
"""
    html_source = """
<template>
  <lightning-button onclick={save}></lightning-button>
  <p>{wiredRecord.data.Name}</p>
</template>
"""
    movements = parse_lwc_native_movements(js_source, html_source)
    types = [m.movement_type for m in movements]
    assert "E" in types
    assert "R" in types
    assert "W" in types
    assert "X" in types
    e_movements = [m for m in movements if m.movement_type == "E"]
    assert len(e_movements) == 1
    assert e_movements[0].tier == 2
    assert e_movements[0].tier_label == "Interactions"
    assert e_movements[0].block_label is not None


def test_parse_lwc_native_movements_detects_partial_types():
    js_source = "import { getRecord } from 'lightning/uiRecordApi'; getRecord({});"
    html_source = "<template><div>{message}</div></template>"
    movements = parse_lwc_native_movements(js_source, html_source)
    assert [movement.movement_type for movement in movements] == ["R", "X"]


def test_infer_bundle_name_returns_directory_name(tmp_path):
    bundle_dir = tmp_path / "myBundle"
    bundle_dir.mkdir()
    assert infer_bundle_name(bundle_dir) == "myBundle"


# ---------------------------------------------------------------------------
# Step 2 RED: HtmlBlockClassifier — one test per block type
# ---------------------------------------------------------------------------

def test_block_classifier_filter_block():
    html = """
<template>
  <div>
    <c-lookup oncustomlookupupdateevent={handleComponentChange}></c-lookup>
    <lightning-input onchange={handleSearchChange}></lightning-input>
  </div>
  <p>{result}</p>
</template>
"""
    movements = parse_lwc_native_movements("", html)
    e_movements = [m for m in movements if m.movement_type == "E"]
    assert len(e_movements) == 1
    assert e_movements[0].block_label == "filter"
    assert e_movements[0].name == "Receive filter criteria"
    assert e_movements[0].data_group_ref == "FilterCriteria"
    assert e_movements[0].tier == 2
    assert "handleComponentChange" in e_movements[0].handler_names
    assert "handleSearchChange" in e_movements[0].handler_names


def test_block_classifier_save_command_block():
    html = """
<template>
  <div class="button-container">
    <lightning-button label="Cancel" onclick={handleCancel}></lightning-button>
    <lightning-button label="Save" onclick={handleSave}></lightning-button>
  </div>
  <p>{result}</p>
</template>
"""
    movements = parse_lwc_native_movements("", html)
    e_movements = [m for m in movements if m.movement_type == "E"]
    assert len(e_movements) == 1
    assert e_movements[0].block_label == "save-command"
    assert e_movements[0].name == "Receive save command"
    assert e_movements[0].data_group_ref == "SaveCommand"
    assert e_movements[0].tier == 2


def test_block_classifier_pagination_block():
    html = """
<template>
  <div>
    <lightning-button label="Previous" onclick={previousHandler}></lightning-button>
    <lightning-button label="Next" onclick={nextHandler}></lightning-button>
  </div>
  <p>{result}</p>
</template>
"""
    movements = parse_lwc_native_movements("", html)
    e_movements = [m for m in movements if m.movement_type == "E"]
    assert len(e_movements) == 1
    assert e_movements[0].block_label == "pagination"
    assert e_movements[0].name == "Receive page navigation"
    assert e_movements[0].data_group_ref == "PageNavigation"


def test_block_classifier_row_edit_block():
    html = """
<template>
  <table>
    <tbody>
      <template for:each={rows} for:item="row">
        <tr key={row.Id}>
          <td><input type="checkbox" onchange={handlecheck}/></td>
          <td><input type="number" onblur={handleQtyInput}/></td>
        </tr>
      </template>
    </tbody>
  </table>
  <p>{result}</p>
</template>
"""
    movements = parse_lwc_native_movements("", html)
    e_movements = [m for m in movements if m.movement_type == "E"]
    assert len(e_movements) == 1
    assert e_movements[0].block_label == "row-edit"
    assert e_movements[0].name == "Receive row edits"
    assert e_movements[0].data_group_ref == "RowData"


def test_block_classifier_select_all_block():
    html = """
<template>
  <thead>
    <tr>
      <th>
        <input type="checkbox" onclick={handleAllCheck}/>
      </th>
    </tr>
  </thead>
  <p>{result}</p>
</template>
"""
    movements = parse_lwc_native_movements("", html)
    e_movements = [m for m in movements if m.movement_type == "E"]
    assert len(e_movements) == 1
    assert e_movements[0].block_label == "select-all"
    assert e_movements[0].name == "Receive select-all"
    assert e_movements[0].data_group_ref == "RowSelection"


def test_block_classifier_generic_block():
    html = """
<template>
  <div>
    <button onclick={handleClick}>Click me</button>
  </div>
  <p>{result}</p>
</template>
"""
    movements = parse_lwc_native_movements("", html)
    e_movements = [m for m in movements if m.movement_type == "E"]
    assert len(e_movements) == 1
    assert e_movements[0].block_label == "generic"
    assert e_movements[0].name == "Receive user interaction"
    assert e_movements[0].data_group_ref == "User"


def test_block_classifier_no_handlers_emits_no_e():
    html = "<template><div>{message}</div><p>{result}</p></template>"
    movements = parse_lwc_native_movements("", html)
    e_movements = [m for m in movements if m.movement_type == "E"]
    assert len(e_movements) == 0


def test_block_classifier_multiple_blocks_dom_order():
    html = """
<template>
  <div>
    <c-lookup oncustomlookupupdateevent={handleFilter}></c-lookup>
  </div>
  <div>
    <lightning-button label="Save" onclick={handleSave}></lightning-button>
  </div>
  <p>{result}</p>
</template>
"""
    movements = parse_lwc_native_movements("", html)
    e_movements = [m for m in movements if m.movement_type == "E"]
    assert len(e_movements) == 2
    assert e_movements[0].block_label == "filter"
    assert e_movements[1].block_label == "save-command"
    assert e_movements[0].order_hint < e_movements[1].order_hint


def test_block_classifier_handler_names_collected():
    html = """
<template>
  <div>
    <c-lookup oncustomlookupupdateevent={handleComponentChange}></c-lookup>
    <lightning-input onchange={handleSearchChange}></lightning-input>
  </div>
  <p>{result}</p>
</template>
"""
    movements = parse_lwc_native_movements("", html)
    e_movements = [m for m in movements if m.movement_type == "E"]
    assert len(e_movements) == 1
    assert set(e_movements[0].handler_names) == {"handleComponentChange", "handleSearchChange"}


# ---------------------------------------------------------------------------
# Step 2.5 RED: extract_handler_apex_calls
# ---------------------------------------------------------------------------

def test_extract_handler_apex_calls_basic():
    js_source = """
import loadData from '@salesforce/apex/AddSORController.loadData';
import saveData from '@salesforce/apex/AddSORController.saveData';

export default class Example extends LightningElement {
    handleFilter() {
        loadData({ filter: this.filter }).then(result => {
            this.data = result;
        });
    }
    handleSave() {
        saveData({ records: this.records });
    }
}
"""
    apex_import_vars = {"loadData": "AddSORController", "saveData": "AddSORController"}
    result = extract_handler_apex_calls(js_source, apex_import_vars)
    assert "handleFilter" in result
    assert "AddSORController" in result["handleFilter"]
    assert "handleSave" in result
    assert "AddSORController" in result["handleSave"]


def test_extract_handler_apex_calls_multiple_classes():
    js_source = """
import getWoli from '@salesforce/apex/WorkOrderLineItemTableController.getWoli';
import saveSor from '@salesforce/apex/AddSORController.saveSor';

export default class Example extends LightningElement {
    handleSave() {
        getWoli({ id: this.recordId });
        saveSor({ items: this.items });
    }
}
"""
    apex_import_vars = {
        "getWoli": "WorkOrderLineItemTableController",
        "saveSor": "AddSORController",
    }
    result = extract_handler_apex_calls(js_source, apex_import_vars)
    assert set(result["handleSave"]) == {"WorkOrderLineItemTableController", "AddSORController"}


def test_extract_handler_apex_calls_no_apex_in_handler():
    js_source = """
export default class Example extends LightningElement {
    handleClick() {
        this.value = 'clicked';
    }
}
"""
    result = extract_handler_apex_calls(js_source, {"someApex": "SomeClass"})
    assert result.get("handleClick", []) == []


def test_extract_handler_apex_calls_returns_empty_for_no_methods():
    js_source = "export default class Example extends LightningElement {}"
    result = extract_handler_apex_calls(js_source, {"someApex": "SomeClass"})
    assert result == {}
