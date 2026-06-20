"""Runtime kernel exceptions."""

from __future__ import annotations


class VoicePilotRuntimeError(Exception):
    """Base exception for runtime kernel errors."""


class CaseNotFoundError(VoicePilotRuntimeError):
    """Raised when a requested case does not exist."""

    def __init__(self, case_id: str) -> None:
        super().__init__(f"Case not found: {case_id}")
        self.case_id = case_id


class CasePersistenceError(VoicePilotRuntimeError):
    """Raised when case persistence fails."""


class PlaybookNotFoundError(VoicePilotRuntimeError):
    """Raised when a playbook file cannot be located."""

    def __init__(self, path: str) -> None:
        super().__init__(f"Playbook not found: {path}")
        self.path = path


class PlaybookValidationError(VoicePilotRuntimeError):
    """Raised when a playbook document fails schema validation."""

    def __init__(self, message: str, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []


class InvalidStateTransitionError(VoicePilotRuntimeError):
    """Raised when a lifecycle state transition is not permitted."""

    def __init__(self, from_state: str, to_state: str) -> None:
        super().__init__(f"Invalid state transition: {from_state} -> {to_state}")
        self.from_state = from_state
        self.to_state = to_state


class EngineNotRegisteredError(VoicePilotRuntimeError):
    """Raised when an unknown engine is requested from the registry."""

    def __init__(self, engine_name: str) -> None:
        super().__init__(f"Engine not registered: {engine_name}")
        self.engine_name = engine_name


class EngineAlreadyRegisteredError(VoicePilotRuntimeError):
    """Raised when registering a duplicate engine name."""

    def __init__(self, engine_name: str) -> None:
        super().__init__(f"Engine already registered: {engine_name}")
        self.engine_name = engine_name


class PluginManifestNotFoundError(VoicePilotRuntimeError):
    """Raised when a plugin directory has no ``manifest.yaml``."""

    def __init__(self, plugin_path: str) -> None:
        super().__init__(f"Plugin manifest not found: {plugin_path}")
        self.plugin_path = plugin_path


class PluginManifestValidationError(VoicePilotRuntimeError):
    """Raised when a plugin manifest fails validation."""

    def __init__(self, message: str, plugin_path: str, errors: list[str] | None = None) -> None:
        super().__init__(message)
        self.plugin_path = plugin_path
        self.errors = errors or []


class PluginNotFoundError(VoicePilotRuntimeError):
    """Raised when a plugin name is not registered."""

    def __init__(self, plugin_name: str) -> None:
        super().__init__(f"Plugin not found: {plugin_name}")
        self.plugin_name = plugin_name


class PlaybookIdNotFoundError(VoicePilotRuntimeError):
    """Raised when a playbook ID is not present in the catalog."""

    def __init__(self, playbook_id: str) -> None:
        super().__init__(f"Playbook ID not found in catalog: {playbook_id}")
        self.playbook_id = playbook_id


class QuestionNotFoundError(VoicePilotRuntimeError):
    """Raised when a question ID is not found on a case."""

    def __init__(self, case_id: str, question_id: str) -> None:
        super().__init__(f"Question {question_id!r} not found on case {case_id}")
        self.case_id = case_id
        self.question_id = question_id


class InvalidInvestigationStateError(VoicePilotRuntimeError):
    """Raised when an operation requires a specific investigation state."""

    def __init__(self, case_id: str, expected: str, actual: str) -> None:
        super().__init__(
            f"Case {case_id} must be in state {expected}, but is {actual}"
        )
        self.case_id = case_id
        self.expected = expected
        self.actual = actual


class PlaybookCatalogLoadError(VoicePilotRuntimeError):
    """Raised when a plugin playbook fails to load into the catalog."""

    def __init__(self, plugin_name: str, path: str, message: str) -> None:
        super().__init__(
            f"Failed to load playbook for plugin '{plugin_name}' from {path}: {message}"
        )
        self.plugin_name = plugin_name
        self.path = path


class UnsupportedPlaybookScenarioError(VoicePilotRuntimeError):
    """Raised when scenario regression is not available for a playbook."""

    def __init__(self, playbook_id: str) -> None:
        super().__init__(f"No scenario pack registered for playbook: {playbook_id}")
        self.playbook_id = playbook_id


class ScenarioNotFoundError(VoicePilotRuntimeError):
    """Raised when a requested scenario ID is not present in the pack."""

    def __init__(self, playbook_id: str, scenario_id: str, available: tuple[str, ...]) -> None:
        available_text = ", ".join(available) if available else "(none)"
        super().__init__(
            f"Scenario {scenario_id!r} not found for playbook {playbook_id}. "
            f"Available: {available_text}"
        )
        self.playbook_id = playbook_id
        self.scenario_id = scenario_id
        self.available = available
