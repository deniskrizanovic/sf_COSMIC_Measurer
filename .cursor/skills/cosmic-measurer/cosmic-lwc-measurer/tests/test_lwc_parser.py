"""Unit tests for lwc_parser helpers."""

from lwc_parser import detect_apex_imports, infer_bundle_name, parse_lwc_native_movements


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
    assert [movement.movement_type for movement in movements] == ["E", "R", "W", "X"]


def test_parse_lwc_native_movements_detects_partial_types():
    js_source = "import { getRecord } from 'lightning/uiRecordApi'; getRecord({});"
    html_source = "<template><div>{message}</div></template>"
    movements = parse_lwc_native_movements(js_source, html_source)
    assert [movement.movement_type for movement in movements] == ["R", "X"]


def test_infer_bundle_name_returns_directory_name(tmp_path):
    bundle_dir = tmp_path / "myBundle"
    bundle_dir.mkdir()
    assert infer_bundle_name(bundle_dir) == "myBundle"
