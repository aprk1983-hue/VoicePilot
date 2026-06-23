"""FastAPI dependency injection for VoicePilot services."""

from __future__ import annotations

from functools import lru_cache

from services import VoicePilotService


@lru_cache
def get_voicepilot_service() -> VoicePilotService:
    """Return the process-wide VoicePilot service facade."""
    return VoicePilotService()
