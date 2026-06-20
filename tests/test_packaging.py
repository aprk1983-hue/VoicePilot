"""Packaging and editable-install safety tests."""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = REPO_ROOT / "examples" / "sample_evidence" / "parser"


def _package_find_config() -> dict:
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return data["tool"]["setuptools"]["packages"]["find"]


class TestPackaging:
    def test_package_discovery_excludes_repo_knowledge_packs(self) -> None:
        config = _package_find_config()

        assert config["where"] == ["core", "cli", "sdk"]
        assert "." not in config["where"]
        assert "knowledge.packs*" in config["exclude"]
        assert (REPO_ROOT / "knowledge" / "packs").is_dir()
        assert not (REPO_ROOT / "core" / "knowledge" / "packs").exists()

    def test_editable_install_succeeds(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        assert completed.returncode == 0, completed.stderr or completed.stdout

    def test_voicepilot_health_works_after_install(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "cli.voicepilot_cli",
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
