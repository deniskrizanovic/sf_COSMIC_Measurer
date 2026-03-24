# cosmic-lwc-measurer Python design

## Modules

- `scripts/lwc_parser.py`
  - static parsing for template events, bindings, LDS calls, and Apex imports.
- `scripts/measure_lwc.py`
  - standalone public API (`measure_lwc`, `measure_lwc_bundle`)
  - optional CLI entrypoint (`main`)
  - Apex merge adapter and required movement validation.

## Public API

- `measure_lwc(request: LwcMeasureRequest) -> LwcMeasureResult`
- `measure_lwc_bundle(...) -> LwcMeasureResult`
- `validate_required_movement_types(...) -> tuple[bool, list[str]]`
- `resolve_lwc_candidate(candidate, *, apex_search_paths) -> LwcMeasureResult` (adapter helper)

## Ordering and output

- Uses `shared.output.build_output` for canonical COSMIC ordering/dedup.
- Sets `implementationType: "lwc"` for native rows.
- Re-labels merged Apex rows with `implementationType: "apex"` based on `viaArtifact`.
- Always appends canonical final `Errors/notifications` via shared output.
