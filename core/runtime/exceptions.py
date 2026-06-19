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


class PlaybookCatalogLoadError(VoicePilotRuntimeError):
    """Raised when a plugin playbook fails to load into the catalog."""

    def __init__(self, plugin_name: str, path: str, message: str) -> None:
        super().__init__(
            f"Failed to load playbook for plugin '{plugin_name}' from {path}: {message}"
        )
        self.plugin_name = plugin_name
        self.path = path
