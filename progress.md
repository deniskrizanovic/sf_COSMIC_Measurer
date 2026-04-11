# Progress Report: Update related list rules in FlexiPage measurer

## Final Summary of Implementation
The implementation updated the FlexiPage measurer to correctly normalize related list API names to their actual object names (Data Groups) and update movement names accordingly. 

Key changes in `flexipage_parser.py`:
- Renamed `_normalize_related_list_to_data_group` to `_normalize_related_list` for better semantics.
- Updated the normalization logic to return a tuple of `(normalized_name, data_group_ref)`.
- Implemented Rule 1: Convert `__r` suffix to `__c`.
- Implemented Rule 2: Map `AttachedContentDocuments` to `ContentDocument`.
- Implemented Rule 3: Map `Histories` to `parentObjectName_History` extracted from `parentFieldApiName` (e.g., `WorkOrder.Id` becomes `WorkOrder_History`).
- Updated all call sites in `extract_tab_bound_component_movements`, `find_reads_from_page`, and `find_exits_from_page` to use both the normalized name for the movement and the data group reference.

## Verification Evidence
- **All tests passed**: 45 tests passed across `test_flexipage_parser.py` and `test_measure_flexipage_cli.py`.
- **Coverage percentages**:
  - `flexipage_parser.py`: 95%
  - `measure_flexipage.py`: 95%
  - **TOTAL**: 95%

```bash
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0
collected 45 items

.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/tests/test_flexipage_parser.py . [  2%]
...................                                                      [ 44%]
.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/tests/test_measure_flexipage_cli.py . [ 46%]
........................                                                 [100%]

================================ tests coverage ================================
Name                                                                                    Stmts   Miss  Cover
-----------------------------------------------------------------------------------------------------------
.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts/flexipage_parser.py      333     16    95%
.cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts/measure_flexipage.py     390     21    95%
-----------------------------------------------------------------------------------------------------------
TOTAL                                                                                     723     37    95%
============================== 45 passed in 0.25s ==============================
```

## Final State
- **Merged to main**: All changes have been integrated into the `main` branch.

## How to Verify
To run the unit tests:
```bash
python3 -m pytest ".cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/tests/test_flexipage_parser.py"
```

To run the measurer on a sample FlexiPage:
```bash
python3 .cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/scripts/measure_flexipage.py samples/flexipages/WorkOrder.flexipage --json
```
