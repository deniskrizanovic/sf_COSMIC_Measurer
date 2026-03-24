"""CLI tests for measure_lwc.py."""

import json
import sys

import measure_lwc


def test_cli_json_stdout(monkeypatch, capsys, project_root):
    bundle_dir = project_root / "samples" / "lwc" / "cfp_FunctionalProcessVisualiser"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "measure_lwc",
            "--bundle-dir",
            str(bundle_dir),
            "--json",
        ],
    )
    assert measure_lwc.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["artifact"]["type"] == "LWC"


def test_cli_output_file(monkeypatch, capsys, tmp_path, project_root):
    bundle_dir = project_root / "samples" / "lwc" / "cfp_FunctionalProcessVisualiser"
    output_path = tmp_path / "lwc.json"
    monkeypatch.setattr(
        sys,
        "argv",
        ["measure_lwc", "--bundle-dir", str(bundle_dir), "-o", str(output_path)],
    )
    assert measure_lwc.main() == 0
    assert output_path.exists()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["artifact"]["type"] == "LWC"
    assert "Functional size" in capsys.readouterr().out


def test_cli_missing_bundle(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["measure_lwc", "--bundle-dir", "/missing/path"])
    assert measure_lwc.main() == 1
    assert "not found" in capsys.readouterr().err
