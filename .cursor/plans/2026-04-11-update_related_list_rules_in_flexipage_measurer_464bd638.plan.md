---
name: Update related list rules in FlexiPage measurer
overview: Update the FlexiPage measurer to correctly normalize related list API names to their actual object names (Data Groups) and update movement names accordingly, specifically handling __r to __c conversion, AttachedContentDocuments to ContentDocument, and Histories with parentFieldApiName lookup.
todos:
  - id: update-normalization-logic
    content: Update _normalize_related_list in flexipage_parser.py
    status: pending
  - id: update-call-sites
    content: Update call sites in flexipage_parser.py to use normalized name and data group
    status: pending
  - id: verify-changes
    content: Verify changes with WorkOrder.flexipage sample
    status: pending
isProject: true
---

1.  Modify `_normalize_related_list_to_data_group` in `flexipage_parser.py` to:
    *   Rename it to `_normalize_related_list` for better semantics.
    *   Accept `parent_field_api_name` as an optional argument.
    *   Return a tuple `(normalized_name, data_group_ref)`.
    *   Implement Rule 1: Convert `__r` suffix to `__c`.
    *   Implement Rule 2: Map `AttachedContentDocuments` to `ContentDocument`.
    *   Implement Rule 3: Map `Histories` to `parentObjectName_History` extracted from `parentFieldApiName` (e.g., `WorkOrder.Id` becomes `WorkOrder_History`).
2.  Update all call sites of `_normalize_related_list` in `flexipage_parser.py`:
    *   In `extract_tab_bound_component_movements`, pass `parentFieldApiName` and use both returned values for `name` and `dataGroupRef`.
    *   In `find_reads_from_page` and `find_exits_from_page`, pass `rl.parent_field_api_name` and use both returned values.
3.  Verify the changes against the provided examples in `samples/flexipages/WorkOrder.flexipage`.
4.  Run existing tests to ensure no regressions.
