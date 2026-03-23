"""Pytest setup: put scripts/ on sys.path so tests can import measure_apex, parser, movements."""

import sys
from pathlib import Path

import pytest

_COSMIC_APEX_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _COSMIC_APEX_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Repo root: samples/ and force-app/ live here."""
    # cosmic-apex-measurer -> cosmic-measurer -> skills -> .cursor -> project
    return _COSMIC_APEX_ROOT.parent.parent.parent.parent


@pytest.fixture(scope="session")
def cosmic_apex_root() -> Path:
    """cosmic-apex-measurer/ (contains scripts/ and tests/)."""
    return _COSMIC_APEX_ROOT
