#!/usr/bin/env python3
"""
COSMIC Flow Measurer — extract data movements from Salesforce .flow-meta.xml files.
Output: JSON for posting to COSMIC database.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

_SCRIPT_DIR = Path(__file__).resolve().parent
_COSMIC_MEASURER_DIR = _SCRIPT_DIR.parent.parent
for p in [str(_SCRIPT_DIR), str(_COSMIC_MEASURER_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from flow_apex_integration import (  # noqa: E402
    apex_rows_to_raw_movements,
    parse_search_paths,
    resolve_invocable_apex_class_file,
)
from flow_parser import parse_flow_with_invocables  # noqa: E402
from shared.output import (  # noqa: E402
    CosmicMeasureOutput,
    build_output,
    to_human_summary,
    to_json_string,
    to_table,
)


def mark_invocable_apex_rows(rows: list[dict[str, Any]]) -> None:
    """Set implementationType to apex for rows originating from invocable Apex."""
    for row in rows:
        if row.get("viaArtifact"):
            row["implementationType"] = "apex"


def filter_framework_class_names(class_names: list[str]) -> list[str]:
    """Keep likely custom Apex classes; drop framework/system pseudo-classes."""
    framework = {
        "Database",
        "System",
        "String",
        "Integer",
        "Boolean",
        "Long",
        "Double",
        "Decimal",
        "Id",
        "List",
        "Set",
        "Map",
        "Object",
        "SObject",
    }
    return [name for name in class_names if name not in framework]


def _load_apex_measurer_helpers() -> tuple[Any, Any]:
    """
    Import Apex measurer functions lazily to avoid hard coupling at module import.
    """
    apex_scripts_dir = _COSMIC_MEASURER_DIR / "cosmic-apex-measurer" / "scripts"
    if str(apex_scripts_dir) not in sys.path:
        sys.path.insert(0, str(apex_scripts_dir))
    from measure_apex import find_class_file, measure_file as measure_apex_file  # type: ignore

    return find_class_file, measure_apex_file


def measure_file(
    path: Path,
    fp_id: str = "<Id>",
    *,
    apex_search_paths: Optional[list[Path]] = None,
    include_invocable_apex: bool = True,
) -> CosmicMeasureOutput:
    """Measure a single Flow file; return output dict."""
    source = path.read_text(encoding="utf-8", errors="replace")
    metadata, flow_movements, invocable_apex_calls = parse_flow_with_invocables(
        source, filename=path.name
    )
    movements = list(flow_movements)
    missing_apex_classes: list[str] = []
    traversal_warnings: list[str] = []

    if include_invocable_apex and invocable_apex_calls:
        find_class_file, measure_apex_file = _load_apex_measurer_helpers()
        search_paths = apex_search_paths or []
        order_hint_start = 10000
        for call in invocable_apex_calls:
            cls_path = resolve_invocable_apex_class_file(
                call.action_name, search_paths, find_class_file
            )
            if cls_path is None:
                missing_apex_classes.append(call.action_name)
                continue
            apex_output = measure_apex_file(
                cls_path,
                fp_id,
                search_paths=search_paths,
                traverse=True,
            )
            called_not_found = filter_framework_class_names(
                apex_output.get("calledClassesNotFound") or []
            )
            if called_not_found:
                traversal_warnings.append(
                    "WARNING: Apex traversal failed for "
                    f"{call.action_name} ({call.element_name}) -> "
                    + ", ".join(sorted(set(called_not_found)))
                )
            movements.extend(
                apex_rows_to_raw_movements(
                    apex_output["dataMovements"],
                    via_artifact=f"{call.action_name} ({call.element_name})",
                    order_hint_start=order_hint_start,
                )
            )
            order_hint_start += 10000

    output = build_output(
        "Flow",
        metadata.name,
        movements,
        fp_id,
        implementation_type="flow",
    )
    mark_invocable_apex_rows(output["dataMovements"])
    if missing_apex_classes:
        output["invocableApexClassesNotFound"] = sorted(set(missing_apex_classes))
    if traversal_warnings:
        output["traversalWarnings"] = sorted(set(traversal_warnings))
    return output


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract COSMIC data movements from Salesforce .flow-meta.xml files"
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help=".flow-meta.xml file(s) to measure",
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
        "--json",
        action="store_true",
        help="Output JSON instead of table (default: table when printing to stdout)",
    )
    parser.add_argument(
        "--apex-search-paths",
        metavar="DIR",
        default="samples,force-app/main/default/classes,src/classes",
        help=(
            "Comma-separated dirs to resolve Flow invocable Apex classes "
            "(default: samples,force-app/main/default/classes,src/classes)"
        ),
    )
    parser.add_argument(
        "--no-invocable-apex",
        action="store_true",
        help="Disable measuring Flow invocable Apex action calls",
    )
    args = parser.parse_args()
    apex_search_paths = parse_search_paths(args.apex_search_paths)

    results: list[CosmicMeasureOutput] = []
    for f in args.files:
        if not f.exists():
            print(f"Error: {f} not found", file=sys.stderr)
            return 1
        if not f.name.endswith(".flow-meta.xml"):
            print(
                f"Warning: {f} may not be a Flow (expected .flow-meta.xml)",
                file=sys.stderr,
            )
        try:
            out = measure_file(
                f,
                args.fp_id,
                apex_search_paths=apex_search_paths,
                include_invocable_apex=not args.no_invocable_apex,
            )
        except ValueError as e:
            print(f"Error: {f}: {e}", file=sys.stderr)
            return 1
        results.append(out)

    if args.output:
        json_str = (
            to_json_string(results[0])
            if len(results) == 1
            else json.dumps(results, indent=2)
        )
        args.output.write_text(json_str, encoding="utf-8")
        for out in results:
            print(to_human_summary(out))
    elif args.json:
        json_str = (
            to_json_string(results[0])
            if len(results) == 1
            else json.dumps(results, indent=2)
        )
        print(json_str)
    else:
        for out in results:
            print(to_table(out))

    return 0


if __name__ == "__main__":
    sys.exit(main())
