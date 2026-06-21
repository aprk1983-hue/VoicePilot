"""Investigation session exceptions."""

from __future__ import annotations

from runtime.exceptions import VoicePilotRuntimeError


class SessionNotFoundError(VoicePilotRuntimeError):
    """Raised when a session ID is not registered."""

    def __init__(self, session_id: str) -> None:
        super().__init__(f"Investigation session not found: {session_id}")
        self.session_id = session_id


class InvalidSessionStateError(VoicePilotRuntimeError):
    """Raised when a session operation is invalid for the current status."""

    def __init__(self, session_id: str, message: str) -> None:
        super().__init__(f"Session {session_id}: {message}")
        self.session_id = session_id
