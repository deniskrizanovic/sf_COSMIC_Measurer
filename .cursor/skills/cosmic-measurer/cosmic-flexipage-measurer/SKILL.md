---
name: cosmic-flexipage-measurer
description: >
  Extracts COSMIC data movements (E/R/X/W) from Salesforce FlexiPage
  .flexipage-meta.xml files and outputs JSON for posting to a COSMIC database.
  Use when measuring Record Pages for functional size and UI-driven movements.
metadata:
  category: Salesforce / COSMIC
---

# COSMIC FlexiPage Measurer

## Goal

Produce a COSMIC measurement for one FlexiPage metadata artifact focused on page display behavior: classify Read and Exit movements, assign order, and emit JSON matching `.cursor/skills/cosmic-measurer/reference.md`.

## Workflow

- Parse one `.flexipage-meta.xml` file.
- Extract page context (`masterLabel`, `sobjectType`, `type`).
- Detect `force:highlightsPanel` and count explicit highlights display movements (`R` + `X`) for the primary record.
- Detect configured page actions (`force:highlightsPanel`) and surface them as investigation notes only.
- Detect record field bindings (`Record.*`) and dynamic related lists for Read/Exit candidates.
- Detect tab-bound LWCs, measure them inline via the LWC measurer by default, and still emit `lwcCandidateMeasurements` for traceability.
- Detect tab-bound Flow interviews (`flowruntime:interview`), measure them inline via the Flow measurer by default, and emit `flowCandidateMeasurements` for traceability.
- Build ordered movements using shared output logic and append canonical final exit (`Errors/notifications`).
- Output JSON to stdout or file.

CLI:

```bash
python3 .cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts/measure_flexipage.py samples/cfp_FunctionalProcess_Record_Page.flexipage-meta.xml --json
python3 .cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts/measure_flexipage.py samples/cfp_FunctionalProcess_Record_Page.flexipage-meta.xml -o out.json --fp-id 001xxx
python3 .cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts/measure_flexipage.py samples/cfp_FunctionalProcess_Record_Page.flexipage-meta.xml --json --no-resolve-lwc-candidates
python3 .cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts/measure_flexipage.py samples/cfp_FunctionalProcess_Record_Page.flexipage-meta.xml --json --no-resolve-flow-candidates
```

## Validation

- `movementType` must be one of `E`, `R`, `W`, `X`.
- `force:highlightsPanel` contributes explicit `R` and `X` rows for highlighted primary-record values.
- FlexiPage action config does not create counted E/W rows in this skill version.
- Configured actions appear in notes (`traversalWarnings`) for follow-up as separate functional processes.
- Tab-bound LWCs are traversed by default and inlined into merged movement ordering.
- Tab-bound Flow interviews are traversed by default and inlined into merged movement ordering.
- `lwcCandidateMeasurements` remain in output for traceability and follow-up validation.
- `flowCandidateMeasurements` remain in output for traceability and follow-up validation.
- Output includes canonical final Exit `Errors/notifications` (`dataGroupRef: status/errors/etc`).
- Data movement ordering and dedup rely on shared COSMIC output module.
- Regression sample: `samples/cfp_FunctionalProcess_Record_Page.flexipage-meta.xml` against `expected/cfp_FunctionalProcess_Record_Page.flexipage.expected.json`.

## Output

Human summary (default, table-first with roll-up totals):

- Run the script first and use its produced movement rows as the single source of truth for human output ordering.
- Present data movements in a markdown table first (`order`, `movementType`, `name`, `dataGroupRef`, `implementationType`, `isApiCall`), including inlined tab-bound LWC movements.
- Render markdown tables directly in the assistant response (do not wrap the full human summary in fenced code blocks).
- Do not collapse, regroup, or re-sort movements (for example, never present all `R` rows first and `X` rows later unless that is exactly what the script emitted).
- Do not omit inferred or placeholder rows emitted by the script (for example tab-bound `tbc` inspection rows) in full-output mode.
- Present a second compact table for totals (`E`, `R`, `W`, `X`, `Total CFP`).
- Include short notes for canonical exit and action follow-up items.
- Present merged roll-up totals (FlexiPage + traversed LWC movements) as the default total view.

JSON (optional / export-oriented):

```json
{
  "functionalProcessId": "<Id>",
  "artifact": { "type": "FlexiPage", "name": "cfp_FunctionalProcess_Record_Page" },
  "dataMovements": [
    { "name": "Read page record (cfp_FunctionalProcess__c)", "order": 1, "movementType": "R", "dataGroupRef": "cfp_FunctionalProcess__c", "implementationType": "flexipage", "isApiCall": false },
    { "name": "Read related list cfp_functionalsteps__r", "order": 2, "movementType": "R", "dataGroupRef": "cfp_functionalsteps__c", "implementationType": "flexipage", "isApiCall": false },
    { "name": "Display page record (cfp_FunctionalProcess__c)", "order": 3, "movementType": "X", "dataGroupRef": "cfp_FunctionalProcess__c", "implementationType": "flexipage", "isApiCall": false },
    { "name": "Display related list cfp_functionalsteps__r", "order": 4, "movementType": "X", "dataGroupRef": "cfp_functionalsteps__c", "implementationType": "flexipage", "isApiCall": false },
    { "name": "Errors/notifications", "order": 5, "movementType": "X", "dataGroupRef": "status/errors/etc", "implementationType": "flexipage", "isApiCall": false }
  ],
  "traversalWarnings": [
    "Investigate configured page actions as separate functional processes: Delete, cfp_FunctionalProcess__c.Create_CRUDL"
  ],
  "lwcCandidateMeasurements": [
    {
      "functionalProcessId": "<Id>",
      "artifact": { "type": "LWC", "name": "cfp_FunctionalProcessVisualiser" },
      "sourceArtifact": { "type": "FlexiPage", "name": "cfp_FunctionalProcess_Record_Page" },
      "tabContext": { "identifier": "flexipage_tab5", "title": "Visualiser" },
      "requiredMovementTypes": ["W"],
      "notes": "Run dedicated lwc-measurer to extract concrete E/R/X/W movements."
    }
  ]
}
```

Default response behavior:

- If the user asks to "measure" a FlexiPage (or uses phrasing like "measure <file>"), treat it as a full-output request by default.
- Full-output request means always return:
  - movement table (ordered rows),
  - totals table (`E`, `R`, `W`, `X`, `Total CFP`),
  - all notes/warnings (including canonical final exit and follow-up investigation notes).
- In full-output mode, the assistant must mirror script output ordering and row cardinality exactly for movement rows (no manual re-interpretation).
- Default to merged roll-up totals (FlexiPage + traversed tab-bound LWC movements).
- Default to merged roll-up totals (FlexiPage + traversed tab-bound LWC/Flow movements).
- Traverse tab-bound LWCs by default before producing totals.
- Traverse tab-bound Flows by default before producing totals.
- Use `--no-resolve-lwc-candidates` to skip inline LWC traversal when needed.
- Use `--no-resolve-flow-candidates` to skip inline Flow traversal when needed.
- Include JSON only when explicitly requested (for example: "as JSON", "for posting", or "export").
- Use fenced code blocks only when the user explicitly asks for raw/plain-text output or literal markdown source.
