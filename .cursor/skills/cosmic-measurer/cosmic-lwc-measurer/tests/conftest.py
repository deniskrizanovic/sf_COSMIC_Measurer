"""Pytest setup for cosmic-lwc-measurer."""

import sys
from pathlib import Path

import pytest

_COSMIC_LWC_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _COSMIC_LWC_ROOT / "scripts"
_COSMIC_MEASURER = _COSMIC_LWC_ROOT.parent

for path_entry in [str(_SCRIPTS), str(_COSMIC_MEASURER)]:
    if path_entry not in sys.path:
        sys.path.insert(0, path_entry)


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Repo root for samples/."""
    return _COSMIC_LWC_ROOT.parent.parent.parent.parent
