from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CHECKED_IN_PLUGIN_DIR = REPO_ROOT / "plugin" / "cursor-cosmic-measurer"


def _collect_files(root: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        files[str(path.relative_to(root))] = path.read_bytes()
    return files


def test_build_cursor_plugin_creates_plugin_bundle(tmp_path):
    plugin_dir = tmp_path / "cursor-cosmic-measurer"
    script = REPO_ROOT / "scripts" / "build_cursor_plugin.py"

    result = subprocess.run(
        [sys.executable, str(script), "--output-dir", str(plugin_dir)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0, result.stderr

def test_placeholder():
    pass
