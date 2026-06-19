"""Investigation lifecycle state machine — transition validation only."""

from __future__ import annotations

from domain.enums import InvestigationState
from domain.interfaces import StateMachinePort
from runtime.exceptions import InvalidStateTransitionError


# Allowed transitions aligned with brain/state-machine specification.
_ALLOWED_TRANSITIONS: dict[InvestigationState, frozenset[InvestigationState]] = {
    InvestigationState.NEW: frozenset({InvestigationState.INTAKE}),
    InvestigationState.INTAKE: frozenset(
        {InvestigationState.DISCOVERY, InvestigationState.TOPOLOGY}
    ),
    InvestigationState.DISCOVERY: frozenset(
        {InvestigationState.TOPOLOGY, InvestigationState.COLLECTION}
    ),
    InvestigationState.TOPOLOGY: frozenset(
        {InvestigationState.COLLECTION, InvestigationState.DISCOVERY}
    ),
    InvestigationState.COLLECTION: frozenset(
        {InvestigationState.ANALYSIS, InvestigationState.TOPOLOGY}
    ),
    InvestigationState.ANALYSIS: frozenset(
        {InvestigationState.HYPOTHESIS, InvestigationState.COLLECTION}
    ),
    InvestigationState.HYPOTHESIS: frozenset(
        {InvestigationState.INVESTIGATION, InvestigationState.COLLECTION}
    ),
    InvestigationState.INVESTIGATION: frozenset(
        {
            InvestigationState.HYPOTHESIS,
            InvestigationState.COLLECTION,
            InvestigationState.RESOLUTION,
        }
    ),
    InvestigationState.RESOLUTION: frozenset(
        {InvestigationState.VERIFICATION, InvestigationState.INVESTIGATION}
    ),
    InvestigationState.VERIFICATION: frozenset(
        {InvestigationState.LEARNING, InvestigationState.RESOLUTION}
    ),
    InvestigationState.LEARNING: frozenset({InvestigationState.CLOSED}),
    InvestigationState.CLOSED: frozenset(),
}


class InvestigationStateMachine(StateMachinePort):
    """Validates investigation lifecycle transitions.

    Gate conditions (confidence, evidence) are enforced by engines in future sprints.
    This class validates structural transitions only.
    """

    def can_transition(
        self,
        from_state: InvestigationState,
        to_state: InvestigationState,
    ) -> bool:
        """Return whether ``to_state`` is allowed from ``from_state``."""
        if from_state == to_state:
            return True
        return to_state in self._allowed(from_state)

    def allowed_transitions(self, from_state: InvestigationState) -> frozenset[InvestigationState]:
        """Return valid target states from ``from_state``."""
        return self._allowed(from_state)

    def validate_transition(
        self,
        from_state: InvestigationState,
        to_state: InvestigationState,
    ) -> None:
        """Raise ``InvalidStateTransitionError`` if transition is not allowed."""
        if not self.can_transition(from_state, to_state):
            raise InvalidStateTransitionError(from_state.value, to_state.value)

    @staticmethod
    def _allowed(from_state: InvestigationState) -> frozenset[InvestigationState]:
        return _ALLOWED_TRANSITIONS.get(from_state, frozenset())
