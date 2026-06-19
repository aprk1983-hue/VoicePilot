"""Domain events for the VoicePilot internal event bus."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from domain.enums import DomainEventType, InvestigationState
from shared.types import CaseId, JsonDict


@dataclass(frozen=True)
class DomainEvent:
    """Base immutable domain event."""

    event_id: str
    event_type: DomainEventType
    occurred_at: datetime
    payload: JsonDict = field(default_factory=dict)

    @classmethod
    def create(cls, event_type: DomainEventType, payload: JsonDict | None = None) -> DomainEvent:
        return cls(
            event_id=str(uuid4()),
            event_type=event_type,
            occurred_at=datetime.now(timezone.utc),
            payload=payload or {},
        )


@dataclass(frozen=True)
class CaseCreatedEvent(DomainEvent):
    """Published when a new case is created."""

    case_id: CaseId = ""

    @classmethod
    def from_case(cls, case_id: CaseId, title: str) -> CaseCreatedEvent:
        base = DomainEvent.create(
            DomainEventType.CASE_CREATED,
            {"case_id": case_id, "title": title},
        )
        return cls(
            event_id=base.event_id,
            event_type=base.event_type,
            occurred_at=base.occurred_at,
            payload=base.payload,
            case_id=case_id,
        )


@dataclass(frozen=True)
class CaseStateChangedEvent(DomainEvent):
    """Published when investigation lifecycle state changes."""

    case_id: CaseId = ""
    from_state: InvestigationState | None = None
    to_state: InvestigationState | None = None

    @classmethod
    def create_transition(
        cls,
        case_id: CaseId,
        from_state: InvestigationState,
        to_state: InvestigationState,
        actor: str,
    ) -> CaseStateChangedEvent:
        base = DomainEvent.create(
            DomainEventType.CASE_STATE_CHANGED,
            {
                "case_id": case_id,
                "from_state": from_state.value,
                "to_state": to_state.value,
                "actor": actor,
            },
        )
        return cls(
            event_id=base.event_id,
            event_type=base.event_type,
            occurred_at=base.occurred_at,
            payload=base.payload,
            case_id=case_id,
            from_state=from_state,
            to_state=to_state,
        )


@dataclass(frozen=True)
class CaseUpdatedEvent(DomainEvent):
    """Published when case fields are updated."""

    case_id: CaseId = ""
    fields_changed: tuple[str, ...] = ()

    @classmethod
    def from_update(cls, case_id: CaseId, fields_changed: list[str]) -> CaseUpdatedEvent:
        base = DomainEvent.create(
            DomainEventType.CASE_UPDATED,
            {"case_id": case_id, "fields_changed": fields_changed},
        )
        return cls(
            event_id=base.event_id,
            event_type=base.event_type,
            occurred_at=base.occurred_at,
            payload=base.payload,
            case_id=case_id,
            fields_changed=tuple(fields_changed),
        )


@dataclass(frozen=True)
class PlaybookLoadedEvent(DomainEvent):
    """Published when a DSL playbook is loaded successfully."""

    playbook_id: str = ""
    version: str = ""

    @classmethod
    def from_playbook(cls, playbook_id: str, version: str) -> PlaybookLoadedEvent:
        base = DomainEvent.create(
            DomainEventType.PLAYBOOK_LOADED,
            {"playbook_id": playbook_id, "version": version},
        )
        return cls(
            event_id=base.event_id,
            event_type=base.event_type,
            occurred_at=base.occurred_at,
            payload=base.payload,
            playbook_id=playbook_id,
            version=version,
        )
