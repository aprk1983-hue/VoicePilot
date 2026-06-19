"""Application use cases — orchestration layer skeleton."""

from __future__ import annotations

from application.commands import (
    CreateCaseCommand,
    LoadPlaybookCommand,
    TransitionCaseStateCommand,
    UpdateCaseCommand,
)
from application.queries import (
    GetAllowedTransitionsQuery,
    GetCaseQuery,
    GetCaseStateQuery,
    ListCasesQuery,
)
from domain.enums import InvestigationState
from domain.models import Case, Playbook
from runtime.case_manager import CaseManager
from runtime.playbook_loader import PlaybookLoader
from runtime.state_machine import InvestigationStateMachine
from shared.types import CaseId


class CreateCaseUseCase:
    """Create a new investigation case."""

    def __init__(self, case_manager: CaseManager) -> None:
        self._case_manager = case_manager

    def execute(self, command: CreateCaseCommand) -> Case:
        """Execute case creation."""
        return self._case_manager.create_case(command.intake)


class GetCaseUseCase:
    """Retrieve a case by id."""

    def __init__(self, case_manager: CaseManager) -> None:
        self._case_manager = case_manager

    def execute(self, query: GetCaseQuery) -> Case:
        return self._case_manager.load_case(query.case_id)


class TransitionCaseStateUseCase:
    """Transition investigation lifecycle state."""

    def __init__(self, case_manager: CaseManager) -> None:
        self._case_manager = case_manager

    def execute(self, command: TransitionCaseStateCommand) -> Case:
        return self._case_manager.transition_state(
            command.case_id,
            command.to_state,
            actor=command.actor,
        )


class UpdateCaseUseCase:
    """Update case fields."""

    def __init__(self, case_manager: CaseManager) -> None:
        self._case_manager = case_manager

    def execute(self, command: UpdateCaseCommand) -> Case:
        return self._case_manager.update_case(command.case_id, **command.fields)


class LoadPlaybookUseCase:
    """Load a DSL playbook file."""

    def __init__(self, playbook_loader: PlaybookLoader) -> None:
        self._playbook_loader = playbook_loader

    def execute(self, command: LoadPlaybookCommand) -> Playbook:
        return self._playbook_loader.load(command.path)


class GetCaseStateUseCase:
    """Return current investigation state."""

    def __init__(self, case_manager: CaseManager) -> None:
        self._case_manager = case_manager

    def execute(self, query: GetCaseStateQuery) -> InvestigationState:
        return self._case_manager.get_investigation_state(query.case_id)


class ListCasesUseCase:
    """List known case ids."""

    def __init__(self, case_manager: CaseManager) -> None:
        self._case_manager = case_manager

    def execute(self, query: ListCasesQuery) -> list[CaseId]:
        return self._case_manager.list_cases()


class GetAllowedTransitionsUseCase:
    """Return structurally allowed transitions."""

    def __init__(self, state_machine: InvestigationStateMachine) -> None:
        self._state_machine = state_machine

    def execute(self, query: GetAllowedTransitionsQuery) -> frozenset[InvestigationState]:
        return self._state_machine.allowed_transitions(query.from_state)
