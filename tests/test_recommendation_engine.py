"""Tests for deterministic recommendation engine."""

from __future__ import annotations

from pathlib import Path

import pytest

from domain.enums import InvestigationState, Severity
from domain.models import AnalysisFinding, Case, Hypothesis
from domain.value_objects import AffectedScope, PlatformRef, SymptomSummary
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.evidence_collection import initialize_evidence_collection, submit_evidence
from runtime.hypothesis_engine import VP_CUBE_0001_PLAYBOOK_ID
from runtime.recommendation_engine import (
    ACTION_LIKELY_ROOT_CAUSE,
    ACTION_NEXT_BEST,
    RecommendationEngine,
)
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


def _case_in_investigation(
    runtime_engine: RuntimeEngine,
    *,
    dial_peer_output: str,
    sip_ua_output: str,
    debug_output: str,
) -> Case:
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
        dial_peer_output,
    )
    case = runtime_engine.case_manager.load_case(case.case_id)
    submit_evidence(
        case,
        runtime_engine.case_manager,
        "show sip-ua status",
        sip_ua_output,
    )
    case = runtime_engine.case_manager.load_case(case.case_id)
    submit_evidence(
        case,
        runtime_engine.case_manager,
        "debug ccsip messages",
        debug_output,
    )
    case = runtime_engine.case_manager.load_case(case.case_id)
    runtime_engine.analyze_case(case.case_id)
    runtime_engine.generate_hypotheses(case.case_id)
    return runtime_engine.case_manager.load_case(case.case_id)


class TestRecommendationEngine:
    def test_high_confidence_sip_ua_disabled_moves_to_resolution(
        self, runtime_engine: RuntimeEngine
    ) -> None:
        case = _case_in_investigation(
            runtime_engine,
            dial_peer_output="dial-peer 1 voip up",
            sip_ua_output="SIP-UA Status: disabled",
            debug_output="SIP/2.0 503 Service Unavailable",
        )

        summary = runtime_engine.generate_recommendation(case.case_id)
        updated = runtime_engine.case_manager.load_case(case.case_id)

        assert summary.recommendation_type == ACTION_LIKELY_ROOT_CAUSE
        assert summary.likely_root_cause == "CUBE SIP user agent disabled"
        assert updated.status == InvestigationState.RESOLUTION
        assert len(updated.recommendations) == 1
        assert updated.recommendations[0].action_type == ACTION_LIKELY_ROOT_CAUSE

    def test_low_confidence_provider_issue_stays_in_investigation(
        self, runtime_engine: RuntimeEngine
    ) -> None:
        case = _case_in_investigation(
            runtime_engine,
            dial_peer_output="dial-peer 1 voip up",
            sip_ua_output="SIP User Agent Status: enabled",
            debug_output="From: a\nTo: b\nCall-ID: c\nSIP/2.0 503 Service Unavailable",
        )

        summary = runtime_engine.generate_recommendation(case.case_id)
        updated = runtime_engine.case_manager.load_case(case.case_id)

        assert summary.recommendation_type == ACTION_NEXT_BEST
        assert updated.status == InvestigationState.INVESTIGATION
        assert "Provider or SIP trunk service issue" in summary.description

    def test_routing_issue_recommends_dial_peer_config_collection(
        self, runtime_engine: RuntimeEngine
    ) -> None:
        case = _case_in_investigation(
            runtime_engine,
            dial_peer_output="dial-peer 1 voip up\n destination-pattern 9T",
            sip_ua_output="SIP User Agent Status: enabled",
            debug_output="SIP/2.0 404 Not Found",
        )

        recommendation = RecommendationEngine().generate(case)

        assert recommendation.action_type == ACTION_NEXT_BEST
        assert recommendation.command == "show run | sec dial-peer"
        assert any("dial-peer" in action.lower() for action in recommendation.recommended_actions)

    def test_recommendation_includes_verification_steps(self) -> None:
        case = Case(
            case_id="CASE-REC",
            title="test",
            status=InvestigationState.INVESTIGATION,
            severity=Severity.HIGH,
            business_impact="test",
            symptom=SymptomSummary(summary="test"),
            affected_scope=AffectedScope(),
            platform=PlatformRef(vendor="cisco"),
            playbook_id=VP_CUBE_0001_PLAYBOOK_ID,
        )
        case.hypotheses = [
            Hypothesis.create(
                case_id=case.case_id,
                title="CUBE SIP user agent disabled",
                confidence=90.0,
                supporting_finding_ids=[],
                category="HYP-SIP-UA-DISABLED",
                rank=1,
            )
        ]

        recommendation = RecommendationEngine().generate(case)

        assert recommendation.verification_steps
        assert any("show sip-ua status" in step for step in recommendation.verification_steps)
