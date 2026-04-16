#!/usr/bin/env python3
"""Build the distributable Cursor plugin bundle for the COSMIC skill pack."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_SKILLS_ROOT = REPO_ROOT / ".cursor" / "skills" / "cosmic-measurer"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "plugin" / "cursor-cosmic-measurer"
SOURCE_REPOSITORY_URL = "https://github.com/deniskrizanovic/sf_COSMIC_Measurer"

IGNORED_NAMES = {
    ".pytest_cache",
    "__pycache__",
    "tests",
    ".coveragerc",
    "requirements-dev.txt",
    "PYTHON_DESIGN.md",
}

CLI_BLOCKS = {
    "cosmic-apex-measurer": """```bash
# List entry points (for multi-process detection)
python3 scripts/measure_apex.py path/to/Class.cls --list-entry-points

# Measure (optionally filter to one entry point)
python3 scripts/measure_apex.py path/to/Class.cls [-o output.json] [--fp-id 001xxx] [--entry-point facilityIds]

# Traversal options (default: traverse into called classes when .cls found)
python3 scripts/measure_apex.py path/to/Class.cls [--search-paths force-app/main/default/classes,src/classes] [--no-traverse]
```""",
    "cosmic-flow-measurer": """```bash
python3 scripts/measure_flow.py path/to/Flow.flow-meta.xml
python3 scripts/measure_flow.py path/to/Flow.flow-meta.xml [-o output.json] [--fp-id 001xxx] [--json]
python3 scripts/measure_flow.py path/to/Flow.flow-meta.xml --apex-search-paths force-app/main/default/classes
python3 scripts/measure_flow.py path/to/Flow.flow-meta.xml --no-invocable-apex
```""",
    "cosmic-flexipage-measurer": """```bash
python3 scripts/measure_flexipage.py path/to/Page.flexipage-meta.xml --json
python3 scripts/measure_flexipage.py path/to/Page.flexipage-meta.xml -o out.json --fp-id 001xxx
python3 scripts/measure_flexipage.py path/to/Page.flexipage-meta.xml --json --no-resolve-lwc-candidates
python3 scripts/measure_flexipage.py path/to/Page.flexipage-meta.xml --json --no-resolve-flow-candidates
```""",
    "cosmic-lwc-measurer": """```bash
python3 scripts/measure_lwc.py --bundle-dir path/to/lwc/MyComponent --json
python3 scripts/measure_lwc.py --bundle-dir path/to/lwc/MyComponent --required-type W --apex-search-paths force-app/main/default/classes
```""",
}


def _copytree(src: Path, dest: Path) -> None:
    shutil.copytree(
        src,
        dest,
        ignore=shutil.ignore_patterns(*IGNORED_NAMES),
    )


def _discover_implemented_skills() -> list[str]:
    return sorted(
        path.name
        for path in SOURCE_SKILLS_ROOT.iterdir()
        if path.is_dir() and (path / "SKILL.md").exists()
    )


def _discover_primary_script_name(skill_name: str) -> str:
    script_dir = SOURCE_SKILLS_ROOT / skill_name / "scripts"
    matches = sorted(script.name for script in script_dir.glob("measure_*.py"))
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one primary measure script in {script_dir}, found {matches}")
    return matches[0]


def _rewrite_skill_markdown(text: str, skill_name: str, script_name: str) -> str:
    cli_block = CLI_BLOCKS[skill_name]

    text = text.replace(
        "[reference.md](../reference.md)",
        "[COSMIC Measurer Reference](references/cosmic-measurer-reference.md)",
    )
    text = text.replace(
        "`.cursor/skills/cosmic-measurer/reference.md`",
        "`references/cosmic-measurer-reference.md`",
    )
    text = text.replace(
        f"python3 .cursor/skills/cosmic-measurer/{skill_name}/scripts/{script_name}",
        f"python3 scripts/{script_name}",
    )
    text = text.replace(
        f"python3 ... {script_name}",
        f"python3 scripts/{script_name}",
    )

    if skill_name in {"cosmic-apex-measurer", "cosmic-flow-measurer"}:
        text = re.sub(
            r"### Python script \(deterministic\)\n\n```bash\n.*?```\n",
            "### Python script (deterministic)\n\n" + cli_block + "\n",
            text,
            count=1,
            flags=re.S,
        )
    else:
        text = re.sub(
            r"CLI:\n\n```bash\n.*?```\n",
            "CLI:\n\n" + cli_block + "\n",
            text,
            count=1,
            flags=re.S,
        )

    text = re.sub(
        r"Run tests:\n\n```bash\n.*?```\n",
        "Maintainer note: automated regression tests live in the source repository and run before plugin releases.\n\n",
        text,
        flags=re.S,
    )
    text = re.sub(
        r"- .*Regression.*\n",
        "- **Regression coverage**: Maintainers validate these rules against source-repo fixtures before publishing this plugin.\n",
        text,
    )

    return text


def _plugin_readme() -> str:
    return f"""# COSMIC Skill Pack

`COSMIC Skill Pack` is a Cursor plugin that bundles COSMIC measurer skills for Salesforce artifacts.

## Included skills

- `cosmic-apex-measurer`
- `cosmic-flow-measurer`
- `cosmic-flexipage-measurer`
- `cosmic-lwc-measurer`

The plugin ships the runtime code needed by those skills under `skills/`, including the shared Python helpers used for cross-artifact traversal.

## Install for local testing

1. Copy this plugin directory into `~/.cursor/plugins/local/cosmic-skill-pack`.
2. Restart Cursor or reload plugins.

The plugin root is the directory that contains:

- `.cursor-plugin/plugin.json`
- `skills/`
- `README.md`

## Source of truth

This bundle is generated from the upstream source repository:

- [`sf_COSMIC_Measurer`]({SOURCE_REPOSITORY_URL})

Do not hand-edit generated files in a downstream plugin repository. Refresh them from the upstream source repository instead.

## Notes

- The public plugin bundle intentionally excludes maintainer-only tests, `.pytest_cache`, and dev-only coverage files.
- Salesforce sample fixtures and golden outputs stay in the source repository so the plugin remains lightweight for end users.
- This generated bundle includes the MIT license for redistribution.
"""


def _publishing_guide() -> str:
    return """# Publishing Guide

## Source vs distribution model

- Source of truth: the upstream `sf_COSMIC_Measurer` repository
- Distribution artifact: this plugin bundle directory
- Sync mechanism: regenerate this bundle from the upstream source repository before publishing

The generated plugin bundle is intended to be copied into a dedicated public plugin repository or installed locally for testing.

## Local validation

Validate this bundle in a plugin repository by:

1. Installing the directory into `~/.cursor/plugins/local/cosmic-skill-pack`
2. Restarting Cursor or reloading plugins
3. Measuring one real Apex, Flow, FlexiPage, and LWC artifact from a Salesforce workspace

Run source-repository test and build commands from the upstream repository, not from this generated bundle.

## Marketplace prep

Before a public release:

1. Refresh `version` and metadata in `.cursor-plugin/plugin.json`.
2. Refresh this bundle from the upstream source repository.
3. Confirm the packaged `SKILL.md` files do not contain `.cursor/skills/...`, `samples/`, or `expected/` paths.
4. Smoke-test one artifact per measurer against a real Salesforce project checkout.
5. Submit the public plugin repository to Cursor Marketplace review.
"""


def _plugin_manifest() -> dict[str, object]:
    return {
        "name": "cosmic-skill-pack",
        "version": "0.1.0",
        "license": "MIT",
        "description": (
            "COSMIC measurer skills for Salesforce Apex, Flow, FlexiPage, "
            "and Lightning Web Components."
        ),
        "repository": SOURCE_REPOSITORY_URL,
        "keywords": [
            "cursor-plugin",
            "skills",
            "salesforce",
            "cosmic",
            "apex",
            "flow",
            "flexipage",
            "lwc",
        ],
    }


def _mit_license_text() -> str:
    return """MIT License

Copyright (c) 2026 Denis Krizanovic

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


def build_plugin_bundle(output_dir: Path) -> Path:
    output_dir = output_dir.resolve()
    if output_dir.exists():
        shutil.rmtree(output_dir)

    skills_output_dir = output_dir / "skills"
    skills_output_dir.mkdir(parents=True, exist_ok=True)

    _copytree(SOURCE_SKILLS_ROOT / "shared", skills_output_dir / "shared")
    shutil.copy2(SOURCE_SKILLS_ROOT / "reference.md", skills_output_dir / "reference.md")

    source_reference = (SOURCE_SKILLS_ROOT / "reference.md").read_text(encoding="utf-8")

    for skill_name in _discover_implemented_skills():
        source_dir = SOURCE_SKILLS_ROOT / skill_name
        destination_dir = skills_output_dir / skill_name
        _copytree(source_dir, destination_dir)

        skill_md_path = destination_dir / "SKILL.md"
        skill_md = skill_md_path.read_text(encoding="utf-8")
        script_name = _discover_primary_script_name(skill_name)
        skill_md_path.write_text(
            _rewrite_skill_markdown(skill_md, skill_name, script_name),
            encoding="utf-8",
        )

        references_dir = destination_dir / "references"
        references_dir.mkdir(exist_ok=True)
        (references_dir / "cosmic-measurer-reference.md").write_text(
            source_reference,
            encoding="utf-8",
        )

    plugin_manifest_dir = output_dir / ".cursor-plugin"
    plugin_manifest_dir.mkdir(parents=True, exist_ok=True)
    (plugin_manifest_dir / "plugin.json").write_text(
        json.dumps(_plugin_manifest(), indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "LICENSE").write_text(_mit_license_text(), encoding="utf-8")
    (output_dir / "README.md").write_text(_plugin_readme(), encoding="utf-8")
    (output_dir / "PUBLISHING.md").write_text(_publishing_guide(), encoding="utf-8")

    return output_dir


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the distributable Cursor plugin bundle for the COSMIC skill pack.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Destination directory for the generated plugin bundle (default: {DEFAULT_OUTPUT_DIR})",
    )
    args = parser.parse_args()

    output_dir = build_plugin_bundle(args.output_dir)
    print(f"Built Cursor plugin bundle at {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
