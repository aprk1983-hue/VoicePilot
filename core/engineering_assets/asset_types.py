"""Engineering Asset Framework — vendor-neutral asset type definitions."""

from __future__ import annotations

from enum import Enum


class EngineeringAssetType(str, Enum):
    """Canonical engineering knowledge asset types."""

    INCIDENT = "INCIDENT"
    RUNBOOK = "RUNBOOK"
    BEST_PRACTICE = "BEST_PRACTICE"
    VERIFICATION_GUIDE = "VERIFICATION_GUIDE"
    CONFIGURATION_GUIDE = "CONFIGURATION_GUIDE"
    BUG = "BUG"
    TAC_RESOLUTION = "TAC_RESOLUTION"
    KNOWLEDGE_ARTICLE = "KNOWLEDGE_ARTICLE"
    LAB_VALIDATION = "LAB_VALIDATION"
    SCRIPT = "SCRIPT"
    COMMAND_REFERENCE = "COMMAND_REFERENCE"
    VIDEO = "VIDEO"
    DOCUMENT = "DOCUMENT"
    REFERENCE = "REFERENCE"
    NOTE = "NOTE"
