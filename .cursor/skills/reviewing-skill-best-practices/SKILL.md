---
description: Review and validate SKILL.md files against skill-best-practices.md. Use when asked to review a skill, audit a SKILL.md, check skill quality, validate skill structure, or run a skill best-practices review. Produces a consistent review report with numbered findings, severity ratings, and recommendations.
globs: **/SKILL.md, **/reviews/**
alwaysApply: false
---

# Reviewing Skill Best Practices

## Goal

Review a SKILL.md file against the documented best practices in `skill-best-practices.md` and produce a structured review report with numbered findings, severity ratings, and concrete recommendations.

## Workflow

### Step 1: Load the Best Practices Reference

Read `skill-best-practices.md` from the repository root. This is the authoritative source for all review criteria. If the file is not found, stop and inform the user.

### Step 2: Load the Target Skill

Read the target SKILL.md file. Also inspect the skill's directory for supporting assets (`docs/`, `examples/`, `templates/`, `scripts/`, `references/`, `assets/`). Note which subdirectories exist and which are absent.

### Step 3: Evaluate Against Review Criteria

Assess the skill against every criterion below. Only report findings where the skill does not fully pass.

#### 3a. Naming (Folder and Frontmatter)

- Folder name uses gerund form (verb ending in "-ing")
- Folder name is lowercase with hyphens
- Frontmatter `name:` matches the folder name exactly
- Name is short, readable, and describes an action Vibes can execute

#### 3b. Description (Frontmatter)

- Roughly 100 words or fewer
- Leads with what the skill produces or the expected outcome
- Includes domain keywords relevant to the task
- Contains trigger phrases for when the skill should activate
- Describes results, not intentions
- Does not contain operational instructions or implementation details

#### 3c. Core Instruction Sections

Verify the presence and quality of all four required sections:

- **Goal** — Explicit section defining the purpose
- **Workflow** — Logical, numbered or sequenced steps
- **Validation** — Checks that ensure outputs follow best practices
- **Output** — Explicit definition of the final artifact

#### 3d. Progressive Disclosure

- SKILL.md is under 500 lines
- Supporting material extracted into `docs/`, `examples/`, or `templates/`
- Core instructions remain focused on goal, workflow, validation, and output

#### 3e. Directory Structure

- Skill directory is one level deep (no deep nesting)
- Supporting files in recognized subdirectories (`docs/`, `examples/`, `templates/`, `scripts/`, `references/`, `assets/`)
- At least one supporting asset exists where content would benefit from it

#### 3f. Context Efficiency

- No unnecessary explanations or filler content
- Instructions are concise and directive
- No redundant or duplicated content blocks
- "When to Use" section does not simply repeat the frontmatter description

#### 3g. Instructional Tone

- Directive/imperative tone ("Ensure...", "Always...", "Never...")
- Reads as instructions *to Vibes*, not documentation *about a topic*

#### 3h. Formatting

- Heading hierarchy is consistent (no H1 inside H2, etc.)
- Markdown is well-formed (proper spacing, consistent list formatting)
- Capitalization is consistent throughout

#### 3i. Metadata Completeness

- Frontmatter includes `name` and `description` (required)
- Optional but recommended: `metadata.version`, `metadata.category`, `license`, `compatibility`

#### 3j. Testing and Maintainability

- Skill appears tested in realistic scenarios
- Instructions are modular and easy to update
- Skill is reusable across projects

### Step 4: Assign Severity

| Severity | Criteria |
|----------|----------|
| **High** | Violates a core best practice that impacts discoverability, activation, or output quality. Fix before merging. |
| **Medium** | Reduces quality or consistency but does not prevent the skill from functioning. Should be addressed. |
| **Low** | Cosmetic, minor efficiency, or nice-to-have improvement. |

### Step 5: Categorize Each Finding

Assign one of: Naming, Discovery, Structure, Architecture, Efficiency, Tone, Formatting, Metadata.

### Step 6: Generate the Review Report

Write the report using the exact format below. Order findings by severity (High first, then Medium, then Low).

### Step 7: Identify Strengths

Note what the skill does well. Include this in the Overall Assessment.

## Validation

Before finalizing, verify:
- Every finding includes a Best Practice Reference blockquote
- Every finding includes Current state, Recommendation, Reasoning, and Severity
- Findings are numbered sequentially with no gaps
- The summary table includes all findings
- The Overall Assessment acknowledges strengths, not just gaps

## Output

Save the report to `reviews/<skill-folder-name>-skill-review.md`.

## Report Template

Every review report MUST follow this exact format:

```markdown
# Skill Review: `<skill-folder-path>/SKILL.md`

Reviewed against: `skill-best-practices.md`

---

## 1. <Short Finding Title> — <Brief Description>

**Best Practice Reference:**
> <Exact quote or close paraphrase from skill-best-practices.md>

**Current:** <What the skill currently has or does>

**Recommendation:** <Specific, actionable suggestion with examples>

**Reasoning:** <Why this matters for Vibes' behavior, discoverability, or output quality>

**Severity:** <High | Medium | Low> — <One-sentence rationale>

---

(Repeat for each finding, numbered sequentially)

---

## Summary

| # | Finding | Severity | Category |
|---|---------|----------|----------|
| 1 | <title> | <High/Medium/Low> | <category> |
| ... | ... | ... | ... |

**Overall Assessment:** <2-3 sentences: acknowledge strengths first, summarize gaps, state what addressing findings would accomplish.>
```

### Report Rules

1. Every finding MUST include a Best Practice Reference blockquote from `skill-best-practices.md`.
2. Recommendations MUST be specific — include example text, renamed values, or restructured sections.
3. Number findings sequentially with no gaps.
4. Use only `High`, `Medium`, or `Low` severity labels.
5. Use only these category labels: Naming, Discovery, Structure, Architecture, Efficiency, Tone, Formatting, Metadata.
6. Order findings by severity: High first, then Medium, then Low.
7. The summary table MUST include every finding.
8. The Overall Assessment MUST acknowledge at least one strength.
