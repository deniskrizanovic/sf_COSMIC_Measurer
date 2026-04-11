---
name: add-artifactname-to-data-movements
overview: Add a new field `artifactName` to all COSMIC data movements to track their source artifact, facilitating database aggregation.
todos:
  - id: update-models-shared
    content: Add artifact_name to RawMovement in shared/models.py
    status: pending
  - id: update-output-shared
    content: Update shared/output.py to include artifactName in JSON output and populate it in build_output
    status: pending
  - id: update-output-apex
    content: Update cosmic-apex-measurer/scripts/movements.py to populate artifactName in its build_output
    status: pending
  - id: update-output-flexipage
    content: Update cosmic-flexipage-measurer/scripts/measure_flexipage.py for manual rows
    status: pending
  - id: update-output-lwc
    content: Update cosmic-lwc-measurer/scripts/measure_lwc.py for manual rows and conversion logic
    status: pending
  - id: update-output-flow-integration
    content: Update flow_apex_integration.py for Apex-to-Flow conversion
    status: pending
  - id: verify-changes
    content: Verify changes by running tests for all measurers
    status: pending
isProject: false
---

I will add the `artifactName` field to the shared data models and ensure all measurers (Apex, Flow, LWC, FlexiPage) populate it during output generation.

### 1. Update Shared Models

Add `artifact_name` to the `RawMovement` class in `shared/models.py`.

### 2. Update Shared Output Logic

Modify `shared/output.py` to:

- Include `artifactName` in the `DataMovementRow` type definition.
- Update `to_json_movement` to map the Python `artifact_name` to the JSON `artifactName`.
- Update `build_output` to populate `artifact_name` on all movements using the provided `artifact_name` parameter if not already set.
- Ensure the canonical `Errors/notifications` exit row also includes `artifactName`.

### 3. Update Apex-Specific Output Logic

Modify `cosmic-apex-measurer/scripts/movements.py` to:

- Populate `artifact_name` on all movements in its specialized `build_output` function.
- Ensure its version of the canonical exit row includes `artifactName`.

### 4. Update FlexiPage, LWC, and Flow-Apex Integration

Update manual row creation and conversion logic to ensure `artifact_name` is correctly propagated:

- `cosmic-flexipage-measurer/scripts/measure_flexipage.py`: Update `_inline_resolved_lwc_tab_movements`, `_inline_resolved_flow_tab_movements`, and `_build_action_candidate_outputs`.
- `cosmic-lwc-measurer/scripts/measure_lwc.py`: Update `_apex_rows_to_raw_movements`.
- `cosmic-flow-measurer/scripts/flow_apex_integration.py`: Update `apex_rows_to_raw_movements`.

### 5. Verification

Run existing tests for all measurers to ensure the new field is present in the JSON output and no regressions were introduced.

- `cosmic-apex-measurer/tests/test_movements.py`
- `cosmic-flow-measurer/tests/test_flow_movements.py`
- LWC and FlexiPage tests.
