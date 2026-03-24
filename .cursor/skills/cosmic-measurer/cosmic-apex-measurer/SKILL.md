---
name: cosmic-apex-measurer
description: >
  Extracts COSMIC data movements (E/R/X/W) from Apex classes and outputs JSON for
  posting to a COSMIC database. Use when measuring Apex classes for functional size,
  analyzing .cls files for data movements, or generating cfp_Data_Movements__c from
  Apex code.
metadata:
  category: Salesforce / COSMIC
---

# COSMIC Apex Measurer

## Goal

Produce a **COSMIC measurement** for one Apex class: classify data movements as Entry, Read, Write, or Exit, assign order, and emit JSON matching [reference.md](../reference.md) for attachment to a functional process.

---

## Workflow

Inspects Apex `.cls` files, identifies data movements, and produces JSON in the format defined in [reference.md](../reference.md).

### Scope (Phase 2+)

- **Single class, single method** — no triggers
- **Call-chain traversal**: Static calls (`ClassName.methodName`) are traversed when `ClassName.cls` is found in search paths; R/W from callees are merged into the FP
- Focus on public/global methods with `@AuraEnabled`, `@InvocableMethod`, or standard entry points

### Entry (E)

- **Method parameters**: Each parameter that brings data into the functional process
- **dataGroupRef**: Infer from parameter type — `Id` for a specific object → use that object; generic `Id` → use object from usage context (e.g. `fpId` used in `cfp_FunctionalProcess__c = :fpId` → `cfp_FunctionalProcess__c`)
- **implementationType**: `apex`

### Read (R)

- **SOQL**: `[SELECT ... FROM ObjectName ...]` — extract object from `FROM` clause
- **Dynamic SOQL**: `Database.query(string)`, `Database.getQueryLocator(string)` — parse string for object name if static
- **RecordType object**: SOQL with `FROM RecordType` resolves record type Ids (metadata/setup). **Do not** count these as functional-process data movements — they are **excluded** from `dataMovements` and the deterministic script surfaces them under **Notes** (and optional JSON `recordTypeReadsExcludedFromCfp`). Other objects queried with `RecordTypeId = :binding` or `RecordType.DeveloperName` filters still map to their **business** object (e.g. `Asset::Location`) and **are** counted as usual.
- **implementationType**: `apex`
- **isApiCall**: `false` unless `@future(callout=true)` or explicit HTTP callout

### Write (W)

- **DML**: `insert`, `update`, `upsert`, `delete` — extract object from first argument type
- **Database methods**: `Database.insert()`, `Database.update()`, etc.
- **implementationType**: `apex`
- **Deduplication**: Multiple Writes to the same data group (same `dataGroupRef`, including composite `Asset::Location` vs `Asset::Component`) count as **one** Write. COSMIC measures functional size; insert vs update is an implementation detail of a single reconciliation/sync.

### Exit (X)

- **Parser**: `return` statements → Exit rows with inferred `dataGroupRef` (typed collections, etc.), as today.
- **Canonical rule (functional process)**: After all other movements, **append** one final Exit — **`Errors/notifications`**, last in order. **`dataGroupRef`**: `status/errors/etc` (see [reference.md](../reference.md)). The deterministic script adds this row in `build_output`; it does **not** replace parser-derived exits.
- **implementationType**: `apex` for the canonical exit when measuring Apex artifacts

### Procedural steps

1. **Check for multi-process**: Run `measure_apex.py path/to/Class.cls --list-entry-points`. If the output shows **more than one** entry point (e.g. `facilityIds`, `surveyIds`), **ask the user** which entry point to measure before proceeding.
2. **Measure**: Run with `--entry-point PARAM` if the user chose one; otherwise run normally.
3. **Read** the Apex `.cls` file
4. **Identify** the primary entry method (e.g. `@AuraEnabled`, `@InvocableMethod`, constructor, or static factory)
5. **Scan** method body for:
   - Parameters → Entry
   - SOQL / Database.query / getQueryLocator → Read
   - DML / Database.insert|update|delete|upsert → Write
   - Return of typed data → Exit (parser)
   - The script then **appends** **Errors/notifications** (X) last — always one extra row at the end.
6. **Assign order**: Entry (1), then Read/Write in code order, parser Exits, then **Errors/notifications** last
7. **Output** JSON to stdout or write to file; **always include** the human **Functional size** line and **Notes** when presenting measurement results (see [Output](#output))

### Python script (deterministic)

A Python implementation provides deterministic output for automation and regression:

```bash
# List entry points (for multi-process detection)
python3 .cursor/skills/cosmic-measurer/cosmic-apex-measurer/scripts/measure_apex.py path/to/Class.cls --list-entry-points

# Measure (optionally filter to one entry point)
python3 .cursor/skills/cosmic-measurer/cosmic-apex-measurer/scripts/measure_apex.py path/to/Class.cls [-o output.json] [--fp-id 001xxx] [--entry-point facilityIds]

# Traversal options (default: traverse into called classes when .cls found)
python3 ... measure_apex.py Class.cls [--search-paths samples,force-app/main/default/classes,src/classes] [--no-traverse]
```

**Call-chain traversal**: By default, static calls (`ClassName.methodName`) are resolved by globbing for `ClassName.cls` in `--search-paths`. If found, R/W from the callee are merged; if not found, the class is listed in `calledClassesNotFound`. Use `--no-traverse` to measure only the primary class.

**Multi-process classes**: When a class has multiple entry points (e.g. constructor with `facilityIds` and static factory `forSurveys(surveyIds)`), always run `--list-entry-points` first. If multiple are found, ask the user which to measure, then run with `--entry-point <param>`.

Run tests:

```bash
python3 .cursor/skills/cosmic-measurer/cosmic-apex-measurer/tests/test_measure_apex.py
```

---

## Validation

- **Schema**: Every `movementType` is exactly `E`, `R`, `X`, or `W`; `dataGroupRef` uses object API names and optional `::RecordTypeDeveloperName` / `::*` suffixes as in [reference.md](../reference.md).
- **Regression**: For [samples/cfp_getDataMovements.cls](../../../samples/cfp_getDataMovements.cls), expect **1 E, 1 R, 2 X** (one return, then **Errors/notifications** last); compare output to [expected/cfp_getDataMovements.expected.json](../../../expected/cfp_getDataMovements.expected.json).
- **Canonical exit**: Last movement is always **Errors/notifications** (`status/errors/etc`); CFP includes parser exits plus this X.
- **Multi-process**: If `--list-entry-points` shows more than one candidate, do not silently pick one — confirm with the user.
- **Deduplication**: Confirm merged Writes to the same data group appear as a single `W` in `dataMovements` when applying the merge rules above.

---

## Output

### Human summary (always)

When reporting measurement results to the user (from script output or synthesized manually):

- **Functional size:** Count E, R, W, and X after deduplication; **CFP = E + R + W + X** (same as the number of rows in `dataMovements`).
- **Notes:** Call out as applicable:
  - **Canonical exit** — last row is always **Errors/notifications** (after any parser `return` exits)
  - **Merged writes** — multiple DML on the same data group collapsed to one W
  - **Callee traversal** — movements with `viaClass` from traversed `.cls` callees
  - **Not found** — `calledClassesNotFound` meaning (system types + classes missing from `--search-paths`)
  - **RecordType reads (excluded from CFP)** — when the code queries `FROM RecordType`, list line(s) and names here; they are not rows in `dataMovements` (see [Read (R)](#read-r))

The CLI prints this automatically: default **table** mode appends the summary after the table; **`-o file.json`** writes JSON and prints the same summary to stdout. **`--json`** to stdout is machine-only (no appended summary, to keep stdout parseable).

### JSON

Produce JSON matching the schema in [reference.md](../reference.md):

```json
{
  "functionalProcessId": "<placeholder or user-provided>",
  "artifact": { "type": "Apex", "name": "ClassName" },
  "dataMovements": [
    { "name": "...", "order": 1, "movementType": "E", "dataGroupRef": "...", "implementationType": "apex", "isApiCall": false },
    { "name": "Upsert Application_Log__c records", "movementType": "W", "viaClass": "ApplicationLogHandler", ... },
    { "name": "Return SomeObject__c list", "movementType": "X", "dataGroupRef": "SomeObject__c", ... },
    { "name": "Errors/notifications", "order": 4, "movementType": "X", "dataGroupRef": "status/errors/etc", "implementationType": "apex", "isApiCall": false }
  ],
  "calledClassesNotFound": ["Database", "String", "SomeExternalUtil"],
  "recordTypeReadsExcludedFromCfp": [
    { "name": "Read RecordType list", "sourceLine": 47 }
  ]
}
```

- **recordTypeReadsExcludedFromCfp**: Present when SOQL `FROM RecordType` was detected; omitted when none. Not part of CFP row count.
- **viaClass**: When a movement comes from a traversed callee, the callee class name is included
- **calledClassesNotFound**: Classes called via static method but not found (no `.cls` in search paths). Includes system classes (System, Database, String, etc.) and external/custom classes not in the project
