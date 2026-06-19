"""Domain enumerations for VoicePilot investigations."""

from __future__ import annotations

from enum import Enum, auto


class InvestigationState(str, Enum):
    """Lifecycle states for an investigation case."""

    NEW = "NEW"
    INTAKE = "INTAKE"
    DISCOVERY = "DISCOVERY"
    TOPOLOGY = "TOPOLOGY"
    COLLECTION = "COLLECTION"
    ANALYSIS = "ANALYSIS"
    HYPOTHESIS = "HYPOTHESIS"
    INVESTIGATION = "INVESTIGATION"
    RESOLUTION = "RESOLUTION"
    VERIFICATION = "VERIFICATION"
    LEARNING = "LEARNING"
    CLOSED = "CLOSED"


class Severity(str, Enum):
    """Case severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class HypothesisStatus(str, Enum):
    """Status of a hypothesis during investigation."""

    CANDIDATE = "candidate"
    ACTIVE = "active"
    CONFIRMED = "confirmed"
    ELIMINATED = "eliminated"


class EvidenceStatus(str, Enum):
    """Status of a collected evidence artifact."""

    SUBMITTED = "submitted"
    PARSED = "parsed"
    VALIDATED = "validated"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"


class DecisionType(str, Enum):
    """Types of recorded technical decisions."""

    ELIMINATION = "elimination"
    CONFIRMATION = "confirmation"
    STRATEGY = "strategy"
    GATE = "gate"
    WAIVER = "waiver"
    ESCALATION = "escalation"


class QuestionStatus(str, Enum):
    """Status of an investigative question."""

    PENDING = "pending"
    ASKED = "asked"
    ANSWERED = "answered"
    DEFERRED = "deferred"
    WAIVED = "waived"


class RecommendationStatus(str, Enum):
    """Status of a recommended next action."""

    RECOMMENDED = "recommended"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class CostLevel(str, Enum):
    """Operational cost classification for investigative actions."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PlaybookStatus(str, Enum):
    """Publication status of a DSL playbook."""

    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"


class DomainEventType(str, Enum):
    """Internal domain event types published on the event bus."""

    CASE_CREATED = auto()
    CASE_UPDATED = auto()
    CASE_STATE_CHANGED = auto()
    CASE_LOADED = auto()
    CASE_SAVED = auto()
    PLAYBOOK_LOADED = auto()
    ENGINE_REGISTERED = auto()
