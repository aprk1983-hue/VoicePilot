"""Tests for VoicePilot scenarios CLI command."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIOS_ROOT = (
    REPO_ROOT / "examples" / "sample_evidence" / "scenarios" / "vp_cube_0001"
)
PLAYBOOK_ID = "VP-CUBE-0001"


class TestScenariosCommand:
    def test_voicepilot_scenarios_runs_all_scenarios(self) -> None:
        from cli.voicepilot_cli import main

        output: list[str] = []
        original_print = __import__("builtins").print

        def capture_print(*args, **kwargs) -> None:
            if args:
                output.append(str(args[0]))

        import builtins

        builtins.print = capture_print
        try:
            code = main(["scenarios", PLAYBOOK_ID])
        finally:
            builtins.print = original_print

        text = "\n".join(output)
        assert code == 0
        assert f"VoicePilot Scenario Regression — {PLAYBOOK_ID}" in text
        assert "sip_ua_disabled" in text
        assert "provider_503" in text
        assert "codec_mismatch_488" in text
        assert "Scenarios: 5 total, 5 passed, 0 failed" in text

    def test_voicepilot_scenarios_runs_one_scenario(self) -> None:
        from cli.voicepilot_cli import main

        output: list[str] = []
        original_print = __import__("builtins").print

        def capture_print(*args, **kwargs) -> None:
            if args:
                output.append(str(args[0]))

        import builtins

        builtins.print = capture_print
        try:
            code = main(["scenarios", PLAYBOOK_ID, "--scenario", "provider_503"])
        finally:
            builtins.print = original_print

        text = "\n".join(output)
        assert code == 0
        assert "provider_503" in text
        assert "Provider or SIP trunk service issue" in text
        assert "Scenarios: 1 total, 1 passed, 0 failed" in text
        assert "sip_ua_disabled" not in text

    def test_output_includes_provider_503(self) -> None:
        from cli.voicepilot_cli import run_scenario_assessment

        output: list[str] = []
        code = run_scenario_assessment(PLAYBOOK_ID, output.append)

        text = "\n".join(output)
        assert code == 0
        assert "provider_503" in text
        assert "Provider or SIP trunk service issue" in text

    def test_output_writes_markdown_file(self, tmp_path: Path) -> None:
        from cli.voicepilot_cli import run_scenario_assessment

        report_path = tmp_path / "scenario_results.md"
        output: list[str] = []
        code = run_scenario_assessment(
            PLAYBOOK_ID,
            output.append,
            output_path=report_path,
            generated_at=__import__("datetime").datetime(
                2026, 6, 20, 12, 0, tzinfo=__import__("datetime").timezone.utc
            ),
        )

        assert code == 0
        assert report_path.exists()
        assert "Scenario report saved:" in "\n".join(output)

        content = report_path.read_text(encoding="utf-8")
        assert content.startswith("# VoicePilot Scenario Results")
        assert f"**Playbook:** {PLAYBOOK_ID}" in content
        assert "provider_503" in content
        assert "Provider or SIP trunk service issue" in content
        assert "**Generated:** 2026-06-20T12:00:00+00:00" in content
        assert f"**Scenarios root:** {SCENARIOS_ROOT}" in content

    def test_output_creates_parent_directory(self, tmp_path: Path) -> None:
        from cli.voicepilot_cli import run_scenario_assessment

        report_path = tmp_path / "reports" / "nested" / "scenario_results.md"
        code = run_scenario_assessment(
            PLAYBOOK_ID,
            lambda _line: None,
            output_path=report_path,
        )

        assert code == 0
        assert report_path.exists()
        assert "# VoicePilot Scenario Results" in report_path.read_text(encoding="utf-8")

    def test_nonexistent_scenario_returns_clear_error(self) -> None:
        from cli.voicepilot_cli import run_scenario_assessment

        output: list[str] = []
        code = run_scenario_assessment(
            PLAYBOOK_ID,
            output.append,
            scenario_id="not_a_real_scenario",
        )

        text = "\n".join(output)
        assert code == 1
        assert "Scenario 'not_a_real_scenario' not found" in text
        assert "provider_503" in text

    def test_unsupported_playbook_returns_clear_error(self) -> None:
        from cli.voicepilot_cli import run_scenario_assessment

        output: list[str] = []
        code = run_scenario_assessment("VP-UNKNOWN-9999", output.append)

        assert code == 1
        assert "No scenario pack registered for playbook: VP-UNKNOWN-9999" in "\n".join(output)

    def test_main_supports_output_option(self, tmp_path: Path) -> None:
        from cli.voicepilot_cli import main

        report_path = tmp_path / "scenario_results.md"
        code = main(
            [
                "scenarios",
                PLAYBOOK_ID,
                "--output",
                str(report_path),
            ]
        )

        assert code == 0
        assert report_path.exists()
        assert "provider_503" in report_path.read_text(encoding="utf-8")

    def test_main_supports_scenario_option(self) -> None:
        from cli.voicepilot_cli import main

        output: list[str] = []
        original_print = __import__("builtins").print

        def capture_print(*args, **kwargs) -> None:
            if args:
                output.append(str(args[0]))

        import builtins

        builtins.print = capture_print
        try:
            code = main(["scenarios", PLAYBOOK_ID, "--scenario", "provider_503"])
        finally:
            builtins.print = original_print

        text = "\n".join(output)
        assert code == 0
        assert "provider_503" in text
        assert "Scenarios: 1 total, 1 passed, 0 failed" in text

    def test_plan_scenario_prints_discovery_plan(self) -> None:
        from cli.voicepilot_cli import run_plan_scenario

        output: list[str] = []
        code = run_plan_scenario(
            PLAYBOOK_ID,
            output.append,
            scenario_id="provider_503",
        )

        text = "\n".join(output)
        assert code == 0
        assert text.startswith("# Discovery Plan")
        assert "Current Confidence" in text
        assert "Estimated Final Confidence" in text
        assert "Remaining Uncertainty" in text

    def test_plan_scenario_partial_evidence_lists_missing_commands(self) -> None:
        from runtime.scenario_runner import EVIDENCE_FILES, run_scenario_to_correlation

        scenario_dir = SCENARIOS_ROOT / "provider_503"
        runtime, case_id = run_scenario_to_correlation(
            scenario_dir,
            evidence_files=EVIDENCE_FILES[:2],
        )
        try:
            plan = runtime.plan_discovery(case_id)
            commands = {request.command for request in plan.requests}
            assert "debug ccsip messages" in commands
        finally:
            runtime.shutdown()

    def test_main_plan_scenario_command(self) -> None:
        from cli.voicepilot_cli import main

        output: list[str] = []
        original_print = __import__("builtins").print

        def capture_print(*args, **kwargs) -> None:
            if args:
                output.append(str(args[0]))

        import builtins

        builtins.print = capture_print
        try:
            code = main(["plan-scenario", PLAYBOOK_ID, "--scenario", "provider_503"])
        finally:
            builtins.print = original_print

        text = "\n".join(output)
        assert code == 0
        assert "# Discovery Plan" in text

    def test_scenario_markdown_can_include_discovery_plan(self, tmp_path: Path) -> None:
        from cli.voicepilot_cli import run_scenario_assessment

        report_path = tmp_path / "scenario_results.md"
        code = run_scenario_assessment(
            PLAYBOOK_ID,
            lambda _line: None,
            scenario_id="provider_503",
            output_path=report_path,
            include_discovery=True,
        )

        assert code == 0
        content = report_path.read_text(encoding="utf-8")
        assert "## Discovery Plan" in content
        assert "Current Confidence" in content
