"""Tests for VP-CUBE-0001 scenario expansion pack."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "core") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "core"))
if str(REPO_ROOT / "sdk") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "sdk"))

from domain.enums import InvestigationState
from runtime.evidence_collection import initialize_evidence_collection, submit_evidence
from runtime.report_engine import format_incident_report
from runtime.scenario_runner import (
    EVIDENCE_FILES,
    INTAKE_ANSWERS,
    VP_CUBE_0001_PLAYBOOK_ID,
    build_scenario_runtime_engine,
    default_scenarios_root,
    discover_scenario_dirs,
    load_expected_result,
    root_cause_matches,
    run_playbook_scenarios,
    run_scenario,
)
from runtime.verification_engine import RESULT_PASSED, VerificationResultSubmission

PLAYBOOK_ID = VP_CUBE_0001_PLAYBOOK_ID
SCENARIOS_ROOT = default_scenarios_root(PLAYBOOK_ID, repo_root=REPO_ROOT)

EXPECTED_SCENARIO_IDS = {
    "sip_ua_disabled",
    "missing_outbound_dial_peer",
    "provider_503",
    "codec_mismatch_488",
    "dial_peer_shutdown",
}


class TestVpCube0001Scenarios:
    def test_all_scenario_folders_present(self) -> None:
        scenario_dirs = discover_scenario_dirs(SCENARIOS_ROOT)
        scenario_ids = {path.name for path in scenario_dirs}
        assert scenario_ids == EXPECTED_SCENARIO_IDS

    def test_all_scenarios_execute_without_crash(self) -> None:
        results = run_playbook_scenarios(PLAYBOOK_ID, repo_root=REPO_ROOT)
        assert len(results) == len(EXPECTED_SCENARIO_IDS)
        for result in results:
            assert result.error is None, result.scenario_id
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
            result = run_scenario(scenario_dir)
            assert result.confidence >= float(expected["min_confidence"]), (
                f"{result.scenario_id}: confidence {result.confidence} "
                f"< {expected['min_confidence']}"
            )

    def test_root_cause_alias_matching(self) -> None:
        expected = {
            "expected_root_cause": "Provider or SIP trunk service issue",
            "expected_root_cause_aliases": ["upstream service issue"],
        }
        assert root_cause_matches("Provider or SIP trunk service issue", expected)
        assert root_cause_matches("Provider/trunk rejection or upstream service issue", expected)

    def test_report_generation_for_sip_ua_disabled_scenario(self) -> None:
        scenario_dir = SCENARIOS_ROOT / "sip_ua_disabled"
        runtime = build_scenario_runtime_engine()
        try:
            turn = runtime.start_investigation(PLAYBOOK_ID)
            for answer in INTAKE_ANSWERS:
                turn = runtime.submit_answer(turn.case_id, turn.question_id, answer)

            case = runtime.case_manager.load_case(turn.case_id)
            playbook = runtime.playbook_catalog.get(PLAYBOOK_ID)
            initialize_evidence_collection(case, runtime.case_manager, playbook)
            case = runtime.case_manager.load_case(case.case_id)

            for command, filename in EVIDENCE_FILES:
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
            assert "CUBE SIP user agent disabled" in markdown
            assert "98%" in markdown
            assert closed_case.learning_record is not None
        finally:
            runtime.shutdown()
