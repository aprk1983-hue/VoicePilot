"""Bootstrap helpers for the investigation session framework."""

from __future__ import annotations

from typing import TYPE_CHECKING

from investigation.session_engine import InvestigationSessionEngine
from investigation.session_registry import InvestigationSessionRegistry
from investigation.session_state_machine import InvestigationSessionStateMachine

if TYPE_CHECKING:
    from runtime.runtime_engine import RuntimeEngine


def default_session_engine(runtime: RuntimeEngine) -> InvestigationSessionEngine:
    """Create a session engine with default in-memory dependencies."""
    return InvestigationSessionEngine(
        runtime,
        registry=InvestigationSessionRegistry(),
        state_machine=InvestigationSessionStateMachine(),
    )
