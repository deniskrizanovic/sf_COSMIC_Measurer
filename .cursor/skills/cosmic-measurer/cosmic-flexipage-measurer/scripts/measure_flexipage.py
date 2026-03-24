#!/usr/bin/env python3
"""
COSMIC FlexiPage Measurer — extract data movements from Salesforce .flexipage-meta.xml.
Output: JSON for posting to COSMIC database.
"""

import argparse
import json
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_COSMIC_MEASURER_DIR = _SCRIPT_DIR.parent.parent
for path_entry in [str(_SCRIPT_DIR), str(_COSMIC_MEASURER_DIR)]:
    if path_entry not in sys.path:
        sys.path.insert(0, path_entry)

from flexipage_parser import (  # noqa: E402
    build_synthetic_action_entry,
    build_synthetic_page_trigger_entry,
    parse_flexipage,
)
from shared.output import build_output, to_human_summary, to_json_string, to_table  # noqa: E402


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
) -> dict:
    source = path.read_text(encoding="utf-8", errors="replace")
    metadata, movements, actions, tab_labels = parse_flexipage(source, filename=path.name)
    if synthetic_trigger_entry:
        movements = [build_synthetic_page_trigger_entry(metadata.sobject_type)] + movements
    output = build_output(
        "FlexiPage",
        metadata.name,
        movements,
        fp_id,
        implementation_type="flexipage",
    )
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
    args = parser.parse_args()

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
