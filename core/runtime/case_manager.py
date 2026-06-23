"""Case aggregate lifecycle management."""

from __future__ import annotations

from typing import Any

from domain.enums import InvestigationState
from domain.events import CaseCreatedEvent, CaseStateChangedEvent, CaseUpdatedEvent
from domain.interfaces import CaseRepository, EventBusPort, LoggerPort, StateMachinePort
from domain.models import Case
from domain.value_objects import CaseIntake
from runtime.event_bus import EventBus
from runtime.exceptions import CaseNotFoundError, InvalidStateTransitionError
from runtime.state_machine import InvestigationStateMachine
from shared.types import CaseId


class CaseManager:
    """Manages investigation case aggregates.

    Responsibilities: create, load, save, update, track state, publish events.
    Business rules are deferred to future engine integration.
    """

    def __init__(
        self,
        repository: CaseRepository,
        state_machine: StateMachinePort | None = None,
        event_bus: EventBusPort | None = None,
        logger: LoggerPort | None = None,
    ) -> None:
        self._repository = repository
        self._state_machine = state_machine or InvestigationStateMachine()
        self._event_bus = event_bus or EventBus()
        self._logger = logger
        self._cases: dict[CaseId, Case] = {}

    def create_case(self, intake: CaseIntake) -> Case:
        """Create a new case in ``NEW`` state and persist it."""
        case = Case.create(
            title=intake.title,
            symptom=intake.symptom,
            severity=intake.severity,
            business_impact=intake.business_impact,
            affected_scope=intake.affected_scope,
            platform=intake.platform,
            playbook_id=intake.playbook_id,
            assigned_engineer=intake.assigned_engineer,
            metadata=intake.metadata or {},
        )
        self._cases[case.case_id] = case
        self.save_case(case)

        if self._logger:
            self._logger.info("Case created", case_id=case.case_id, title=case.title)

        self._event_bus.publish(CaseCreatedEvent.from_case(case.case_id, case.title))
        return case

    def load_case(self, case_id: CaseId) -> Case:
        """Load a case from memory or repository."""
        if case_id in self._cases:
            return self._cases[case_id]

        try:
            case = self._repository.load(case_id)
        except Exception as exc:
            raise CaseNotFoundError(case_id) from exc

        self._cases[case_id] = case
        if self._logger:
            self._logger.debug("Case loaded", case_id=case_id)
        return case

    def save_case(self, case: Case) -> None:
        """Persist the case aggregate."""
        # TODO: Implement repository serialization in infrastructure sprint.
        self._cases[case.case_id] = case
        try:
            self._repository.save(case)
        except Exception:
            # In-memory fallback until filesystem repository is complete.
            pass

    def update_case(self, case_id: CaseId, **fields: Any) -> Case:
        """Update allowed scalar fields on a case and publish update event."""
        case = self.load_case(case_id)
        changed: list[str] = []

        for key, value in fields.items():
            if hasattr(case, key) and key not in {"case_id", "opened_at"}:
                setattr(case, key, value)
                changed.append(key)

        if changed:
            self.save_case(case)
            self._event_bus.publish(CaseUpdatedEvent.from_update(case_id, changed))
            if self._logger:
                self._logger.debug("Case updated", case_id=case_id, fields=changed)

        return case

    def transition_state(
        self,
        case_id: CaseId,
        to_state: InvestigationState,
        actor: str = "runtime",
    ) -> Case:
        """Validate and apply a lifecycle state transition."""
        case = self.load_case(case_id)
        from_state = case.status

        try:
            self._state_machine.validate_transition(from_state, to_state)
        except InvalidStateTransitionError:
            raise

        case.status = to_state
        self.save_case(case)

        self._event_bus.publish(
            CaseStateChangedEvent.create_transition(case_id, from_state, to_state, actor)
        )
        if self._logger:
            self._logger.info(
                "Case state changed",
                case_id=case_id,
                from_state=from_state.value,
                to_state=to_state.value,
            )
        return case

    def get_investigation_state(self, case_id: CaseId) -> InvestigationState:
        """Return current investigation lifecycle state."""
        return self.load_case(case_id).status

    def list_cases(self) -> list[CaseId]:
        """Return identifiers of cases held in memory."""
        return list(self._cases.keys())

    def delete_case(self, case_id: CaseId) -> None:
        """Remove a case from memory and the repository."""
        self.load_case(case_id)
        self._cases.pop(case_id, None)
        delete = getattr(self._repository, "delete", None)
        if callable(delete):
            delete(case_id)
        if self._logger:
            self._logger.info("Case deleted", case_id=case_id)
