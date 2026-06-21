"""Packaging and editable-install safety tests."""

from __future__ import annotations

import importlib
import subprocess
import sys
import tomllib
from importlib.metadata import entry_points
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = REPO_ROOT / "examples" / "sample_evidence" / "parser"


def _package_find_config() -> dict:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return data["tool"]["setuptools"]["packages"]["find"]


class TestPackaging:
    def test_package_discovery_includes_cli_sdk_and_plugins(self) -> None:
        config = _package_find_config()

        assert config["where"] == [".", "core"]
        assert "cli*" in config["include"]
        assert "services*" in config["include"]
        assert "sdk*" in config["include"]
        assert "plugins*" in config["include"]
        assert "knowledge.packs*" in config["exclude"]
        assert (REPO_ROOT / "knowledge" / "packs").is_dir()
        assert not (REPO_ROOT / "core" / "knowledge" / "packs").exists()

    def test_cli_import_succeeds(self) -> None:
        module = importlib.import_module("cli.voicepilot_cli")

        assert module.main is not None
        assert callable(module.main)

    def test_services_import_succeeds(self) -> None:
        module = importlib.import_module("services")

        assert module.VoicePilotService is not None

    def test_console_entry_point_target_exists(self) -> None:
        scripts = entry_points(group="console_scripts")
        voicepilot = next(script for script in scripts if script.name == "voicepilot")

        assert voicepilot.value == "cli.voicepilot_cli:main"
        module_name, _, attr = voicepilot.value.partition(":")
        module = importlib.import_module(module_name)
        assert hasattr(module, attr)

    def test_editable_install_succeeds(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        assert completed.returncode == 0, completed.stderr or completed.stdout

        top_level = (
            REPO_ROOT / "voicepilot.egg-info" / "top_level.txt"
        ).read_text(encoding="utf-8")
        assert "cli" in top_level.splitlines()
        assert "services" in top_level.splitlines()

    def test_voicepilot_console_script_runs_health(self) -> None:
        voicepilot = Path(sys.executable).with_name("voicepilot")
        completed = subprocess.run(
            [
                str(voicepilot),
                "health",
                "--samples",
                str(SAMPLE_DIR),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        assert completed.returncode == 0, completed.stderr or completed.stdout
        assert "VoicePilot Health Assessment" in completed.stdout
        assert "Score:" in completed.stdout
