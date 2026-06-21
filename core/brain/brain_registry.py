"""In-memory Brain session registry."""

from __future__ import annotations

from brain.brain_exceptions import BrainSessionNotFoundError, DuplicateBrainSessionError
from brain.brain_models import BrainSession


class BrainRegistry:
    """Store and retrieve Brain sessions in memory."""

    def __init__(self) -> None:
        self._sessions: dict[str, BrainSession] = {}

    def create_session(self, session: BrainSession) -> BrainSession:
        """Register a new Brain session, preventing duplicate IDs."""
        if session.session_id in self._sessions:
            raise DuplicateBrainSessionError(session.session_id)
        self._sessions[session.session_id] = session
        return session

    def register_session(self, session: BrainSession) -> BrainSession:
        """Register or replace a Brain session (used when restoring persisted sessions)."""
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> BrainSession:
        """Return a Brain session by ID."""
        session = self._sessions.get(session_id)
        if session is None:
            raise BrainSessionNotFoundError(session_id)
        return session

    def save_session(self, session: BrainSession) -> BrainSession:
        """Replace an existing Brain session."""
        if session.session_id not in self._sessions:
            raise BrainSessionNotFoundError(session.session_id)
        self._sessions[session.session_id] = session
        return session

    def list_sessions(self) -> tuple[BrainSession, ...]:
        """Return all Brain sessions in deterministic order."""
        return tuple(self._sessions[session_id] for session_id in sorted(self._sessions))

    def remove_session(self, session_id: str) -> None:
        """Remove a Brain session from the registry."""
        if session_id not in self._sessions:
            raise BrainSessionNotFoundError(session_id)
        del self._sessions[session_id]
