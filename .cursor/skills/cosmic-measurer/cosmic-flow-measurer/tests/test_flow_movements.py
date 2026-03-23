"""Tests for shared output functions with flow-specific inputs."""

import json

from shared.models import RawMovement
from shared.output import (
    CANONICAL_EXIT_DATA_GROUP_REF,
    CANONICAL_EXIT_NAME,
    build_output,
    count_movement_types,
    order_movements,
    to_human_summary,
    to_json_string,
    to_table,
)


def test_order_movements_e_r_w_x_order():
    e = RawMovement("E", "Account", "Receive recordId", 1)
    r = RawMovement("R", "Account", "Read Account", 2)
    w = RawMovement("W", "Account", "Create Account", 3)
    x = RawMovement("X", "Contact", "Output result", 4)
    ordered = order_movements([w, x, e, r])
    types = [m.movement_type for m, _ in ordered]
    assert types == ["E", "R", "W", "X"]


def test_write_dedup_same_object():
    w1 = RawMovement("W", "Case", "Create Case", 1)
    w2 = RawMovement("W", "Case", "Update Case", 2)
    ordered = order_movements([w1, w2])
    assert len(ordered) == 1
    assert ordered[0][1] == [{"name": "Update Case"}]


def test_write_no_dedup_different_objects():
    w1 = RawMovement("W", "Case", "Create Case", 1)
    w2 = RawMovement("W", "Account", "Update Account", 2)
    ordered = order_movements([w1, w2])
    assert len(ordered) == 2


def test_canonical_exit_appended_last():
    r = RawMovement("R", "Account", "Read Account", 1)
    out = build_output("Flow", "TestFlow", [r], implementation_type="flow")
    dm = out["dataMovements"]
    assert dm[-1]["name"] == CANONICAL_EXIT_NAME
    assert dm[-1]["dataGroupRef"] == CANONICAL_EXIT_DATA_GROUP_REF
    assert dm[-1]["movementType"] == "X"


def test_canonical_exit_with_no_other_exits():
    out = build_output("Flow", "EmptyFlow", [], implementation_type="flow")
    dm = out["dataMovements"]
    assert len(dm) == 1
    assert dm[0]["name"] == CANONICAL_EXIT_NAME


def test_build_output_artifact_type_is_flow():
    out = build_output("Flow", "TestFlow", [], implementation_type="flow")
    assert out["artifact"]["type"] == "Flow"
    assert out["artifact"]["name"] == "TestFlow"


def test_build_output_implementation_type_is_flow():
    r = RawMovement("R", "Account", "Read Account", 1)
    out = build_output("Flow", "TestFlow", [r], implementation_type="flow")
    for dm in out["dataMovements"]:
        assert dm["implementationType"] == "flow"


def test_build_output_json_schema_matches_reference():
    r = RawMovement("R", "Account", "Read Account", 1)
    out = build_output("Flow", "TestFlow", [r], functional_process_id="FP-1", implementation_type="flow")
    assert "functionalProcessId" in out
    assert out["functionalProcessId"] == "FP-1"
    for dm in out["dataMovements"]:
        assert "name" in dm
        assert "order" in dm
        assert "movementType" in dm
        assert "dataGroupRef" in dm
        assert "implementationType" in dm
        assert "isApiCall" in dm


def test_count_movement_types_flow():
    out = build_output(
        "Flow", "F", [
            RawMovement("E", "A", "entry", 1),
            RawMovement("R", "B", "read", 2),
            RawMovement("W", "C", "write", 3),
        ],
        implementation_type="flow",
    )
    counts = count_movement_types(out["dataMovements"])
    assert counts == {"E": 1, "R": 1, "W": 1, "X": 1}


def test_to_human_summary_flow():
    out = build_output(
        "Flow", "F", [RawMovement("R", "A", "Read A", 1)],
        implementation_type="flow",
    )
    text = to_human_summary(out)
    assert "Functional size" in text
    assert "1 R" in text
    assert "1 X" in text


def test_to_table_flow():
    out = build_output(
        "Flow", "MyFlow", [RawMovement("R", "A", "Read A", 1)],
        implementation_type="flow",
    )
    text = to_table(out)
    assert "**MyFlow** (Flow)" in text
    assert "| Order |" in text


def test_to_json_string_roundtrip():
    out = build_output("Flow", "F", [], implementation_type="flow")
    s = to_json_string(out, indent=2)
    data = json.loads(s)
    assert data["artifact"]["type"] == "Flow"
    assert len(data["dataMovements"]) == 1
