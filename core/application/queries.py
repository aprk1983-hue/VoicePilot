"""Application queries (read-side intent objects)."""

from __future__ import annotations

from dataclasses import dataclass

from domain.enums import InvestigationState


@dataclass(frozen=True)
class GetCaseQuery:
    """Query a case by identifier."""

    case_id: str


@dataclass(frozen=True)
class GetCaseStateQuery:
    """Query current investigation state for a case."""

    case_id: str


@dataclass(frozen=True)
class ListCasesQuery:
    """List all in-memory case identifiers."""

    pass


@dataclass(frozen=True)
class GetAllowedTransitionsQuery:
    """Query allowed lifecycle transitions from a state."""

    from_state: InvestigationState
