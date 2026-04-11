---
name: path-component-dms
overview: Add explicit Path component data movements to the FlexiPage measurer so Path contributes one Read and one Exit movement as separate rows with stable ordering and test coverage.
todos:
  - id: detect-path-component
    content: Add parser detection for runtime_sales_pathassistant:pathAssistant component instances
    status: pending
  - id: emit-path-rx-movements
    content: Create Path movement builder that emits separate R and X RawMovement rows
    status: pending
  - id: wire-into-parse-flow
    content: Merge Path rows into parse_flexipage movement assembly without breaking existing ordering
    status: pending
  - id: add-parser-tests
    content: Add unit tests validating Path emits distinct R and X rows and expected pairing/order
    status: pending
  - id: add-cli-regression-test
    content: Add CLI test asserting Path rows are present in output dataMovements
    status: pending
  - id: verify-flexipage-suite
    content: Run FlexiPage measurer tests and validate no regressions
    status: pending
isProject: false
---

# Path Component DM Plan

## Goal
Add Path-specific data movement extraction in the FlexiPage measurer so `runtime_sales_pathassistant:pathAssistant` emits two distinct rows: one `R` and one `X`.

## Scope
- Update FlexiPage parsing/movement construction in [`/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts/flexipage_parser.py`](/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts/flexipage_parser.py)
- Keep ordering/dedup behavior compatible with [`/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts/measure_flexipage.py`](/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts/measure_flexipage.py)
- Add parser + CLI tests in:
  - [`/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/tests/test_flexipage_parser.py`](/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/tests/test_flexipage_parser.py)
  - [`/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/tests/test_measure_flexipage_cli.py`](/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/tests/test_measure_flexipage_cli.py)

## Implementation Steps
1. Add explicit Path detector(s) in the parser for `runtime_sales_pathassistant:pathAssistant` component instances.
2. Implement a semantic movement builder that returns exactly two `RawMovement` rows for each detected Path instance:
- `R` row (Path state/steps read)
- `X` row (Path rendered/displayed)
3. Integrate Path rows into the main FlexiPage movement list in `parse_flexipage()` so they pass through existing output ordering and canonical-exit handling.
4. Ensure naming is self-descriptive and stable for dedupe behavior; if needed, include region/identifier context to avoid accidental collapse of distinct Path instances.
5. Add parser-level unit tests proving:
- Path presence yields both `R` and `X`
- `R`/`X` are separate rows (not merged)
- expected order pairing is preserved.
6. Add CLI-level regression test with a Path component fixture (can use WorkOrder-like XML shape) asserting both rows appear in `dataMovements`.
7. Run FlexiPage measurer tests and confirm no regressions in highlights/related-list/tab movement expectations.

## Expected Outcome
- FlexiPage outputs include a new Path pair of DMs (`R` + `X`) whenever the Path component is present.
- Behavior remains backward-compatible for existing movement families and canonical output ordering.
