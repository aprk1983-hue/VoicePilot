"""Knowledge severity levels for VKF packs."""

from __future__ import annotations

from enum import Enum


class KnowledgeSeverity(str, Enum):
    """Severity assigned to a knowledge pack."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
