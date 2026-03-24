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
- Detect configured page actions (`force:highlightsPanel`) and surface them as investigation notes only.
- Detect record field bindings (`Record.*`) and dynamic related lists for Read/Exit candidates.
- Detect tab-bound LWCs and emit delegated `lwcCandidateMeasurements` entries for follow-up measurement.
- Build ordered movements using shared output logic and append canonical final exit (`Errors/notifications`).
- Output JSON to stdout or file.

CLI:

```bash
python3 .cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts/measure_flexipage.py samples/cfp_FunctionalProcess_Record_Page.flexipage-meta.xml --json
python3 .cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts/measure_flexipage.py samples/cfp_FunctionalProcess_Record_Page.flexipage-meta.xml -o out.json --fp-id 001xxx
```

## Validation

- `movementType` must be one of `E`, `R`, `W`, `X`.
- FlexiPage action config does not create counted E/W rows in this skill version.
- Configured actions appear in notes (`traversalWarnings`) for follow-up as separate functional processes.
- Tab-bound LWCs are emitted as delegated candidates with `requiredMovementTypes` including `W`.
- Output includes canonical final Exit `Errors/notifications` (`dataGroupRef: User`).
- Data movement ordering and dedup rely on shared COSMIC output module.
- Regression sample: `samples/cfp_FunctionalProcess_Record_Page.flexipage-meta.xml` against `samples/expected/cfp_FunctionalProcess_Record_Page.flexipage.expected.json`.

## Output

Human summary:

- Functional size with E/R/W/X counts and total CFP.
- Notes about canonical exit and action follow-up items.

JSON:

```json
{
  "functionalProcessId": "<Id>",
  "artifact": { "type": "FlexiPage", "name": "cfp_FunctionalProcess_Record_Page" },
  "dataMovements": [
    { "name": "Read page record (cfp_FunctionalProcess__c)", "order": 1, "movementType": "R", "dataGroupRef": "cfp_FunctionalProcess__c", "implementationType": "flexipage", "isApiCall": false },
    { "name": "Read related list cfp_functionalsteps__r", "order": 2, "movementType": "R", "dataGroupRef": "cfp_functionalsteps__c", "implementationType": "flexipage", "isApiCall": false },
    { "name": "Display page record (cfp_FunctionalProcess__c)", "order": 3, "movementType": "X", "dataGroupRef": "cfp_FunctionalProcess__c", "implementationType": "flexipage", "isApiCall": false },
    { "name": "Display related list cfp_functionalsteps__r", "order": 4, "movementType": "X", "dataGroupRef": "cfp_functionalsteps__c", "implementationType": "flexipage", "isApiCall": false },
    { "name": "Errors/notifications", "order": 5, "movementType": "X", "dataGroupRef": "User", "implementationType": "flexipage", "isApiCall": false }
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
