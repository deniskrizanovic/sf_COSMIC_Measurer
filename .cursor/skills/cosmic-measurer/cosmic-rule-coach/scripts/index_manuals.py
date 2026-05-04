"""Index COSMIC manual PDFs into chunked, citation-friendly markdown.

CLI:
    python3 -m scripts.index_manuals <manuals_dir> <out_dir>

Idempotent: a PDF whose mtime predates the corresponding indexed folder's
mtime is skipped. Delete a manual's indexed folder to force a re-index.
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
from pathlib import Path

try:
    from .chunk_by_section import (
        SECTION_NUMBER_RE,
        StructuralLine,
        parse_sections,
        slugify,
        write_chunked_markdown,
        write_toc,
    )
except ImportError:
    from chunk_by_section import (  # type: ignore[no-redef]
        SECTION_NUMBER_RE,
        StructuralLine,
        parse_sections,
        slugify,
        write_chunked_markdown,
        write_toc,
    )


_PYMUPDF_BOLD_FLAG = 16  # bit 4 in pymupdf span flags = bold render
_TOC_LEADER_RE = re.compile(r"\.{2,}\s*\d+\s*$")


def extract_structural_lines(pdf_path: Path) -> list[StructuralLine]:
    """Use pymupdf to read a PDF as `StructuralLine` records.

    A line is classified as a heading when ALL hold:
      1. its leading text matches `SECTION_NUMBER_RE`,
      2. it is NOT a table-of-contents entry (no trailing dot leaders + page no.),
      3. EITHER any span is rendered bold OR its dominant font size is at
         least 1.5pt larger than the document's body-text mode.

    Bold is the primary signal because COSMIC manuals use 11pt body and 11pt
    bold headings. Font-size delta is the fallback for manuals that use
    larger heading fonts.
    """
    import fitz  # type: ignore[import-not-found]

    document = fitz.open(pdf_path)
    raw_lines: list[tuple[str, float, bool]] = []

    for page in document:
        page_dict = page.get_text("dict")
        for block in page_dict.get("blocks", []):
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue
                text = "".join(span["text"] for span in spans).strip()
                if not text:
                    continue
                dominant_size = max(span["size"] for span in spans)
                is_bold = any(
                    span.get("flags", 0) & _PYMUPDF_BOLD_FLAG for span in spans
                )
                raw_lines.append((text, dominant_size, is_bold))

    if not raw_lines:
        return []

    body_size = statistics.mode(round(size, 1) for _, size, _ in raw_lines)
    heading_size_threshold = body_size + 1.5

    structural: list[StructuralLine] = []
    for text, size, is_bold in raw_lines:
        looks_numbered = bool(SECTION_NUMBER_RE.match(text))
        is_toc_entry = bool(_TOC_LEADER_RE.search(text))
        size_says_heading = round(size, 1) >= heading_size_threshold
        is_heading = (
            looks_numbered
            and not is_toc_entry
            and (is_bold or size_says_heading)
        )
        structural.append(StructuralLine(text=text, is_heading=is_heading))
    return structural


def index_pdf(pdf_path: Path, out_dir: Path) -> Path:
    """Index a single PDF; returns the per-manual output folder."""
    manual_slug = slugify(pdf_path.stem)
    manual_out = out_dir / manual_slug

    if manual_out.exists() and manual_out.stat().st_mtime > pdf_path.stat().st_mtime:
        return manual_out

    lines = extract_structural_lines(pdf_path)
    sections = parse_sections(lines)
    if not sections:
        raise RuntimeError(f"No numbered sections detected in {pdf_path}")

    if manual_out.exists():
        for child in manual_out.iterdir():
            if child.is_file():
                child.unlink()
    manual_out.mkdir(parents=True, exist_ok=True)

    entries = write_chunked_markdown(sections, manual_out, manual_slug)
    write_toc(entries, manual_out, manual_slug)
    return manual_out


def index_directory(manuals_dir: Path, out_dir: Path) -> list[Path]:
    """Index every `.pdf` in `manuals_dir`; returns the output folders."""
    if not manuals_dir.is_dir():
        raise FileNotFoundError(f"Manuals dir not found: {manuals_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)

    indexed: list[Path] = []
    for pdf_path in sorted(manuals_dir.glob("*.pdf")):
        indexed.append(index_pdf(pdf_path, out_dir))
    return indexed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manuals_dir", type=Path)
    parser.add_argument("out_dir", type=Path)
    args = parser.parse_args(argv)

    indexed = index_directory(args.manuals_dir, args.out_dir)
    if not indexed:
        print(f"No PDFs found in {args.manuals_dir}", file=sys.stderr)
        return 1
    for path in indexed:
        print(f"Indexed: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
