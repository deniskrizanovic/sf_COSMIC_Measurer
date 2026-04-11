# Python Apex Measurer — Design Sketch

Deterministic, script-based extraction of COSMIC data movements from Apex `.cls` files.

---

## Goals

- **Deterministic**: Same input → same output
- **Regression-friendly**: `python measure.py sample.cls | diff expected.json -`
- **Complement SKILL.md**: Agent uses skill for edge cases; script for automation

---

## Parsing Strategy

**Regex-based** (no Apex grammar/parser dependency). Apex is close enough to Java/C-style that targeted regex works for common patterns.

| Movement | Pattern | Regex / Approach |
|----------|---------|------------------|
| **R** | SOQL `[SELECT ... FROM X ...]` | `\[SELECT\s+[\w\s,\.]+FROM\s+(\w+)` — capture object after FROM |
| **R** | `Database.getQueryLocator([...])` | Same SOQL extraction inside brackets |
| **R** | `Database.query('...')` | Parse string literal for `FROM ObjectName` if static |
| **W** | `insert|update|upsert|delete\s+` | DML keyword + extract type from next token (variable type or generic) |
| **W** | `Database\.(insert|update|delete|upsert)` | Same |
| **E** | Method params `(Type name, ...)` | Extract param types; `Id`/`List<Id>` → infer from usage or use placeholder |
| **X** | `return\s+` + typed var | Infer from variable declaration or return type in signature |

**Output layer**: `build_output` in `movements.py` **appends** one canonical Exit after all parser movements — **`Errors/notifications`** (`dataGroupRef`: `status/errors/etc`) — so every FP ends with that row (parser `return` exits remain when present).

**Limitation**: `Id` and generic types need heuristics. Options: (a) use `"Unknown"` placeholder, (b) scan for `= :paramName` in WHERE to infer object, (c) config file mapping param names → objects.

---

## Module Structure

```
cosmic-measurer/cosmic-apex-measurer/
├── SKILL.md
├── PYTHON_DESIGN.md          # this file
├── scripts/
│   ├── measure_apex.py        # main entry
│   ├── parser.py             # regex extraction
│   ├── movements.py          # movement builders, ordering
│   └── __init__.py
└── tests/
    └── test_measure_apex.py
```

---

## Parser Module (`parser.py`)

```python
# Pseudocode / interface

def extract_class_name(source: str) -> str
def extract_methods(source: str) -> list[dict]  # name, params, body, return_type

def find_reads(source: str) -> list[dict]       # {object, line, context}
def find_writes(source: str) -> list[dict]
def find_entries(method: dict) -> list[dict]    # from params
def find_exits(method: dict) -> list[dict]       # from return
```

**Read detection**:
```python
# SOQL: [SELECT ... FROM ObjectName ...]
SOQL_FROM = re.compile(r'\[\s*SELECT\s+[\w\s,\.\(\):]+FROM\s+(\w+)\s+', re.IGNORECASE | re.DOTALL)
# Database.getQueryLocator([...]) — extract inner SOQL
```

**Write detection**:
```python
# insert x; update y; delete z; Database.update(list, false);
DML = re.compile(r'(?:^|\s)(insert|update|upsert|delete)\s+(\w+)', re.IGNORECASE)
DB_DML = re.compile(r'Database\.(insert|update|delete|upsert)\s*\([^,]+,\s*(\w+)\)')
# Object from first arg: for "Database.update(surveys)" need type of surveys → List<Survey__c>
# Fallback: scan for "List<X>" or "X[]" in scope
```

**Entry detection**:
```python
# Params: (Id fpId) or (List<Id> surveyIds, String action, ...)
# For Id/List<Id>: try to infer from param name (fpId→FunctionalProcess) or config
PARAM = re.compile(r'\((?:(\w+(?:<[^>]+>)?)\s+(\w+)(?:\s*,\s*)*)*\)')
```

---

## Batch / Multi-Method Handling

For `Database.Batchable` and similar:

1. **Scope**: Treat constructor + `start` + `execute` (+ `finish` if returns data) as one functional process
2. **Order**: Constructor params (E) → start reads (R) → execute reads/writes (R/W) → finish exit (X) if any
3. **Detection**: Run parser on whole class; merge movements from constructor, start, execute

Config flag: `--scope=method|class` (default `class` for batch, `method` for simple)

---

## CLI Interface

```bash
# Single file, stdout
python scripts/measure_apex.py path/to/MyClass.cls

# Single file, write to file
python scripts/measure_apex.py path/to/MyClass.cls -o output.json

# With functional process ID
python scripts/measure_apex.py MyClass.cls --fp-id 001xxx

# Batch mode (multiple files)
python scripts/measure_apex.py classes/*.cls -o results/
```

---

## Output

Same JSON schema as reference.md. Example:

```json
{
  "functionalProcessId": "<Id>",
  "artifact": { "type": "Apex", "name": "cfp_getDataMovements" },
  "dataMovements": [
    { "name": "Receive fpId", "order": 1, "movementType": "E", "dataGroupRef": "cfp_FunctionalProcess__c", "implementationType": "apex", "isApiCall": false },
    { "name": "Read cfp_Data_Movements__c", "order": 2, "movementType": "R", "dataGroupRef": "cfp_Data_Movements__c", "implementationType": "apex", "isApiCall": false },
    { "name": "Return cfp_Data_Movements__c list", "order": 3, "movementType": "X", "dataGroupRef": "cfp_Data_Movements__c", "implementationType": "apex", "isApiCall": false },
    { "name": "Errors/notifications", "order": 4, "movementType": "X", "dataGroupRef": "status/errors/etc", "implementationType": "apex", "isApiCall": false }
  ]
}
```

---

## Write Deduplication (COSMIC Interpretation)

Multiple DML operations to the **same data group** (e.g. `insert` + `update` for Asset) are merged into **one** Write per functional process. Rationale:

- COSMIC measures functional size, not implementation.
- A single reconciliation/sync that creates and updates records = one boundary crossing (write to persistent storage).
- Using `upsert` would yield one Write; splitting into insert + update should not inflate the count.

**Implementation**: In `order_movements()`, dedupe Writes by `(movement_type, data_group_ref)` only — keep the first (earliest execution order). Reads remain deduped by `(type, dataGroupRef, name)` to avoid parser duplicates only.

**Record types**: `data_group_ref` may be `ObjectApiName::RecordTypeDeveloperName` (e.g. `Asset::Location`) or `ObjectApiName::unknown RT` when record types are involved but unresolved. Merging applies only within the same full `data_group_ref` string.

---

## Param-to-Object Inference (Entry)

When param is `Id` or `List<Id>`, infer `dataGroupRef` by:

1. **Name convention**: `fpId` → `cfp_FunctionalProcess__c`, `surveyIds` → `Survey__c`, `accId` → `Account`
2. **Usage scan**: `WHERE cfp_FunctionalProcess__c = :fpId` → `cfp_FunctionalProcess__c`
3. **Config file** (optional): `param_mappings.json` — `{"fpId": "cfp_FunctionalProcess__c"}`
4. **Fallback**: `"Unknown"` or skip

---

## Regression Test

```bash
python scripts/measure_apex.py samples/cfp_getDataMovements.cls -o /tmp/out.json
diff expected/cfp_getDataMovements.expected.json /tmp/out.json
```

Or in pytest: assert JSON output matches golden (with `functionalProcessId` normalized).

### Automated tests and coverage

From `cosmic-apex-measurer/` (install dev deps once: `pip install -r requirements-dev.txt`):

```bash
python3 -m pytest tests/ -v
python3 -m coverage run -m pytest tests/ -v
python3 -m coverage report --include="scripts/*" --fail-under=95
```

Configuration lives in [`.coveragerc`](.coveragerc) (`source = scripts`, `fail_under = 95`, excludes the `if __name__ == "__main__"` shim in `measure_apex.py`).

---

## Dependencies

- **Python 3.10+**
- **stdlib only** for runtime (`measure_apex.py`, `parser.py`, `movements.py`)
- **Dev:** `pytest`, `coverage` — see `requirements-dev.txt`
- Optional: `jsonschema` for output validation

---

## Implementation Order

1. `parser.py` — SOQL Read extraction (highest confidence)
2. `parser.py` — DML Write extraction
3. `parser.py` — Method params (Entry), Return (Exit)
4. `movements.py` — Ordering, dedup, JSON build
5. `measure_apex.py` — CLI, file I/O
6. Param inference heuristics
7. Batch/multi-method scope
8. Tests + golden file validation
