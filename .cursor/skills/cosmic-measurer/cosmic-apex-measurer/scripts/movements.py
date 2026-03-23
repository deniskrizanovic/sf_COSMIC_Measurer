"""
Ordering and JSON output for COSMIC data movements.
"""

import json
from typing import Any, Optional, TypedDict

try:
    from .parser import RawMovement
except ImportError:
    from parser import RawMovement


class ArtifactDict(TypedDict):
    type: str
    name: str


class DataMovementRow(TypedDict):
    name: str
    order: int
    movementType: str
    dataGroupRef: str
    implementationType: str
    isApiCall: bool


class DataMovementRowOptional(DataMovementRow, total=False):
    sourceLine: int
    mergedFrom: list[dict[str, Any]]
    viaClass: str


class CosmicMeasureOutputCore(TypedDict):
    functionalProcessId: str
    artifact: ArtifactDict
    dataMovements: list[DataMovementRowOptional]


class RecordTypeReadExcludedRow(TypedDict, total=False):
    """SOQL against RecordType excluded from CFP; listed for traceability."""

    name: str
    sourceLine: int


class CosmicMeasureOutput(CosmicMeasureOutputCore, total=False):
    calledClassesNotFound: list[str]
    recordTypeReadsExcludedFromCfp: list[RecordTypeReadExcludedRow]


# Order: E first, then all R, then all W, then X last (logical/execution order)
TYPE_ORDER = {"E": 0, "R": 1, "W": 2, "X": 3}

# Appended after all parser-derived movements: one final Exit (X) for errors/notifications (COSMIC FP rule).
# Parser-detected `return` exits remain as their own X rows; this row is always last.
CANONICAL_EXIT_NAME = "Errors/notifications"
CANONICAL_EXIT_DATA_GROUP_REF = "User"

# SOQL `FROM RecordType` — metadata lookup for Ids; excluded from FP data movements (see SKILL).
RECORD_TYPE_DATA_GROUP = "RecordType"


def partition_record_type_reads(
    movements: list[RawMovement],
) -> tuple[list[RawMovement], list[RawMovement]]:
    """Split out Read movements on the RecordType object (not counted toward CFP)."""
    kept: list[RawMovement] = []
    excluded: list[RawMovement] = []
    for m in movements:
        if m.movement_type == "R" and m.data_group_ref.lower() == RECORD_TYPE_DATA_GROUP.lower():
            excluded.append(m)
        else:
            kept.append(m)
    return kept, excluded


def order_movements(movements: list[RawMovement]) -> list[tuple[RawMovement, list]]:
    """Sort movements; dedupe R/W. Returns (movement, merged_from) — merged_from lists operations merged into Writes."""
    def sort_key(m: RawMovement) -> tuple:
        type_ord = TYPE_ORDER.get(m.movement_type, 1)
        exec_ord = m.execution_order if m.execution_order is not None else 999999
        line_ord = m.source_line if m.source_line is not None else 999999
        hint = m.order_hint
        return (type_ord, exec_ord, line_ord, hint)

    ordered = sorted(movements, key=sort_key)

    # Dedupe: R by (type, dataGroupRef, name); W by (type, dataGroupRef) only.
    # Writes: merge insert+update to same object → 1 Write (COSMIC: one boundary crossing per data group).
    seen_r: set[tuple[str, str, str]] = set()
    seen_w: dict[tuple[str, str], int] = {}  # key -> index in result
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
    m: RawMovement, order: int, merged_from: Optional[list[dict[str, Any]]] = None
) -> DataMovementRowOptional:
    out: DataMovementRowOptional = {
        "name": m.name,
        "order": order,
        "movementType": m.movement_type,
        "dataGroupRef": m.data_group_ref,
        "implementationType": "apex",
        "isApiCall": False,
    }
    if m.source_line is not None:
        out["sourceLine"] = m.source_line
    if merged_from:
        out["mergedFrom"] = merged_from
    if m.via_class:
        out["viaClass"] = m.via_class
    return out


def build_output(
    class_name: str,
    movements: list[RawMovement],
    functional_process_id: str = "<Id>",
    *,
    called_classes_not_found: Optional[list[str]] = None,
    implementation_type: str = "apex",
) -> CosmicMeasureOutput:
    movements, record_type_reads_excluded = partition_record_type_reads(movements)
    ordered = order_movements(movements)
    data_movements: list[DataMovementRowOptional] = [
        to_json_movement(m, i + 1, merged) for i, (m, merged) in enumerate(ordered)
    ]
    data_movements.append(
        {
            "name": CANONICAL_EXIT_NAME,
            "order": len(data_movements) + 1,
            "movementType": "X",
            "dataGroupRef": CANONICAL_EXIT_DATA_GROUP_REF,
            "implementationType": implementation_type,
            "isApiCall": False,
        }
    )
    result: CosmicMeasureOutput = {
        "functionalProcessId": functional_process_id,
        "artifact": {"type": "Apex", "name": class_name},
        "dataMovements": data_movements,
    }
    if called_classes_not_found is not None:
        result["calledClassesNotFound"] = called_classes_not_found
    if record_type_reads_excluded:
        rows: list[RecordTypeReadExcludedRow] = []
        for m in sorted(
            record_type_reads_excluded,
            key=lambda x: (x.source_line if x.source_line is not None else 0, x.name),
        ):
            row: RecordTypeReadExcludedRow = {"name": m.name}
            if m.source_line is not None:
                row["sourceLine"] = m.source_line
            rows.append(row)
        result["recordTypeReadsExcludedFromCfp"] = rows
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
    """
    Functional size (CFP) line + Notes for human-readable measurement output.
    CFP = count of data movements (E + R + W + X) after deduplication.
    """
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
            "**Merged writes:** Multiple DML operations on the same data group are one W "
            "(insert/update/delete merged per COSMIC rules)."
        )
    if any(m.get("viaClass") for m in rows):
        notes.append(
            "**Callee traversal:** Movements with Via include R/W merged from statically "
            "resolved `.cls` callees."
        )
    not_found = output.get("calledClassesNotFound") or []
    if not_found:
        notes.append(
            "**Not found:** `calledClassesNotFound` lists system types (e.g. Database, String) "
            "and Apex classes not found under `--search-paths`."
        )
    rt_excluded = output.get("recordTypeReadsExcludedFromCfp") or []
    if rt_excluded:
        parts = []
        for row in rt_excluded:
            line = row.get("sourceLine")
            nm = row.get("name", "Read RecordType")
            if line is not None:
                parts.append(f"L{line}: {nm}")
            else:
                parts.append(nm)
        notes.append(
            "**RecordType reads (excluded from CFP):** "
            + "; ".join(parts)
            + " — not counted as functional-process data movements (metadata lookup)."
        )
    notes.append(
        "**Canonical exit:** Last movement is always X — Errors/notifications "
        f"(`{CANONICAL_EXIT_DATA_GROUP_REF}`), after any parser-derived exits."
    )

    if notes:
        lines.append("")
        lines.append("**Notes:**")
        for n in notes:
            lines.append(f"- {n}")

    return "\n".join(lines)


def to_table(output: CosmicMeasureOutput) -> str:
    """Format data movements as a markdown-style table with line numbers."""
    rows = output["dataMovements"]
    if not rows:
        return f"{output['artifact']['name']}: no data movements"

    lines: list[str] = []
    lines.append(f"| Order | Type | Data group | Name | LineNumber | Via | Merged |")
    lines.append("|-------|------|------------|------|------------|-----|--------|")
    for m in rows:
        order = m.get("order", "")
        mtype = m.get("movementType", "")
        dg = m.get("dataGroupRef", "")
        name = m.get("name", "")
        line = m.get("sourceLine", "—")
        via = m.get("viaClass", "—")
        merged = m.get("mergedFrom", [])
        merged_str = ", ".join(f"{x.get('name', '?')} (L{x.get('sourceLine', '?')})" for x in merged) if merged else "—"
        lines.append(f"| {order} | {mtype} | {dg} | {name} | {line} | {via} | {merged_str} |")

    artifact = output["artifact"]
    header = f"**{artifact['name']}** ({artifact['type']})"
    out = header + "\n\n" + "\n".join(lines)
    not_found = output.get("calledClassesNotFound") or []
    if not_found:
        out += f"\n\nCalled classes not found: {', '.join(not_found)}"
    rt_excluded = output.get("recordTypeReadsExcludedFromCfp") or []
    if rt_excluded:
        out += "\n\nRecordType reads (excluded from CFP): " + "; ".join(
            (
                f"L{r['sourceLine']}: {r['name']}"
                if r.get("sourceLine") is not None
                else r.get("name", "")
            )
            for r in rt_excluded
        )
    out += to_human_summary(output)
    return out
