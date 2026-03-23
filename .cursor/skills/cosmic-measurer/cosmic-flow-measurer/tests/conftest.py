"""Pytest setup: put scripts/ and cosmic-measurer/ on sys.path."""

import sys
from pathlib import Path

import pytest

_COSMIC_FLOW_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _COSMIC_FLOW_ROOT / "scripts"
_COSMIC_MEASURER = _COSMIC_FLOW_ROOT.parent

for p in [str(_SCRIPTS), str(_COSMIC_MEASURER)]:
    if p not in sys.path:
        sys.path.insert(0, p)


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Repo root: samples/ live here."""
    return _COSMIC_FLOW_ROOT.parent.parent.parent.parent


@pytest.fixture(scope="session")
def cosmic_flow_root() -> Path:
    """cosmic-flow-measurer/ (contains scripts/ and tests/)."""
    return _COSMIC_FLOW_ROOT


FLOW_NS = "http://soap.sforce.com/2006/04/metadata"


def make_flow_xml(
    process_type: str = "Flow",
    label: str = "TestFlow",
    api_version: str = "66.0",
    body: str = "",
    status: str = "Active",
) -> str:
    """Build a minimal .flow-meta.xml string for testing."""
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<Flow xmlns="{FLOW_NS}">\n'
        f"    <apiVersion>{api_version}</apiVersion>\n"
        f"    <label>{label}</label>\n"
        f"    <processType>{process_type}</processType>\n"
        f"    <status>{status}</status>\n"
        f"    <start><locationX>0</locationX><locationY>0</locationY></start>\n"
        f"{body}"
        "</Flow>\n"
    )
