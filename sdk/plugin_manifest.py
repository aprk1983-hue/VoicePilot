"""Plugin manifest model for VoicePilot plugins."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sdk.plugin_types import PluginType


@dataclass(frozen=True)
class PluginEntryPoints:
    """Filesystem entry points declared by a plugin manifest."""

    playbooks: tuple[str, ...] = ()
    parsers: tuple[str, ...] = ()
    knowledge: tuple[str, ...] = ()
    ai: tuple[str, ...] = ()


@dataclass(frozen=True)
class PluginManifest:
    """Parsed ``manifest.yaml`` for a VoicePilot plugin.

    Attributes:
        name: Unique plugin identifier (e.g. ``cisco``).
        display_name: Human-readable plugin name.
        version: Semantic version of the plugin package.
        vendor: Plugin publisher.
        plugin_type: Plugin classification.
        capabilities: Capability tokens supported by the plugin.
        supported_platforms: Platform labels for discovery and filtering.
        entry_points: Relative paths to plugin assets.
        root_path: Absolute path to the plugin root directory.
    """

    name: str
    display_name: str
    version: str
    vendor: str
    plugin_type: PluginType
    capabilities: tuple[str, ...]
    supported_platforms: tuple[str, ...]
    entry_points: PluginEntryPoints
    root_path: Path
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def resolve_playbook_paths(self) -> list[Path]:
        """Return absolute paths to declared playbook entry points."""
        return [self.root_path / rel for rel in self.entry_points.playbooks]

    @classmethod
    def from_mapping(cls, data: dict[str, Any], root_path: Path) -> PluginManifest:
        """Build a manifest from a parsed YAML mapping.

        TODO: Add JSON Schema validation in a future sprint.
        """
        entry_raw = data.get("entry_points", {}) or {}
        plugin_type_raw = data.get("plugin_type", PluginType.CUSTOM.value)
        return cls(
            name=data["name"],
            display_name=data["display_name"],
            version=data["version"],
            vendor=data["vendor"],
            plugin_type=PluginType(plugin_type_raw),
            capabilities=tuple(data.get("capabilities", [])),
            supported_platforms=tuple(data.get("supported_platforms", [])),
            entry_points=PluginEntryPoints(
                playbooks=tuple(entry_raw.get("playbooks", [])),
                parsers=tuple(entry_raw.get("parsers", [])),
                knowledge=tuple(entry_raw.get("knowledge", [])),
                ai=tuple(entry_raw.get("ai", [])),
            ),
            root_path=root_path,
            description=data.get("description"),
            metadata=dict(data.get("metadata", {})),
        )
