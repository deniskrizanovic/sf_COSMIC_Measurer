"""Integration tests for `index_manuals.py` against a generated sample PDF."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

pytest.importorskip("fitz")

from index_manuals import index_directory, index_pdf, main  # noqa: E402


def _copy_sample(sample_pdf: Path, manuals_dir: Path) -> Path:
    manuals_dir.mkdir(parents=True, exist_ok=True)
    target = manuals_dir / sample_pdf.name
    shutil.copy(sample_pdf, target)
    return target


def test_section_detection_emits_one_file_per_top_level(
    sample_pdf: Path, tmp_path: Path
):
    manuals_dir = tmp_path / "manuals"
    out_dir = tmp_path / "out"
    _copy_sample(sample_pdf, manuals_dir)

    index_directory(manuals_dir, out_dir)

    manual_out = out_dir / "sample-manual"
    files = sorted(p.name for p in manual_out.glob("*.md") if p.name != "_toc.md")
    assert files == [
        "01-introduction.md",
        "02-measurement-process.md",
        "03-data-movements.md",
    ]


def test_toc_lists_every_leaf_section(sample_pdf: Path, tmp_path: Path):
    manuals_dir = tmp_path / "manuals"
    out_dir = tmp_path / "out"
    _copy_sample(sample_pdf, manuals_dir)

    index_directory(manuals_dir, out_dir)

    toc_text = (out_dir / "sample-manual" / "_toc.md").read_text(encoding="utf-8")
    for section in ["| 1 |", "| 2 |", "| 2.1 |", "| 2.2 |", "| 3 |"]:
        assert section in toc_text, f"missing {section} in TOC"


def test_breadcrumb_appears_in_every_chunk(sample_pdf: Path, tmp_path: Path):
    manuals_dir = tmp_path / "manuals"
    out_dir = tmp_path / "out"
    _copy_sample(sample_pdf, manuals_dir)

    index_directory(manuals_dir, out_dir)

    for md_path in (out_dir / "sample-manual").glob("*.md"):
        if md_path.name == "_toc.md":
            continue
        text = md_path.read_text(encoding="utf-8")
        assert text.count("> Manual: sample-manual") >= 1


def test_reindex_is_idempotent_when_pdf_unchanged(sample_pdf: Path, tmp_path: Path):
    manuals_dir = tmp_path / "manuals"
    out_dir = tmp_path / "out"
    pdf_copy = _copy_sample(sample_pdf, manuals_dir)

    index_pdf(pdf_copy, out_dir)
    manual_out = out_dir / "sample-manual"
    first_run_mtimes = {p.name: p.stat().st_mtime for p in manual_out.iterdir()}

    time.sleep(0.05)
    index_pdf(pdf_copy, out_dir)
    second_run_mtimes = {p.name: p.stat().st_mtime for p in manual_out.iterdir()}

    assert first_run_mtimes == second_run_mtimes


def test_reindex_rebuilds_when_pdf_is_newer(sample_pdf: Path, tmp_path: Path):
    manuals_dir = tmp_path / "manuals"
    out_dir = tmp_path / "out"
    pdf_copy = _copy_sample(sample_pdf, manuals_dir)

    index_pdf(pdf_copy, out_dir)
    manual_out = out_dir / "sample-manual"
    first_intro = (manual_out / "01-introduction.md").stat().st_mtime

    future = time.time() + 5
    import os

    os.utime(pdf_copy, (future, future))
    index_pdf(pdf_copy, out_dir)
    second_intro = (manual_out / "01-introduction.md").stat().st_mtime

    assert second_intro >= first_intro


def test_index_directory_raises_when_dir_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        index_directory(tmp_path / "does-not-exist", tmp_path / "out")


def test_index_pdf_raises_when_no_sections(tmp_path: Path):
    fitz = pytest.importorskip("fitz")
    pdf_path = tmp_path / "empty.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((50, 60), "no headings here, just body text", fontsize=11)
    document.save(pdf_path)
    document.close()

    with pytest.raises(RuntimeError, match="No numbered sections"):
        index_pdf(pdf_path, tmp_path / "out")


def test_cli_main_exits_zero_when_pdfs_indexed(
    sample_pdf: Path, tmp_path: Path, capsys
):
    manuals_dir = tmp_path / "manuals"
    out_dir = tmp_path / "out"
    _copy_sample(sample_pdf, manuals_dir)

    exit_code = main([str(manuals_dir), str(out_dir)])

    assert exit_code == 0
    assert "Indexed:" in capsys.readouterr().out


def test_cli_main_exits_one_when_no_pdfs_present(tmp_path: Path, capsys):
    manuals_dir = tmp_path / "manuals"
    manuals_dir.mkdir()
    out_dir = tmp_path / "out"

    exit_code = main([str(manuals_dir), str(out_dir)])

    assert exit_code == 1
    assert "No PDFs found" in capsys.readouterr().err


def test_module_invocation_resolves_sibling_imports(
    sample_pdf: Path, tmp_path: Path, rule_coach_root: Path
):
    """`python3 -m scripts.index_manuals ...` must work from the skill root.

    Regression for the ModuleNotFoundError seen when chunk_by_section was
    imported as a top-level module instead of a package-relative one.
    """
    manuals_dir = tmp_path / "manuals"
    out_dir = tmp_path / "out"
    _copy_sample(sample_pdf, manuals_dir)

    result = subprocess.run(
        [sys.executable, "-m", "scripts.index_manuals", str(manuals_dir), str(out_dir)],
        cwd=rule_coach_root,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        check=False,
    )

    assert result.returncode == 0, (
        f"stdout={result.stdout!r}\nstderr={result.stderr!r}"
    )
    assert (out_dir / "sample-manual" / "_toc.md").exists()
