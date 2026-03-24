---
name: Flow Part5 Screens
overview: Implement Part 5 screen parsing for the Flow measurer with fine-grained per-data-group counting and explicit handling of display-only screens as Exit movements.
todos:
  - id: implement-screen-parser
    content: Add screen movement extraction with per-data-group E/X classification in flow_parser.py
    status: completed
  - id: wire-screen-movements
    content: Integrate screen entries/exits into measure_flow.py before build_output
    status: completed
  - id: add-screen-fixtures-tests
    content: Create conftest fixtures and parser tests for display/input/datatable and primitive exclusion
    status: completed
  - id: add-integration-tests
    content: Extend measure_flow integration tests for mixed movements and canonical exit ordering
    status: completed
  - id: docs-sync
    content: Update PYTHON_DESIGN.md with final screen parsing rules and examples
    status: cancelled
isProject: false
---

# Part 5 Screens Plan (Flow Measurer)

## Goal

Add deterministic screen parsing so Flow screens produce COSMIC `E`/`X` movements per distinct data group, with display-only screens contributing `X` when they show resolved business data.

## Scope

- Extend Flow parsing only in `cosmic-flow-measurer`.
- Reuse shared ordering/dedup/output behavior from `shared/output.py`.
- Keep non-screen flow types and subflow traversal out of scope.

## Files To Change

- [/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flow-measurer/scripts/flow_parser.py](/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flow-measurer/scripts/flow_parser.py)
- [/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flow-measurer/scripts/measure_flow.py](/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flow-measurer/scripts/measure_flow.py)
- [/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flow-measurer/tests/conftest.py](/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flow-measurer/tests/conftest.py)
- [/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flow-measurer/tests/test_flow_parser.py](/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flow-measurer/tests/test_flow_parser.py)
- [/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flow-measurer/tests/test_measure_flow.py](/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flow-measurer/tests/test_measure_flow.py)
- Optional docs sync: [/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flow-measurer/PYTHON_DESIGN.md](/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flow-measurer/PYTHON_DESIGN.md)

## Parsing Design

- Add `find_screen_movements(root, variables) -> tuple[list[RawMovement], list[RawMovement]]` returning `(screen_entries, screen_exits)`.
- Parse each `<screens>` element and inspect child field/component definitions.
- Resolve references to data groups using this precedence:
  - Bound SObject variable `objectType`
  - Record collection variable `objectType`
  - Explicit object-like reference in field binding path
  - Fallback: skip unresolved primitives/non-business refs
- Build sets per screen:
  - `entry_data_groups`: data groups with editable input interactions
  - `exit_data_groups`: data groups displayed/rendered to user
- Emit one movement per distinct data group in each set (fine-grained policy).
- Count display-only screens as `X` when `exit_data_groups` is non-empty.

## Classification Rules

- `E` candidates:
  - Input-style fields/components that write into SObject-bound variables.
  - User-editable controls bound to SObject fields/records.
- `X` candidates:
  - DisplayText/readonly fields/components rendering SObject-derived values.
  - Datatable/repeater style outputs bound to record collections.
  - Confirm/summary screens that display resolved business data.
- Exclusions:
  - Pure primitive/local UI values without SObject/business data-group binding.
  - Navigation-only or static text without business data references.

## Integration Points

- In `measure_flow.py`, merge `screen_entries` with existing entries and `screen_exits` with existing exits before `build_output`.
- Keep canonical `Errors/notifications` exit behavior unchanged in shared output.
- Rely on existing output dedup/order so movement order remains deterministic.

## Test Strategy

- Add focused fixtures in `conftest.py`:
  - Screen with mixed input + display on same data group
  - Screen with two different data groups
  - Display-only confirmation screen
  - Screen with primitive-only fields (no movement)
  - Datatable bound to record collection
- Add parser unit tests in `test_flow_parser.py`:
  - `test_find_screen_entries_per_data_group`
  - `test_find_screen_exits_per_data_group`
  - `test_display_only_screen_counts_as_exit`
  - `test_screen_dedups_same_data_group_within_screen`
  - `test_screen_skips_unresolved_primitive_refs`
  - `test_screen_handles_multiple_screens_accumulation`
- Add integration tests in `test_measure_flow.py`:
  - Ensure final output includes screen `E/X` plus canonical exit last.
  - Ensure mixed flow (lookups/mutations/screens) preserves expected type order.

## Acceptance Criteria

- Screen-derived movements appear in JSON output with `implementationType: flow`.
- Fine-grained count is enforced: one movement per distinct data group.
- Display-only screens produce `X` when bound business data is shown.
- Existing non-screen tests keep passing.
- Canonical exit remains last regardless of screen exits.

## Risks And Mitigations

- XML shape variance across Flow versions: keep parser tolerant and test with minimal+realistic fixtures.
- False positives from primitive bindings: require SObject/objectType resolution before movement emission.
- Overcounting due to repeated fields: dedup by `(movementType, dataGroupRef, screenName)` before shared output ordering.

## Execution Sequence

1. Implement screen parsing helpers in `flow_parser.py`.
2. Wire screen movements into `measure_flow.py` assembly.
3. Add fixtures and parser tests.
4. Add integration coverage for ordering + canonical exit.
5. Run flow measurer test suite and adjust edge-case parsing.

