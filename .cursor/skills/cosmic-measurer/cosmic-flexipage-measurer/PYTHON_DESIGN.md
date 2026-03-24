# COSMIC FlexiPage Measurer Python Design

## Structure

- `scripts/flexipage_parser.py`
  - Parses metadata XML.
  - Extracts page metadata and movement candidates.
  - Returns `RawMovement` rows for shared ordering/dedup/output.
- `scripts/measure_flexipage.py`
  - CLI entry point.
  - Calls parser, then `shared.output.build_output(...)`.
  - Supports `--json`, `-o`, and `--fp-id`.

## Rule Set (v1)

- Entry (E): actions from `force:highlightsPanel` (`actionNames`).
- Read (R): page record field bindings (`Record.*`) and dynamic related lists.
- Write (W): action names that imply mutation (`create/new/add/update/edit/delete/remove`).
- Exit (X): displayed page record fields and dynamic related lists.
- Canonical final exit (`Errors/notifications`) is appended by shared output.

## Known Limits

- Metadata-only inference can over/under-count true runtime writes.
- Custom component internals are not analyzed in v1.
- Related list data-group mapping uses API-name normalization (`__r` -> `__c`).
