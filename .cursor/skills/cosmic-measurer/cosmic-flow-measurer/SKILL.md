---
name: cosmic-flow-measurer
description: >
  Extracts COSMIC data movements (E/R/X/W) from Salesforce Flow .flow-meta.xml
  files and outputs JSON for posting to a COSMIC database. Use when measuring
  Flows for functional size, analyzing flow XML for data movements, or generating
  cfp_Data_Movements__c from Flow metadata.
metadata:
  category: Salesforce / COSMIC
---

# COSMIC Flow Measurer

## Goal

Produce a **COSMIC measurement** for one Salesforce Flow: classify data movements as Entry, Read, Write, or Exit, assign order, and emit JSON matching [reference.md](../reference.md) for attachment to a functional process.

---

## Workflow

Inspects `.flow-meta.xml` files, identifies data movements, and produces JSON in the format defined in [reference.md](../reference.md).

### Scope

- **Single flow file** per measurement
- **Flow types**: Screen Flow, AutoLaunched Flow, Record-Triggered Flow, Scheduled Flow, Platform Event Flow
- **No subflow traversal** (deferred to future iteration)
- **Invocable Apex**: Supported for `actionCalls` where `actionType=apex` by calling the Apex measurer

### Entry (E)

- **Input variables**: `<variables>` with `<isInput>true</isInput>` and SObject `objectType`
- **recordId**: Common `String` input variable — infer object from the first `recordLookup` that filters by `Id = {!recordId}`
- **Record-triggered flows**: Triggering record from `<start>` element's `<object>`
- **implementationType**: `flow`

### Read (R)

- **recordLookups**: `<recordLookups>` elements — extract object from `<object>` child element
- **implementationType**: `flow`

### Invocable Apex integration

- **Detection**: `<actionCalls>` with `<actionType>apex</actionType>`
- **Class resolution**: resolve `<actionName>` to `<actionName>.cls` in search paths
- **Measurement source**: calls `cosmic-apex-measurer` and merges Apex movements (`E/R/W/X`) into Flow output
- **Fallback**: unresolved classes do not fail measurement; output includes `invocableApexClassesNotFound`
- **Provenance**: merged rows include `viaArtifact` showing the originating invocable Apex action

### Write (W)

- **recordCreates / recordUpdates / recordDeletes**: Extract object from `<object>` child or resolve from `<inputReference>` via variable's `<objectType>`
- **Deduplication**: Multiple mutations to the same data group count as one Write (same COSMIC rule as Apex)
- **implementationType**: `flow`

### Exit (X)

- **Output variables**: `<variables>` with `<isOutput>true</isOutput>` and SObject type
- **Canonical rule**: After all other movements, append one final Exit — **Errors/notifications**, last in order. `dataGroupRef: status/errors/etc`. See [reference.md](../reference.md).
- **implementationType**: `flow`

### Procedural steps

1. **Read** the `.flow-meta.xml` file
2. **Parse** XML, extract flow metadata (name, processType, apiVersion)
3. **Extract** variables (for inputReference resolution and Entry/Exit detection)
4. **Scan** for:
   - Input variables / start element → Entry
   - `recordLookups` → Read
   - `recordCreates` / `recordUpdates` / `recordDeletes` → Write
   - Output variables → Exit
5. **Append** canonical Errors/notifications (X) last
6. **Assign order**: E first, then R/W in document order, then X last
7. **Output** JSON to stdout or write to file

### Python script (deterministic)

```bash
python3 .cursor/skills/cosmic-measurer/cosmic-flow-measurer/scripts/measure_flow.py path/to/Flow.flow-meta.xml
python3 ... measure_flow.py Flow.flow-meta.xml [-o output.json] [--fp-id 001xxx] [--json]
python3 ... measure_flow.py Flow.flow-meta.xml --apex-search-paths samples,force-app/main/default/classes
python3 ... measure_flow.py Flow.flow-meta.xml --no-invocable-apex
```

Run tests:

```bash
python3 -m pytest .cursor/skills/cosmic-measurer/cosmic-flow-measurer/tests/ -v
```

---

## Validation

- **Schema**: Every `movementType` is exactly `E`, `R`, `X`, or `W`; `dataGroupRef` uses object API names as in [reference.md](../reference.md).
- **Regression**: For [samples/cfp_createCRUDLwithRelatedLists.flow-meta.xml](../../../samples/cfp_createCRUDLwithRelatedLists.flow-meta.xml), compare output to [expected/cfp_createCRUDLwithRelatedLists.expected.json](../../../expected/cfp_createCRUDLwithRelatedLists.expected.json).
- **Canonical exit**: Last movement is always Errors/notifications (status/errors/etc).
- **Deduplication**: Confirm merged Writes to the same data group appear as a single W.

---

## Output

### Human summary (always)

- Present data movements in a markdown table first (`order`, `movementType`, `name`, `dataGroupRef`, `implementationType`, `artifactName`, `isApiCall`).
- **Functional size:** Count E, R, W, and X after deduplication; CFP = E + R + W + X.
- **Notes:** Canonical exit, merged writes (if any).

### JSON

```json
{
  "functionalProcessId": "<placeholder or user-provided>",
  "artifact": { "type": "Flow", "name": "FlowApiName.flow" },
  "dataMovements": [
    { "name": "Receive recordId", "order": 1, "movementType": "E", "dataGroupRef": "cfp_FunctionalProcess__c", "implementationType": "flow", "isApiCall": false },
    { "name": "Read cfp_FunctionalProcess__c (getFunctionalProcess)", "order": 2, "movementType": "R", "dataGroupRef": "cfp_FunctionalProcess__c", "implementationType": "flow", "isApiCall": false },
    { "name": "Create cfp_Data_Movements__c (createDMs)", "order": 3, "movementType": "W", "dataGroupRef": "cfp_Data_Movements__c", "implementationType": "flow", "isApiCall": false },
    { "name": "Errors/notifications", "order": 4, "movementType": "X", "dataGroupRef": "status/errors/etc", "implementationType": "flow", "isApiCall": false }
  ]
}
```
