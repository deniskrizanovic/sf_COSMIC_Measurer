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

from parser import RawMovement, get_entry_points, parse, find_static_calls
from movements import (
    CosmicMeasureOutput,
    build_output,
    to_human_summary,
    to_json_string,
    to_table,
)

# Project root: scripts -> cosmic-apex-measurer -> cosmic-measurer -> skills -> .cursor -> project
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent.parent


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
    """Parse callees, merge R/W movements, return (merged_movements, called_not_found)."""
    called_not_found: set[str] = set()
    callee_classes = find_static_calls(source)

    for cls in callee_classes:
        if cls == current_class:
            continue
        if cls in visited:
            continue

        cls_path = find_class_file(cls, search_paths)
        if cls_path is None:
            called_not_found.add(cls)
            continue

        visited.add(cls)
        try:
            callee_source = cls_path.read_text(encoding="utf-8", errors="replace")
            _, callee_movements = parse(callee_source)
            for m in callee_movements:
                if m.movement_type in ("R", "W"):
                    movements.append(dataclasses.replace(m, via_class=cls))
        finally:
            visited.discard(cls)

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
    class_name, movements = parse(source, entry_param_filter=entry_param_filter)

    called_classes_not_found: list[str] = []
    if traverse and search_paths:
        # Resolve search_paths relative to project root if needed
        resolved = []
        for p in search_paths:
            if not p.is_absolute():
                resolved.append(_PROJECT_ROOT / p)
            else:
                resolved.append(p)
        movements, called_not_found = _traverse_callees(
            source, list(movements), resolved, set(), class_name
        )
        called_classes_not_found = sorted(called_not_found)

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
