#!/usr/bin/env python3
"""
COSMIC Apex Measurer — extract data movements from Apex .cls files.
Output: JSON for posting to COSMIC database.
Traverses into called custom classes when .cls file is found in search paths.
"""

import argparse
import dataclasses
import json
import sys
from pathlib import Path
from typing import Optional

# Allow running as script: python measure_apex.py ...
_SCRIPT_DIR = Path(__file__).resolve().parent
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from parser import (
    RawMovement,
    _parse_record_type_string_constants,
    find_enqueue_job_calls,
    find_execute_batch_calls,
    find_external_constant_calls,
    find_static_calls,
    find_system_schedule_calls,
    get_entry_points,
    parse,
)
from movements import (
    CosmicMeasureOutput,
    build_output,
    to_human_summary,
    to_json_string,
    to_table,
)


def _find_source_repo_root() -> Optional[Path]:
    for candidate in _SCRIPT_DIR.parents:
        if not (candidate / "COUNTING_RULES.md").exists():
            continue
        if (candidate / ".cursor" / "skills" / "cosmic-measurer").exists():
            return candidate
    return None


_SOURCE_REPO_ROOT = _find_source_repo_root()


def _resolve_search_path(path_entry: Path) -> Path:
    if path_entry.is_absolute():
        return path_entry

    cwd_candidate = (Path.cwd() / path_entry).resolve()
    if cwd_candidate.exists():
        return cwd_candidate

    if _SOURCE_REPO_ROOT is not None:
        repo_candidate = (_SOURCE_REPO_ROOT / path_entry).resolve()
        if repo_candidate.exists():
            return repo_candidate

    return cwd_candidate


def find_class_file(class_name: str, search_paths: list[Path]) -> Optional[Path]:
    """Glob for ClassName.cls in search_paths. Return path if found, else None."""
    for base in search_paths:
        if not base.exists():
            continue
        matches = list(base.rglob(f"{class_name}.cls"))
        if matches:
            return matches[0]
    return None


def _traverse_callees(
    source: str,
    movements: list[RawMovement],
    search_paths: list[Path],
    visited: set[str],
    current_class: str,
) -> tuple[list[RawMovement], set[str]]:
    """Recursively parse transitive callees and merge only R/W movements."""
    called_not_found: set[str] = set()
    processed: set[str] = set()
    stack = [current_class]
    class_sources: dict[str, str] = {current_class: source}
    class_async: dict[str, bool] = {current_class: False}

    while stack:
        cls_name = stack.pop()
        if cls_name in processed:
            continue
        processed.add(cls_name)

        cls_source = class_sources[cls_name]
        parent_is_async = class_async.get(cls_name, False)

        edge_targets: dict[str, bool] = {}
        for target in sorted(find_static_calls(cls_source)):
            edge_targets[target] = edge_targets.get(target, False) or parent_is_async
        for target in sorted(find_execute_batch_calls(cls_source)):
            edge_targets[target] = True
        for target in sorted(find_enqueue_job_calls(cls_source)):
            edge_targets[target] = True
        for target in sorted(find_system_schedule_calls(cls_source)):
            edge_targets[target] = True

        for target, edge_is_async in edge_targets.items():
            if target == cls_name:
                continue
            if target in visited:
                continue
            if target in processed:
                continue

            cls_path = find_class_file(target, search_paths)
            if cls_path is None:
                called_not_found.add(target)
                continue

            visited.add(target)
            try:
                callee_source = cls_path.read_text(encoding="utf-8", errors="replace")
                _, callee_movements = parse(callee_source)
                for movement in callee_movements:
                    if movement.movement_type not in ("R", "W"):
                        continue
                    movements.append(
                        dataclasses.replace(
                            movement,
                            via_artifact=target,
                            is_async=edge_is_async,
                        )
                    )

                class_sources[target] = callee_source
                class_async[target] = edge_is_async
                stack.append(target)
            finally:
                visited.discard(target)

    return movements, called_not_found


def measure_file(
    path: Path,
    fp_id: str = "<Id>",
    *,
    entry_param_filter: Optional[str] = None,
    search_paths: Optional[list[Path]] = None,
    traverse: bool = True,
) -> CosmicMeasureOutput:
    """Measure a single Apex file; return output dict."""
    source = path.read_text(encoding="utf-8", errors="replace")

    resolved_paths = []
    if search_paths:
        for path_entry in search_paths:
            resolved_paths.append(_resolve_search_path(path_entry))

    # First pass: identify external constant references
    class_name, movements = parse(source, entry_param_filter=entry_param_filter)

    external_constants: dict[str, str] = {}
    missing_classes: set[str] = set()

    if traverse and resolved_paths:
        provider_classes = find_external_constant_calls(source)
        for provider in provider_classes:
            provider_path = find_class_file(provider, resolved_paths)
            if provider_path:
                provider_source = provider_path.read_text(encoding="utf-8", errors="replace")
                constants = _parse_record_type_string_constants(provider_source)
                for cname, cval in constants.items():
                    external_constants[f"{provider}.{cname}"] = cval
            else:
                missing_classes.add(provider)

        # Second pass: re-run with resolved external constants
        if external_constants:
            class_name, movements = parse(
                source,
                entry_param_filter=entry_param_filter,
                external_constants=external_constants
            )

    called_classes_not_found: list[str] = list(missing_classes)
    if traverse and resolved_paths:
        movements, called_not_found = _traverse_callees(
            source, list(movements), resolved_paths, set(), class_name
        )
        called_classes_not_found.extend(list(called_not_found))
        called_classes_not_found = sorted(list(set(called_classes_not_found)))

    return build_output(
        class_name,
        movements,
        fp_id,
        called_classes_not_found=called_classes_not_found if traverse else None,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract COSMIC data movements from Apex .cls files"
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="Apex .cls file(s) to measure",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Write JSON to file (default: stdout)",
    )
    parser.add_argument(
        "--fp-id",
        default="<Id>",
        help="Functional process ID for output (default: <Id>)",
    )
    parser.add_argument(
        "--list-entry-points",
        action="store_true",
        help="List entry point params (for multi-process detection); output JSON and exit",
    )
    parser.add_argument(
        "--entry-point",
        metavar="PARAM",
        help="Measure only the functional process for this entry param (e.g. facilityIds, surveyIds)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of table (default: table when printing to stdout)",
    )
    parser.add_argument(
        "--search-paths",
        metavar="DIR",
        default="samples,force-app/main/default/classes,src/classes",
        help="Comma-separated dirs to search for called classes (default: samples,force-app/main/default/classes,src/classes)",
    )
    parser.add_argument(
        "--no-traverse",
        action="store_true",
        help="Disable traversal into called classes",
    )
    args = parser.parse_args()

    search_paths = [Path(p.strip()) for p in args.search_paths.split(",") if p.strip()]

    if args.list_entry_points:
        if len(args.files) != 1:
            print("Error: --list-entry-points requires exactly one file", file=sys.stderr)
            return 1
        f = args.files[0]
        if not f.exists():
            print(f"Error: {f} not found", file=sys.stderr)
            return 1
        source = f.read_text(encoding="utf-8", errors="replace")
        entry_points = get_entry_points(source)
        print(json.dumps({"entryPoints": entry_points}, indent=2))
        return 0

    if args.entry_point and args.files:
        f = args.files[0]
        if f.exists():
            source = f.read_text(encoding="utf-8", errors="replace")
            entry_points = get_entry_points(source)
            valid = [ep["param"] for ep in entry_points]
            if valid and args.entry_point.strip().lower() not in [p.lower() for p in valid]:
                print(
                    f"Error: --entry-point '{args.entry_point}' not found. Valid: {valid}",
                    file=sys.stderr,
                )
                return 1
        # If multiple files, only validate first; measurement will use filter per-file

    results: list[CosmicMeasureOutput] = []
    for f in args.files:
        if not f.exists():
            print(f"Error: {f} not found", file=sys.stderr)
            return 1
        if not f.suffix == ".cls":
            print(f"Warning: {f} may not be Apex (expected .cls)", file=sys.stderr)
        out = measure_file(
            f,
            args.fp_id,
            entry_param_filter=args.entry_point,
            search_paths=search_paths,
            traverse=not args.no_traverse,
        )
        results.append(out)

    if args.output:
        json_str = to_json_string(results[0]) if len(results) == 1 else json.dumps(results, indent=2)
        args.output.write_text(json_str, encoding="utf-8")
        for out in results:
            print(to_human_summary(out))
    elif args.json:
        json_str = to_json_string(results[0]) if len(results) == 1 else json.dumps(results, indent=2)
        print(json_str)
    else:
        for out in results:
            print(to_table(out))

    return 0


if __name__ == "__main__":
    sys.exit(main())
