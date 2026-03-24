# COSMIC FlexiPage Measurer Python Design

## Structure

- `scripts/flexipage_parser.py`
  - Parses metadata XML.
  - Extracts page metadata and movement candidates.
  - Returns `RawMovement` rows for shared ordering/dedup/output.
- `scripts/measure_flexipage.py`
  - CLI entry point.
  - Calls parser, then `shared.output.build_output(...)`.
  - Supports `--json`, `-o`, `--fp-id`, `--no-resolve-lwc-candidates`, and `--no-resolve-flow-candidates`.
  - Resolves tab-bound LWC candidates by default and inlines their movements.
  - Resolves tab-bound Flow interview candidates by default and inlines their movements.

## Rule Set (v1)

- Entry (E): page-open trigger for record pages (plus optional action candidate outputs when requested).
- Read (R): page record read, explicit highlights-panel field read, and dynamic related lists.
- Write (W): no direct highlights-panel write rows in default FlexiPage measurement.
- Exit (X): page record display, explicit highlights-panel field display, and dynamic related lists.
- Canonical final exit (`Errors/notifications`) is appended by shared output.

## Known Limits

- Metadata-only inference can over/under-count true runtime writes.
- Custom component internals are not analyzed in v1.
- Related list data-group mapping uses API-name normalization (`__r` -> `__c`).
