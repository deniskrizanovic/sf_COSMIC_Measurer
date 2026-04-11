---
name: cross-class-constant-resolution
overview: Implement cross-class constant resolution for the COSMIC Apex measurer to accurately resolve record types from external constant classes like GlobalConstants.
todos:
  - id: update-parser-constants
    content: Update parser.py to identify external constants and support public constants.
    status: in_progress
  - id: update-measure-traversal
    content: Update measure_apex.py to resolve external constant classes and re-run inference.
    status: pending
  - id: verify-resolution-on-addsor-controller-with-mocked-globalconstants-if-necessary
    content: Verify resolution on AddSORController with mocked GlobalConstants if necessary.
    status: pending
isProject: false
---

### Cross-Class Constant Resolution Plan

Enable the COSMIC Apex measurer to resolve `ClassName.CONSTANT_NAME` references by searching for the corresponding Apex class in the project's search paths and extracting their literal values.

#### 1. Update `parser.py` ([.cursor/skills/cosmic-measurer/cosmic-apex-measurer/scripts/parser.py](.cursor/skills/cosmic-measurer/cosmic-apex-measurer/scripts/parser.py))

*   **Update `STATIC_STRING_CONST` regex:** Support `public`, `global`, etc., in addition to `private`.
    ```python
    STATIC_STRING_CONST = re.compile(
        r"(?:public|private|global|protected)\s+static\s+final\s+String\s+(\w+)\s*=\s*'([^']+)'",
        re.IGNORECASE,
    )
    ```
*   **Add `EXTERNAL_CONSTANT_REF` regex:** Identify `ClassName.ConstantName` patterns in SOQL binds.
    ```python
    EXTERNAL_CONSTANT_REF = re.compile(r"\b([A-Z][a-zA-Z0-9_]*)\s*\.\s*([A-Z0-9_]+)\b")
    ```
*   **Modify `find_reads` and `find_writes`:**
    -   Capture any `ClassName.ConstantName` used in SOQL binds or DML.
    -   Allow passing an optional `external_constants` dictionary (mapping `ClassName.ConstantName` to literal values).
    -   Incorporate these into `_infer_record_type_from_bind`.
*   **Add helper `find_external_constant_calls(source)`:** Scans the source and returns a list of unique `ClassName` strings appearing in constant calls.

#### 2. Update `measure_apex.py` ([.cursor/skills/cosmic-measurer/cosmic-apex-measurer/scripts/measure_apex.py](.cursor/skills/cosmic-measurer/cosmic-apex-measurer/scripts/measure_apex.py))

*   **Update `measure_file`:**
    -   After initial parsing, use `find_external_constant_calls` to identify potential provider classes.
    -   For each class found:
        1.  Search for its `.cls` file using `find_class_file`.
        2.  If found, read the source and call `_parse_record_type_string_constants`.
        3.  Map the results to `ClassName.ConstantName` keys.
        4.  **If not found:** Add the class name to `called_classes_not_found` (standard behavior for missing dependencies).
    -   Re-run the parsing/inference pass with the collected `external_constants` map. If a constant reference cannot be resolved (either because the class is missing or the constant isn't in it), the data group will fall back to `::unknown RT`.

#### 3. Update `movements.py` ([.cursor/skills/cosmic-measurer/cosmic-apex-measurer/scripts/movements.py](.cursor/skills/cosmic-measurer/cosmic-apex-measurer/scripts/movements.py))

*   Ensure the `to_human_summary` correctly reports these resolved record types in the output table.

#### 4. Verification

*   Test with `AddSORController.cls` if `GlobalConstants.cls` is provided or mocked.
*   Run the existing test suite: `python3 .cursor/skills/cosmic-measurer/cosmic-apex-measurer/tests/test_measure_apex.py`.
