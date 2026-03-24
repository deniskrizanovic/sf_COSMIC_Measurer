---
name: Highlights Panel R/X Measurement Plan
overview: Revise FlexiPage measurement rules so highlights panel fields are explicitly counted as Read and Exit movements, with dedicated movement rows.
todos:
  - id: add-highlights-presence-detection
    content: Detect highlights panel presence and generate explicit highlights R/X raw movements
    status: pending
  - id: wire-into-output-ordering
    content: Integrate highlights movements into movement list with stable ordering and dedup-safe naming
    status: pending
  - id: update-tests
    content: Add parser/CLI assertions for explicit highlights rows and output ordering
    status: pending
  - id: update-docs
    content: Align SKILL.md and PYTHON_DESIGN.md with explicit highlights R/X policy
    status: pending
isProject: false
---

# Highlights Panel R/X Measurement Plan

## Decision Captured

- Count values shown in `force:highlightsPanel` as explicit COSMIC movements:
  - `R`: read highlighted fields from the primary record.
  - `X`: display highlighted fields to the user.
- Keep these as dedicated rows (not just implied by generic page-record rows).

## Rule Update Scope

- Update FlexiPage parsing/measuring logic to emit two explicit movements when a record page contains `force:highlightsPanel`:
  - `Read highlights panel fields (<SObject>)`
  - `Display highlights panel fields (<SObject>)`
- Preserve existing action handling policy for `actionNames` (warnings/candidates) unless separately changed.

## Target Files

- Measurement logic: `[/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts/flexipage_parser.py](/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts/flexipage_parser.py)`
- Measurer orchestration/output checks: `[/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts/measure_flexipage.py](/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts/measure_flexipage.py)`
- Parser tests: `[/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/tests/test_flexipage_parser.py](/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/tests/test_flexipage_parser.py)`
- CLI/integration tests: `[/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/tests/test_measure_flexipage_cli.py](/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/tests/test_measure_flexipage_cli.py)`
- Skill docs/design notes: `[/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/SKILL.md](/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/SKILL.md)`, `[/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/PYTHON_DESIGN.md](/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/PYTHON_DESIGN.md)`

## Verification

- Add/update tests to assert that pages with `force:highlightsPanel` include the two dedicated rows.
- Confirm ordering remains stable and canonical final `Errors/notifications` exit still appears.
- Confirm no duplicate dedup side-effects remove the new highlights rows.

## WorkOrder Interpretation

- For `[/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/samples/flexipages/WorkOrder.flexipage](/Users/dkrizanovic/My Drive/salesforce/sf_COSMIC-Measurer/samples/flexipages/WorkOrder.flexipage)`, the header highlights panel will contribute one explicit `R` and one explicit `X` row in addition to other page movements.

