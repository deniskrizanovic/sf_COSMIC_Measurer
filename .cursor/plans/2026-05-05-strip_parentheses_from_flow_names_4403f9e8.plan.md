---
name: Strip parentheses from flow names
overview: Remove all parenthetical segments from generated data movement names in the flow measurer — both in the Python source and the corresponding expected JSON fixtures and tests.
todos:
  - id: edit-flow-parser
    content: "Edit flow_parser.py: remove all (...) suffixes from the 8 name f-strings"
    status: completed
  - id: edit-expected-json
    content: Update expected/cfp_createCRUDLwithRelatedLists.expected.json to strip parentheses from names
    status: completed
  - id: edit-tests
    content: Update test_flow_parser.py and test_measure_flow.py assertions that reference parenthesised name fragments
    status: completed
  - id: edit-skill-md
    content: Update SKILL.md example JSON to match new name format
    status: completed
  - id: run-tests
    content: Run pytest to confirm all flow measurer tests pass
    status: completed
isProject: false
---

# Strip Parentheses from Flow Movement Names

## What changes

Every `name` produced by [`flow_parser.py`](.cursor/skills/cosmic-measurer/cosmic-flow-measurer/scripts/flow_parser.py) currently appends contextual detail in `(...)`. The new format strips all parenthetical suffixes, with one exception: Screen display gets the data group prepended as the primary label.

| Current | New |
|---------|-----|
| `Read {obj} ({label})` | `Read {obj}` |
| `{verb} {obj} ({label})` | `{verb} {obj}` |
| `Trigger record ({object})` | `Trigger record` |
| `Receive {var.name} ({object_type})` | `Receive {var.name}` |
| `Receive recordId ({obj})` | `Receive recordId` |
| `Output {var.name} ({object_type})` | `Output {var.name}` |
| `Screen input ({screen_name}) ({dg})` | `Screen input` |
| `Screen display ({screen_name}) ({dg})` | `Display {dg}` |

## Files to change

### 1. `flow_parser.py` — 8 f-string edits
All name-building expressions at lines 134, 166, 203, 215, 225, 244, 416, 424.

### 2. `expected/cfp_createCRUDLwithRelatedLists.expected.json` — regression fixture
Update the 6 names that contain parentheses (lines 9, 18, 27, 36, 45, 54).

### 3. Tests — update hardcoded name assertions
- [`test_flow_parser.py`](.cursor/skills/cosmic-measurer/cosmic-flow-measurer/tests/test_flow_parser.py): line 146 checks `"getFunctionalProcess" in reads[0].name` — will need to change to check the object name instead (the label is no longer in the name).
- [`test_measure_flow.py`](.cursor/skills/cosmic-measurer/cosmic-flow-measurer/tests/test_measure_flow.py): lines 244/246 check `"Trigger record (Program__c)"` and `"Receive programIds (Program__c)"` — strip the `(...)` from those assertions.
- [`test_flow_movements.py`](.cursor/skills/cosmic-measurer/cosmic-flow-measurer/tests/test_flow_movements.py): line 128–137 (`test_build_output_caps_movement_name_at_80_characters`) constructs a long `"Read VeryLong..."` name — no parentheses, unaffected.

### 4. SKILL.md — update JSON example
The example JSON in [`SKILL.md`](.cursor/skills/cosmic-measurer/cosmic-flow-measurer/SKILL.md) (lines 118–122) shows names with parentheses — update to match new format.

## No other files affected
- Apex/LWC/FlexiPage measurers use their own name logic; not touched.
- `cfp_getDataMovements.expected.json` and `dk_PASSurveyToAssetBatch_facilityIds.json` are Apex/LWC fixtures; not touched.
