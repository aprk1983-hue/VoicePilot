"""Tests for VoicePilot health CLI command."""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = REPO_ROOT / "examples" / "sample_evidence" / "parser"


@pytest.fixture(autouse=True)
def _reset_knowledge_cache() -> None:
    from runtime.knowledge_bootstrap import reset_default_knowledge_engine

    reset_default_knowledge_engine()
    yield
    reset_default_knowledge_engine()


class TestCliBootstrap:
    def test_bootstrap_adds_core_and_plugins_to_sys_path(self) -> None:
        core_path = str(REPO_ROOT / "core")
        plugins_path = str(REPO_ROOT / "plugins")
        filtered_path = [
            entry
            for entry in sys.path
            if entry not in {core_path, plugins_path, str(REPO_ROOT), str(REPO_ROOT / "sdk")}
        ]
        sys.path[:] = filtered_path

        from cli import voicepilot_cli

        importlib.reload(voicepilot_cli)

        assert str(REPO_ROOT / "core") in sys.path
        assert str(REPO_ROOT / "plugins") in sys.path
        import model  # noqa: F401

    def test_cli_import_path_works_from_entry_point_style_import(self) -> None:
        env = {key: value for key, value in __import__("os").environ.items() if key != "PYTHONPATH"}
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from cli.voicepilot_cli import bootstrap_import_paths, main; "
                    "bootstrap_import_paths(); "
                    "import model; "
                    "raise SystemExit(main(['health', '--samples', "
                    f"'{SAMPLE_DIR}']))"
                ),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

        assert completed.returncode == 0, completed.stderr
        assert "VoicePilot Health Assessment" in completed.stdout


class TestHealthCommand:
    def test_voicepilot_health_runs(self) -> None:
        from cli.voicepilot_cli import main

        output: list[str] = []
        original_print = __import__("builtins").print

        def capture_print(*args, **kwargs) -> None:
            if args:
                output.append(str(args[0]))

        import builtins

        builtins.print = capture_print
        try:
            code = main(["health", "--samples", str(SAMPLE_DIR)])
        finally:
            builtins.print = original_print

        assert code == 0
        assert "VoicePilot Health Assessment" in "\n".join(output)

    def test_health_output_includes_score(self) -> None:
        from cli.voicepilot_cli import run_health_assessment

        output: list[str] = []
        code = run_health_assessment(SAMPLE_DIR, output.append)

        text = "\n".join(output)
        assert code == 0
        assert "Score:" in text
        assert "/100" in text
        assert "Status:" in text
        assert "Counts:" in text
        assert "PASS" in text
        assert "WARN" in text or "FAIL" in text

    def test_health_output_includes_sip_ua_disabled_when_disabled_sample_exists(
        self, tmp_path: Path
    ) -> None:
        from cli.voicepilot_cli import run_health_assessment

        disabled_sample = SAMPLE_DIR / "show_sip_ua_status_disabled.txt"
        target = tmp_path / "show_sip_ua_status_disabled.txt"
        target.write_text(disabled_sample.read_text(encoding="utf-8"), encoding="utf-8")

        output: list[str] = []
        code = run_health_assessment(tmp_path, output.append)

        text = "\n".join(output)
        assert code == 0
        assert "SIP-UA is disabled." in text
        assert "Enable SIP-UA and validate registration." in text

    def test_health_output_includes_matched_cisco_knowledge(self) -> None:
        from cli.voicepilot_cli import run_health_assessment

        output: list[str] = []
        code = run_health_assessment(SAMPLE_DIR, output.append)

        text = "\n".join(output)
        assert code == 0
        assert "Matched Knowledge:" in text
        assert "CISCO-BP-SIP-UA-ENABLED" in text
        assert "Enable SIP-UA and verify SIP registration before closing the incident." in text

    def test_health_uses_default_samples_dir_when_available(self) -> None:
        from cli.voicepilot_cli import default_samples_dir, resolve_samples_dir

        assert default_samples_dir().is_dir()
        assert resolve_samples_dir(None) == default_samples_dir()

    def test_health_reports_missing_samples_directory(self) -> None:
        from cli.voicepilot_cli import run_health_assessment

        output: list[str] = []
        code = run_health_assessment(Path("/nonexistent/samples"), output.append)

        assert code == 1
        assert "Sample evidence directory not found." in "\n".join(output)


class TestHealthReportExport:
    def test_output_writes_markdown_file(self, tmp_path: Path) -> None:
        from cli.voicepilot_cli import run_health_assessment

        report_path = tmp_path / "health_report.md"
        output: list[str] = []
        code = run_health_assessment(
            SAMPLE_DIR,
            output.append,
            output_path=report_path,
            generated_at=__import__("datetime").datetime(
                2026, 6, 20, 12, 0, tzinfo=__import__("datetime").timezone.utc
            ),
        )

        assert code == 0
        assert report_path.exists()
        assert "VoicePilot Health Assessment" in "\n".join(output)

        content = report_path.read_text(encoding="utf-8")
        assert content.startswith("# VoicePilot Health Assessment")
        assert "**Score:**" in content
        assert "/100" in content
        assert "SIP-UA is disabled." in content
        assert "CISCO-BP-SIP-UA-ENABLED" in content
        assert "Enable SIP-UA and verify SIP registration before closing the incident." in content
        assert "**Generated:** 2026-06-20T12:00:00+00:00" in content
        assert f"**Samples:** {SAMPLE_DIR}" in content

    def test_output_creates_parent_directory(self, tmp_path: Path) -> None:
        from cli.voicepilot_cli import run_health_assessment

        report_path = tmp_path / "reports" / "nested" / "health_report.md"
        code = run_health_assessment(
            SAMPLE_DIR,
            lambda _line: None,
            output_path=report_path,
        )

        assert code == 0
        assert report_path.exists()
        assert "# VoicePilot Health Assessment" in report_path.read_text(encoding="utf-8")

    def test_main_supports_output_option(self, tmp_path: Path) -> None:
        from cli.voicepilot_cli import main

        report_path = tmp_path / "health_report.md"
        code = main(
            [
                "health",
                "--samples",
                str(SAMPLE_DIR),
                "--output",
                str(report_path),
            ]
        )

        assert code == 0
        assert report_path.exists()
        assert "**Score:**" in report_path.read_text(encoding="utf-8")
