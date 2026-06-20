"""Tests for deterministic correlation engine."""

from __future__ import annotations

from pathlib import Path

import pytest

from domain.enums import InvestigationState, Severity
from domain.models import AnalysisFinding, Case, Hypothesis
from domain.value_objects import AffectedScope, PlatformRef, SymptomSummary
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.correlation_engine import (
    HYP_CODEC_TITLE,
    HYP_MISSING_DIAL_PEER_TITLE,
    HYP_PROVIDER_TITLE,
    HYP_SIP_UA_DISABLED_TITLE,
    CorrelationEngine,
    format_correlation_summary,
)
from runtime.exceptions import InvalidInvestigationStateError
from runtime.hypothesis_engine import HypothesisEngine, VP_CUBE_0001_PLAYBOOK_ID
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry
from runtime.runtime_engine import RuntimeEngine
from shared.config import RuntimeConfig

PLUGINS_ROOT = Path(__file__).resolve().parents[1] / "plugins"


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


def _case_with_signals(case_id: str, signals: list[str]) -> Case:
    case = Case(
        case_id=case_id,
        title="test",
        status=InvestigationState.INVESTIGATION,
        severity=Severity.HIGH,
        business_impact="test",
        symptom=SymptomSummary(summary="test"),
        affected_scope=AffectedScope(),
        platform=PlatformRef(vendor="cisco"),
        playbook_id=VP_CUBE_0001_PLAYBOOK_ID,
    )
    case.analysis_findings = [
        AnalysisFinding.create(case_id, f"EVD-{index}", "debug ccsip messages", signal)
        for index, signal in enumerate(signals, start=1)
    ]
    return case


def _case_with_hypotheses(case_id: str, signals: list[str]) -> Case:
    case = _case_with_signals(case_id, signals)
    case.hypotheses = HypothesisEngine().generate(case)
    case.status = InvestigationState.INVESTIGATION
    return case


class TestCorrelationEngineRules:
    def test_sip_ua_disabled_and_config_confirms_boosts_to_98(self) -> None:
        case = _case_with_hypotheses(
            "CASE-CONFIRM",
            ["sip_ua_disabled", "sip_ua_disabled_by_config"],
        )

        summary = CorrelationEngine().correlate(case)
        ua_hypothesis = next(
            hypothesis for hypothesis in case.hypotheses if hypothesis.title == HYP_SIP_UA_DISABLED_TITLE
        )

        assert ua_hypothesis.confidence == 98.0
        assert ua_hypothesis.rank == 1
        assert any(item.rule_id == "sip_ua_disabled_confirmed" for item in summary.correlations)
        assert case.correlation_results
        assert "sip_ua_disabled_confirmed (+8 confidence)" in format_correlation_summary(summary)

    def test_sip_ua_status_contradiction_reduces_confidence(self) -> None:
        case = _case_with_signals(
            "CASE-MISMATCH",
            ["sip_ua_enabled", "sip_ua_disabled_by_config"],
        )
        case.hypotheses = [
            Hypothesis.create(
                case_id=case.case_id,
                title=HYP_SIP_UA_DISABLED_TITLE,
                confidence=90.0,
                supporting_finding_ids=[],
                rank=1,
            )
        ]

        CorrelationEngine().correlate(case)
        ua_hypothesis = case.hypotheses[0]

        assert ua_hypothesis.confidence == 80.0
        assert any(item.rule_id == "sip_ua_status_config_mismatch" for item in case.correlation_results)

    def test_provider_503_and_registration_issue_boosts_provider_hypothesis(self) -> None:
        case = _case_with_hypotheses(
            "CASE-PROVIDER",
            ["sip_503_detected", "sip_registration_issue", "sip_trace_present"],
        )

        CorrelationEngine().correlate(case)
        provider = next(
            hypothesis for hypothesis in case.hypotheses if hypothesis.title == HYP_PROVIDER_TITLE
        )

        assert provider.confidence == 85.0
        assert any(item.rule_id == "provider_or_trunk_unavailable" for item in case.correlation_results)

    def test_404_and_missing_dial_peer_boosts_routing_hypothesis(self) -> None:
        case = _case_with_hypotheses(
            "CASE-ROUTING",
            ["sip_404_detected", "dial_peer_summary_missing_or_empty"],
        )

        CorrelationEngine().correlate(case)
        routing = next(
            hypothesis
            for hypothesis in case.hypotheses
            if hypothesis.title == HYP_MISSING_DIAL_PEER_TITLE
        )

        assert routing.confidence == 92.0
        assert any(
            item.rule_id == "routing_evidence_missing_dial_peer"
            for item in case.correlation_results
        )

    def test_488_codec_signal_without_confidence_boost(self) -> None:
        case = _case_with_hypotheses("CASE-CODEC", ["sip_488_detected"])

        summary = CorrelationEngine().correlate(case)
        codec = next(
            hypothesis for hypothesis in case.hypotheses if hypothesis.title == HYP_CODEC_TITLE
        )

        assert codec.confidence == 82.0
        correlation = next(
            item for item in summary.correlations if item.rule_id == "codec_negotiation_failure_signal"
        )
        assert correlation.confidence_delta == 0.0


class TestRuntimeCorrelateCase:
    def test_correlate_case_requires_investigation_state(self, runtime_engine: RuntimeEngine) -> None:
        turn = runtime_engine.start_investigation("VP-CUBE-0001")

        with pytest.raises(InvalidInvestigationStateError):
            runtime_engine.correlate_case(turn.case_id)
