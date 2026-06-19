"""Tests for InvestigationStateMachine."""

from __future__ import annotations

import pytest

from domain.enums import InvestigationState
from runtime.exceptions import InvalidStateTransitionError
from runtime.state_machine import InvestigationStateMachine


class TestInvestigationStateMachine:
    @pytest.fixture
    def state_machine(self) -> InvestigationStateMachine:
        return InvestigationStateMachine()

    def test_new_to_intake_allowed(self, state_machine) -> None:
        assert state_machine.can_transition(InvestigationState.NEW, InvestigationState.INTAKE)

    def test_new_to_closed_not_allowed(self, state_machine) -> None:
        assert not state_machine.can_transition(InvestigationState.NEW, InvestigationState.CLOSED)

    def test_closed_has_no_outbound_transitions(self, state_machine) -> None:
        assert state_machine.allowed_transitions(InvestigationState.CLOSED) == frozenset()

    def test_investigation_to_resolution_allowed(self, state_machine) -> None:
        assert state_machine.can_transition(
            InvestigationState.INVESTIGATION,
            InvestigationState.RESOLUTION,
        )

    def test_validate_transition_raises_on_invalid(self, state_machine) -> None:
        with pytest.raises(InvalidStateTransitionError):
            state_machine.validate_transition(InvestigationState.NEW, InvestigationState.RESOLUTION)

    def test_same_state_transition_allowed(self, state_machine) -> None:
        assert state_machine.can_transition(InvestigationState.INTAKE, InvestigationState.INTAKE)

    @pytest.mark.parametrize(
        ("from_state", "expected_targets"),
        [
            (InvestigationState.NEW, {InvestigationState.INTAKE}),
            (InvestigationState.LEARNING, {InvestigationState.CLOSED}),
        ],
    )
    def test_allowed_transitions(
        self,
        state_machine,
        from_state: InvestigationState,
        expected_targets: set[InvestigationState],
    ) -> None:
        assert state_machine.allowed_transitions(from_state) == frozenset(expected_targets)
