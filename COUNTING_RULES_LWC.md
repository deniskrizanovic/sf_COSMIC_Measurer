# LWC Counting Rules

Detailed counting rules for the LWC measurer. For a summary and the data flow diagram, see [COUNTING_RULES.md](COUNTING_RULES.md#lwc-rules).

## The 3-tier model

LWC measurement replaces the flat `E → R → W → X` ordering with a 3-tier interaction-driven model. Each tier groups movements by when they occur in the component lifecycle.

| Tier | Label | Contents | Ordering |
|---|---|---|---|
| **1** | Init | `@wire` R movements + Apex R movements called from `connectedCallback` + Apex E (method params) | By `order_hint` / source line |
| **2** | Interactions | One E-led cluster per detected HTML block; each cluster includes R movements whose Apex class is linked to that block's handlers | In DOM order; within each cluster: E → associated R(s) → display X (if this cluster first populates the view) |
| **3** | Terminal | All W movements + canonical X (`Errors/notifications`) | Writes first, canonical X last |

The display X (`"Display LWC output to user"`) sits at the end of the **first Interactions cluster that has an associated R** — expressing that the view is populated after that interaction fires, not at load. For read-only components with no interaction blocks, it falls back to the end of Init.

## HTML block classification

The `HtmlBlockClassifier` walks the HTML template using Python's built-in `html.parser`. It builds a lightweight element tree and collects **structural containers** that have at least one event handler (`on*` attribute) anywhere inside them. One `E` movement is emitted per container.

The block name and data group are derived by inspecting what the container holds:

| Container contents | Derived E name | Derived data group | Block label |
|---|---|---|---|
| `for:each` with event handlers on row elements | `"Receive row edits"` | `"RowData"` | `row-edit` |
| `<input type="checkbox">` with `onclick`/`onchange` outside `for:each` | `"Receive select-all"` | `"RowSelection"` | `select-all` |
| `oncustomlookupupdateevent` or search `lightning-input` with `onchange` | `"Receive filter criteria"` | `"FilterCriteria"` | `filter` |
| `lightning-button` with `onclick` — label matches save/submit/confirm | `"Receive save command"` | `"SaveCommand"` | `save-command` |
| `lightning-button` with `onclick` — label matches previous/next/page | `"Receive page navigation"` | `"PageNavigation"` | `pagination` |
| Anything else | `"Receive user interaction"` | `"User"` | `generic` |

- All block `E` movements are assigned `tier=2, tier_label="Interactions"`.
- `block_label` is set to the classification key (e.g. `"row-edit"`, `"filter"`).
- DOM order is preserved: blocks are emitted in the order they appear in the HTML.
- Each block records its **handler method names** (collected from `on*` attribute values) for use in the call graph step.
- Components with no event handlers emit no block `E` (read-only components).

## JS handler → Apex call graph

`extract_handler_apex_calls(js_source, apex_import_vars) → dict[str, list[str]]`

Scans the JS source for class method definitions. Uses brace-depth counting to extract each method body, then checks which Apex import variable names are called within that body. Cross-references with `detect_apex_import_vars` (maps var → class name) to resolve to Apex class names.

Returns a handler-name → Apex class name mapping, for example:

```
{
  "handleFilterChange": ["AddSORController"],
  "handleSave": ["AddSORController", "WorkOrderLineItemTableController"]
}
```

Each block's collected handler names are looked up in this map to produce `block.apex_classes: list[str]` — the Apex classes whose R movements should be placed in that block's Interactions cluster rather than Init.

## Tier assignment

After all movements are collected (native + merged Apex), tiers are assigned using the block → apex_classes map:

| Movement | Tier | Notes |
|---|---|---|
| Apex E (method params) | 1 — Init | Fire as part of the load sequence |
| `@wire` R | 1 — Init | |
| Apex R — class **not** linked to any block | 1 — Init | Called from `connectedCallback` or load lifecycle |
| Apex R — class **linked** to a block | 2 — Interactions | `triggering_block` set to the block label |
| E from block classifier | 2 — Interactions | Already set by classifier |
| `X "Display LWC output to user"` | 2 — Interactions (or 1 fallback) | Tier 2 on the first Interactions block with associated R; tier 1 for read-only components |
| W movements | 3 — Terminal | |
| Canonical `X "Errors/notifications"` | 3 — Terminal | Always last |

## Ordering

`order_movements()` uses a 3-tier sort key:

- **Primary**: tier (1 → 2 → 3)
- **Within tier 1**: Apex E → R by `order_hint` → display X (if no interaction-linked R)
- **Within tier 2**: by DOM block order (`order_hint`); within each block: E → R → X
- **Within tier 3**: W movements by `order_hint`, canonical X always last

`DataMovementRowOptional` includes three optional backward-compatible fields: `tier`, `tierLabel`, `triggeringBlock`.

## Table output (`to_table()`)

Output rows are grouped by `tierLabel` with a section header per tier (`### Init`, `### Interactions`, `### Terminal`). Components with no Interactions-tier movements (read-only) render only Init and Terminal sections.

## Native extraction

- JS/HTML analysis produces native `E/R/W/X` candidates (events, reads, writes, rendered outputs).

## Apex import integration

- Imported Apex methods are measured through the Apex measurer.
- Imported Apex exits are treated as internal handoff and excluded from LWC visible exits.
- Canonical final exit is appended once at LWC output stage.

## Validation contract

- Optional `--required-type` validates presence of required movement types and reports missing ones.
