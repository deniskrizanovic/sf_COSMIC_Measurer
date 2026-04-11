#!/usr/bin/env python3
"""COSMIC LWC measurer with standalone API and CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Literal, Optional, TypedDict

_SCRIPT_DIR = Path(__file__).resolve().parent
_COSMIC_MEASURER_DIR = _SCRIPT_DIR.parent.parent
for path_entry in [str(_SCRIPT_DIR), str(_COSMIC_MEASURER_DIR)]:
    if path_entry not in sys.path:
        sys.path.insert(0, path_entry)

from lwc_parser import (  # noqa: E402
    _detect_apex_import_var_map,
    detect_apex_import_vars,
    detect_apex_imports,
    extract_handler_apex_calls,
    infer_bundle_name,
    parse_lwc_native_movements,
)
from shared.models import LwcRawMovement, RawMovement  # noqa: E402
from shared.output import (  # noqa: E402
    CANONICAL_EXIT_DATA_GROUP_REF,
    CANONICAL_EXIT_NAME,
    build_output,
    to_human_summary,
    to_json_string,
    to_table,
)

MovementType = Literal["E", "R", "W", "X"]


class ArtifactRef(TypedDict):
    type: str
    name: str


class TabContext(TypedDict, total=False):
    identifier: str
    title: str


class _LwcMeasureRequestRequired(TypedDict):
    lwc_bundle_dir: str


class LwcMeasureRequest(_LwcMeasureRequestRequired, total=False):
    lwc_name: str
    functional_process_id: str
    apex_search_paths: list[str]
    required_movement_types: list[MovementType]
    source_artifact: ArtifactRef
    tab_context: TabContext


class DataMovementRow(TypedDict, total=False):
    name: str
    order: int
    movementType: MovementType
    dataGroupRef: str
    implementationType: str
    isApiCall: bool
    viaArtifact: str
    mergedFrom: list[dict[str, Any]]


class LwcMeasureResult(TypedDict, total=False):
    functionalProcessId: str
    artifact: ArtifactRef
    dataMovements: list[DataMovementRow]
    traversalWarnings: list[str]
    sourceArtifact: ArtifactRef
    tabContext: TabContext
    requiredMovementTypes: list[MovementType]
    missingRequiredMovementTypes: list[MovementType]
    satisfiesRequiredMovementTypes: bool


def _load_apex_measurer_helpers() -> tuple[Any, Any]:
    apex_scripts_dir = _COSMIC_MEASURER_DIR / "cosmic-apex-measurer" / "scripts"
    if str(apex_scripts_dir) not in sys.path:
        sys.path.insert(0, str(apex_scripts_dir))
    from measure_apex import find_class_file, measure_file as measure_apex_file  # type: ignore

    return find_class_file, measure_apex_file


def _is_canonical_exit_row(row: dict[str, Any]) -> bool:
    return (
        row.get("movementType") == "X"
        and row.get("name") == CANONICAL_EXIT_NAME
        and row.get("dataGroupRef") == CANONICAL_EXIT_DATA_GROUP_REF
    )


def _build_class_to_block_map(
    movements: list[LwcRawMovement],
    js_source: str,
) -> dict[str, str]:
    apex_var_map = _detect_apex_import_var_map(js_source)
    if not apex_var_map:
        return {}
    handler_apex_map = extract_handler_apex_calls(js_source, apex_var_map)
    class_to_block: dict[str, str] = {}
    for m in movements:
        if m.movement_type != "E" or not m.block_label or not m.handler_names:
            continue
        for handler in m.handler_names:
            for cls in handler_apex_map.get(handler, []):
                if cls not in class_to_block:
                    class_to_block[cls] = m.block_label
    return class_to_block


def _assign_tiers(movements: list[LwcRawMovement], js_source: str) -> None:
    class_to_block = _build_class_to_block_map(movements, js_source)

    has_interaction_linked_r = False
    display_x_movements: list[LwcRawMovement] = []

    for m in movements:
        if m.tier is not None:
            continue
        if m.movement_type == "E":
            m.tier = 1
            m.tier_label = "Init"
        elif m.movement_type == "R":
            via = m.via_artifact
            if via and via in class_to_block:
                m.tier = 2
                m.tier_label = "Interactions"
                m.triggering_block = class_to_block[via]
                has_interaction_linked_r = True
            else:
                m.tier = 1
                m.tier_label = "Init"
        elif m.movement_type == "W":
            m.tier = 3
            m.tier_label = "Terminal"
        elif m.movement_type == "X":
            if m.name == CANONICAL_EXIT_NAME:
                m.tier = 3
                m.tier_label = "Terminal"
            else:
                display_x_movements.append(m)

    tier = 2 if has_interaction_linked_r else 1
    label = "Interactions" if has_interaction_linked_r else "Init"
    for m in display_x_movements:
        m.tier = tier
        m.tier_label = label


def _apex_rows_to_raw_movements(
    rows: list[dict[str, Any]],
    *,
    via_artifact: str,
    order_hint_start: int,
) -> list[LwcRawMovement]:
    raw: list[LwcRawMovement] = []
    hint = order_hint_start
    for row in rows:
        # Imported Apex exits are internal handoffs to LWC code, not user-visible exits.
        if row.get("movementType") == "X":
            continue
        if _is_canonical_exit_row(row):
            continue
        movement_type = row.get("movementType")
        data_group_ref = row.get("dataGroupRef")
        name = row.get("name")
        if not movement_type or not data_group_ref or not name:
            continue
        hint += 1
        raw.append(
            LwcRawMovement(
                movement_type=movement_type,
                data_group_ref=data_group_ref,
                name=name,
                order_hint=hint,
                source_line=row.get("sourceLine"),
                via_artifact=via_artifact,
                artifact_name=row.get("artifactName"),
            )
        )
    return raw


def validate_required_movement_types(
    data_movements: list[DataMovementRow],
    required: list[MovementType],
) -> tuple[bool, list[MovementType]]:
    present = {str(row.get("movementType", "")) for row in data_movements}
    missing = [movement_type for movement_type in required if movement_type not in present]
    return (len(missing) == 0, missing)


def measure_lwc(request: LwcMeasureRequest) -> LwcMeasureResult:
    bundle_dir = Path(request["lwc_bundle_dir"])
    return measure_lwc_bundle(
        bundle_dir,
        lwc_name=request.get("lwc_name"),
        functional_process_id=request.get("functional_process_id"),
        apex_search_paths=request.get("apex_search_paths"),
        required_movement_types=request.get("required_movement_types"),
        source_artifact=request.get("source_artifact"),
        tab_context=request.get("tab_context"),
    )


def measure_lwc_bundle(
    lwc_bundle_dir: str | Path,
    *,
    lwc_name: str | None = None,
    functional_process_id: str | None = None,
    apex_search_paths: list[str | Path] | None = None,
    required_movement_types: list[MovementType] | None = None,
    source_artifact: ArtifactRef | None = None,
    tab_context: TabContext | None = None,
) -> LwcMeasureResult:
    bundle_dir = Path(lwc_bundle_dir)
    if not bundle_dir.exists():
        raise ValueError(f"{bundle_dir} not found")
    if not bundle_dir.is_dir():
        raise ValueError(f"{bundle_dir} is not a directory")

    bundle_name = lwc_name or infer_bundle_name(bundle_dir)
    js_path = bundle_dir / f"{bundle_name}.js"
    html_path = bundle_dir / f"{bundle_name}.html"
    if not js_path.exists() or not html_path.exists():
        raise ValueError(f"Missing {bundle_name}.js or {bundle_name}.html in {bundle_dir}")

    js_source = js_path.read_text(encoding="utf-8", errors="replace")
    html_source = html_path.read_text(encoding="utf-8", errors="replace")

    warnings: list[str] = []
    inferred_user_output_group: str | None = None
    imports = detect_apex_imports(js_source)
    apex_import_vars = detect_apex_import_vars(js_source)
    movements = parse_lwc_native_movements(js_source, html_source, apex_import_names=apex_import_vars)
    search_paths = [Path(path) for path in (apex_search_paths or [])]
    order_hint_start = 10000
    if imports:
        find_class_file, measure_apex_file = _load_apex_measurer_helpers()
        seen_classes: set[str] = set()
        for class_name, _method_name in imports:
            if class_name in seen_classes:
                continue
            seen_classes.add(class_name)
            class_file = find_class_file(class_name, search_paths)
            if class_file is None:
                warnings.append(f"Unable to resolve Apex class for LWC import: {class_name}")
                continue
            apex_output = measure_apex_file(
                class_file,
                functional_process_id or "<Id>",
                search_paths=search_paths,
                traverse=True,
            )
            # Propagate traversal warnings from Apex measurement
            for missing in apex_output.get("calledClassesNotFound", []):
                if missing not in warnings:
                    warnings.append(f"Unable to resolve Apex class: {missing} (called via {class_name})")

            apex_rows = apex_output.get("dataMovements", [])
            for row in apex_rows:
                if _is_canonical_exit_row(row):
                    continue
                if row.get("movementType") != "X":
                    continue
                candidate_group = row.get("dataGroupRef")
                if isinstance(candidate_group, str) and candidate_group:
                    inferred_user_output_group = candidate_group
                    break
            movements.extend(
                _apex_rows_to_raw_movements(
                    apex_rows,
                    via_artifact=class_name,
                    order_hint_start=order_hint_start,
                )
            )
            order_hint_start += 10000

    _assign_tiers(movements, js_source)

    output = build_output(
        "LWC",
        bundle_name,
        movements,
        functional_process_id or "<Id>",
        implementation_type="lwc",
    )
    for row in output["dataMovements"]:
        if row.get("viaArtifact"):
            row["implementationType"] = "apex"
        if (
            inferred_user_output_group
            and row.get("movementType") == "X"
            and row.get("implementationType") == "lwc"
            and row.get("name") == "Display LWC output to user"
        ):
            row["dataGroupRef"] = inferred_user_output_group

    if warnings:
        output["traversalWarnings"] = warnings
    if source_artifact:
        output["sourceArtifact"] = source_artifact
    if tab_context:
        output["tabContext"] = tab_context

    if required_movement_types is not None:
        satisfies, missing = validate_required_movement_types(
            output["dataMovements"],
            required_movement_types,
        )
        output["requiredMovementTypes"] = required_movement_types
        output["missingRequiredMovementTypes"] = missing
        output["satisfiesRequiredMovementTypes"] = satisfies

    return output


def resolve_lwc_candidate(
    candidate: dict,
    *,
    apex_search_paths: list[str],
) -> LwcMeasureResult:
    artifact = candidate.get("artifact") or {}
    request: LwcMeasureRequest = {
        "lwc_name": artifact.get("name"),
        "lwc_bundle_dir": artifact.get("name", ""),
        "functional_process_id": candidate.get("functionalProcessId", "<Id>"),
        "apex_search_paths": apex_search_paths,
        "required_movement_types": candidate.get("requiredMovementTypes") or [],
    }
    if candidate.get("sourceArtifact"):
        request["source_artifact"] = candidate["sourceArtifact"]
    if candidate.get("tabContext"):
        request["tab_context"] = candidate["tabContext"]
    return measure_lwc(request)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Extract COSMIC data movements from LWC bundles")
    parser.add_argument("--bundle-dir", type=Path, required=True, help="Path to LWC bundle directory")
    parser.add_argument("--lwc-name", help="Override component name (default: bundle dir name)")
    parser.add_argument("--fp-id", default="<Id>", help="Functional process ID for output")
    parser.add_argument(
        "--apex-search-paths",
        default="samples,force-app/main/default/classes,src/classes",
        help="Comma-separated dirs for resolving imported Apex classes",
    )
    parser.add_argument(
        "--required-type",
        action="append",
        choices=["E", "R", "W", "X"],
        help="Required movement type (repeatable)",
    )
    parser.add_argument("-o", "--output", type=Path, help="Write JSON to file (default: stdout)")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args(argv)

    try:
        result = measure_lwc_bundle(
            args.bundle_dir,
            lwc_name=args.lwc_name,
            functional_process_id=args.fp_id,
            apex_search_paths=[item.strip() for item in args.apex_search_paths.split(",") if item.strip()],
            required_movement_types=args.required_type,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        args.output.write_text(to_json_string(result), encoding="utf-8")
        print(to_human_summary(result))
    elif args.json:
        print(to_json_string(result))
    else:
        print(to_table(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
