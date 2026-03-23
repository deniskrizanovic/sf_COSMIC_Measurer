# Skill Review: `.cursor/plans/cosmic_measurer_skills.plan.md`

Reviewed against: [`skill-best-practices.md`](../skill-best-practices.md) at the repository root. Blockquotes in the original review referred to the same criteria; they align with that file’s sections.

**Scope:** This document is an **implementation plan** for multiple Cursor skills, not a `SKILL.md`. Findings assess how well the plan prepares future `SKILL.md` files and repository layout to satisfy skill best practices.

---

## 1. Plan does not require the four core SKILL.md sections — acceptance criteria gap

**Best Practice Reference:**
> #### 3c. Core Instruction Sections  
> Verify the presence and quality of all four required sections:  
> - **Goal** — Explicit section defining the purpose  
> - **Workflow** — Logical, numbered or sequenced steps  
> - **Validation** — Checks that ensure outputs follow best practices  
> - **Output** — Explicit definition of the final artifact

**Current:** Phases 2–4 specify deliverables (e.g. “Create …/SKILL.md”, inspection rules, tests) but never state that each `SKILL.md` must include **Goal**, **Workflow**, **Validation**, and **Output** as explicit sections. Phase 1 lists `reference.md`, mapping config, and a JSON template, but does not list “SKILL skeleton with four required sections” as a foundation deliverable.

**Recommendation:** Add to **Phase 1** (or each phase checklist) a non-negotiable acceptance criterion, for example: “Each artifact skill’s `SKILL.md` includes sections: Goal; Workflow; Validation; Output (final artifact definition).” Optionally add one line to the **Suggested Chat Sequence** table: “Deliverable: SKILL.md (4 sections) + …”.

**Reasoning:** Without this, implementers may produce long reference-style docs or inspection notes inside `SKILL.md` that omit Validation/Output, which directly hurts agent behavior and consistency across `cosmic-apex-measurer`, `cosmic-flow-measurer`, and `cosmic-layout-measurer`.

**Severity:** High — Violates a core structural practice that impacts output quality of the skills the plan is meant to create.

---

## 2. Planned skill folder names do not follow the gerund (“-ing”) naming convention

**Best Practice Reference:**
> #### 3a. Naming (Folder and Frontmatter)  
> - Folder name uses gerund form (verb ending in "-ing")
> - Folder name is lowercase with hyphens

**Current:** The plan standardizes on `cosmic-apex-measurer`, `cosmic-flow-measurer`, and `cosmic-layout-measurer` (noun “measurer”, not gerund).

**Recommendation:** Rename to gerund form (e.g. `cosmic-apex-measuring`, `cosmic-flow-measuring`, `cosmic-layout-measuring`) **or** document a deliberate exception: “We use *-measurer* for product naming consistency; frontmatter `name` matches folder exactly.” If renaming, update every path in the plan and the **File Structure (final)** tree in one pass.

**Reasoning:** Aligns folder names with discoverability and convention checks used by skill reviewers and tooling.

**Severity:** Medium — Reduces consistency with documented naming; does not block implementation if explicitly exempted.

---

## 3. No explicit requirement for skill `description` frontmatter (discovery / activation)

**Best Practice Reference:**
> #### 3b. Description (Frontmatter)  
> - Roughly 100 words or fewer  
> - Leads with what the skill produces or the expected outcome  
> - Includes domain keywords relevant to the task  
> - Contains trigger phrases for when the skill should activate

**Current:** Phase deliverables describe creating `SKILL.md` and inspection rules but do not require YAML frontmatter fields `name` and `description`, nor a description that leads with outcomes and trigger phrases.

**Recommendation:** Add a **Phase 1** bullet (or a shared “SKILL.md contract” subsection): “Each `SKILL.md` frontmatter includes `name` (exact folder match), `description` (≤100 words, outcome-first, COSMIC/Salesforce keywords, trigger phrases such as ‘measure Apex for COSMIC’, ‘data movements E/R/X/W’).”

**Reasoning:** Improves Cursor activation and matching user intent to the right skill.

**Severity:** Medium — Affects discoverability and activation, not the Python parser logic.

---

## 4. Optional metadata not mentioned for long-lived skills

**Best Practice Reference:**
> #### 3i. Metadata Completeness  
> - Frontmatter includes `name` and `description` (required)  
> - Optional but recommended: `metadata.version`, `metadata.category`, `license`, `compatibility`

**Current:** The plan does not mention optional `metadata.version`, `metadata.category`, `license`, or `compatibility`.

**Recommendation:** Add one optional line under the SKILL contract: “Consider `metadata.category` (e.g. Salesforce, COSMIC) and `metadata.version` when skills stabilize.”

**Reasoning:** Helps maintenance and filtering in large skill collections.

**Severity:** Low — Nice-to-have for governance.

---

## 5. Minor duplication and list formatting in the plan body

**Best Practice Reference:**
> #### 3h. Formatting  
> - Heading hierarchy is consistent (no H1 inside H2, etc.)  
> - Markdown is well-formed (proper spacing, consistent list formatting)

**Current:** Flow inspection rules list `recordLookups` twice (lines 139–140). Under **Phase 2**, nested bullets use 2-space indent for some sub-items; mixed indentation can reduce readability. Extra blank lines appear around the Mermaid block (cosmetic).

**Recommendation:** Deduplicate Flow **Read (R)** bullets to a single `recordLookups` / getRecords line. Normalize nested list indentation to 4 spaces under numbered items. Trim redundant blank lines around fenced diagrams.

**Reasoning:** Easier review and copy-paste from the plan into issues or chats.

**Severity:** Low — Cosmetic.

---

## Summary

| # | Finding | Severity | Category |
|---|---------|----------|----------|
| 1 | Four core SKILL.md sections not in plan acceptance criteria | High | Structure |
| 2 | Folder names `*-measurer` vs gerund `-ing` convention | Medium | Naming |
| 3 | No explicit `description` frontmatter requirement for skills | Medium | Discovery |
| 4 | Optional metadata not mentioned for skills | Low | Metadata |
| 5 | Duplicate Flow bullet and minor markdown formatting | Low | Formatting |

**Overall Assessment:** The plan is strong on **architecture**, **phased delivery**, **sample-based testing**, and **golden JSON** for regression, which aligns well with **Testing and maintainability** and progressive disclosure via `reference.md`, `scripts/`, and `examples/`. The main gap is that it does not yet **encode the four required SKILL.md sections** and **description frontmatter** as explicit deliverables, so future skills risk being structurally incomplete until those are added to Phase 1 or each phase’s checklist. Future reviews can cite [`skill-best-practices.md`](../skill-best-practices.md) directly.
