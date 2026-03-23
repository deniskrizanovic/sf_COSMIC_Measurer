# Cursor skill best practices

Authoritative criteria for authoring and reviewing `SKILL.md` files in this repository. Use with `.cursor/skills/reviewing-skill-best-practices/SKILL.md` when running structured skill reviews.

---

## Naming (folder and frontmatter)

- Folder name uses gerund form (verb ending in `-ing`)
- Folder name is lowercase with hyphens
- Frontmatter `name:` matches the folder name exactly
- Name is short, readable, and describes an action the agent can execute

---

## Description (frontmatter)

- Roughly 100 words or fewer
- Leads with what the skill produces or the expected outcome
- Includes domain keywords relevant to the task
- Contains trigger phrases for when the skill should activate
- Describes results, not intentions
- Does not contain operational instructions or implementation details

---

## Core instruction sections

Each `SKILL.md` must include all four of the following sections, with clear, usable content:

| Section | Purpose |
|--------|---------|
| **Goal** | Explicit purpose of the skill |
| **Workflow** | Logical, numbered or sequenced steps |
| **Validation** | Checks that ensure outputs follow best practices |
| **Output** | Explicit definition of the final artifact |

---

## Progressive disclosure

- `SKILL.md` is under 500 lines
- Supporting material is extracted into `docs/`, `examples/`, or `templates/` (and related folders below)
- Core instructions stay focused on goal, workflow, validation, and output

---

## Directory structure

- Skill directory is one level deep (no deep nesting of skill folders)
- Supporting files live in recognized subdirectories: `docs/`, `examples/`, `templates/`, `scripts/`, `references/`, `assets/`
- At least one supporting asset exists where content would benefit from it

---

## Context efficiency

- No unnecessary explanations or filler content
- Instructions are concise and directive
- No redundant or duplicated content blocks
- A “When to Use” section does not simply repeat the frontmatter description

---

## Instructional tone

- Directive / imperative tone (“Ensure…”, “Always…”, “Never…”)
- Reads as instructions *to the agent*, not documentation *about a topic*

---

## Formatting

- Heading hierarchy is consistent (e.g. no `H1` inside `H2`)
- Markdown is well-formed (spacing, lists)
- Capitalization is consistent throughout

---

## Metadata completeness

**Required in frontmatter:**

- `name`
- `description`

**Optional but recommended:**

- `metadata.version`
- `metadata.category`
- `license`
- `compatibility`

---

## Testing and maintainability

- Skill is exercised in realistic scenarios (or clearly testable)
- Instructions are modular and easy to update
- Skill is reusable across projects where applicable

---

## Review: severity

| Severity | When to use |
|----------|----------------|
| **High** | Violates a core practice that impacts discoverability, activation, or output quality. Fix before merging. |
| **Medium** | Reduces quality or consistency; skill can still function. Should be addressed. |
| **Low** | Cosmetic, minor efficiency, or nice-to-have. |

---

## Review: finding categories

Use exactly one category per finding:

`Naming` · `Discovery` · `Structure` · `Architecture` · `Efficiency` · `Tone` · `Formatting` · `Metadata`
