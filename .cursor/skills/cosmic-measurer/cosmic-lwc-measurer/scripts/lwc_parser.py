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
_WIRE_RE = re.compile(r"@wire\s*\(")
_LDS_READ_RE = re.compile(r"\b(getRecord|getListUi|getRecordUi|getObjectInfo)\s*\(")
_LDS_WRITE_RE = re.compile(r"\b(createRecord|updateRecord|deleteRecord)\s*\(")


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


def parse_lwc_native_movements(js_source: str, html_source: str) -> list[RawMovement]:
    """Extract native LWC E/R/W/X movement candidates from JS/HTML."""
    movements: list[RawMovement] = []
    order_hint = 1

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

    if _WIRE_RE.search(js_source) or _LDS_READ_RE.search(js_source):
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
