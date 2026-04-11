"""
Apex-specific ordering and JSON output for COSMIC data movements.
Thin wrapper around shared.output with RecordType exclusion logic.
"""

import sys
from pathlib import Path
from typing import Any, Optional, TypedDict

_SCRIPTS_DIR = Path(__file__).resolve().parent
_COSMIC_MEASURER_DIR = _SCRIPTS_DIR.parent.parent
if str(_COSMIC_MEASURER_DIR) not in sys.path:
    sys.path.insert(0, str(_COSMIC_MEASURER_DIR))

from shared.models import RawMovement  # noqa: E402
from shared.output import (  # noqa: E402
    CANONICAL_EXIT_DATA_GROUP_REF,
    CANONICAL_EXIT_NAME,
    TYPE_ORDER,
    ArtifactDict,
    DataMovementRow,
    DataMovementRowOptional,
    count_movement_types,
    order_movements,
    to_json_string,
)
from shared.output import to_human_summary as _shared_to_human_summary  # noqa: E402
from shared.output import to_table as _shared_to_table  # noqa: E402
from shared.output import to_json_movement as _shared_to_json_movement  # noqa: E402

RECORD_TYPE_DATA_GROUP = "RecordType"


class RecordTypeReadExcludedRow(TypedDict, total=False):
    """SOQL against RecordType excluded from CFP; listed for traceability."""
    name: str
    sourceLine: int


class CosmicMeasureOutputCore(TypedDict):
    functionalProcessId: str
    artifact: ArtifactDict
    dataMovements: list[DataMovementRowOptional]


class CosmicMeasureOutput(CosmicMeasureOutputCore, total=False):
    calledClassesNotFound: list[str]
    recordTypeReadsExcludedFromCfp: list[RecordTypeReadExcludedRow]


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


def to_json_movement(
    m: RawMovement, order: int, merged_from: Optional[list[dict[str, Any]]] = None
) -> DataMovementRowOptional:
    return _shared_to_json_movement(m, order, merged_from, implementation_type="apex")


def build_output(
    class_name: str,
    movements: list[RawMovement],
    functional_process_id: str = "<Id>",
    *,
    called_classes_not_found: Optional[list[str]] = None,
    implementation_type: str = "apex",
) -> CosmicMeasureOutput:
    # Append filetype so artifacts and movements identify their source clearly
    class_name = f"{class_name}.apex"

    for m in movements:
        if m.artifact_name is None:
            m.artifact_name = class_name
    movements, record_type_reads_excluded = partition_record_type_reads(movements)
    ordered = order_movements(movements)
    data_movements: list[DataMovementRowOptional] = [
        _shared_to_json_movement(m, i + 1, merged, implementation_type="apex")
        for i, (m, merged) in enumerate(ordered)
    ]
    data_movements.append(
        {
            "name": CANONICAL_EXIT_NAME,
            "order": len(data_movements) + 1,
            "movementType": "X",
            "dataGroupRef": CANONICAL_EXIT_DATA_GROUP_REF,
            "implementationType": implementation_type,
            "isApiCall": False,
            "artifactName": class_name,
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


def to_human_summary(output: CosmicMeasureOutput) -> str:
    """Apex-specific summary: adds calledClassesNotFound and RecordType notes."""
    base = _shared_to_human_summary(output)
    if not base:
        return ""

    extra_notes: list[str] = []
    not_found = output.get("calledClassesNotFound") or []
    if not_found:
        extra_notes.append(
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
        extra_notes.append(
            "**RecordType reads (excluded from CFP):** "
            + "; ".join(parts)
            + " — not counted as functional-process data movements (metadata lookup)."
        )

    if extra_notes:
        for n in extra_notes:
            base += f"\n- {n}"
    return base


def to_table(output: CosmicMeasureOutput) -> str:
    """Apex-specific table: adds calledClassesNotFound and RecordType notes."""
    base = _shared_to_table(output)
    not_found = output.get("calledClassesNotFound") or []
    if not_found:
        base += f"\n\nCalled classes not found: {', '.join(not_found)}"
    rt_excluded = output.get("recordTypeReadsExcludedFromCfp") or []
    if rt_excluded:
        base += "\n\nRecordType reads (excluded from CFP): " + "; ".join(
            (
                f"L{r['sourceLine']}: {r['name']}"
                if r.get("sourceLine") is not None
                else r.get("name", "")
            )
            for r in rt_excluded
        )
    return base
