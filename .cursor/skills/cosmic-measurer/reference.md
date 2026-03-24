# COSMIC Measurer Reference

## Data Movement Types (E/R/X/W)

| Code | Name   | Definition |
|------|--------|------------|
| E    | Entry  | Data crossing the boundary into the functional process (inputs) |
| R    | Read   | Data read from persistent storage |
| W    | Write  | Data written to persistent storage |
| X    | Exit   | Data crossing the boundary out of the functional process (outputs) |

One CFP (Cosmic Function Point) per movement of a data group.

---

## JSON Schema

All measurer skills produce this structure:

```json
{
  "functionalProcessId": "<Id>",
  "artifact": { "type": "Apex|Flow|FlexiPage|LWC|PageLayout", "name": "..." },
  "dataMovements": [
    {
      "name": "Human-readable description",
      "order": 1,
      "movementType": "E|R|X|W",
      "dataGroupRef": "ObjectApiName",
      "implementationType": "apex|flow|flexipage|lwc|ootb|config|listview",
      "isApiCall": false
    }
  ]
}
```

### Field Rules

- **movementType**: Must be exactly `E`, `R`, `X`, or `W`
- **dataGroupRef**: Salesforce object API name (e.g. `Account`, `cfp_Data_Movements__c`), or a composite `ObjectApiName::RecordTypeDeveloperName` when the movement is scoped to a record type (e.g. `Asset::Location`). Use `ObjectApiName::*` when record types apply but the DeveloperName could not be resolved. Resolution to cfp_DataGroups__c Id happens at post time.
- **implementationType**: `apex` = custom code; `flow` = declarative flow; `flexipage` = record-page metadata traversal; `lwc` = Lightning Web Component static analysis; `ootb` = standard Salesforce; `config` = declarative (non-flow)
- **isApiCall**: `true` if movement involves external API (REST, callout)
- **sourceLine** (optional): Apex line number for traceability
- **mergedFrom** (optional): For Writes: list of `{name, sourceLine}` for operations merged into this movement (COSMIC: multiple DML to same data group = 1 Write). Use for inspection/audit.

---

## Data Group Mapping

- Standard objects: Use API name (Account, Contact, Opportunity, etc.)
- Custom objects: Use API name (e.g. `cfp_Data_Movements__c`)
- Unknown objects: Use object API name; flag if unresolvable at post time

---

## Ordering

Assign `order` sequentially (1, 2, 3...) in execution flow. For Apex: Entry first, then Read/Write in code order, then parser Exits (`return`), then append **Errors/notifications** (see [Canonical FP exit](#canonical-fp-exit-all-measurer-skills)).

---

## Canonical FP exit (all measurer skills)

Every **functional process** includes **one additional** Exit (**X**) as the **final** data movement (after any parser- or artifact-derived E/R/W/X):

| Field | Value |
|-------|--------|
| **name** | `Errors/notifications` |
| **movementType** | `X` |
| **dataGroupRef** | `status/errors/etc` (user-visible errors and notifications; remap in your org’s COSMIC data-group model if needed) |
| **order** | Last — always after all other movements for that FP |

**Apex:** `build_output` (`movements.py`) keeps all parser-derived movements (including `return` exits), then **appends** this row. If the parser finds no Exit (e.g. batch `execute` returns void), the output still has this single **`Errors/notifications`** X.

**Flow:** `build_output` (`shared/output.py`) appends this row with `implementationType: "flow"` after all parsed entries, reads, writes, and output-variable exits.

---

## Cursor `SKILL.md` contract (artifact skills)

Each measurer skill’s `SKILL.md` uses YAML frontmatter (`name` matching the folder, `description` ≤100 words with outcome-first + trigger phrases) and body sections **Goal**, **Workflow**, **Validation**, **Output** in that order. Optional: `metadata.category`, `metadata.version`. Repository-wide rules: [skill-best-practices.md](../../../skill-best-practices.md). This project names folders `*-measurer` by convention (documented exception to gerund `-ing` naming in that doc).
