---
name: cosmic-lwc-measurer
description: >
  Extracts COSMIC data movements (E/R/X/W) from Salesforce Lightning Web Components
  and outputs JSON for posting to a COSMIC database. Supports standalone measurement
  and optional adapter use by other measurers such as FlexiPage.
metadata:
  category: Salesforce / COSMIC
---

# COSMIC LWC Measurer

## Goal

Produce a COSMIC measurement for one LWC bundle: classify Entry, Read, Write, and Exit movements, merge imported Apex class movements, and emit JSON matching `.cursor/skills/cosmic-measurer/reference.md`.

## Workflow

- Parse one LWC bundle directory (`<name>.js`, `<name>.html`, optional `<name>.js-meta.xml`).
- Extract LWC-native movement candidates from HTML/JS:
  - Entry: user event handlers in template.
  - Read: `@wire` and known LDS/UI API read calls.
  - Write: known LDS write calls.
  - Exit: template-bound rendered output.
- Detect imported Apex methods (`@salesforce/apex/Class.method`), resolve class files in configured search paths, run `cosmic-apex-measurer`, and merge returned rows (excluding Apex canonical exit).
- Build ordered movements through shared output logic and append canonical final exit (`Errors/notifications`).
- Optionally validate required movement types (`E/R/W/X`) for caller contracts.

CLI:

```bash
python3 .cursor/skills/cosmic-measurer/cosmic-lwc-measurer/scripts/measure_lwc.py --bundle-dir samples/cfp_FunctionalProcessVisualiser --json
python3 .cursor/skills/cosmic-measurer/cosmic-lwc-measurer/scripts/measure_lwc.py --bundle-dir samples/cfp_FunctionalProcessVisualiser --required-type W --apex-search-paths samples
```

## Validation

- `movementType` must be one of `E`, `R`, `W`, `X`.
- Output always includes canonical final Exit `Errors/notifications` (`dataGroupRef: User`).
- Apex-imported rows include `viaArtifact` and use `implementationType: apex`.
- Missing Apex classes do not fail measurement; they are reported in `traversalWarnings`.
- Regression sample: `samples/cfp_FunctionalProcessVisualiser` against `samples/expected/cfp_FunctionalProcessVisualiser.lwc.expected.json`.

## Output

Human summary:

- Functional size with E/R/W/X counts and total CFP.
- Notes about traversal warnings and canonical exit.

JSON:

```json
{
  "functionalProcessId": "<Id>",
  "artifact": { "type": "LWC", "name": "cfp_FunctionalProcessVisualiser" },
  "dataMovements": [
    { "name": "Receive user interaction", "order": 1, "movementType": "E", "dataGroupRef": "User", "implementationType": "lwc", "isApiCall": false },
    { "name": "Read data via LWC data services", "order": 2, "movementType": "R", "dataGroupRef": "Unknown", "implementationType": "lwc", "isApiCall": false },
    { "name": "Errors/notifications", "order": 3, "movementType": "X", "dataGroupRef": "User", "implementationType": "lwc", "isApiCall": false }
  ],
  "traversalWarnings": []
}
```
