"""Pytest setup: put scripts/ and cosmic-measurer/ on sys.path."""

import sys
from pathlib import Path

import pytest

_COSMIC_APEX_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _COSMIC_APEX_ROOT / "scripts"
_COSMIC_MEASURER = _COSMIC_APEX_ROOT.parent

for p in [str(_SCRIPTS), str(_COSMIC_MEASURER)]:
    if p not in sys.path:
        sys.path.insert(0, p)


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Repo root: samples/ and force-app/ live here."""
    return _COSMIC_APEX_ROOT.parent.parent.parent.parent


@pytest.fixture(scope="session")
def cosmic_apex_root() -> Path:
    """cosmic-apex-measurer/ (contains scripts/ and tests/)."""
    return _COSMIC_APEX_ROOT
