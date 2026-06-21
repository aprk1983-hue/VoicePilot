"""Tests for the VoicePilot public service layer."""

from __future__ import annotations

import inspect
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from domain.enums import InvestigationState
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.evidence_collection import submit_evidence
from runtime.exceptions import CaseNotFoundError
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry
from runtime.runtime_engine import RuntimeEngine
from runtime.scenario_runner import (
    VP_CUBE_0001_PLAYBOOK_ID,
    default_scenarios_root,
    run_scenario_to_correlation,
)
from runtime.verification_engine import RESULT_PASSED, VerificationResultSubmission
from services import VoicePilotService
from services.service_exceptions import (
    ServiceBrainSessionNotFoundError,
    ServiceCaseNotFoundError,
)
from services.service_models import (
    ServiceAnalysisResult,
    ServiceBrainSessionResult,
    ServiceCaseResult,
    ServiceDiscoveryResult,
    ServiceEvidenceResult,
    ServiceQualityResult,
    ServiceRecommendationResult,
    ServiceReportResult,
    ReportResult,
)
from reporting import ReportType
from services import voicepilot_service as voicepilot_service_module
from shared.config import RuntimeConfig

PLUGINS_ROOT = Path(__file__).resolve().parents[1] / "plugins"
PLAYBOOK_ID = VP_CUBE_0001_PLAYBOOK_ID
SCENARIOS_ROOT = default_scenarios_root(PLAYBOOK_ID, repo_root=PLUGINS_ROOT.parent)
PARTIAL_EVIDENCE_FILES = (
    ("show dial-peer voice summary", "show_dial_peer_voice_summary.txt"),
    ("show sip-ua status", "show_sip_ua_status.txt"),
)
SAMPLE_EVIDENCE = (
    Path(__file__).resolve().parents[1]
    / "examples"
    / "sample_evidence"
    / "parser"
    / "show_sip_ua_status_disabled.txt"
)


@pytest.fixture
def runtime_engine() -> RuntimeEngine:
    registry = PluginRegistry(plugins_root=PLUGINS_ROOT)
    loader = PlaybookLoader(repository=FilesystemPlaybookRepository(YamlLoader()))
    catalog = PlaybookCatalog(plugin_registry=registry, playbook_loader=loader)
    catalog.load_all()
    engine = RuntimeEngine(
        config=RuntimeConfig(playbooks_path=PLUGINS_ROOT),
        case_repository=InMemoryCaseRepository(),
        playbook_repository=FilesystemPlaybookRepository(YamlLoader()),
        plugin_registry=registry,
        playbook_catalog=catalog,
    )
    engine.start()
    return engine


@pytest.fixture
def service(runtime_engine: RuntimeEngine) -> VoicePilotService:
    return VoicePilotService(runtime_engine=runtime_engine)


def _closed_case() -> tuple[VoicePilotService, str]:
    scenario_dir = SCENARIOS_ROOT / "provider_503"
    runtime, case_id = run_scenario_to_correlation(scenario_dir)
    closed_service = VoicePilotService(runtime_engine=runtime)
    closed_service._started = True
    closed_service.generate_recommendation(case_id)

    checklist = runtime.generate_verification_checklist(case_id)
    assert checklist is not None
    submissions = [
        VerificationResultSubmission(
            verification_id=item.verification_id,
            status=RESULT_PASSED,
        )
        for item in checklist.items
    ]
    runtime.submit_verification(case_id, submissions)
    runtime.close_case_with_learning(case_id)
    return closed_service, case_id


class TestVoicePilotService:
    def test_create_case_returns_dto(self, service: VoicePilotService) -> None:
        result = service.create_case(PLAYBOOK_ID)

        assert isinstance(result, ServiceCaseResult)
        assert result.playbook_id == PLAYBOOK_ID
        assert result.state == InvestigationState.INTAKE.value
        assert result.case_id.startswith("CASE-")

    def test_upload_evidence_returns_accepted_result(self, service: VoicePilotService) -> None:
        case = service.create_case(PLAYBOOK_ID)
        raw_text = SAMPLE_EVIDENCE.read_text(encoding="utf-8")

        result = service.upload_evidence(
            case.case_id,
            "show sip-ua status",
            raw_text,
        )

        assert isinstance(result, ServiceEvidenceResult)
        assert result.accepted is True
        assert result.command == "show sip-ua status"
        assert result.evidence_id.startswith("EVD-")

    def test_analyze_case_returns_finding_and_hypothesis_summary(
        self,
        service: VoicePilotService,
    ) -> None:
        scenario_dir = SCENARIOS_ROOT / "provider_503"
        runtime, case_id = run_scenario_to_correlation(
            scenario_dir,
            evidence_files=PARTIAL_EVIDENCE_FILES,
        )
        scenario_service = VoicePilotService(runtime_engine=runtime)

        result = scenario_service.analyze_case(case_id)

        assert isinstance(result, ServiceAnalysisResult)
        assert result.finding_count > 0
        assert result.top_hypothesis is not None
        assert result.confidence is not None

    def test_plan_discovery_returns_next_best_command_for_partial_evidence(
        self,
        service: VoicePilotService,
    ) -> None:
        scenario_dir = SCENARIOS_ROOT / "provider_503"
        runtime, case_id = run_scenario_to_correlation(
            scenario_dir,
            evidence_files=PARTIAL_EVIDENCE_FILES,
        )
        scenario_service = VoicePilotService(runtime_engine=runtime)

        result = scenario_service.plan_discovery(case_id)

        assert isinstance(result, ServiceDiscoveryResult)
        assert result.request_count > 0
        assert result.next_best_command == "show run | sec voice service voip"

    def test_evaluate_quality_returns_score(self, service: VoicePilotService) -> None:
        scenario_dir = SCENARIOS_ROOT / "provider_503"
        runtime, case_id = run_scenario_to_correlation(
            scenario_dir,
            evidence_files=PARTIAL_EVIDENCE_FILES,
        )
        scenario_service = VoicePilotService(runtime_engine=runtime)
        scenario_service.plan_discovery(case_id)

        result = scenario_service.evaluate_quality(case_id)

        assert isinstance(result, ServiceQualityResult)
        assert 0 <= result.overall_score <= 100
        assert result.overall_status

    def test_generate_recommendation_returns_recommendation_summary(
        self,
        service: VoicePilotService,
    ) -> None:
        scenario_dir = SCENARIOS_ROOT / "provider_503"
        runtime, case_id = run_scenario_to_correlation(scenario_dir)
        scenario_service = VoicePilotService(runtime_engine=runtime)

        result = scenario_service.generate_recommendation(case_id)

        assert isinstance(result, ServiceRecommendationResult)
        assert result.recommendation_count == 1
        assert result.top_recommendation is not None

    def test_generate_report_returns_markdown(self) -> None:
        closed_service, case_id = _closed_case()

        result = closed_service.generate_report(case_id, ReportType.ENGINEERING)

        assert isinstance(result, ReportResult)
        assert result.case_id == case_id
        assert result.report_type == "ENGINEERING"
        assert "# VoicePilot Incident Report" in result.markdown

    def test_start_brain_session_returns_session_dto(self, service: VoicePilotService) -> None:
        result = service.start_brain_session(PLAYBOOK_ID)

        assert isinstance(result, ServiceBrainSessionResult)
        assert result.session_id.startswith("BRN-")
        assert result.playbook_id == PLAYBOOK_ID
        assert result.current_stage == "WAITING_FOR_EVIDENCE"

    def test_get_brain_status_works(self, service: VoicePilotService) -> None:
        started = service.start_brain_session(PLAYBOOK_ID)

        result = service.get_brain_status(started.session_id)

        assert result.session_id == started.session_id
        assert result.case_id == started.case_id

    def test_list_cases_works(self, service: VoicePilotService) -> None:
        first = service.create_case(PLAYBOOK_ID)
        second = service.create_case(PLAYBOOK_ID)

        results = service.list_cases()

        assert len(results) == 2
        case_ids = {item.case_id for item in results}
        assert first.case_id in case_ids
        assert second.case_id in case_ids

    def test_service_does_not_duplicate_engine_logic(self) -> None:
        source = inspect.getsource(voicepilot_service_module)
        forbidden = (
            "AnalysisEngine(",
            "HypothesisEngine(",
            "CorrelationEngine(",
            "PlannerEngine(",
            "InvestigationQualityEngine(",
            "RecommendationEngine(",
            "ReportEngine(",
        )
        for token in forbidden:
            assert token not in source

        runtime = MagicMock()
        runtime.start = MagicMock()
        runtime.case_manager.load_case.side_effect = CaseNotFoundError("CASE-missing")
        delegated = VoicePilotService(runtime_engine=runtime)
        delegated._started = True

        with pytest.raises(ServiceCaseNotFoundError):
            delegated.get_case("CASE-missing")

        runtime.case_manager.load_case.assert_called_once_with("CASE-missing")

    def test_invalid_case_error_is_clear(self, service: VoicePilotService) -> None:
        with pytest.raises(ServiceCaseNotFoundError, match="Case not found: CASE-missing"):
            service.get_case("CASE-missing")

    def test_invalid_brain_session_error_is_clear(self, service: VoicePilotService) -> None:
        with pytest.raises(
            ServiceBrainSessionNotFoundError,
            match="Brain session not found: BRN-missing",
        ):
            service.get_brain_status("BRN-missing")

    def test_replay_brain_session_returns_markdown(self, service: VoicePilotService) -> None:
        started = service.start_brain_session(PLAYBOOK_ID)

        replay = service.replay_brain_session(started.session_id)

        assert "Investigation Replay" in replay
        assert started.session_id in replay
