---
name: ignore-user-pageref-lwc-bindings
overview: Exclude LWC-native data movements associated with User and PageReference bindings (adapters and schema imports) from COSMIC measurements.
todos:
  - id: define-ignored
    content: Identify and define ignored adapters and objects in lwc_parser.py
    status: pending
  - id: filter-movements
    content: Update _resolve_wire_reads to filter out ignored movements
    status: pending
  - id: update-tests
    content: Update tests to reflect the new filtering rules
    status: pending
  - id: verify-fix
    content: Verify fix with AddSORs sample and unit tests
    status: pending
isProject: false
---

I will update `lwc_parser.py` to filter out specific adapters and objects that are commonly used for UI context rather than functional data movements.

### Research
- Confirmed that `@wire(CurrentPageReference)` and `@wire(getRecord, { ... User fields ... })` are currently included as `Read` movements in `AddSORs.lwc`.
- identified `_resolve_wire_reads` in `lwc_parser.py` as the primary location for extracting these movements.

### Proposed Changes

#### `lwc_parser.py`
- Define `_IGNORED_LWC_ADAPTERS = {"CurrentPageReference", "PageReference"}`.
- Define `_IGNORED_LWC_OBJECTS = {"User", "PageReference"}`.
- Update `_resolve_wire_reads` to:
    - Skip any `adapter` in `_IGNORED_LWC_ADAPTERS`.
    - Skip any `obj` in `_IGNORED_LWC_OBJECTS` when processing `getRecord`.

#### `test_measure_lwc.py`
- Update `test_wire_r_movements_get_init_tier` to expect *zero* `R` movements if only `CurrentPageReference` is wired, or add another wire to keep the test valid but verify `CurrentPageReference` is gone.

#### `test_lwc_parser.py`
- Add unit tests for the filtering logic in `lwc_parser.py`.

### Verification
- Run `measure_lwc.py` on `samples/lwc/AddSORs` and verify that "Read CurrentPageReference" and "Read User record" are no longer present.
- Run existing tests to ensure no regressions.
