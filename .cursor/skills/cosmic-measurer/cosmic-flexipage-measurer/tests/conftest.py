"""Pytest setup for cosmic-flexipage-measurer."""

import sys
from pathlib import Path

import pytest

_COSMIC_FLEXIPAGE_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _COSMIC_FLEXIPAGE_ROOT / "scripts"
_COSMIC_MEASURER = _COSMIC_FLEXIPAGE_ROOT.parent

for path_entry in [str(_SCRIPTS), str(_COSMIC_MEASURER)]:
    if path_entry not in sys.path:
        sys.path.insert(0, path_entry)


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Repo root for samples/."""
    return _COSMIC_FLEXIPAGE_ROOT.parent.parent.parent.parent


FLEXIPAGE_NS = "http://soap.sforce.com/2006/04/metadata"


def make_flexipage_xml(
    master_label: str = "Test Record Page",
    sobject_type: str = "Account",
    body: str = "",
) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<FlexiPage xmlns="{FLEXIPAGE_NS}">\n'
        f"    <masterLabel>{master_label}</masterLabel>\n"
        f"    <sobjectType>{sobject_type}</sobjectType>\n"
        "    <template><name>flexipage:recordHomeSimpleViewTemplate</name></template>\n"
        "    <type>RecordPage</type>\n"
        f"{body}"
        "</FlexiPage>\n"
    )
