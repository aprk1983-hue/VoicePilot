"""Bootstrap helpers for the VoicePilot Brain."""

from __future__ import annotations

from typing import TYPE_CHECKING

from brain.brain_engine import BrainEngine
from brain.brain_registry import BrainRegistry

if TYPE_CHECKING:
    from runtime.runtime_engine import RuntimeEngine


def default_brain_engine(runtime: RuntimeEngine) -> BrainEngine:
    """Create a Brain engine with default in-memory dependencies."""
    return BrainEngine(runtime, registry=BrainRegistry())
