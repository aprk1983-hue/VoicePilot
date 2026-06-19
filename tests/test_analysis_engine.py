"""Tests for deterministic analysis engine."""

from __future__ import annotations

from pathlib import Path

import pytest

from domain.enums import InvestigationState, Severity
from domain.models import Case, Evidence
from domain.value_objects import AffectedScope, PlatformRef, SymptomSummary
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.analysis_engine import AnalysisEngine, analyze_ccsip_debug, analyze_dial_peer_summary, analyze_sip_ua_status
from runtime.evidence_collection import initialize_evidence_collection, submit_evidence
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry
from runtime.runtime_engine import RuntimeEngine
from shared.config import RuntimeConfig

PLUGINS_ROOT = Path(__file__).resolve().parents[1] / "plugins"
PLAYBOOK_ID = "VP-CUBE-0001"
INTAKE_ANSWERS = [
    "yes",
    "2026-06-10",
    "no changes",
    "all destinations",
    "yes",
]


@pytest.fixture
def runtime_engine() -> RuntimeEngine:
    registry = PluginRegistry(plugins_root=PLUGINS_ROOT)
    loader = PlaybookLoader(
        repository=FilesystemPlaybookRepository(YamlLoader()),
    )
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


def _case_in_analysis(runtime_engine: RuntimeEngine) -> Case:
    turn = runtime_engine.start_investigation(PLAYBOOK_ID)
    for answer in INTAKE_ANSWERS:
        turn = runtime_engine.submit_answer(turn.case_id, turn.question_id, answer)
    case = runtime_engine.case_manager.load_case(turn.case_id)
    playbook = runtime_engine.playbook_catalog.get(PLAYBOOK_ID)
    initialize_evidence_collection(case, runtime_engine.case_manager, playbook)
    case = runtime_engine.case_manager.load_case(case.case_id)

    submit_evidence(
        case,
        runtime_engine.case_manager,
        "show dial-peer voice summary",
        "dial-peer 1 voip up\n destination-pattern 9T",
    )
    case = runtime_engine.case_manager.load_case(case.case_id)
    submit_evidence(
        case,
        runtime_engine.case_manager,
        "show sip-ua status",
        "SIP User Agent Status: enabled\n registrar registered",
    )
    case = runtime_engine.case_manager.load_case(case.case_id)
    submit_evidence(
        case,
        runtime_engine.case_manager,
        "debug ccsip messages",
        "From: sip:user@example.com\nTo: sip:provider\nCall-ID: abc123\nSIP/2.0 503 Service Unavailable",
    )
    return runtime_engine.case_manager.load_case(case.case_id)


class TestAnalysisEnginePatterns:
    def test_detects_sip_503(self) -> None:
        findings = analyze_ccsip_debug("SIP/2.0 503 Service Unavailable")

        assert "sip_503_detected" in findings

    def test_detects_sip_404(self) -> None:
        findings = analyze_ccsip_debug("SIP/2.0 404 Not Found")

        assert "sip_404_detected" in findings

    def test_detects_sip_ua_disabled(self) -> None:
        findings = analyze_sip_ua_status("SIP-UA Status: disabled")

        assert "sip_ua_disabled" in findings

    def test_detects_dial_peer_present(self) -> None:
        findings = analyze_dial_peer_summary("dial-peer 1 voip\n destination-pattern 9T")

        assert "dial_peer_config_present" in findings


class TestAnalyzeCase:
    def test_analyze_case_transitions_to_hypothesis(self, runtime_engine: RuntimeEngine) -> None:
        case = _case_in_analysis(runtime_engine)

        summary = runtime_engine.analyze_case(case.case_id)

        updated = runtime_engine.case_manager.load_case(case.case_id)
        assert updated.status == InvestigationState.HYPOTHESIS
        assert summary.state == InvestigationState.HYPOTHESIS

    def test_findings_saved_on_case(self, runtime_engine: RuntimeEngine) -> None:
        case = _case_in_analysis(runtime_engine)

        runtime_engine.analyze_case(case.case_id)
        updated = runtime_engine.case_manager.load_case(case.case_id)

        signals = {finding.signal for finding in updated.analysis_findings}
        assert "dial_peer_config_present" in signals
        assert "sip_registration_present" in signals
        assert "sip_trace_present" in signals
        assert "sip_503_detected" in signals
        assert len(updated.analysis_findings) >= 4
