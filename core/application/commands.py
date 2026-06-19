"""Application commands (write-side intent objects)."""

from __future__ import annotations

from dataclasses import dataclass

from domain.enums import InvestigationState
from domain.value_objects import CaseIntake
from pathlib import Path


@dataclass(frozen=True)
class CreateCaseCommand:
    """Command to open a new investigation case."""

    intake: CaseIntake


@dataclass(frozen=True)
class TransitionCaseStateCommand:
    """Command to transition case lifecycle state."""

    case_id: str
    to_state: InvestigationState
    actor: str = "runtime"


@dataclass(frozen=True)
class LoadPlaybookCommand:
    """Command to load a DSL playbook from disk."""

    path: Path


@dataclass(frozen=True)
class UpdateCaseCommand:
    """Command to update case scalar fields."""

    case_id: str
    fields: dict[str, object]
