"""VoicePilot service layer exceptions."""

from __future__ import annotations


class VoicePilotServiceError(Exception):
    """Base exception for the VoicePilot public service layer."""


class ServiceCaseNotFoundError(VoicePilotServiceError):
    """Raised when a case ID is not registered."""

    def __init__(self, case_id: str) -> None:
        super().__init__(f"Case not found: {case_id}")
        self.case_id = case_id


class ServiceBrainSessionNotFoundError(VoicePilotServiceError):
    """Raised when a Brain session ID is not registered."""

    def __init__(self, session_id: str) -> None:
        super().__init__(f"Brain session not found: {session_id}")
        self.session_id = session_id


class ServicePlaybookNotFoundError(VoicePilotServiceError):
    """Raised when a playbook ID is not in the catalog."""

    def __init__(self, playbook_id: str) -> None:
        super().__init__(f"Playbook not found: {playbook_id}")
        self.playbook_id = playbook_id
