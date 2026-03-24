---
name: tab-level-flexipage-movements
overview: Extend the FlexiPage measurer to derive data movements from each tab's bound components and emit them in the main movement table with tab name appended to movement names.
todos:
  - id: add-tab-movement-extractor
    content: Implement semantic tab-component movement extraction helpers in flexipage_parser.py with tab-suffixed movement names
    status: pending
  - id: enrich-tab-binding-context
    content: Expose component property context needed to infer movements for relatedList, flowruntime, and relatedRecord tab targets
    status: pending
  - id: merge-tab-movements-in-main-output
    content: Integrate tab-derived movements into measure_file output pipeline without duplicating LWC delegated rows
    status: pending
  - id: add-warning-coverage
    content: Add warnings for unsupported/partially inferred tab components and fallback data groups
    status: pending
  - id: expand-tests
    content: Add parser and CLI tests for tab-derived movements and WorkOrder regression with tab notes preserved
    status: pending
  - id: verify-measurer-behavior
    content: Run flexipage measurer tests and validate final WorkOrder table output includes tab-appended movement rows
    status: pending
isProject: false
---

# Tab-Level FlexiPage Movement Extraction Plan

## Objective

Update the FlexiPage measurer so it inspects each tab body, derives data movements from the tab’s target components, and appends tab context to movement names in the main output table (same pattern as delegated LWC rows).

## Current Baseline

- Parser already resolves tab-to-component bindings via `extract_tab_component_bindings()` in [/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts/flexipage_parser.py](/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts/flexipage_parser.py).
- CLI currently emits tab labels and tab-component binding notes, and delegates tab-bound LWCs in [/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts/measure_flexipage.py](/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts/measure_flexipage.py).
- Existing tests cover tab labels, binding warnings, LWC delegation, and default ordering in:
  - [/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/tests/test_flexipage_parser.py](/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/tests/test_flexipage_parser.py)
  - [/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/tests/test_measure_flexipage_cli.py](/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/tests/test_measure_flexipage_cli.py)

## Implementation Steps

1. Add a tab-component movement extractor in `flexipage_parser.py`:

- Introduce semantic helper(s) that map each `TabComponentBinding` to zero or more `RawMovement` rows.
- Start with deterministic rules for known component families already present in sample pages:
  - `force:relatedListSingleContainer` and `lst:dynamicRelatedList` -> `R` + `X` using `relatedListApiName` normalized to data-group.
  - `flowruntime:interview` -> conservative `X` movement for rendered flow output, with explicit notes for potential E/W follow-up.
  - `console:relatedRecord` -> `R` + `X` for displayed related record details (derive data-group from `lookupFieldName` / quick action context where possible; fallback to stable placeholder + warning).
  - LWC bindings continue through existing delegation path (no duplicate counting).
- Append  `| tab:<TabTitle>` to generated movement names for all tab-derived rows.

1. Ensure component metadata is available for extraction:

- Extend tab binding/facet indexing to include component properties needed for movement inference (for example `relatedListApiName`, `flowName`, `lookupFieldName`, action names) while keeping the binding structure self-describing.
- Keep unknown/unsupported components traceable via warnings, not silent skips.

1. Integrate tab-derived rows into the main output in `measure_flexipage.py`:

- Merge tab-derived rows into `movements` before `build_output()` so they naturally appear in the primary table/JSON order.
- Preserve existing canonical exit behavior and primary-record row promotion.
- Keep dedup stable by data-group + movement type + tab suffix so shared components on different tabs remain distinct.

1. Expand warning/traceability behavior:

- Keep existing tab labels and tab-component bindings warnings.
- Add targeted warnings for unsupported or partially inferred tab components and fallback data groups.

1. Update and add tests:

- Parser tests for new per-component tab movement inference and tab-suffixed naming.
- CLI tests asserting tab-derived rows appear in `dataMovements` with `| tab:<name>` for non-LWC components.
- Regression test on `samples/flexipages/WorkOrder.flexipage` (or `.flexipage-meta.xml` alias) confirming tabs contribute movements and notes remain present.
- Validate no double counting when a tab hosts LWC (delegated path only once).

1. Validate with local test run:

- Run FlexiPage measurer test suite and verify table output on `WorkOrder.flexipage` includes tab-derived rows and current warnings.

## Guardrails

- Do not remove existing page-level read/display behavior unless duplicated by explicit tab-derived logic.
- Maintain canonical final `Errors/notifications` exit ordering.
- Prefer explicit, self-documenting semantic helper functions over ad-hoc branching in `measure_file()`.

