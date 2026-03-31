"""Static parsing helpers for LWC COSMIC measurement."""

from __future__ import annotations

import re
from pathlib import Path

from shared.models import RawMovement

_APEX_IMPORT_RE = re.compile(
    r"@salesforce/apex/(?P<class_name>[A-Za-z_][A-Za-z0-9_]*)\.(?P<method_name>[A-Za-z_][A-Za-z0-9_]*)"
)
_TEMPLATE_EVENT_RE = re.compile(r"\son[a-z]+\s*=")
_TEMPLATE_BINDING_RE = re.compile(r"\{[A-Za-z_][A-Za-z0-9_.]*\}")
_LDS_READ_RE = re.compile(r"\b(getRecord|getListUi|getRecordUi|getObjectInfo)\s*\(")
_LDS_WRITE_RE = re.compile(r"\b(createRecord|updateRecord|deleteRecord)\s*\(")

_APEX_IMPORT_VAR_RE = re.compile(
    r"import\s+(?P<var>\w+)\s+from\s+['\"]@salesforce/apex/"
)
_SCHEMA_IMPORT_RE = re.compile(
    r"import\s+(?P<var>\w+)\s+from\s+['\"]@salesforce/schema/"
    r"(?P<object>[A-Za-z_][A-Za-z0-9_]*)\.(?P<field>[A-Za-z_][A-Za-z0-9_]*)['\"]"
)
_WIRE_CALL_RE = re.compile(
    r"@wire\s*\(\s*(?P<adapter>[A-Za-z_][A-Za-z0-9_]*)(?:\s*,\s*\{(?P<args>[^}]*)\})?\s*\)"
)
_WIRE_FIELDS_RE = re.compile(r"fields\s*:\s*\[(?P<fields>[^\]]*)\]")


def detect_apex_imports(js_source: str) -> list[tuple[str, str]]:
    """Return unique (class_name, method_name) imports from @salesforce/apex."""
    seen: set[tuple[str, str]] = set()
    imports: list[tuple[str, str]] = []
    for match in _APEX_IMPORT_RE.finditer(js_source):
        key = (match.group("class_name"), match.group("method_name"))
        if key in seen:
            continue
        seen.add(key)
        imports.append(key)
    return imports


def detect_apex_import_vars(js_source: str) -> set[str]:
    """Return the local variable names used for all @salesforce/apex imports."""
    return {m.group("var") for m in _APEX_IMPORT_VAR_RE.finditer(js_source)}


def _extract_schema_object_map(js_source: str) -> dict[str, str]:
    """Map import variable name to Salesforce object API name from @salesforce/schema imports."""
    return {m.group("var"): m.group("object") for m in _SCHEMA_IMPORT_RE.finditer(js_source)}


def _resolve_wire_reads(js_source: str, apex_import_names: set[str]) -> list[tuple[str, str]]:
    """Return (name, data_group_ref) per LWC-native @wire call, skipping Apex wires."""
    schema_map = _extract_schema_object_map(js_source)
    results: list[tuple[str, str]] = []
    for m in _WIRE_CALL_RE.finditer(js_source):
        adapter = m.group("adapter")
        if adapter in apex_import_names:
            continue
        if adapter == "getRecord":
            args_text = m.group("args") or ""
            fields_match = _WIRE_FIELDS_RE.search(args_text)
            if fields_match:
                field_vars = [v.strip() for v in fields_match.group("fields").split(",") if v.strip()]
                objects = list(dict.fromkeys(schema_map[v] for v in field_vars if v in schema_map))
                for obj in objects:
                    results.append((f"Read {obj} record", obj))
                if not objects:
                    results.append(("Read record via getRecord", "Unknown"))
            else:
                results.append(("Read record via getRecord", "Unknown"))
        else:
            results.append((f"Read {adapter}", adapter))
    return results


def parse_lwc_native_movements(
    js_source: str,
    html_source: str,
    apex_import_names: set[str] | None = None,
) -> list[RawMovement]:
    """Extract native LWC E/R/W/X movement candidates from JS/HTML."""
    movements: list[RawMovement] = []
    order_hint = 1
    known_apex = apex_import_names or set()

    if _TEMPLATE_EVENT_RE.search(html_source):
        movements.append(
            RawMovement(
                movement_type="E",
                data_group_ref="User",
                name="Receive user interaction",
                order_hint=order_hint,
            )
        )
        order_hint += 1

    for name, data_group_ref in _resolve_wire_reads(js_source, known_apex):
        movements.append(
            RawMovement(
                movement_type="R",
                data_group_ref=data_group_ref,
                name=name,
                order_hint=order_hint,
            )
        )
        order_hint += 1

    if _LDS_READ_RE.search(js_source):
        movements.append(
            RawMovement(
                movement_type="R",
                data_group_ref="Unknown",
                name="Read data via LWC data services",
                order_hint=order_hint,
            )
        )
        order_hint += 1

    if _LDS_WRITE_RE.search(js_source):
        movements.append(
            RawMovement(
                movement_type="W",
                data_group_ref="Unknown",
                name="Write data via LWC data services",
                order_hint=order_hint,
            )
        )
        order_hint += 1

    if _TEMPLATE_BINDING_RE.search(html_source):
        movements.append(
            RawMovement(
                movement_type="X",
                data_group_ref="User",
                name="Display LWC output to user",
                order_hint=order_hint,
            )
        )

    return movements


def infer_bundle_name(bundle_dir: Path) -> str:
    return bundle_dir.name
