"""
Shared ordering, dedup, and JSON output for COSMIC data movements.
Parameterized for artifact_type and implementation_type so all measurer skills can reuse.
"""

import json
from typing import Any, Optional, TypedDict

from .models import MovementType, RawMovement


class ArtifactDict(TypedDict):
    type: str
    name: str


class DataMovementRow(TypedDict):
    name: str
    order: int
    movementType: MovementType
    dataGroupRef: str
    implementationType: str
    isApiCall: bool


class DataMovementRowOptional(DataMovementRow, total=False):
    sourceLine: int
    mergedFrom: list[dict[str, Any]]
    viaArtifact: str
    artifactName: str
    isAsync: bool
    tier: int
    tierLabel: str
    triggeringBlock: str


class CosmicMeasureOutputCore(TypedDict):
    functionalProcessId: str
    artifact: ArtifactDict
    dataMovements: list[DataMovementRowOptional]


class CosmicMeasureOutput(CosmicMeasureOutputCore, total=False):
    traversalWarnings: list[str]


TYPE_ORDER = {"E": 0, "R": 1, "W": 2, "X": 3}

CANONICAL_EXIT_NAME = "Errors/notifications"
CANONICAL_EXIT_DATA_GROUP_REF = "status/errors/etc"
MAX_MOVEMENT_NAME_LENGTH = 80


def cap_movement_name(name: str) -> str:
    return name[:MAX_MOVEMENT_NAME_LENGTH]


def order_movements(movements: list[RawMovement]) -> list[tuple[RawMovement, list]]:
    """Sort movements by tier then type; dedupe R/W. Returns (movement, merged_from)."""
    def sort_key(m: RawMovement) -> tuple:
        tier_ord = getattr(m, "tier", None) or 1
        type_ord = TYPE_ORDER.get(m.movement_type, 1)
        exec_ord = m.execution_order if m.execution_order is not None else 999999
        hint = m.order_hint
        line_ord = m.source_line if m.source_line is not None else 999999
        return (tier_ord, type_ord, exec_ord, hint, line_ord)

    ordered = sorted(movements, key=sort_key)

    seen_r: set[tuple[str, str, str]] = set()
    seen_w: dict[tuple[str, str], int] = {}
    result: list[tuple[RawMovement, list]] = []
    for m in ordered:
        if m.movement_type == "R":
            key = (m.movement_type, m.data_group_ref, m.name)
            if key in seen_r:
                continue
            seen_r.add(key)
            result.append((m, []))
        elif m.movement_type == "W":
            key = (m.movement_type, m.data_group_ref)
            if key in seen_w:
                idx = seen_w[key]
                merged_item = {"name": m.name}
                if m.source_line is not None:
                    merged_item["sourceLine"] = m.source_line
                result[idx][1].append(merged_item)
                continue
            seen_w[key] = len(result)
            result.append((m, []))
        else:
            result.append((m, []))

    return result


def to_json_movement(
    m: RawMovement,
    order: int,
    merged_from: Optional[list[dict[str, Any]]] = None,
    implementation_type: str = "apex",
) -> DataMovementRowOptional:
    out: DataMovementRowOptional = {
        "name": cap_movement_name(m.name),
        "order": order,
        "movementType": m.movement_type,
        "dataGroupRef": m.data_group_ref,
        "implementationType": implementation_type,
        "isApiCall": False,
    }
    if m.source_line is not None:
        out["sourceLine"] = m.source_line
    if merged_from:
        out["mergedFrom"] = merged_from
    if m.via_artifact:
        out["viaArtifact"] = m.via_artifact
    if m.artifact_name:
        out["artifactName"] = m.artifact_name
    if m.is_async:
        out["isAsync"] = True
    tier = getattr(m, "tier", None)
    if tier is not None:
        out["tier"] = tier
    tier_label = getattr(m, "tier_label", None)
    if tier_label is not None:
        out["tierLabel"] = tier_label
    triggering_block = getattr(m, "triggering_block", None)
    if triggering_block is not None:
        out["triggeringBlock"] = triggering_block
    return out


def build_output(
    artifact_type: str,
    artifact_name: str,
    movements: list[RawMovement],
    functional_process_id: str = "<Id>",
    *,
    implementation_type: str = "apex",
) -> CosmicMeasureOutput:
    # Append filetype so artifacts and movements identify their source clearly
    artifact_name = f"{artifact_name}.{artifact_type.lower()}"

    for m in movements:
        if m.artifact_name is None:
            m.artifact_name = artifact_name
    ordered = order_movements(movements)
    data_movements: list[DataMovementRowOptional] = [
        to_json_movement(m, i + 1, merged, implementation_type)
        for i, (m, merged) in enumerate(ordered)
    ]
    data_movements.append(
        {
            "name": cap_movement_name(CANONICAL_EXIT_NAME),
            "order": len(data_movements) + 1,
            "movementType": "X",
            "dataGroupRef": CANONICAL_EXIT_DATA_GROUP_REF,
            "implementationType": implementation_type,
            "isApiCall": False,
            "tier": 3,
            "tierLabel": "Terminal",
            "artifactName": artifact_name,
        }
    )
    result: CosmicMeasureOutput = {
        "functionalProcessId": functional_process_id,
        "artifact": {"type": artifact_type, "name": artifact_name},
        "dataMovements": data_movements,
    }
    return result


def to_json_string(output: CosmicMeasureOutput, indent: int = 2) -> str:
    return json.dumps(output, indent=indent)


def count_movement_types(rows: list[DataMovementRowOptional]) -> dict[str, int]:
    """Count E/R/W/X in ordered data movements."""
    counts = {"E": 0, "R": 0, "W": 0, "X": 0}
    for m in rows:
        t = m.get("movementType", "")
        if t in counts:
            counts[t] += 1
    return counts


def to_human_summary(output: CosmicMeasureOutput) -> str:
    """Functional size (CFP) line + Notes for human-readable output."""
    rows = output["dataMovements"]
    if not rows:
        return ""

    counts = count_movement_types(rows)
    total = sum(counts.values())
    parts: list[str] = []
    if counts["E"]:
        parts.append(f"{counts['E']} E")
    if counts["R"]:
        parts.append(f"{counts['R']} R")
    if counts["W"]:
        parts.append(f"{counts['W']} W")
    if counts["X"]:
        parts.append(f"{counts['X']} X")
    equation = " + ".join(parts) if parts else "0"

    lines: list[str] = [
        "",
        f"**Functional size:** {equation} = **{total} CFP**",
    ]

    notes: list[str] = []
    if any(m.get("mergedFrom") for m in rows):
        notes.append(
            "**Merged writes:** Multiple operations on the same data group are one W "
            "(merged per COSMIC rules)."
        )
    if any(m.get("viaArtifact") for m in rows):
        notes.append(
            "**Artifact traversal:** Movements with Via include R/W merged from "
            "traversed artifacts."
        )
    if any(m.get("isAsync") for m in rows):
        notes.append("**Async traversal:** Rows marked `isAsync=true` are asynchronous handoffs.")
    warnings = output.get("traversalWarnings") or []
    for warning in warnings:
        notes.append(f"**Warning:** {warning}")
    notes.append(
        "**Canonical exit:** Last movement is always X — Errors/notifications "
        f"(`{CANONICAL_EXIT_DATA_GROUP_REF}`), after any artifact-derived exits."
    )

    if notes:
        lines.append("")
        lines.append("**Notes:**")
        for n in notes:
            lines.append(f"- {n}")

    return "\n".join(lines)


_TIER_LABELS_IN_ORDER = ["Init", "Interactions", "Terminal"]


def _table_rows_block(rows: list) -> list[str]:
    lines: list[str] = []
    lines.append("| Order | Type | Name | Data group | LineNumber | ArtifactName | Via | Merged |")
    lines.append("|-------|------|------|------------|------------|--------------|-----|--------|")
    for m in rows:
        order = m.get("order", "")
        mtype = m.get("movementType", "")
        dg = m.get("dataGroupRef", "")
        name = m.get("name", "")
        line = m.get("sourceLine", "—")
        artifact = m.get("artifactName", "—")
        via = m.get("viaArtifact", "—")
        merged = m.get("mergedFrom", [])
        merged_str = (
            ", ".join(
                f"{x.get('name', '?')} (L{x.get('sourceLine', '?')})"
                for x in merged
            )
            if merged
            else "—"
        )
        lines.append(
            f"| {order} | {mtype} | {name} | {dg} | {line} | {artifact} | {via} | {merged_str} |"
        )
    return lines


def to_table(output: CosmicMeasureOutput) -> str:
    """Format data movements as a markdown table, grouped by tier when tier data is present."""
    rows = output["dataMovements"]
    if not rows:
        return f"{output['artifact']['name']}: no data movements"

    artifact = output["artifact"]
    header = f"**{artifact['name']}** ({artifact['type']})"

    has_tiers = any(r.get("tierLabel") for r in rows)
    if not has_tiers:
        lines = _table_rows_block(rows)
        out = header + "\n\n" + "\n".join(lines)
        out += to_human_summary(output)
        return out

    grouped: dict[str, list] = {}
    ungrouped: list = []
    for r in rows:
        label = r.get("tierLabel")
        if label:
            grouped.setdefault(label, []).append(r)
        else:
            ungrouped.append(r)

    sections: list[str] = [header]
    for label in _TIER_LABELS_IN_ORDER:
        group = grouped.get(label)
        if not group:
            continue
        sections.append(f"\n## {label}")
        sections.append("\n".join(_table_rows_block(group)))
    if ungrouped:
        sections.append("\n## Other")
        sections.append("\n".join(_table_rows_block(ungrouped)))

    out = "\n\n".join(sections)
    out += to_human_summary(output)
    return out
