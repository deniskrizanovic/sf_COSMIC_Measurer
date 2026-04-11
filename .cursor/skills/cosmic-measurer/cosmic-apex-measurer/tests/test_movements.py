"""Unit tests for movements.py ordering and presentation helpers."""

import json

from shared.models import RawMovement

from movements import (
    CosmicMeasureOutput,
    build_output,
    count_movement_types,
    order_movements,
    partition_record_type_reads,
    to_human_summary,
    to_json_movement,
    to_json_string,
    to_table,
)


def test_partition_record_type_reads_removes_only_from_recordtype():
    r_rt = RawMovement("R", "RecordType", "Read RecordType list", 1, source_line=10)
    r_acc = RawMovement("R", "Account", "Read Account list", 2, source_line=20)
    kept, ex = partition_record_type_reads([r_rt, r_acc])
    assert kept == [r_acc]
    assert ex == [r_rt]


def test_build_output_puts_record_type_reads_in_metadata_not_rows():
    r_rt = RawMovement("R", "RecordType", "Read RecordType list", 1, source_line=99)
    r_acc = RawMovement("R", "Account", "Read Account list", 2, source_line=1)
    out = build_output("C", [r_rt, r_acc], called_classes_not_found=None)
    assert len(out["dataMovements"]) == 2  # R Account + canonical X
    assert out["dataMovements"][0]["dataGroupRef"] == "Account"
    assert out["recordTypeReadsExcludedFromCfp"] == [
        {"name": "Read RecordType list", "sourceLine": 99}
    ]


def test_to_human_summary_record_type_note():
    out: CosmicMeasureOutput = {
        "functionalProcessId": "x",
        "artifact": {"type": "Apex", "name": "X"},
        "dataMovements": [
            {
                "name": "Errors/notifications",
                "order": 1,
                "movementType": "X",
                "dataGroupRef": "status/errors/etc",
                "implementationType": "apex",
                "isApiCall": False,
            },
        ],
        "recordTypeReadsExcludedFromCfp": [
            {"name": "Read RecordType list", "sourceLine": 47},
        ],
    }
    text = to_human_summary(out)
    assert "RecordType reads (excluded from CFP)" in text
    assert "L47" in text


def test_order_movements_keeps_separate_writes_per_record_type_suffix():
    w_loc = RawMovement(
        "W", "Asset::Location", "Insert Asset::Location records", 1, source_line=1
    )
    w_comp = RawMovement(
        "W", "Asset::Component", "Insert Asset::Component records", 2, source_line=2
    )
    out = order_movements([w_loc, w_comp])
    assert len(out) == 2
    assert all(not merged for _, merged in out)


def test_order_movements_dedupes_reads_and_merges_writes():
    r1 = RawMovement("R", "Account", "Read Account list", 1, source_line=10)
    r_dup = RawMovement("R", "Account", "Read Account list", 2, source_line=11)
    w1 = RawMovement("W", "Foo__c", "Insert Foo__c records", 3, source_line=20)
    w2 = RawMovement("W", "Foo__c", "Update Foo__c records", 4, source_line=21)
    w3 = RawMovement("W", "Foo__c", "Delete Foo__c records", 5, source_line=22)
    out = order_movements([r1, r_dup, w1, w2, w3])
    assert len(out) == 2
    assert out[0][1] == []
    merged = out[1][1]
    assert len(merged) == 2
    assert merged[0]["name"] == "Update Foo__c records"
    assert merged[0]["sourceLine"] == 21
    assert merged[1]["name"] == "Delete Foo__c records"
    assert merged[1]["sourceLine"] == 22


def test_order_movements_merge_write_without_source_line_on_second():
    w1 = RawMovement("W", "Bar__c", "Insert Bar__c records", 1, source_line=5)
    w2 = RawMovement("W", "Bar__c", "Update Bar__c records", 2, source_line=None)
    out = order_movements([w1, w2])
    assert len(out) == 1
    assert out[0][1] == [{"name": "Update Bar__c records"}]


def test_order_movements_non_rw_passthrough():
    e = RawMovement("E", "X__c", "Receive fpId", 1)
    x = RawMovement("X", "Y__c", "Return Y list", 2)
    z = RawMovement("Z", "?", "odd", 3)
    out = order_movements([e, x, z])
    assert len(out) == 3
    assert all(merged == [] for _, merged in out)


def test_to_json_movement_merged_and_via():
    m = RawMovement(
        "W",
        "Foo__c",
        "Insert Foo__c records",
        1,
        source_line=9,
        via_artifact="Helper",
    )
    row = to_json_movement(
        m,
        1,
        [{"name": "Update Foo__c records", "sourceLine": 10}],
    )
    assert row["sourceLine"] == 9
    assert row["mergedFrom"] == [{"name": "Update Foo__c records", "sourceLine": 10}]
    assert row["viaArtifact"] == "Helper"


def test_build_output_custom_implementation_and_called_not_found():
    m = RawMovement("R", "A__c", "Read A__c list", 1)
    out = build_output(
        "MyClass",
        [m],
        functional_process_id="fp1",
        called_classes_not_found=["Database"],
        implementation_type="custom",
    )
    assert out["calledClassesNotFound"] == ["Database"]
    assert out["dataMovements"][-1]["implementationType"] == "custom"
    assert out["dataMovements"][0]["implementationType"] == "apex"


def test_to_json_string_roundtrip():
    out = build_output("C", [], called_classes_not_found=None)
    s = to_json_string(out, indent=4)
    data = json.loads(s)
    assert data["artifact"]["name"] == "C.apex"


def test_count_movement_types():
    rows = [
        {"movementType": "E"},
        {"movementType": "R"},
        {"movementType": "R"},
        {"movementType": "W"},
        {"movementType": "X"},
        {"movementType": "X"},
        {"movementType": "Z"},
    ]
    c = count_movement_types(rows)
    assert c == {"E": 1, "R": 2, "W": 1, "X": 2}


def test_to_human_summary_empty_rows():
    out: CosmicMeasureOutput = {
        "functionalProcessId": "x",
        "artifact": {"type": "Apex", "name": "Foo"},
        "dataMovements": [],
    }
    assert to_human_summary(out) == ""


def test_to_human_summary_includes_x_count_only():
    out: CosmicMeasureOutput = {
        "functionalProcessId": "x",
        "artifact": {"type": "Apex", "name": "OnlyX"},
        "dataMovements": [
            {
                "name": "exit",
                "order": 1,
                "movementType": "X",
                "dataGroupRef": "status/errors/etc",
                "implementationType": "apex",
                "isApiCall": False,
            },
        ],
    }
    text = to_human_summary(out)
    assert "1 X" in text


def test_to_human_summary_all_note_branches():
    out: CosmicMeasureOutput = {
        "functionalProcessId": "x",
        "artifact": {"type": "Apex", "name": "Foo"},
        "dataMovements": [
            {
                "name": "a",
                "order": 1,
                "movementType": "E",
                "dataGroupRef": "G",
                "implementationType": "apex",
                "isApiCall": False,
                "mergedFrom": [{"name": "m"}],
            },
            {
                "name": "b",
                "order": 2,
                "movementType": "R",
                "dataGroupRef": "H",
                "implementationType": "apex",
                "isApiCall": False,
                "viaArtifact": "Other",
            },
        ],
    }
    text = to_human_summary(out)
    assert "1 E" in text
    assert "1 R" in text
    assert "Merged writes" in text
    assert "Artifact traversal" in text
    assert "Canonical exit" in text


def test_to_table_no_rows():
    out: CosmicMeasureOutput = {
        "functionalProcessId": "x",
        "artifact": {"type": "Apex", "name": "Foo"},
        "dataMovements": [],
    }
    assert to_table(out) == "Foo: no data movements"


def test_to_table_with_via_merged_and_not_found():
    out: CosmicMeasureOutput = {
        "functionalProcessId": "x",
        "artifact": {"type": "Apex", "name": "Demo"},
        "dataMovements": [
            {
                "name": "w",
                "order": 1,
                "movementType": "W",
                "dataGroupRef": "Z__c",
                "implementationType": "apex",
                "isApiCall": False,
                "sourceLine": 5,
                "viaArtifact": "Helper",
                "mergedFrom": [{"name": "u", "sourceLine": 6}],
            },
        ],
    }
    text = to_table(out)
    assert "| 1 | W | w | Z__c |" in text
    assert "Helper" in text
    assert "u (L6)" in text
    assert "Functional size" in text
