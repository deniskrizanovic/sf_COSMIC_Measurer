---
name: lwc-traversal-improvement
overview: Improve lwc-measurer to recursively traverse into custom child LWCs (c- prefix) and merge their data movements.
todos:
  - id: update-parser-detect-children
    content: Add detect_custom_child_components and kebab_to_component_name to lwc_parser.py
    status: in_progress
  - id: implement-lwc-traversal
    content: Implement recursive LWC traversal and merging in measure_lwc.py
    status: pending
  - id: verify-traversal-test
    content: Verify traversal with AddSORs and sui_UploadEvidence components
    status: pending
isProject: false
---

# LWC Traversal Improvement Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enable the LWC measurer to detect custom child components in HTML templates, traverse into their bundle directories, and merge their COSMIC data movements into the parent measurement.

**Architecture:**
- Update `lwc_parser.py` to extract custom child tags from HTML.
- Implement kebab-to-component-name conversion logic.
- Update `measure_lwc.py` to recursively call `measure_lwc_bundle` for child LWCs.
- Merge child movements with appropriate `viaArtifact` and `implementationType`.
- Use a `visited_lwcs` set to prevent infinite recursion.

**Tech Stack:** Python 3, HTMLParser, Regex

---

### Task 1: Update LWC Parser to detect child components

**Files:**
- Modify: `.cursor/skills/cosmic-measurer/cosmic-lwc-measurer/scripts/lwc_parser.py`

- [ ] **Step 1: Add `detect_custom_child_components` function**
  Extract all tags starting with `c-` from the HTML template.

- [ ] **Step 2: Implement `kebab_to_component_name` helper**
  Convert LWC kebab-case tags to component names (e.g., `sui_-upload-evidence` -> `sui_UploadEvidence`).

### Task 2: Implement LWC Traversal in Measurer

**Files:**
- Modify: `.cursor/skills/cosmic-measurer/cosmic-lwc-measurer/scripts/measure_lwc.py`

- [ ] **Step 1: Add `find_lwc_bundle_dir` helper**
  Search for the LWC bundle directory in the same parent directory as the current bundle.

- [ ] **Step 2: Update `measure_lwc_bundle` to support recursive traversal**
  - Add `visited_lwcs` parameter to track recursion.
  - Detect child LWCs using the new parser function.
  - For each child LWC, resolve its directory and call `measure_lwc_bundle` recursively.
  - Merge the resulting data movements into the parent's movements.

### Task 3: Verification and Testing

**Files:**
- Create: `.cursor/skills/cosmic-measurer/cosmic-lwc-measurer/tests/test_lwc_traversal.py`

- [ ] **Step 1: Write a test case for traversal**
  Use `metadata-to-measure/AddSORs` which calls `sui_UploadEvidence` to verify that movements from the child are included in the parent's output.

- [ ] **Step 2: Run tests**
  Ensure all tests pass, including existing ones.
