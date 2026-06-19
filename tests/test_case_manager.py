"""Tests for CaseManager."""

from __future__ import annotations

import pytest

from domain.enums import DomainEventType, InvestigationState
from domain.events import DomainEvent
from runtime.exceptions import InvalidStateTransitionError


class TestCaseManager:
    def test_create_case_starts_in_new_state(self, case_manager, sample_intake) -> None:
        case = case_manager.create_case(sample_intake)
        assert case.case_id.startswith("CASE-")
        assert case.status == InvestigationState.NEW
        assert case.title == sample_intake.title

    def test_load_case_returns_created_case(self, case_manager, sample_intake) -> None:
        created = case_manager.create_case(sample_intake)
        loaded = case_manager.load_case(created.case_id)
        assert loaded.case_id == created.case_id

    def test_transition_state_updates_status(self, case_manager, sample_intake) -> None:
        case = case_manager.create_case(sample_intake)
        updated = case_manager.transition_state(case.case_id, InvestigationState.INTAKE)
        assert updated.status == InvestigationState.INTAKE

    def test_invalid_transition_raises(self, case_manager, sample_intake) -> None:
        case = case_manager.create_case(sample_intake)
        with pytest.raises(InvalidStateTransitionError):
            case_manager.transition_state(case.case_id, InvestigationState.CLOSED)

    def test_create_case_publishes_event(self, case_manager, sample_intake, event_bus) -> None:
        received: list[DomainEvent] = []
        event_bus.subscribe(DomainEventType.CASE_CREATED, received.append)
        case_manager.create_case(sample_intake)
        assert len(received) == 1
        assert received[0].payload["case_id"]

    def test_update_case_publishes_update_event(self, case_manager, sample_intake, event_bus) -> None:
        received: list[DomainEvent] = []
        event_bus.subscribe(DomainEventType.CASE_UPDATED, received.append)
        case = case_manager.create_case(sample_intake)
        case_manager.update_case(case.case_id, title="Updated title")
        assert len(received) == 1
