"""
Helpers for integrating Flow invocable Apex actions into Flow measurements.
"""

from pathlib import Path
from typing import Any, Callable, Optional

from shared.models import RawMovement
from shared.output import CANONICAL_EXIT_DATA_GROUP_REF, CANONICAL_EXIT_NAME


def parse_search_paths(csv_paths: str) -> list[Path]:
    return [Path(p.strip()) for p in csv_paths.split(",") if p.strip()]


def resolve_invocable_apex_class_file(
    action_name: str,
    search_paths: list[Path],
    find_class_file: Callable[[str, list[Path]], Optional[Path]],
) -> Optional[Path]:
    return find_class_file(action_name, search_paths)


def is_canonical_exit_row(row: dict[str, Any]) -> bool:
    return (
        row.get("movementType") == "X"
        and row.get("name") == CANONICAL_EXIT_NAME
        and row.get("dataGroupRef") == CANONICAL_EXIT_DATA_GROUP_REF
    )


def apex_rows_to_raw_movements(
    rows: list[dict[str, Any]],
    *,
    via_artifact: str,
    order_hint_start: int,
) -> list[RawMovement]:
    raw: list[RawMovement] = []
    hint = order_hint_start
    for row in rows:
        if is_canonical_exit_row(row):
            continue
        movement_type = row.get("movementType")
        data_group_ref = row.get("dataGroupRef")
        name = row.get("name")
        if not movement_type or not data_group_ref or not name:
            continue
        hint += 1
        raw.append(
            RawMovement(
                movement_type=movement_type,
                data_group_ref=data_group_ref,
                name=name,
                order_hint=hint,
                source_line=row.get("sourceLine"),
                via_artifact=via_artifact,
            )
        )
    return raw
