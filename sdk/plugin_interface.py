"""VoicePilot plugin interfaces and base plugin contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from sdk.plugin_manifest import PluginManifest
from sdk.plugin_types import PluginType


@runtime_checkable
class PlaybookProvider(Protocol):
    """Provides DSL playbook documents to the runtime."""

    def list_playbooks(self) -> list[Path]:
        """Return absolute paths to ``.vpb.yaml`` playbooks."""
        ...

    def get_playbook(self, playbook_id: str) -> Path | None:
        """Resolve a playbook path by identifier."""
        ...


@runtime_checkable
class ParserProvider(Protocol):
    """Provides evidence parsers and finding extractors."""

    def supported_signal_types(self) -> list[str]:
        """Return signal types this parser can emit."""
        ...

    def parse(self, artifact_path: Path, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Parse an artifact and return structured findings.

        TODO: Return canonical ParserFinding objects when parser engine exists.
        """
        ...


@runtime_checkable
class KnowledgeProvider(Protocol):
    """Provides curated knowledge items."""

    def list_knowledge_domains(self) -> list[str]:
        """Return knowledge domains supplied by this plugin."""
        ...

    def get_knowledge_item(self, knowledge_item_id: str) -> dict[str, Any] | None:
        """Load a knowledge item by identifier."""
        ...


@runtime_checkable
class AIProvider(Protocol):
    """Optional AI augmentation provider.

    VoicePilot core investigations remain evidence-driven. AI providers may
    assist with ranking or summarization but must not bypass canonical objects.
    """

    def is_enabled(self) -> bool:
        """Return whether AI augmentation is active for this deployment."""
        ...

    def summarize(self, payload: dict[str, Any]) -> str:
        """Produce a summary from structured investigation context."""
        ...


class VoicePilotPlugin(ABC):
    """Base class for all VoicePilot plugins.

    Plugins extend the core platform with vendor playbooks, parsers, knowledge,
    and optional AI capabilities without modifying core runtime code.
    """

    @property
    @abstractmethod
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""

    @property
    def name(self) -> str:
        """Unique plugin name from manifest."""
        return self.manifest.name

    @property
    def plugin_type(self) -> PluginType:
        """Plugin classification from manifest."""
        return self.manifest.plugin_type

    def on_load(self) -> None:
        """Called when the plugin is registered with the platform.

        TODO: Wire plugin lifecycle hooks in PluginRegistry (future sprint).
        """

    def on_unload(self) -> None:
        """Called when the plugin is unloaded."""

    def get_playbook_provider(self) -> PlaybookProvider | None:
        """Return playbook provider if supported."""
        return None

    def get_parser_provider(self) -> ParserProvider | None:
        """Return parser provider if supported."""
        return None

    def get_knowledge_provider(self) -> KnowledgeProvider | None:
        """Return knowledge provider if supported."""
        return None

    def get_ai_provider(self) -> AIProvider | None:
        """Return AI provider if supported."""
        return None
