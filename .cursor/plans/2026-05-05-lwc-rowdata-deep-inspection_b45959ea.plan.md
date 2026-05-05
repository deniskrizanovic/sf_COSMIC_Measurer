---
name: lwc-rowdata-deep-inspection
overview: Enhance the LWC measurer to trace 'RowData' back to its source (Apex, Wire, or API) to provide specific Salesforce Object data groups.
todos:
  - id: enhance-parser-iterator-source
    content: Update lwc_parser.py to capture for:each source variables and pass them to LwcRawMovement.
    status: pending
  - id: implement-source-tracer
    content: Implement trace_js_variable_source and resolve_data_group_from_source in measure_lwc.py.
    status: pending
  - id: refine-rowdata-movements
    content: Update measure_lwc_bundle to refine 'RowData' data groups using the new tracer.
    status: pending
  - id: verify-deep-inspection-test
    content: Verify deep inspection with AddSORs and ensure all tests pass.
    status: pending
isProject: false
---

# LWC 'RowData' Deep Inspection Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace generic 'RowData' data groups in LWC measurements with specific Salesforce Object names by tracing template iterators back to their source in the JavaScript controller.

**Architecture:**
- **Parser Enhancement**: Update `lwc_parser.py` to capture the `for:each` source variable and associate it with event handlers.
- **Source Tracer**: Implement logic in `measure_lwc.py` to scan the JS controller for assignments to the iterator variable.
- **Apex Integration**: Leverage existing Apex resolution to determine the SObject type returned by methods populating the traced variables.
- **Data Group Refinement**: Update the final data movements to use the resolved SObject name instead of 'RowData'.

---

### Task 1: Enhance LWC Parser to capture iterator sources

**Files:**
- Modify: `[.cursor/skills/cosmic-measurer/cosmic-lwc-measurer/scripts/lwc_parser.py](.cursor/skills/cosmic-measurer/cosmic-lwc-measurer/scripts/lwc_parser.py)`

- [ ] **Step 1: Update `_HtmlNode` and `_HandlerInfo`**
  Add a `for_each_source` field to store the variable name from `for:each={variable}`.

- [ ] **Step 2: Update `_classify_node` and `_BlockInfo`**
  Pass the `for_each_source` through to the interaction blocks.

- [ ] **Step 3: Update `parse_lwc_native_movements`**
  Ensure the `LwcRawMovement` objects for 'RowData' include the source variable name.

### Task 2: Implement Data Source Tracing in Measurer

**Files:**
- Modify: `[.cursor/skills/cosmic-measurer/cosmic-lwc-measurer/scripts/measure_lwc.py](.cursor/skills/cosmic-measurer/cosmic-lwc-measurer/scripts/measure_lwc.py)`

- [ ] **Step 1: Implement `trace_js_variable_source` helper**
  Use regex to find where a variable is assigned in the JS source.
  - Detect `@wire` properties and functions.
  - Detect assignments in `.then()` blocks (e.g., `this.tempSorList = result`).
  - Detect direct assignments in methods.

- [ ] **Step 2: Implement `resolve_data_group_from_source`**
  If the source is an Apex method, look up the return type from the already resolved Apex movements.
  If the source is an `@api` property, mark it as the property name or "External".

- [ ] **Step 3: Update `measure_lwc_bundle` to refine 'RowData'**
  Iterate through collected movements. For any with `dataGroupRef == "RowData"`, call the tracer and update the `dataGroupRef` with the resolved name.

### Task 3: Verification and Regression Testing

**Files:**
- Modify: `[.cursor/skills/cosmic-measurer/cosmic-lwc-measurer/tests/test_lwc_traversal.py](.cursor/skills/cosmic-measurer/cosmic-lwc-measurer/tests/test_lwc_traversal.py)`

- [ ] **Step 1: Update traversal test for AddSORs**
  Verify that the 'RowData' movement in `AddSORs` is now correctly identified as `Service_Catalogue__c` (traced via `tempSorList` -> `sorList` -> `fetchAllSORList`).

- [ ] **Step 2: Run all LWC tests**
  Ensure no regressions in existing measurements.
