"""Unit tests for the heading-aware chunker (no PDF dependency)."""

from __future__ import annotations

from pathlib import Path

from chunk_by_section import (
    Section,
    StructuralLine,
    parse_sections,
    render_section_markdown,
    slugify,
    write_chunked_markdown,
    write_toc,
)


def line(text: str, is_heading: bool = False) -> StructuralLine:
    return StructuralLine(text=text, is_heading=is_heading)


def test_parse_sections_splits_on_numbered_headings():
    sections = parse_sections(
        [
            line("1 Introduction", is_heading=True),
            line("Body of intro."),
            line("2 Process", is_heading=True),
            line("2.1 Triggers", is_heading=True),
            line("Body of triggers."),
        ]
    )
    assert [s.number for s in sections] == ["1", "2", "2.1"]
    assert sections[0].title == "Introduction"
    assert sections[2].body == ["Body of triggers."]


def test_parse_sections_ignores_unnumbered_headings():
    sections = parse_sections(
        [
            line("Preface", is_heading=True),
            line("1 Introduction", is_heading=True),
            line("Body of intro."),
        ]
    )
    assert [s.number for s in sections] == ["1"]


def test_parse_sections_accepts_trailing_dot_on_top_level_number():
    """Real manuals write `1. INTRODUCTION` with a period after the digit."""
    sections = parse_sections(
        [
            line("1. INTRODUCTION", is_heading=True),
            line("Body of intro."),
            line("2. SCOPE", is_heading=True),
            line("Body of scope."),
        ]
    )
    assert [s.number for s in sections] == ["1", "2"]
    assert sections[0].title == "INTRODUCTION"


def test_parse_sections_treats_numeric_lookalikes_in_body_as_body():
    sections = parse_sections(
        [
            line("1 Introduction", is_heading=True),
            line("See 1.2.3 for details."),
        ]
    )
    assert sections[0].body == ["See 1.2.3 for details."]


def test_section_depth_and_top_level():
    section = Section(number="3.2.1", title="Triggering events")
    assert section.depth == 3
    assert section.top_level_number == "3"


def test_render_section_includes_breadcrumb():
    rendered = render_section_markdown(
        Section(number="2.1", title="Functional users", body=["A user sends data."]),
        manual_short_name="cosmic-mm-v5",
    )
    assert rendered.startswith("### 2.1 Functional users\n")
    assert "> Manual: cosmic-mm-v5" in rendered
    assert "A user sends data." in rendered


def test_slugify_normalises_filenames():
    assert slugify("COSMIC Measurement Manual v5.0") == "cosmic-measurement-manual-v5-0"
    assert slugify("   ") == "untitled"


def test_write_chunked_markdown_groups_by_top_level_section(tmp_path: Path):
    sections = [
        Section(number="1", title="Introduction", body=["Intro body."]),
        Section(number="2", title="Process", body=["Process intro."]),
        Section(number="2.1", title="Triggers", body=["Trigger body."]),
        Section(number="3", title="Data Movements", body=["Movements body."]),
    ]
    entries = write_chunked_markdown(sections, tmp_path, "test-manual")

    files = sorted(p.name for p in tmp_path.glob("*.md"))
    assert files == [
        "01-introduction.md",
        "02-process.md",
        "03-data-movements.md",
    ]

    process_md = (tmp_path / "02-process.md").read_text(encoding="utf-8")
    assert "## 2 Process" in process_md
    assert "### 2.1 Triggers" in process_md

    by_number = {entry.number: entry for entry in entries}
    assert set(by_number) == {"1", "2", "2.1", "3"}
    process_entry = by_number["2.1"]
    assert process_entry.file == "02-process.md"
    assert process_entry.start_line < process_entry.end_line


def test_write_toc_has_one_row_per_section(tmp_path: Path):
    sections = [
        Section(number="1", title="Introduction", body=["Intro."]),
        Section(number="2", title="Process", body=["Process."]),
        Section(number="2.1", title="Triggers", body=["Triggers."]),
    ]
    entries = write_chunked_markdown(sections, tmp_path, "test-manual")
    toc_path = write_toc(entries, tmp_path, "test-manual")

    body = toc_path.read_text(encoding="utf-8")
    assert "# TOC: test-manual" in body
    assert "| 1 | Introduction |" in body
    assert "| 2.1 | Triggers |" in body
    assert body.count("\n|") == 1 + 1 + 3  # header sep + header + 3 rows


def test_every_chunk_starts_with_breadcrumb(tmp_path: Path):
    sections = [
        Section(number="1", title="Introduction", body=["Body."]),
        Section(number="2", title="Process", body=["Body."]),
        Section(number="2.1", title="Triggers", body=["Body."]),
    ]
    write_chunked_markdown(sections, tmp_path, "test-manual")
    for md_path in tmp_path.glob("*.md"):
        text = md_path.read_text(encoding="utf-8")
        for chunk in text.split("\n## ")[1:] + text.split("\n### ")[1:]:
            assert "> Manual: test-manual" in chunk
