"""Heading-aware chunker.

Given a list of structural lines extracted from a PDF (each tagged as either a
heading at some depth or as body text), produce the per-top-level-section
markdown files plus a `_toc.md` mapping every leaf section to file + line range.

Kept separate from `index_manuals.py` so the chunking logic is testable without
pymupdf — pymupdf only feeds in `StructuralLine` records.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


SECTION_NUMBER_RE = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.+?)\s*$")


@dataclass(frozen=True)
class StructuralLine:
    """A line from the source PDF, classified as heading or body."""

    text: str
    is_heading: bool


@dataclass
class Section:
    """A leaf section in the heading tree.

    `number` is dotted (e.g. "3.2.1"), `title` is the heading text without the
    number, `body` is the body lines that follow until the next heading.
    """

    number: str
    title: str
    body: list[str] = field(default_factory=list)

    @property
    def depth(self) -> int:
        return self.number.count(".") + 1

    @property
    def top_level_number(self) -> str:
        return self.number.split(".", 1)[0]


def parse_sections(lines: Iterable[StructuralLine]) -> list[Section]:
    """Walk structural lines and yield `Section` records in document order.

    Every heading starts a new section. Body lines accumulate against the most
    recent section. Heading lines that do not match `SECTION_NUMBER_RE` are
    treated as body (they are not numbered, so they cannot be cited).
    """
    sections: list[Section] = []
    current: Section | None = None

    for line in lines:
        if line.is_heading:
            match = SECTION_NUMBER_RE.match(line.text.strip())
            if match:
                current = Section(number=match.group(1), title=match.group(2))
                sections.append(current)
                continue
        if current is None:
            continue
        current.body.append(line.text)

    return sections


def slugify(value: str) -> str:
    """Produce a filesystem-safe slug for filenames and folder names."""
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "untitled"


def render_section_markdown(section: Section, manual_short_name: str) -> str:
    """Render a leaf section as the markdown block written into its file.

    Format:

        ### 3.2.1 Triggering events
        > Manual: cosmic-measurement-manual-v5.0
        <body lines, blank-line-stripped at the edges>
    """
    heading_hashes = "#" * (section.depth + 1)
    body = "\n".join(section.body).strip("\n")
    return (
        f"{heading_hashes} {section.number} {section.title}\n"
        f"> Manual: {manual_short_name}\n"
        f"\n"
        f"{body}\n"
    )


@dataclass
class TocEntry:
    """One row in `_toc.md`."""

    number: str
    title: str
    file: str
    start_line: int
    end_line: int


def write_chunked_markdown(
    sections: list[Section],
    out_dir: Path,
    manual_short_name: str,
) -> list[TocEntry]:
    """Write one `.md` file per top-level section and return TOC entries.

    Each top-level section's file contains every descendant section as nested
    headings, each prefixed by its breadcrumb. Returns the line ranges so the
    caller can render `_toc.md`.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    grouped: dict[str, list[Section]] = {}
    top_level_titles: dict[str, str] = {}
    for section in sections:
        top = section.top_level_number
        grouped.setdefault(top, []).append(section)
        if section.depth == 1:
            top_level_titles[top] = section.title

    entries: list[TocEntry] = []
    for top in sorted(grouped, key=lambda n: int(n)):
        children = grouped[top]
        title = top_level_titles.get(top, children[0].title)
        filename = f"{int(top):02d}-{slugify(title)}.md"
        path = out_dir / filename

        rendered_blocks: list[str] = []
        line_cursor = 1
        section_ranges: dict[str, tuple[int, int]] = {}

        for section in children:
            block = render_section_markdown(section, manual_short_name)
            block_lines = block.count("\n")
            section_ranges[section.number] = (
                line_cursor,
                line_cursor + block_lines - 1,
            )
            rendered_blocks.append(block)
            line_cursor += block_lines + 1

        path.write_text("\n".join(rendered_blocks), encoding="utf-8")

        for section in children:
            start, end = section_ranges[section.number]
            entries.append(
                TocEntry(
                    number=section.number,
                    title=section.title,
                    file=filename,
                    start_line=start,
                    end_line=end,
                )
            )

    return entries


def write_toc(entries: list[TocEntry], out_dir: Path, manual_short_name: str) -> Path:
    """Render `_toc.md` for one manual; returns its path."""
    lines = [
        f"# TOC: {manual_short_name}",
        "",
        "| Section | Title | File | Lines |",
        "|---|---|---|---|",
    ]
    for entry in entries:
        lines.append(
            f"| {entry.number} | {entry.title} | "
            f"[{entry.file}]({entry.file}#L{entry.start_line}-L{entry.end_line}) | "
            f"{entry.start_line}-{entry.end_line} |"
        )
    path = out_dir / "_toc.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
