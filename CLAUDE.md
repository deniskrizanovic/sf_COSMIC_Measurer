# Claude Code Configuration for sf_COSMIC-Measurer

## Project Overview
This is a Python-based COSMIC measurement toolkit for Salesforce artifacts. It's also configured as a Cursor project with custom skills in the `.cursor/skills/cosmic-measurer/` directory.

## Key Commands

### Testing
- **Run all tests**: `python3 -m pytest ".cursor/skills/cosmic-measurer" -v`
- **Run specific measurer tests**:
  - `python3 -m pytest ".cursor/skills/cosmic-measurer/cosmic-apex-measurer/tests" -v`
  - `python3 -m pytest ".cursor/skills/cosmic-measurer/cosmic-flow-measurer/tests" -v`
  - `python3 -m pytest ".cursor/skills/cosmic-measurer/cosmic-flexipage-measurer/tests" -v`
  - `python3 -m pytest ".cursor/skills/cosmic-measurer/cosmic-lwc-measurer/tests" -v`

### Coverage
- **Run coverage**: `python3 -m pytest ".cursor/skills/cosmic-measurer" --cov=".cursor/skills/cosmic-measurer" --cov-report=term`

### Dependencies
- **Install dependencies**: `pip install -r requirements.txt`

### Build Cursor Plugin
- **Build plugin**: `python3 scripts/build_cursor_plugin.py`

## Project Structure
- `.cursor/skills/cosmic-measurer/` - Cursor skills for COSMIC measurement
- `samples/` - Sample artifacts for testing
- `expected/` - Expected JSON fixtures for regression tests
- `metadata-to-measure/` - Scratch directory for ad-hoc measurements (gitignored)
- `tests/` - Additional project-level tests

## Development Notes
- This project serves dual purposes as both a standalone Python toolkit and a Cursor skills package
- The COSMIC Rule Coach requires PDF manual indexing before use
- All measurers produce deterministic JSON output suitable for sf_CosmicWorkBench integration