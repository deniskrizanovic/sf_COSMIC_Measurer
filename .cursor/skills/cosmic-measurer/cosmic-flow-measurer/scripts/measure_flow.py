#!/usr/bin/env python3
"""
COSMIC Flow Measurer — extract data movements from Salesforce .flow-meta.xml files.
Output: JSON for posting to COSMIC database.
"""

import argparse
import json
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_COSMIC_MEASURER_DIR = _SCRIPT_DIR.parent.parent
for p in [str(_SCRIPT_DIR), str(_COSMIC_MEASURER_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from flow_parser import parse_flow  # noqa: E402
from shared.output import (  # noqa: E402
    CosmicMeasureOutput,
    build_output,
    to_human_summary,
    to_json_string,
    to_table,
)


def measure_file(path: Path, fp_id: str = "<Id>") -> CosmicMeasureOutput:
    """Measure a single Flow file; return output dict."""
    source = path.read_text(encoding="utf-8", errors="replace")
    metadata, movements = parse_flow(source, filename=path.name)
    return build_output(
        "Flow",
        metadata.name,
        movements,
        fp_id,
        implementation_type="flow",
    )


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
    args = parser.parse_args()

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
            out = measure_file(f, args.fp_id)
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
