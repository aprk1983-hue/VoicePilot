"""Tests for VP-AUDIOCODES-0001 scenario regression pack."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "core") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "core"))
if str(REPO_ROOT / "sdk") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "sdk"))

from domain.enums import InvestigationState
from runtime.audiocodes_investigation import (
    AUDIOCODES_EVIDENCE_FILES,
    AUDIOCODES_INTAKE_ANSWERS,
    VP_AUDIOCODES_0001_PLAYBOOK_ID,
)
from runtime.evidence_collection import initialize_evidence_collection, submit_evidence
from runtime.report_engine import format_incident_report
from runtime.scenario_runner import (
    build_scenario_runtime_engine,
    default_scenarios_root,
    discover_scenario_dirs,
    load_expected_result,
    run_playbook_scenarios,
    run_scenario,
)
from runtime.verification_engine import RESULT_PASSED, VerificationResultSubmission

PLAYBOOK_ID = VP_AUDIOCODES_0001_PLAYBOOK_ID
SCENARIOS_ROOT = default_scenarios_root(PLAYBOOK_ID, repo_root=REPO_ROOT)

EXPECTED_SCENARIO_IDS = {
    "sip_options_failed",
    "provider_503",
    "proxy_set_unavailable",
    "ip_group_disabled",
    "routing_rule_missing",
    "tls_certificate_expired",
    "media_realm_down",
    "rtp_one_way_audio",
    "session_license_exhausted",
    "ha_sync_failure",
}


class TestVpAudiocodes0001Scenarios:
    @pytest.mark.parametrize("scenario_id", sorted(EXPECTED_SCENARIO_IDS))
    def test_each_scenario_passes_individually(self, scenario_id: str) -> None:
        result = run_scenario(SCENARIOS_ROOT / scenario_id, playbook_id=PLAYBOOK_ID)
        assert result.error is None, result.error
        assert result.passed, f"{scenario_id}: {result.actual_top_hypothesis}"

    def test_all_scenario_folders_present(self) -> None:
        scenario_dirs = discover_scenario_dirs(SCENARIOS_ROOT)
        scenario_ids = {path.name for path in scenario_dirs}
        assert scenario_ids == EXPECTED_SCENARIO_IDS

    def test_all_scenarios_execute_without_crash(self) -> None:
        results = run_playbook_scenarios(PLAYBOOK_ID, repo_root=REPO_ROOT)
        assert len(results) == len(EXPECTED_SCENARIO_IDS)
        for result in results:
            assert result.error is None, f"{result.scenario_id}: {result.error}"
            assert result.actual_top_hypothesis is not None

    def test_all_scenarios_match_expected_root_cause(self) -> None:
        results = run_playbook_scenarios(PLAYBOOK_ID, repo_root=REPO_ROOT)
        for result in results:
            assert result.passed, (
                f"{result.scenario_id}: expected {result.expected_root_cause!r}, "
                f"got {result.actual_top_hypothesis!r} ({int(result.confidence)}%)"
            )

    def test_expected_confidence_thresholds_met(self) -> None:
        for scenario_dir in discover_scenario_dirs(SCENARIOS_ROOT):
            expected = load_expected_result(scenario_dir)
            result = run_scenario(scenario_dir, playbook_id=PLAYBOOK_ID)
            assert result.confidence >= float(expected["min_confidence"]), (
                f"{result.scenario_id}: confidence {result.confidence} "
                f"< {expected['min_confidence']}"
            )

    @pytest.mark.parametrize("scenario_id", sorted(EXPECTED_SCENARIO_IDS))
    def test_golden_report_present(self, scenario_id: str) -> None:
        golden = SCENARIOS_ROOT / scenario_id / "golden_report.md"
        assert golden.is_file()
        content = golden.read_text(encoding="utf-8")
        assert "VoicePilot" in content
        expected = load_expected_result(SCENARIOS_ROOT / scenario_id)
        assert expected["expected_root_cause"] in content

    @pytest.mark.parametrize("filename", [name for _, name in AUDIOCODES_EVIDENCE_FILES])
    def test_each_scenario_has_required_evidence_file(self, filename: str) -> None:
        for scenario_dir in discover_scenario_dirs(SCENARIOS_ROOT):
            assert (scenario_dir / filename).is_file(), f"{scenario_dir.name}: missing {filename}"

    def test_full_lifecycle_with_report_and_learning(self) -> None:
        scenario_dir = SCENARIOS_ROOT / "sip_options_failed"
        runtime = build_scenario_runtime_engine()
        try:
            turn = runtime.start_investigation(PLAYBOOK_ID)
            for answer in AUDIOCODES_INTAKE_ANSWERS:
                turn = runtime.submit_answer(turn.case_id, turn.question_id, answer)

            case = runtime.case_manager.load_case(turn.case_id)
            playbook = runtime.playbook_catalog.get(PLAYBOOK_ID)
            initialize_evidence_collection(case, runtime.case_manager, playbook)
            case = runtime.case_manager.load_case(case.case_id)

            for command, filename in AUDIOCODES_EVIDENCE_FILES:
                submit_evidence(
                    case,
                    runtime.case_manager,
                    command,
                    (scenario_dir / filename).read_text(encoding="utf-8"),
                    decision_log=runtime.decision_log_engine,
                )
                case = runtime.case_manager.load_case(case.case_id)

            runtime.analyze_case(case.case_id)
            runtime.generate_hypotheses(case.case_id)
            runtime.correlate_case(case.case_id)
            runtime.generate_recommendation(case.case_id)
            runtime.evaluate_investigation_quality(case.case_id)
            runtime.generate_change_package(case.case_id)

            checklist = runtime.generate_verification_checklist(case.case_id)
            assert checklist is not None
            submissions = [
                VerificationResultSubmission(
                    verification_id=item.verification_id,
                    status=RESULT_PASSED,
                )
                for item in checklist.items
            ]
            runtime.submit_verification(case.case_id, submissions)
            runtime.close_case_with_learning(case.case_id)

            closed_case = runtime.case_manager.load_case(case.case_id)
            assert closed_case.status == InvestigationState.CLOSED

            report = runtime.generate_report(case.case_id)
            markdown = format_incident_report(report)
            assert "# VoicePilot Incident Report" in markdown
            assert "SIP OPTIONS failure" in markdown
            assert closed_case.learning_record is not None
        finally:
            runtime.shutdown()

    def test_validate_command_supports_audiocodes_playbook(self) -> None:
        from cli.voicepilot_cli import main

        assert main(["validate", PLAYBOOK_ID]) == 0

    def test_discovery_plan_for_partial_evidence_scenario(self) -> None:
        runtime = build_scenario_runtime_engine()
        try:
            turn = runtime.start_investigation(PLAYBOOK_ID)
            for answer in AUDIOCODES_INTAKE_ANSWERS:
                turn = runtime.submit_answer(turn.case_id, turn.question_id, answer)
            case = runtime.case_manager.load_case(turn.case_id)
            playbook = runtime.playbook_catalog.get(PLAYBOOK_ID)
            initialize_evidence_collection(case, runtime.case_manager, playbook)
            submit_evidence(
                case,
                runtime.case_manager,
                "show sip-options",
                (SCENARIOS_ROOT / "sip_options_failed" / "show_sip_options.txt").read_text(),
            )
            runtime.analyze_case(case.case_id)
            plan = runtime.plan_discovery(case.case_id)
            assert plan.requests
        finally:
            runtime.shutdown()
