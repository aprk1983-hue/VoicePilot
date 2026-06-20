"""Tests for deterministic hypothesis engine."""

from __future__ import annotations

from pathlib import Path

import pytest

from domain.enums import HypothesisStatus, InvestigationState, Severity
from domain.models import AnalysisFinding, Case
from domain.value_objects import AffectedScope, PlatformRef, SymptomSummary
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.analysis_engine import AnalysisEngine
from runtime.evidence_collection import initialize_evidence_collection, submit_evidence
from runtime.hypothesis_engine import (
    INSUFFICIENT_EVIDENCE_TITLE,
    HypothesisEngine,
    VP_CUBE_0001_PLAYBOOK_ID,
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


def _case_in_hypothesis(runtime_engine: RuntimeEngine, *, debug_output: str) -> Case:
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
        "show run | sec voice service voip",
        "voice service voip\n sip\n",
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
    return runtime_engine.case_manager.load_case(case.case_id)


def _case_with_signals(case_id: str, signals: list[str]) -> Case:
    case = Case(
        case_id=case_id,
        title="test",
        status=InvestigationState.HYPOTHESIS,
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


class TestHypothesisEngineRules:
    def test_503_creates_provider_hypothesis(self) -> None:
        case = _case_with_signals(
            "CASE-503",
            ["sip_503_detected", "sip_trace_present"],
        )
        hypotheses = HypothesisEngine().generate(case)

        assert any(h.title == "Provider or SIP trunk service issue" for h in hypotheses)
        provider = next(h for h in hypotheses if h.title == "Provider or SIP trunk service issue")
        assert provider.confidence == 75.0

    def test_488_creates_codec_hypothesis(self) -> None:
        case = _case_with_signals("CASE-488", ["sip_488_detected"])
        hypotheses = HypothesisEngine().generate(case)

        assert any(h.title == "Codec / SDP negotiation issue" for h in hypotheses)
        assert next(h for h in hypotheses if h.title == "Codec / SDP negotiation issue").confidence == 82.0

    def test_sip_ua_disabled_creates_high_confidence_hypothesis(self) -> None:
        case = _case_with_signals("CASE-UA", ["sip_ua_disabled"])
        hypotheses = HypothesisEngine().generate(case)

        ua_hypothesis = next(h for h in hypotheses if h.title == "CUBE SIP user agent disabled")
        assert ua_hypothesis.confidence == 90.0
        assert ua_hypothesis.status == HypothesisStatus.CANDIDATE

    def test_no_findings_returns_insufficient_evidence_hypothesis(self) -> None:
        case = _case_with_signals("CASE-EMPTY", [])
        case.analysis_findings = []
        hypotheses = HypothesisEngine().generate(case)

        assert len(hypotheses) == 1
        assert hypotheses[0].title == INSUFFICIENT_EVIDENCE_TITLE
        assert hypotheses[0].confidence == 25.0


class TestGenerateHypotheses:
    def test_generate_hypotheses_transitions_to_investigation(
        self, runtime_engine: RuntimeEngine
    ) -> None:
        case = _case_in_hypothesis(
            runtime_engine,
            debug_output="From: a\nTo: b\nCall-ID: c\nSIP/2.0 503 Service Unavailable",
        )

        summary = runtime_engine.generate_hypotheses(case.case_id)

        updated = runtime_engine.case_manager.load_case(case.case_id)
        assert updated.status == InvestigationState.INVESTIGATION
        assert summary.state == InvestigationState.INVESTIGATION

    def test_hypotheses_are_saved_on_case(self, runtime_engine: RuntimeEngine) -> None:
        case = _case_in_hypothesis(
            runtime_engine,
            debug_output="From: a\nTo: b\nCall-ID: c\nSIP/2.0 503 Service Unavailable",
        )

        runtime_engine.generate_hypotheses(case.case_id)
        updated = runtime_engine.case_manager.load_case(case.case_id)

        assert len(updated.hypotheses) >= 1
        assert any(h.title == "Provider or SIP trunk service issue" for h in updated.hypotheses)
        assert all(h.status == HypothesisStatus.CANDIDATE for h in updated.hypotheses)
