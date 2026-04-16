# sf_COSMIC-Measurer

`sf_COSMIC-Measurer` is a Python-based measurement toolkit for extracting COSMIC data movements from Salesforce artifacts.

It analyzes metadata and code, classifies movements as `E` (Entry), `R` (Read), `W` (Write), and `X` (Exit), and outputs structured JSON suitable for posting into a COSMIC data model (for example, `cfp_Data_Movements__c` pipelines).

## What this project does

- Measures **Apex classes** (`.cls`)
- Measures **Flows** (`.flow-meta.xml`)
- Measures **FlexiPages** (`.flexipage-meta.xml`)
- Measures **Lightning Web Components** (bundle directories with `.js` + `.html`)
- Produces deterministic JSON outputs with ordered movements and consistent schema
- **Traversal Warning Management**: Automatically filters out standard Salesforce framework classes (e.g., `System`, `Database`, `Schema`, `String`) from traversal warnings to ensure focused results.
- Supports cross-artifact traversal:
  - Flow measurer can resolve and merge invocable Apex movements
  - LWC measurer can resolve and merge imported Apex movements
  - FlexiPage measurer can resolve tab-bound Flow and LWC candidates

## COSMIC model used here

Each movement is one COSMIC Function Point and is represented with:

- `movementType`: `E`, `R`, `W`, or `X`
- `dataGroupRef`: Salesforce object API name (or supported composite form)
- `order`: execution ordering within a functional process
- `implementationType`: `apex`, `flow`, `flexipage`, `lwc`, `ootb`, `config`, or `listview`
- `isApiCall`: external API interaction flag

Shared reference: `.cursor/skills/cosmic-measurer/reference.md`  
Implementation counting behavior: `COUNTING_RULES.md`

## Repository layout

- `samples/` - sample Apex, Flow, FlexiPage, and LWC inputs used for testing and examples
- `expected/` - expected JSON fixtures for regression checks
- `.cursor/skills/cosmic-measurer/` - artifact-specific measurers and shared modules
  - `cosmic-apex-measurer/`
  - `cosmic-flow-measurer/`
  - `cosmic-flexipage-measurer/`
  - `cosmic-lwc-measurer/`
  - `shared/` (common models/output logic)

## Cursor plugin bundle

This repository provides build infrastructure to generate a Cursor plugin bundle. The generated output is intentionally excluded from the repository as it is a build artifact.

- **Source of truth**: `.cursor/skills/cosmic-measurer/`
- **Build command**: `python3 scripts/build_cursor_plugin.py`
- **Output location**: `plugin/cursor-cosmic-measurer/` (generated on-demand)

To use the plugin, run the build script to generate the `plugin/` directory.

## Prerequisites

- Python 3.10+ (3.11+ recommended)
- `pytest` for test execution
- `coverage` for coverage runs

Minimal install:

```bash
python3 -m pip install -U pytest "coverage[toml]"
```

## Quick start

Run a measurer directly from repo root.

### Apex

```bash
python3 .cursor/skills/cosmic-measurer/cosmic-apex-measurer/scripts/measure_apex.py \
  samples/classes/cfp_getDataMovements.cls
```

`measure_apex.py` implements high-fidelity parsing:

- **Comment Stripping**: Automatically removes block and line comments before extraction to avoid false positives.
- **Improved Object Resolution**: Ignores custom objects and metadata types during class resolution to maintain focus on traversable business logic.

Useful flags:

- `--json` -> print JSON to stdout
- `-o out.json` -> write JSON to file
- `--fp-id <Id>` -> set functional process id
- `--list-entry-points` -> detect multiple entry points
- `--entry-point <param>` -> filter to one functional process
- `--search-paths <csv>` -> class resolution paths for traversal
- `--no-traverse` -> disable called-class traversal

### Flow

```bash
python3 .cursor/skills/cosmic-measurer/cosmic-flow-measurer/scripts/measure_flow.py \
  samples/flows/cfp_createCRUDLwithRelatedLists.flow-meta.xml
```

Useful flags:

- `--json`
- `-o out.json`
- `--fp-id <Id>`
- `--apex-search-paths <csv>` -> resolve invocable Apex classes
- `--no-invocable-apex` -> skip invocable Apex traversal

### FlexiPage

```bash
python3 .cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts/measure_flexipage.py \
  samples/flexipages/cfp_FunctionalProcess_Record_Page.flexipage-meta.xml
```

Useful flags:

- `--json`
- `-o out.json`
- `--fp-id <Id>`
- `--lwc-search-paths <csv>`
- `--flow-search-paths <csv>`
- `--apex-search-paths <csv>`
- `--no-resolve-lwc-candidates`
- `--no-resolve-flow-candidates`
- `--include-resolution-details` -> include diagnostic candidate/resolution arrays in JSON

## Example: Table-based FlexiPage output

Command:

```bash
python3 .cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts/measure_flexipage.py \
  samples/flexipages/cfp_FunctionalProcess_Record_Page.flexipage-meta.xml
```

**cfp_FunctionalProcess_Record_Page.flexipage** (FlexiPage)

## Init

| Order | Type | Name | Data group | LineNumber | ArtifactName | Via | Merged |
|-------|------|------|------------|------------|--------------|-----|--------|
| 11 | E | Receive fpId (Functional Process) | tab:Visualiser | cfp_FunctionalProcess__c | 7 | cfp_getDataMovements.apex | cfp_getDataMovements | — |
| 12 | R | Read cfp_Data_Movements__c list | tab:Visualiser | cfp_Data_Movements__c | 9 | cfp_getDataMovements.apex | cfp_getDataMovements | — |
| 13 | X | Display LWC output to user | tab:Visualiser | cfp_Data_Movements__c | — | cfp_FunctionalProcessVisualiser.lwc | — | — |

## Other

| Order | Type | Name | Data group | LineNumber | ArtifactName | Via | Merged |
|-------|------|------|------------|------------|--------------|-----|--------|
| 1 | E | Open record page (cfp_FunctionalProcess__c) | cfp_FunctionalProcess__c | — | cfp_FunctionalProcess_Record_Page.flexipage | — | — |
| 2 | R | Read page record (cfp_FunctionalProcess__c) | cfp_FunctionalProcess__c | — | cfp_FunctionalProcess_Record_Page.flexipage | — | — |
| 3 | X | Display page record (cfp_FunctionalProcess__c) | cfp_FunctionalProcess__c | — | cfp_FunctionalProcess_Record_Page.flexipage | — | — |
| 4 | E | Edit page record (cfp_FunctionalProcess__c) | cfp_FunctionalProcess__c | — | cfp_FunctionalProcess_Record_Page.flexipage | — | — |
| 5 | W | Write page record (cfp_FunctionalProcess__c) | cfp_FunctionalProcess__c | — | cfp_FunctionalProcess_Record_Page.flexipage | — | — |
| 6 | R | Read highlights panel fields (cfp_FunctionalProcess__c) | cfp_FunctionalProcess__c | — | cfp_FunctionalProcess_Record_Page.flexipage | — | — |
| 7 | X | Display highlights panel fields (cfp_FunctionalProcess__c) | cfp_FunctionalProcess__c | — | cfp_FunctionalProcess_Record_Page.flexipage | — | — |
| 8 | R | Read related list cfp_functionalsteps__c | cfp_functionalsteps__c | — | cfp_FunctionalProcess_Record_Page.flexipage | — | — |
| 9 | X | Display related list cfp_functionalsteps__c | cfp_functionalsteps__c | — | cfp_FunctionalProcess_Record_Page.flexipage | — | — |
| 10 | X | Inspect LWC cfp_FunctionalProcessVisualiser data movements (TBC) on tab Visualis | tbc | — | cfp_FunctionalProcess_Record_Page.flexipage | — | — |
| 14 | X | Errors/notifications | status/errors/etc | — | cfp_FunctionalProcess_Record_Page.flexipage | — | — |

**Functional size:** 3 E + 4 R + 1 W + 6 X = **14 CFP**

**Notes:**
- **Artifact traversal:** Movements with Via include R/W merged from traversed artifacts.
- **Warning:** Investigate configured page actions as separate functional processes: Delete, cfp_FunctionalProcess__c.Create_CRUDL, cfp_FunctionalProcess__c.cfp_Add_Email_Notification, cfp_FunctionalProcess__c.cfp_Create_ReadDisplayPair
- **Warning:** Tab-aware notes: page contains tabs = Listview, metadataView, Visualiser
- **Warning:** Tab-component bindings: Listview -> aura(lst:dynamicRelatedList), metadataView -> aura(lst:dynamicRelatedList), Visualiser -> lwc(cfp_FunctionalProcessVisualiser)
- **Warning:** Delegate tab-bound LWCs to lwc-measurer with additional write movement handling: cfp_FunctionalProcessVisualiser
- **Canonical exit:** Last movement is always X — Errors/notifications (`status/errors/etc`), after any artifact-derived exits.

### LWC

```bash
python3 .cursor/skills/cosmic-measurer/cosmic-lwc-measurer/scripts/measure_lwc.py \
  --bundle-dir samples/lwc/cfp_FunctionalProcessVisualiser
```

Useful flags:

- `--json`
- `-o out.json`
- `--fp-id <Id>`
- `--apex-search-paths <csv>`
- `--required-type E|R|W|X` (repeatable)

## Output shape

All measurers emit the same core structure:

```json
{
  "functionalProcessId": "<Id>",
  "artifact": { "type": "Apex|Flow|FlexiPage|LWC", "name": "..." },
  "dataMovements": [
    {
      "name": "Human-readable movement",
      "order": 1,
      "movementType": "E|R|W|X",
      "dataGroupRef": "ObjectApiName",
      "implementationType": "apex|flow|flexipage|lwc|...",
      "isApiCall": false
    }
  ]
}
```

By convention, a canonical final exit row is included:

- `name`: `Errors/notifications`
- `movementType`: `X`
- `dataGroupRef`: `status/errors/etc`

For FlexiPage output, `dataMovements` is the canonical consumer contract. Candidate/resolution arrays (`lwcCandidateMeasurements`, `flowCandidateMeasurements`, `resolvedLwcMeasurements`, `resolvedFlowMeasurements`) are diagnostics and are only emitted when `--include-resolution-details` is passed.

## Integration with CosmicWorkBench

`sf_COSMIC-Measurer` output JSON is compatible with [sf_CosmicWorkBench](https://github.com/deniskrizanovic/sf_CosmicWorkBench).

### JSON Importer Flow

The [cfp_DataMovementsJSONImporter](https://github.com/deniskrizanovic/sf_CosmicWorkBench/blob/main/src/main/default/flows/cfp_DataMovementsJSONImporter.flow-meta.xml) flow in `sf_CosmicWorkBench` imports measurements into Salesforce records.

#### How to Import:

1.  **Generate JSON**: Run a measurer (e.g., Apex, Flow, LWC) to create a `.json` file in [measurements/](measurements/).
2.  **Locate Output**: Open the `.json` file and copy its entire content.
3.  **Run Flow**: In Salesforce, navigate to the `sf_CosmicWorkBench` app or Flow list and run **Import Data Movements JSON** (`cfp_DataMovementsJSONImporter`).
4.  **Enter Inputs**:
    *   **Functional Process Id**: Salesforce ID of the target `cfp_Functional_Process__c` record.
    *   **JSON Payload**: Paste the copied JSON.
    *   **Replace Existing**: Toggle to delete previous movements for this process before importing.
5.  **Submit**: Click **Next**. The Flow calls Apex `Run_DataMovements_Importer` to parse and upsert `cfp_Data_Movement__c` records.

#### JSON Structure:
`sf_COSMIC-Measurer` produces:
- `functionalProcessId`: Target ID placeholder.
- `artifact`: Source metadata (type/name).
- `dataMovements`: List of E/R/X/W movements with line references.
- `traversalWarnings`: Resolution issues during measurement.

The workbench importer maps these fields to Salesforce Custom Objects.

## Validation and tests

Run full project test suite:

```bash
python3 -m pytest ".cursor/skills/cosmic-measurer"
```

Per-measurer test runs:

```bash
python3 -m pytest ".cursor/skills/cosmic-measurer/cosmic-apex-measurer/tests" -v
python3 -m pytest ".cursor/skills/cosmic-measurer/cosmic-flow-measurer/tests" -v
python3 -m pytest ".cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/tests" -v
python3 -m pytest ".cursor/skills/cosmic-measurer/cosmic-lwc-measurer/tests" -v
```

Coverage examples:

```bash
python3 -m pytest ".cursor/skills/cosmic-measurer/cosmic-apex-measurer/tests" --cov=".cursor/skills/cosmic-measurer/cosmic-apex-measurer/scripts" --cov-report=term
python3 -m pytest ".cursor/skills/cosmic-measurer/cosmic-flow-measurer/tests" --cov=".cursor/skills/cosmic-measurer/cosmic-flow-measurer/scripts" --cov-report=term
python3 -m pytest ".cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/tests" --cov=".cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts" --cov-report=term
python3 -m pytest ".cursor/skills/cosmic-measurer/cosmic-lwc-measurer/tests" --cov=".cursor/skills/cosmic-measurer/cosmic-lwc-measurer/scripts" --cov-report=term
```

## Notes

- Measurers are designed for deterministic output and regression testing via `expected/` fixtures.
- Some artifact integrations are best-effort (for example unresolved classes are surfaced as warnings, not hard failures).
- Skill definitions in `.cursor/skills/cosmic-measurer/*/SKILL.md` document each artifact measurer's current scope and rules.
