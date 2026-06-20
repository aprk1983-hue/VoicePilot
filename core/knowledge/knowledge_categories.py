"""Knowledge categories for VKF packs."""

from __future__ import annotations

from enum import Enum


class KnowledgeCategory(str, Enum):
    """Vendor-neutral knowledge classification."""

    BEST_PRACTICE = "best_practice"
    BUG = "bug"
    SECURITY = "security"
    DESIGN = "design"
    CONFIGURATION = "configuration"
    PERFORMANCE = "performance"
    COMPATIBILITY = "compatibility"
    LICENSING = "licensing"
    OPERATIONS = "operations"
    GENERAL = "general"
