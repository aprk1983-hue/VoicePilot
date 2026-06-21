"""In-memory registry for investigation sessions."""

from __future__ import annotations

from investigation.session_models import InvestigationSession
from investigation.session_exceptions import SessionNotFoundError


class InvestigationSessionRegistry:
    """Store and retrieve investigation sessions in memory."""

    def __init__(self) -> None:
        self._sessions: dict[str, InvestigationSession] = {}

    def register(self, session: InvestigationSession) -> None:
        """Register or replace a session."""
        self._sessions[session.session_id] = session

    def get(self, session_id: str) -> InvestigationSession:
        """Return a session by ID."""
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)
        return session

    def save(self, session: InvestigationSession) -> None:
        """Persist an updated session."""
        self.register(session)

    def all_sessions(self) -> tuple[InvestigationSession, ...]:
        """Return all sessions in deterministic order."""
        return tuple(
            self._sessions[session_id]
            for session_id in sorted(self._sessions)
        )
