"""Tests for the VoicePilot Brain orchestration engine."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path

import pytest

from brain import (
    BrainRegistry,
    BrainSession,
    BrainSessionNotFoundError,
    BrainStage,
    DuplicateBrainSessionError,
    build_investigation_replay,
    format_brain_replay,
    format_brain_status,
)
from cli.voicepilot_cli import run_brain_list, run_brain_replay, run_brain_start, run_brain_status
from domain.enums import DomainEventType, InvestigationState
from domain.events import DomainEvent
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.evidence_collection import submit_evidence
from runtime.exceptions import PlaybookIdNotFoundError
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry
from runtime.runtime_engine import RuntimeEngine
from shared.config import RuntimeConfig

PLUGINS_ROOT = Path(__file__).resolve().parents[1] / "plugins"
PLAYBOOK_ID = "VP-CUBE-0001"
RESOLUTION_EVIDENCE = (
    ("show dial-peer voice summary", "dial-peer 1 voip up"),
    ("show sip-ua status", "SIP-UA Status: disabled"),
    ("show run | sec voice service voip", "voice service voip\n no sip\n"),
    ("debug ccsip messages", "SIP/2.0 503 Service Unavailable"),
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


def _submit_resolution_evidence(runtime: RuntimeEngine, case_id: str) -> None:
    case = runtime.case_manager.load_case(case_id)
    for command, raw_text in RESOLUTION_EVIDENCE:
        submit_evidence(
            case,
            runtime.case_manager,
            command,
            raw_text,
            decision_log=runtime.decision_log_engine,
        )
        case = runtime.case_manager.load_case(case_id)


class TestBrainModels:
    def test_brain_session_is_immutable(self) -> None:
        session = BrainSession(
            session_id="BRN-test",
            case_id="CASE-test",
            playbook=PLAYBOOK_ID,
            current_stage=BrainStage.WAITING_FOR_EVIDENCE,
            started_at=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
            current_confidence=None,
            current_quality_score=None,
            completed=False,
            failed=False,
            decision_log_ids=(),
        )

        with pytest.raises(FrozenInstanceError):
            session.completed = True  # type: ignore[misc]


class TestBrainRegistry:
    def test_duplicate_session_rejection(self) -> None:
        registry = BrainRegistry()
        now = datetime.now(timezone.utc)
        session = BrainSession(
            session_id="BRN-dup",
            case_id="CASE-dup",
            playbook=PLAYBOOK_ID,
            current_stage=BrainStage.WAITING_FOR_EVIDENCE,
            started_at=now,
            last_updated=now,
            current_confidence=None,
            current_quality_score=None,
            completed=False,
            failed=False,
            decision_log_ids=(),
        )
        registry.create_session(session)
        with pytest.raises(DuplicateBrainSessionError):
            registry.create_session(session)

    def test_remove_session(self) -> None:
        registry = BrainRegistry()
        now = datetime.now(timezone.utc)
        session = BrainSession(
            session_id="BRN-remove",
            case_id="CASE-remove",
            playbook=PLAYBOOK_ID,
            current_stage=BrainStage.WAITING_FOR_EVIDENCE,
            started_at=now,
            last_updated=now,
            current_confidence=None,
            current_quality_score=None,
            completed=False,
            failed=False,
            decision_log_ids=(),
        )
        registry.create_session(session)
        registry.remove_session("BRN-remove")
        with pytest.raises(BrainSessionNotFoundError):
            registry.get_session("BRN-remove")


class TestBrainEngine:
    def test_start_session_waits_for_evidence(self, runtime_engine: RuntimeEngine) -> None:
        session = runtime_engine.start_brain_session(PLAYBOOK_ID)

        assert session.session_id.startswith("BRN-")
        assert session.current_stage == BrainStage.WAITING_FOR_EVIDENCE
        assert session.completed is False

        case = runtime_engine.case_manager.load_case(session.case_id)
        assert case.metadata["brain_session"]["session_id"] == session.session_id

    def test_advance_without_evidence_stays_waiting(self, runtime_engine: RuntimeEngine) -> None:
        session = runtime_engine.start_brain_session(PLAYBOOK_ID)
        result = runtime_engine.advance_brain_session(session.session_id)

        assert result.session.current_stage == BrainStage.WAITING_FOR_EVIDENCE
        assert result.messages

    def test_advance_runs_pipeline_to_complete(self, runtime_engine: RuntimeEngine) -> None:
        session = runtime_engine.start_brain_session(PLAYBOOK_ID)
        _submit_resolution_evidence(runtime_engine, session.case_id)

        result = runtime_engine.advance_brain_session(session.session_id)
        updated = result.session

        assert updated.completed is True
        assert updated.current_stage == BrainStage.COMPLETE
        assert updated.current_quality_score == 100

        case = runtime_engine.case_manager.load_case(session.case_id)
        assert case.status == InvestigationState.CLOSED
        assert case.discovery_plan is not None
        assert case.investigation_quality_report is not None
        assert case.recommendations

    def test_build_context_exposes_reports(self, runtime_engine: RuntimeEngine) -> None:
        session = runtime_engine.start_brain_session(PLAYBOOK_ID)
        _submit_resolution_evidence(runtime_engine, session.case_id)
        runtime_engine.advance_brain_session(session.session_id)

        context = runtime_engine.brain_engine.build_context(session.session_id)
        assert context.discovery_plan is not None
        assert context.investigation_quality_report is not None
        assert context.hypotheses
        assert context.top_hypothesis is not None

    def test_stage_transitions_record_journey(self, runtime_engine: RuntimeEngine) -> None:
        session = runtime_engine.start_brain_session(PLAYBOOK_ID)
        _submit_resolution_evidence(runtime_engine, session.case_id)
        updated = runtime_engine.advance_brain_session(session.session_id).session

        stages = {entry.stage for entry in updated.journey}
        assert BrainStage.PARSING in stages
        assert BrainStage.DISCOVERY_PLANNING in stages
        assert BrainStage.QUALITY_EVALUATION in stages
        assert BrainStage.COMPLETE in stages

    def test_publishes_brain_events(self, runtime_engine: RuntimeEngine) -> None:
        received: list[DomainEvent] = []

        def handler(event: DomainEvent) -> None:
            received.append(event)

        runtime_engine.event_bus.subscribe(DomainEventType.BRAIN_SESSION_STARTED, handler)
        runtime_engine.event_bus.subscribe(DomainEventType.BRAIN_COMPLETED, handler)

        session = runtime_engine.start_brain_session(PLAYBOOK_ID)
        _submit_resolution_evidence(runtime_engine, session.case_id)
        runtime_engine.advance_brain_session(session.session_id)

        event_types = {event.event_type for event in received}
        assert DomainEventType.BRAIN_SESSION_STARTED in event_types
        assert DomainEventType.BRAIN_COMPLETED in event_types

    def test_start_unknown_playbook_raises(self, runtime_engine: RuntimeEngine) -> None:
        with pytest.raises(PlaybookIdNotFoundError):
            runtime_engine.start_brain_session("VP-DOES-NOT-EXIST")


class TestBrainReplay:
    def test_replay_uses_journey_and_decision_log(self, runtime_engine: RuntimeEngine) -> None:
        session = runtime_engine.start_brain_session(PLAYBOOK_ID)
        _submit_resolution_evidence(runtime_engine, session.case_id)
        updated = runtime_engine.advance_brain_session(session.session_id).session
        context = runtime_engine.brain_engine.build_context(updated.session_id)

        replay = build_investigation_replay(updated, context)
        text = format_brain_replay(updated, context)

        assert replay
        assert "Investigation Replay" in text
        assert "Discovery Plan Generated" in text
        assert "Investigation Closed" in text
        assert "↓" in text


class TestBrainCli:
    def test_brain_start_prints_status(self, runtime_engine: RuntimeEngine) -> None:
        output: list[str] = []
        code = run_brain_start(
            PLAYBOOK_ID,
            output.append,
            engine=runtime_engine,
        )

        assert code == 0
        text = "\n".join(output)
        assert "Brain session started" in text
        assert "Brain Status" in text
        assert "WAITING_FOR_EVIDENCE" in text
        assert "Session:" in text

    def test_brain_status_and_list_with_shared_engine(self, runtime_engine: RuntimeEngine) -> None:
        session = runtime_engine.start_brain_session(PLAYBOOK_ID)

        status_output: list[str] = []
        assert (
            run_brain_status(session.session_id, status_output.append, engine=runtime_engine) == 0
        )
        assert "Next Expected Engine" in "\n".join(status_output)

        list_output: list[str] = []
        assert run_brain_list(list_output.append, engine=runtime_engine) == 0
        assert session.session_id in "\n".join(list_output)

    def test_brain_replay_after_pipeline(self, runtime_engine: RuntimeEngine) -> None:
        session = runtime_engine.start_brain_session(PLAYBOOK_ID)
        _submit_resolution_evidence(runtime_engine, session.case_id)
        runtime_engine.advance_brain_session(session.session_id)

        output: list[str] = []
        assert run_brain_replay(session.session_id, output.append, engine=runtime_engine) == 0
        assert "Investigation Replay" in "\n".join(output)

    def test_brain_status_missing_session_returns_error(self, runtime_engine: RuntimeEngine) -> None:
        output: list[str] = []
        code = run_brain_status("BRN-missing", output.append, engine=runtime_engine)
        assert code == 1
        assert "Brain session not found" in "\n".join(output)

    def test_format_brain_status_shows_hypothesis(self, runtime_engine: RuntimeEngine) -> None:
        session = runtime_engine.start_brain_session(PLAYBOOK_ID)
        _submit_resolution_evidence(runtime_engine, session.case_id)
        updated = runtime_engine.advance_brain_session(session.session_id).session
        context = runtime_engine.brain_engine.build_context(updated.session_id)

        text = format_brain_status(updated, context)
        assert "Current Hypothesis:" in text
        assert "Quality Score:" in text
