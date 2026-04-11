---
name: Refine LWC Entry Movements
overview: Exclude page navigation and merge save commands into interaction blocks in LWC measurements to better align with COSMIC functional process boundaries.
todos:
  - id: update-parser-logic平衡
    content: Update _classify_node in lwc_parser.py to remove pagination and merge save commands
    status: completed
  - id: update-unit-tests平衡
    content: Update and add unit tests in test_lwc_parser.py
    status: completed
  - id: verify-and-update-measurement平衡
    content: Verify changes with AddSORs measurement and update JSON file
    status: completed
isProject: false
---

Modify `lwc_parser.py` to refine how interaction blocks are classified and merged, then update tests and re-measure the `AddSORs` component.

### Implementation Details

#### `lwc_parser.py`
- In `_classify_node`:
    - Remove the logic that creates the `pagination` block.
    - Update the `save-command` logic to attempt a merge with any preceding `filter`, `row-edit`, or `select-all` block in the same node.
    - If merged, append the save handlers to the existing block and append " and save command" to the movement name.
    - If not merged, ensure the `save-command` block only includes the handlers associated with the save buttons themselves, rather than all handlers in the node.

#### `test_lwc_parser.py`
- Update `test_block_classifier_pagination_block` to assert that no Entry movements are created for pagination-only buttons.
- Add `test_block_classifier_save_merge` to verify that a Save button in the same container as a filter or row-edit merges correctly.

### Verification
- Run `pytest` on `.cursor/skills/cosmic-measurer/cosmic-lwc-measurer/tests/test_lwc_parser.py`.
- Re-run the measurement for `samples/lwc/AddSORs` and verify that movements 13 (navigation) is gone and 14 (save) is merged into 12 (row edits).
- Update `measurements/AddSORs.lwc.measure.json` with the new results.
