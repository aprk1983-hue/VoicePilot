"""Tests for the interactive investigation session engine."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from cli.voicepilot_cli import run_continue_session, run_investigation, run_session_status
from domain.enums import InvestigationState
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from investigation import (
    InvestigationSessionRegistry,
    InvestigationSessionStatus,
    SessionActionType,
    SessionNotFoundError,
)
from investigation.session_models import InvestigationSession
from investigation.session_state_machine import InvestigationSessionStateMachine
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry
from runtime.report_engine import build_incident_report, format_incident_report
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
EVIDENCE_INPUTS = [
    "dial-peer 1 voip up",
    "END",
    "SIP UAS registered",
    "END",
    "voice service voip",
    " sip",
    "END",
    "SIP/2.0 404 Not Found",
    "END",
]
FULL_INPUTS = INTAKE_ANSWERS + EVIDENCE_INPUTS


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


class TestInvestigationSessionModels:
    def test_investigation_session_is_immutable(self) -> None:
        from datetime import datetime, timezone

        session = InvestigationSession(
            session_id="SES-test",
            case_id="CASE-test",
            playbook_id=PLAYBOOK_ID,
            status=InvestigationSessionStatus.ACTIVE,
            current_action=SessionActionType.INTAKE_QUESTION,
            case_state=InvestigationState.INTAKE,
            turn_number=1,
            journey=(),
            started_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        with pytest.raises(FrozenInstanceError):
            session.status = InvestigationSessionStatus.COMPLETED  # type: ignore[misc]


class TestInvestigationSessionRegistry:
    def test_get_raises_for_missing_session(self) -> None:
        registry = InvestigationSessionRegistry()
        with pytest.raises(SessionNotFoundError):
            registry.get("SES-missing")

    def test_register_and_get_round_trip(self) -> None:
        from datetime import datetime, timezone

        registry = InvestigationSessionRegistry()
        session = InvestigationSession(
            session_id="SES-test",
            case_id="CASE-test",
            playbook_id=PLAYBOOK_ID,
            status=InvestigationSessionStatus.ACTIVE,
            current_action=SessionActionType.INTAKE_QUESTION,
            case_state=InvestigationState.INTAKE,
            turn_number=1,
            journey=(),
            started_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        registry.register(session)
        assert registry.get("SES-test") is session


class TestInvestigationSessionStateMachine:
    def test_auto_actions_do_not_require_input(self) -> None:
        machine = InvestigationSessionStateMachine()
        assert machine.can_auto_advance(SessionActionType.DISCOVERY_PLANNING)
        assert not machine.requires_input(SessionActionType.DISCOVERY_PLANNING)

    def test_input_actions_require_input(self) -> None:
        machine = InvestigationSessionStateMachine()
        assert machine.requires_input(SessionActionType.INTAKE_QUESTION)
        assert machine.requires_input(SessionActionType.COLLECT_EVIDENCE)


class TestInvestigationSessionEngine:
    def test_start_session_registers_case_journey(self, runtime_engine: RuntimeEngine) -> None:
        session = runtime_engine.start_investigation_session(PLAYBOOK_ID)

        assert session.session_id.startswith("SES-")
        assert session.playbook_id == PLAYBOOK_ID
        assert session.current_action == SessionActionType.INTAKE_QUESTION
        assert len(session.journey) == 1

        case = runtime_engine.case_manager.load_case(session.case_id)
        assert case.metadata["investigation_session"]["session_id"] == session.session_id

    def test_continue_presents_intake_question(self, runtime_engine: RuntimeEngine) -> None:
        session = runtime_engine.start_investigation_session(PLAYBOOK_ID)
        result = runtime_engine.continue_investigation_session(session.session_id)

        assert result.session.status == InvestigationSessionStatus.AWAITING_INPUT
        assert result.session.pending_question_id is not None
        assert any("[Q-INT-001]" in message for message in result.messages)

    def test_full_session_reaches_investigation_state(self, runtime_engine: RuntimeEngine) -> None:
        answers = iter(FULL_INPUTS)
        session = runtime_engine.start_investigation_session(PLAYBOOK_ID)

        while session.status not in {
            InvestigationSessionStatus.COMPLETED,
            InvestigationSessionStatus.FAILED,
        }:
            if session.status == InvestigationSessionStatus.AWAITING_INPUT:
                result = runtime_engine.continue_investigation_session(
                    session.session_id,
                    input_provider=lambda: next(answers),
                )
            else:
                result = runtime_engine.continue_investigation_session(session.session_id)
            session = result.session

        case = runtime_engine.case_manager.load_case(session.case_id)
        assert case.status == InvestigationState.INVESTIGATION
        assert case.discovery_plan is not None
        assert case.investigation_quality_report is not None
        assert len(case.evidence) == 4
        assert any(
            entry.action == SessionActionType.QUALITY_EVALUATION for entry in session.journey
        )

    def test_format_session_status_includes_journey(self, runtime_engine: RuntimeEngine) -> None:
        session = runtime_engine.start_investigation_session(PLAYBOOK_ID)
        runtime_engine.continue_investigation_session(session.session_id)
        text = runtime_engine.format_investigation_session_status(session.session_id)

        assert "Investigation Session Status" in text
        assert session.session_id in text
        assert "Journey" in text


class TestInvestigationSessionRuntimeIntegration:
    def test_run_investigation_uses_session_engine(self, runtime_engine: RuntimeEngine) -> None:
        output: list[str] = []
        answers = iter(FULL_INPUTS)

        code = run_investigation(
            PLAYBOOK_ID,
            input_provider=lambda: next(answers),
            output_writer=output.append,
            engine=runtime_engine,
        )

        text = "\n".join(output)
        assert code == 0
        assert "Session:  SES-" in text
        assert "Intake complete. Next phase: DISCOVERY." in text
        assert "Discovery plan generated." in text
        assert "Investigation quality evaluated." in text
        assert "Correlation complete." in text

    def test_status_and_continue_with_shared_engine(self, runtime_engine: RuntimeEngine) -> None:
        session = runtime_engine.start_investigation_session(PLAYBOOK_ID)
        runtime_engine.continue_investigation_session(session.session_id)

        status_output: list[str] = []
        assert (
            run_session_status(
                session.session_id,
                status_output.append,
                engine=runtime_engine,
            )
            == 0
        )
        assert "AWAITING_INPUT" in "\n".join(status_output)

        answers = iter(INTAKE_ANSWERS)
        continue_output: list[str] = []
        assert (
            run_continue_session(
                session.session_id,
                input_provider=lambda: next(answers),
                output_writer=continue_output.append,
                engine=runtime_engine,
            )
            == 0
        )
        assert any("[Q-INT-002]" in line for line in continue_output)


class TestInvestigationJourneyReport:
    def test_closed_case_report_includes_journey_section(
        self, runtime_engine: RuntimeEngine
    ) -> None:
        answers = iter(FULL_INPUTS)
        session = runtime_engine.start_investigation_session(PLAYBOOK_ID)

        while session.status not in {
            InvestigationSessionStatus.COMPLETED,
            InvestigationSessionStatus.FAILED,
        }:
            if session.status == InvestigationSessionStatus.AWAITING_INPUT:
                result = runtime_engine.continue_investigation_session(
                    session.session_id,
                    input_provider=lambda: next(answers),
                )
            else:
                result = runtime_engine.continue_investigation_session(session.session_id)
            session = result.session

        case = runtime_engine.case_manager.load_case(session.case_id)
        case.status = InvestigationState.CLOSED
        report = build_incident_report(case)
        markdown = format_incident_report(report)

        assert report.investigation_journey.available is True
        assert report.investigation_journey.session_id == session.session_id
        assert "## Investigation Journey" in markdown
        assert "discovery_planning" in markdown

    def test_report_without_session_shows_placeholder(self) -> None:
        from domain.enums import Severity
        from domain.models import Case
        from domain.value_objects import AffectedScope, PlatformRef, SymptomSummary

        case = Case.create(
            title="Test",
            symptom=SymptomSummary(summary="test"),
            severity=Severity.LOW,
            business_impact="test",
            affected_scope=AffectedScope(),
            platform=PlatformRef(vendor="cisco", products=("CUBE",)),
        )
        case.status = InvestigationState.CLOSED
        report = build_incident_report(case)
        markdown = format_incident_report(report)

        assert report.investigation_journey.available is False
        assert "_No investigation session recorded._" in markdown
