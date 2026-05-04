"""Pytest setup: put scripts/ on sys.path."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_RULE_COACH_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _RULE_COACH_ROOT / "scripts"

if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))


@pytest.fixture(scope="session")
def rule_coach_root() -> Path:
    return _RULE_COACH_ROOT


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return _RULE_COACH_ROOT / "tests" / "fixtures"


@pytest.fixture(scope="session")
def sample_pdf(tmp_path_factory, fixtures_dir: Path) -> Path:
    """Build a tiny multi-section PDF on demand using pymupdf.

    Avoids committing a binary fixture and re-uses the same library the
    indexer depends on, so a successful build of this fixture is itself a
    smoke test for the pymupdf install.
    """
    fitz = pytest.importorskip("fitz")
    out = tmp_path_factory.mktemp("manuals") / "sample-manual.pdf"
    document = fitz.open()
    page = document.new_page()
    cursor = 60.0
    body_size = 11
    heading_size = 16

    def write(text: str, size: int) -> None:
        nonlocal cursor
        page.insert_text((50, cursor), text, fontsize=size)
        cursor += size + 6

    write("1 Introduction", heading_size)
    write("This manual explains the rules.", body_size)
    write("It defines terms used throughout.", body_size)
    write("2 Measurement Process", heading_size)
    write("The process has several steps.", body_size)
    write("2.1 Identify functional users", heading_size)
    write("Functional users send and receive data.", body_size)
    write("2.2 Identify functional processes", heading_size)
    write("A functional process is triggered by an event.", body_size)
    write("3 Data Movements", heading_size)
    write("There are four types: E, R, X, W.", body_size)

    document.save(out)
    document.close()
    return out
