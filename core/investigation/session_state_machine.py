"""Investigation session state machine."""

from __future__ import annotations

from investigation.session_exceptions import InvalidSessionStateError
from investigation.session_models import (
    InvestigationSessionStatus,
    SessionActionType,
)


class InvestigationSessionStateMachine:
    """Validate session status and action transitions."""

    _AUTO_ACTIONS = frozenset(
        {
            SessionActionType.DISCOVERY_PLANNING,
            SessionActionType.RUN_ANALYSIS,
            SessionActionType.RUN_HYPOTHESIS,
            SessionActionType.RUN_CORRELATION,
            SessionActionType.QUALITY_EVALUATION,
            SessionActionType.RUN_RECOMMENDATION,
            SessionActionType.RUN_CLOSURE,
        }
    )

    _INPUT_ACTIONS = frozenset(
        {
            SessionActionType.INTAKE_QUESTION,
            SessionActionType.COLLECT_EVIDENCE,
            SessionActionType.COLLECT_DISCOVERY_EVIDENCE,
            SessionActionType.RUN_VERIFICATION,
        }
    )

    def can_auto_advance(self, action: SessionActionType) -> bool:
        """Return whether an action runs without user input."""
        return action in self._AUTO_ACTIONS

    def requires_input(self, action: SessionActionType) -> bool:
        """Return whether an action waits for user input."""
        return action in self._INPUT_ACTIONS

    def validate_continue(
        self,
        session_id: str,
        status: InvestigationSessionStatus,
        *,
        has_input: bool,
    ) -> None:
        """Validate that continue is permitted for the session status."""
        if status in {
            InvestigationSessionStatus.COMPLETED,
            InvestigationSessionStatus.FAILED,
        }:
            raise InvalidSessionStateError(session_id, f"session is {status.value}")

        if status == InvestigationSessionStatus.AWAITING_INPUT and not has_input:
            return

        if status == InvestigationSessionStatus.ACTIVE:
            return

    def next_status_for_action(
        self,
        action: SessionActionType,
        *,
        awaiting_input: bool,
        completed: bool = False,
        failed: bool = False,
    ) -> InvestigationSessionStatus:
        """Resolve session status after an action step."""
        if failed:
            return InvestigationSessionStatus.FAILED
        if completed:
            return InvestigationSessionStatus.COMPLETED
        if awaiting_input:
            return InvestigationSessionStatus.AWAITING_INPUT
        if self.can_auto_advance(action):
            return InvestigationSessionStatus.ACTIVE
        return InvestigationSessionStatus.AWAITING_INPUT
