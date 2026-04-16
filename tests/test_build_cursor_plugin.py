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

    manifest_path = plugin_dir / ".cursor-plugin" / "plugin.json"
    assert manifest_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["name"] == "cosmic-skill-pack"
    assert manifest["license"] == "MIT"

    license_path = plugin_dir / "LICENSE"
    assert license_path.exists()
    assert "MIT License" in license_path.read_text(encoding="utf-8")

    readme_text = (plugin_dir / "README.md").read_text(encoding="utf-8")
    publishing_text = (plugin_dir / "PUBLISHING.md").read_text(encoding="utf-8")
    assert "scripts/build_cursor_plugin.py" not in readme_text
    assert "scripts/build_cursor_plugin.py" not in publishing_text
    assert ".cursor/skills/cosmic-measurer" not in publishing_text

    for skill_name in (
        "cosmic-apex-measurer",
        "cosmic-flow-measurer",
        "cosmic-flexipage-measurer",
        "cosmic-lwc-measurer",
    ):
        skill_path = plugin_dir / "skills" / skill_name / "SKILL.md"
        assert skill_path.exists()
        skill_text = skill_path.read_text(encoding="utf-8")
        assert ".cursor/skills/cosmic-measurer" not in skill_text
        assert "samples/" not in skill_text
        assert "expected/" not in skill_text

    shared_output = plugin_dir / "skills" / "shared" / "output.py"
    assert shared_output.exists()


def test_checked_in_plugin_bundle_matches_fresh_build(tmp_path):
    plugin_dir = tmp_path / "cursor-cosmic-measurer"
    script = REPO_ROOT / "scripts" / "build_cursor_plugin.py"

    result = subprocess.run(
        [sys.executable, str(script), "--output-dir", str(plugin_dir)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )

    assert result.returncode == 0, result.stderr
    assert _collect_files(plugin_dir) == _collect_files(CHECKED_IN_PLUGIN_DIR)
