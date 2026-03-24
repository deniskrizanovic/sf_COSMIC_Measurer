#!/usr/bin/env python3
"""
COSMIC FlexiPage Measurer — extract data movements from Salesforce .flexipage-meta.xml.
Output: JSON for posting to COSMIC database.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

_SCRIPT_DIR = Path(__file__).resolve().parent
_COSMIC_MEASURER_DIR = _SCRIPT_DIR.parent.parent
for path_entry in [str(_SCRIPT_DIR), str(_COSMIC_MEASURER_DIR)]:
    if path_entry not in sys.path:
        sys.path.insert(0, path_entry)

from flexipage_parser import (  # noqa: E402
    build_synthetic_action_entry,
    build_synthetic_page_trigger_entry,
    extract_sidebar_component_movements,
    extract_tab_bound_component_movements,
    extract_tab_component_bindings,
    parse_flexipage,
    parse_xml,
)
from shared.output import (  # noqa: E402
    CANONICAL_EXIT_DATA_GROUP_REF,
    CANONICAL_EXIT_NAME,
    build_output,
    to_human_summary,
    to_json_string,
    to_table,
)


def _is_errors_notifications_row(row: dict) -> bool:
    return (
        row.get("movementType") == "X"
        and row.get("name") == CANONICAL_EXIT_NAME
        and row.get("dataGroupRef") == CANONICAL_EXIT_DATA_GROUP_REF
    )


def _inline_resolved_lwc_tab_movements(
    output: dict,
    resolved_lwc_measurements: list[dict],
) -> None:
    base_rows = output.get("dataMovements") or []
    merged_rows: list[dict] = [row for row in base_rows if not _is_errors_notifications_row(row)]

    for resolved in resolved_lwc_measurements:
        tab_context = resolved.get("tabContext") or {}
        tab_title = (tab_context.get("title") or tab_context.get("identifier") or "").strip()
        tab_suffix = f" | tab:{tab_title}" if tab_title else ""
        for row in resolved.get("dataMovements") or []:
            if _is_errors_notifications_row(row):
                continue
            merged_row = dict(row)
            merged_row["name"] = f"{merged_row.get('name', '')}{tab_suffix}"
            merged_rows.append(merged_row)

    merged_rows.append(
        {
            "name": CANONICAL_EXIT_NAME,
            "order": 0,
            "movementType": "X",
            "dataGroupRef": CANONICAL_EXIT_DATA_GROUP_REF,
            "implementationType": "flexipage",
            "isApiCall": False,
        }
    )
    for idx, row in enumerate(merged_rows, start=1):
        row["order"] = idx
    output["dataMovements"] = merged_rows


def _promote_primary_record_rows(output: dict, sobject_type: str) -> None:
    rows = output.get("dataMovements") or []
    if not rows:
        return

    canonical_exit = next((row for row in rows if _is_errors_notifications_row(row)), None)
    non_canonical_rows = [row for row in rows if not _is_errors_notifications_row(row)]
    if not non_canonical_rows:
        return

    open_record_name = f"Open record page ({sobject_type})"
    promoted_order = [
        ("E", open_record_name),
        ("R", f"Read page record ({sobject_type})"),
        ("X", f"Display page record ({sobject_type})"),
        ("E", f"Edit page record ({sobject_type})"),
        ("W", f"Write page record ({sobject_type})"),
    ]

    promoted: list[dict] = []
    remaining = list(non_canonical_rows)
    for movement_type, movement_name in promoted_order:
        for index, row in enumerate(remaining):
            if row.get("movementType") == movement_type and row.get("name") == movement_name:
                promoted.append(remaining.pop(index))
                break

    def pair_rows_by_prefix(
        rows: list[dict],
        read_prefix: str,
        display_prefix: str,
    ) -> tuple[list[dict], list[dict]]:
        paired_rows: list[dict] = []
        used_ids: set[int] = set()
        for idx, row in enumerate(rows):
            if idx in used_ids or row.get("movementType") != "R":
                continue
            row_name = str(row.get("name") or "")
            if not row_name.startswith(read_prefix):
                continue

            paired_rows.append(row)
            used_ids.add(idx)

            match_index: Optional[int] = None
            for candidate_idx, candidate in enumerate(rows):
                if candidate_idx in used_ids:
                    continue
                if candidate.get("movementType") != "X":
                    continue
                if candidate.get("dataGroupRef") != row.get("dataGroupRef"):
                    continue
                candidate_name = str(candidate.get("name") or "")
                if not candidate_name.startswith(display_prefix):
                    continue
                if candidate_name.removeprefix(display_prefix) != row_name.removeprefix(read_prefix):
                    continue
                match_index = candidate_idx
                break
            if match_index is not None:
                paired_rows.append(rows[match_index])
                used_ids.add(match_index)

        unpaired_rows = [row for idx, row in enumerate(rows) if idx not in used_ids]
        return paired_rows, unpaired_rows

    paired_highlights, remaining_after_highlights = pair_rows_by_prefix(
        remaining,
        "Read highlights panel fields ",
        "Display highlights panel fields ",
    )
    paired_path_rows, remaining_after_path_rows = pair_rows_by_prefix(
        remaining_after_highlights, "Read path state ", "Display path state "
    )
    paired_related_lists, remaining_after_related_lists = pair_rows_by_prefix(
        remaining_after_path_rows, "Read related list ", "Display related list "
    )
    paired_related_records, leftovers = pair_rows_by_prefix(
        remaining_after_related_lists, "Read related record ", "Display related record "
    )
    ordered_rows = (
        promoted
        + paired_highlights
        + paired_path_rows
        + paired_related_lists
        + paired_related_records
        + leftovers
    )
    if canonical_exit is not None:
        ordered_rows.append(canonical_exit)

    for idx, row in enumerate(ordered_rows, start=1):
        row["order"] = idx
    output["dataMovements"] = ordered_rows


def _normalize_name_for_dedup(name: str) -> str:
    tab_delimiter = " | tab:"
    if tab_delimiter in name:
        return name.split(tab_delimiter, 1)[0].strip()
    return name.strip()


def _deduplicate_data_movements(output: dict) -> None:
    rows = output.get("dataMovements") or []
    if not rows:
        return

    canonical_exit = next((row for row in rows if _is_errors_notifications_row(row)), None)
    non_canonical_rows = [row for row in rows if not _is_errors_notifications_row(row)]

    unique_rows: list[dict] = []
    seen_keys: set[tuple[str, str, str]] = set()
    for row in non_canonical_rows:
        key = (
            str(row.get("movementType") or ""),
            str(row.get("dataGroupRef") or ""),
            _normalize_name_for_dedup(str(row.get("name") or "")),
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        unique_rows.append(row)

    if canonical_exit is not None:
        unique_rows.append(canonical_exit)

    for idx, row in enumerate(unique_rows, start=1):
        row["order"] = idx
    output["dataMovements"] = unique_rows


def _parse_search_paths(csv_paths: str) -> list[Path]:
    return [Path(p.strip()) for p in csv_paths.split(",") if p.strip()]


def _find_lwc_bundle_dir(lwc_name: str, search_paths: list[Path]) -> Optional[Path]:
    for base in search_paths:
        if not base.exists():
            continue
        for match in base.rglob(lwc_name):
            if match.is_dir():
                js_file = match / f"{lwc_name}.js"
                html_file = match / f"{lwc_name}.html"
                if js_file.exists() and html_file.exists():
                    return match
    return None


def _resolve_lwc_candidates(
    lwc_candidates: list[dict],
    *,
    lwc_search_paths: list[Path],
    apex_search_paths: list[Path],
) -> list[dict]:
    if not lwc_candidates:
        return []

    lwc_scripts_dir = _COSMIC_MEASURER_DIR / "cosmic-lwc-measurer" / "scripts"
    if str(lwc_scripts_dir) not in sys.path:
        sys.path.insert(0, str(lwc_scripts_dir))
    from measure_lwc import measure_lwc_bundle  # type: ignore

    resolved: list[dict] = []
    for candidate in lwc_candidates:
        artifact = candidate.get("artifact") or {}
        lwc_name = artifact.get("name")
        if not lwc_name:
            continue
        bundle_dir = _find_lwc_bundle_dir(lwc_name, lwc_search_paths)
        if bundle_dir is None:
            unresolved = {
                "artifact": {"type": "LWC", "name": lwc_name},
                "traversalWarnings": [
                    f"Unable to resolve LWC bundle directory for {lwc_name}"
                ],
            }
            resolved.append(unresolved)
            continue
        result = measure_lwc_bundle(
            bundle_dir,
            lwc_name=lwc_name,
            functional_process_id=candidate.get("functionalProcessId", "<Id>"),
            apex_search_paths=apex_search_paths,
            required_movement_types=candidate.get("requiredMovementTypes"),
            source_artifact=candidate.get("sourceArtifact"),
            tab_context=candidate.get("tabContext"),
        )
        resolved.append(result)
    return resolved


def _find_flow_file(flow_name: str, search_paths: list[Path]) -> Optional[Path]:
    candidate_filenames = (
        f"{flow_name}.flow-meta.xml",
        f"{flow_name}.flow",
    )
    for base in search_paths:
        if not base.exists():
            continue
        for filename in candidate_filenames:
            direct_match = base / filename
            if direct_match.exists() and direct_match.is_file():
                return direct_match
            for match in base.rglob(filename):
                if match.is_file():
                    return match
    return None


def _resolve_flow_candidates(
    flow_candidates: list[dict],
    *,
    flow_search_paths: list[Path],
    apex_search_paths: list[Path],
) -> list[dict]:
    if not flow_candidates:
        return []

    flow_scripts_dir = _COSMIC_MEASURER_DIR / "cosmic-flow-measurer" / "scripts"
    if str(flow_scripts_dir) not in sys.path:
        sys.path.insert(0, str(flow_scripts_dir))
    from measure_flow import measure_file as measure_flow_file  # type: ignore

    resolved: list[dict] = []
    for candidate in flow_candidates:
        artifact = candidate.get("artifact") or {}
        flow_name = artifact.get("name")
        if not flow_name:
            continue
        flow_file = _find_flow_file(flow_name, flow_search_paths)
        if flow_file is None:
            resolved.append(
                {
                    "artifact": {"type": "Flow", "name": flow_name},
                    "traversalWarnings": [f"Unable to resolve Flow metadata for {flow_name}"],
                }
            )
            continue
        result = measure_flow_file(
            flow_file,
            fp_id=candidate.get("functionalProcessId", "<Id>"),
            apex_search_paths=apex_search_paths,
            include_invocable_apex=True,
        )
        result["sourceArtifact"] = candidate.get("sourceArtifact")
        result["tabContext"] = candidate.get("tabContext")
        resolved.append(result)
    return resolved


def _build_lwc_candidate_outputs(
    artifact_name: str,
    tab_bindings: list,
    fp_id: str,
) -> list[dict]:
    write_keywords = (
        "edit",
        "create",
        "new",
        "add",
        "update",
        "delete",
        "save",
        "submit",
        "compose",
        "wizard",
        "form",
    )

    def infer_required_movement_types(binding: object) -> list[str]:
        signals = " ".join(
            [
                str(getattr(binding, "tab_title", "") or ""),
                str(getattr(binding, "target_component_name", "") or ""),
                str(getattr(binding, "tab_identifier", "") or ""),
            ]
        ).lower()
        if any(keyword in signals for keyword in write_keywords):
            return ["W"]
        return []

    candidates: list[dict] = []
    for binding in tab_bindings:
        if binding.target_component_kind != "lwc" or not binding.target_component_name:
            continue
        candidates.append(
            {
                "functionalProcessId": fp_id,
                "artifact": {
                    "type": "LWC",
                    "name": binding.target_component_name,
                },
                "sourceArtifact": {
                    "type": "FlexiPage",
                    "name": artifact_name,
                },
                "tabContext": {
                    "identifier": binding.tab_identifier,
                    "title": binding.tab_title,
                },
                "requiredMovementTypes": infer_required_movement_types(binding),
                "notes": "Run dedicated lwc-measurer to extract concrete E/R/X/W movements.",
            }
        )
    return candidates


def _build_flow_candidate_outputs(
    artifact_name: str,
    tab_bindings: list,
    fp_id: str,
) -> list[dict]:
    candidates: list[dict] = []
    for binding in tab_bindings:
        if binding.target_component_name != "flowruntime:interview":
            continue
        flow_name = (binding.target_component_properties or {}).get("flowName", "").strip()
        if not flow_name:
            continue
        candidates.append(
            {
                "functionalProcessId": fp_id,
                "artifact": {
                    "type": "Flow",
                    "name": flow_name,
                },
                "sourceArtifact": {
                    "type": "FlexiPage",
                    "name": artifact_name,
                },
                "tabContext": {
                    "identifier": binding.tab_identifier,
                    "title": binding.tab_title,
                },
                "notes": "Run dedicated flow-measurer to extract concrete E/R/W/X movements.",
            }
        )
    return candidates


def _build_lwc_tbc_data_movements(lwc_candidates: list[dict]) -> list[dict]:
    key_counts: dict[tuple[str, str], int] = {}
    for candidate in lwc_candidates:
        artifact = candidate.get("artifact") or {}
        tab_context = candidate.get("tabContext") or {}
        lwc_name = str(artifact.get("name") or "").strip()
        tab_title = str(tab_context.get("title") or tab_context.get("identifier") or "").strip()
        if lwc_name:
            key = (lwc_name, tab_title)
            key_counts[key] = key_counts.get(key, 0) + 1

    placeholder_rows: list[dict] = []
    key_seen: dict[tuple[str, str], int] = {}
    for candidate in lwc_candidates:
        artifact = candidate.get("artifact") or {}
        tab_context = candidate.get("tabContext") or {}
        lwc_name = str(artifact.get("name") or "").strip()
        if not lwc_name:
            continue
        tab_title = str(tab_context.get("title") or tab_context.get("identifier") or "").strip()
        tab_suffix = f" on tab {tab_title}" if tab_title else ""
        key = (lwc_name, tab_title)
        sequence = key_seen.get(key, 0) + 1
        key_seen[key] = sequence
        instance_suffix = f" [instance {sequence}]" if key_counts.get(key, 0) > 1 else ""
        placeholder_rows.append(
            {
                "name": f"Inspect LWC {lwc_name} data movements (TBC){tab_suffix}{instance_suffix}",
                "order": 0,
                "movementType": "X",
                "dataGroupRef": "tbc",
                "implementationType": "flexipage",
                "isApiCall": False,
            }
        )
    return placeholder_rows


def _inline_resolved_flow_tab_movements(output: dict, resolved_flow_measurements: list[dict]) -> None:
    rows = output.get("dataMovements") or []
    filtered_rows: list[dict] = []
    flow_placeholder_names: set[str] = set()
    for resolved in resolved_flow_measurements:
        tab_context = resolved.get("tabContext") or {}
        tab_name = (tab_context.get("title") or tab_context.get("identifier") or "").strip()
        flow_name = ((resolved.get("artifact") or {}).get("name") or "").strip()
        if tab_name and flow_name:
            flow_placeholder_names.add(f"Display flow interview {flow_name} | tab:{tab_name}")
        elif flow_name:
            flow_placeholder_names.add(f"Display flow interview {flow_name}")

    for row in rows:
        if _is_errors_notifications_row(row):
            continue
        if row.get("movementType") == "X" and str(row.get("name") or "") in flow_placeholder_names:
            continue
        filtered_rows.append(row)

    for resolved in resolved_flow_measurements:
        tab_context = resolved.get("tabContext") or {}
        tab_title = (tab_context.get("title") or tab_context.get("identifier") or "").strip()
        tab_suffix = f" | tab:{tab_title}" if tab_title else ""
        for row in resolved.get("dataMovements") or []:
            if _is_errors_notifications_row(row):
                continue
            merged_row = dict(row)
            merged_row["name"] = f"{merged_row.get('name', '')}{tab_suffix}"
            filtered_rows.append(merged_row)

    filtered_rows.append(
        {
            "name": CANONICAL_EXIT_NAME,
            "order": 0,
            "movementType": "X",
            "dataGroupRef": CANONICAL_EXIT_DATA_GROUP_REF,
            "implementationType": "flexipage",
            "isApiCall": False,
        }
    )
    for idx, row in enumerate(filtered_rows, start=1):
        row["order"] = idx
    output["dataMovements"] = filtered_rows


def _build_action_candidate_outputs(
    artifact_name: str,
    sobject_type: str,
    actions: list[str],
    fp_id: str,
) -> list[dict]:
    candidates: list[dict] = []
    for action in actions:
        entry = build_synthetic_action_entry(action, sobject_type)
        candidate = build_output(
            "FlexiPageAction",
            f"{artifact_name}::{action}",
            [entry],
            fp_id,
            implementation_type="flexipage",
        )
        candidates.append(candidate)
    return candidates


def measure_file(
    path: Path,
    fp_id: str = "<Id>",
    *,
    synthetic_trigger_entry: bool = True,
    include_action_candidates: bool = False,
    resolve_lwc_candidates: bool = True,
    resolve_flow_candidates: bool = True,
    lwc_search_paths: Optional[list[Path]] = None,
    flow_search_paths: Optional[list[Path]] = None,
    apex_search_paths: Optional[list[Path]] = None,
    deduplicate_movements: bool = True,
) -> dict:
    source = path.read_text(encoding="utf-8", errors="replace")
    root = parse_xml(source)
    metadata, movements, actions, tab_labels = parse_flexipage(source, filename=path.name)
    tab_bindings = extract_tab_component_bindings(root)
    tab_component_movements, tab_component_warnings = extract_tab_bound_component_movements(
        root, metadata.sobject_type
    )
    sidebar_component_movements, sidebar_component_warnings = extract_sidebar_component_movements(
        root, metadata.sobject_type
    )
    if tab_component_movements:
        movements = movements + tab_component_movements
    if sidebar_component_movements:
        movements = movements + sidebar_component_movements
    if synthetic_trigger_entry:
        movements = [build_synthetic_page_trigger_entry(metadata.sobject_type)] + movements
    output = build_output(
        "FlexiPage",
        metadata.name,
        movements,
        fp_id,
        implementation_type="flexipage",
    )
    _promote_primary_record_rows(output, metadata.sobject_type)
    if actions:
        action_list = ", ".join(actions)
        output["traversalWarnings"] = [
            "Investigate configured page actions as separate functional processes: "
            f"{action_list}"
        ]
        if include_action_candidates:
            output["actionCandidateMeasurements"] = _build_action_candidate_outputs(
                metadata.name, metadata.sobject_type, actions, fp_id
            )
    if tab_labels:
        tab_list = ", ".join(tab_labels)
        warning = f"Tab-aware notes: page contains tabs = {tab_list}"
        output.setdefault("traversalWarnings", []).append(warning)
    if tab_bindings:
        readable_bindings = []
        for binding in tab_bindings:
            if binding.tab_title and binding.target_component_name:
                readable_bindings.append(
                    f"{binding.tab_title} -> {binding.target_component_kind}({binding.target_component_name})"
                )
        if readable_bindings:
            output.setdefault("traversalWarnings", []).append(
                "Tab-component bindings: " + ", ".join(readable_bindings)
            )
    for warning in tab_component_warnings:
        output.setdefault("traversalWarnings", []).append(warning)
    for warning in sidebar_component_warnings:
        output.setdefault("traversalWarnings", []).append(warning)
    lwc_candidates = _build_lwc_candidate_outputs(metadata.name, tab_bindings, fp_id)
    flow_candidates = _build_flow_candidate_outputs(metadata.name, tab_bindings, fp_id)
    if lwc_candidates:
        output["lwcCandidateMeasurements"] = lwc_candidates
        output["dataMovements"] = (output.get("dataMovements") or []) + _build_lwc_tbc_data_movements(
            lwc_candidates
        )
        lwc_names = ", ".join(candidate["artifact"]["name"] for candidate in lwc_candidates)
        output.setdefault("traversalWarnings", []).append(
            "Delegate tab-bound LWCs to lwc-measurer with additional write movement handling: "
            f"{lwc_names}"
        )
        if resolve_lwc_candidates:
            resolved_lwc_measurements = _resolve_lwc_candidates(
                lwc_candidates,
                lwc_search_paths=lwc_search_paths or [],
                apex_search_paths=apex_search_paths or [],
            )
            output["resolvedLwcMeasurements"] = resolved_lwc_measurements
            _inline_resolved_lwc_tab_movements(output, resolved_lwc_measurements)
    if flow_candidates:
        output["flowCandidateMeasurements"] = flow_candidates
        flow_names = ", ".join(candidate["artifact"]["name"] for candidate in flow_candidates)
        output.setdefault("traversalWarnings", []).append(
            "Delegate tab-bound Flows to flow-measurer for concrete E/R/W/X movements: "
            f"{flow_names}"
        )
        if resolve_flow_candidates:
            resolved_flow_measurements = _resolve_flow_candidates(
                flow_candidates,
                flow_search_paths=flow_search_paths or [],
                apex_search_paths=apex_search_paths or [],
            )
            output["resolvedFlowMeasurements"] = resolved_flow_measurements
            _inline_resolved_flow_tab_movements(output, resolved_flow_measurements)
            unresolved_flow_names = sorted(
                {
                    (item.get("artifact") or {}).get("name", "")
                    for item in resolved_flow_measurements
                    if item.get("traversalWarnings")
                }
            )
            if unresolved_flow_names:
                output.setdefault("traversalWarnings", []).append(
                    "Unable to resolve tab-bound Flow metadata: " + ", ".join(unresolved_flow_names)
                )
        else:
            output.setdefault("traversalWarnings", []).append(
                "Flow candidate resolution disabled (--no-resolve-flow-candidates)"
            )
    if deduplicate_movements:
        _deduplicate_data_movements(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract COSMIC data movements from Salesforce .flexipage-meta.xml files"
    )
    parser.add_argument("files", nargs="+", type=Path, help=".flexipage-meta.xml file(s) to measure")
    parser.add_argument("-o", "--output", type=Path, help="Write JSON to file (default: stdout)")
    parser.add_argument("--fp-id", default="<Id>", help="Functional process ID for output (default: <Id>)")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of table (default: table when printing to stdout)",
    )
    parser.add_argument(
        "--no-synthetic-trigger-e",
        action="store_true",
        help="Disable synthetic trigger Entry (E) for page-open functional process",
    )
    parser.add_argument(
        "--include-action-candidates",
        action="store_true",
        help="Include synthetic per-action candidate measurements in JSON output",
    )
    parser.add_argument(
        "--no-resolve-lwc-candidates",
        action="store_true",
        help="Disable resolving lwcCandidateMeasurements via standalone cosmic-lwc-measurer",
    )
    parser.add_argument(
        "--no-resolve-flow-candidates",
        action="store_true",
        help="Disable resolving flowCandidateMeasurements via standalone cosmic-flow-measurer",
    )
    parser.add_argument(
        "--lwc-search-paths",
        metavar="DIR",
        default="samples,force-app/main/default/lwc",
        help="Comma-separated dirs to resolve LWC bundle directories",
    )
    parser.add_argument(
        "--apex-search-paths",
        metavar="DIR",
        default="samples,force-app/main/default/classes,src/classes",
        help="Comma-separated dirs for LWC imported Apex class resolution",
    )
    parser.add_argument(
        "--flow-search-paths",
        metavar="DIR",
        default="samples,force-app/main/default/flows",
        help="Comma-separated dirs to resolve Flow metadata files",
    )
    parser.add_argument(
        "--no-dedupe-movements",
        action="store_true",
        help="Disable deduplication of repeated movements",
    )
    args = parser.parse_args()
    lwc_search_paths = _parse_search_paths(args.lwc_search_paths)
    flow_search_paths = _parse_search_paths(args.flow_search_paths)
    apex_search_paths = _parse_search_paths(args.apex_search_paths)

    results: list[dict] = []
    for candidate in args.files:
        if not candidate.exists():
            print(f"Error: {candidate} not found", file=sys.stderr)
            return 1
        if not candidate.name.endswith(".flexipage-meta.xml"):
            print(
                f"Warning: {candidate} may not be a FlexiPage (expected .flexipage-meta.xml)",
                file=sys.stderr,
            )
        try:
            result = measure_file(
                candidate,
                args.fp_id,
                synthetic_trigger_entry=not args.no_synthetic_trigger_e,
                include_action_candidates=args.include_action_candidates,
                resolve_lwc_candidates=not args.no_resolve_lwc_candidates,
                resolve_flow_candidates=not args.no_resolve_flow_candidates,
                lwc_search_paths=lwc_search_paths,
                flow_search_paths=flow_search_paths,
                apex_search_paths=apex_search_paths,
                deduplicate_movements=not args.no_dedupe_movements,
            )
        except ValueError as exc:
            print(f"Error: {candidate}: {exc}", file=sys.stderr)
            return 1
        results.append(result)

    if args.output:
        json_payload = to_json_string(results[0]) if len(results) == 1 else json.dumps(results, indent=2)
        args.output.write_text(json_payload, encoding="utf-8")
        for out in results:
            print(to_human_summary(out))
    elif args.json:
        print(to_json_string(results[0]) if len(results) == 1 else json.dumps(results, indent=2))
    else:
        for out in results:
            print(to_table(out))

    return 0


if __name__ == "__main__":
    sys.exit(main())
