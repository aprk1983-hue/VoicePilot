"""Discovers and loads VoicePilot plugins from the plugins directory."""

from __future__ import annotations

from pathlib import Path

from domain.interfaces import LoggerPort
from infrastructure.yaml_loader import YamlLoader
from runtime.exceptions import (
    PluginManifestNotFoundError,
    PluginManifestValidationError,
    PluginNotFoundError,
)
from sdk.plugin_manifest import PluginManifest
from sdk.plugin_types import PluginType
from shared.types import JsonDict


class PluginRegistry:
    """Discovers plugin manifests and exposes playbook entry points.

    Scans a configurable plugins root for ``<plugin>/manifest.yaml`` files,
    validates required fields, and registers ``PluginManifest`` instances.
    """

    MANIFEST_FILENAME: str = "manifest.yaml"

    _REQUIRED_FIELDS: tuple[str, ...] = (
        "name",
        "display_name",
        "version",
        "vendor",
        "plugin_type",
    )

    def __init__(
        self,
        plugins_root: Path,
        yaml_loader: YamlLoader | None = None,
        logger: LoggerPort | None = None,
    ) -> None:
        self._plugins_root = plugins_root
        self._yaml_loader = yaml_loader or YamlLoader()
        self._logger = logger
        self._manifests: dict[str, PluginManifest] = {}

    @property
    def plugins_root(self) -> Path:
        """Configured root directory containing plugin packages."""
        return self._plugins_root

    def discover(self) -> list[PluginManifest]:
        """Scan ``plugins_root`` and load all valid plugin manifests.

        Directories without ``manifest.yaml`` are skipped silently.
        """
        if not self._plugins_root.exists():
            if self._logger:
                self._logger.debug("Plugins root does not exist", path=str(self._plugins_root))
            return []

        discovered: list[PluginManifest] = []
        for entry in sorted(self._plugins_root.iterdir()):
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            manifest_path = entry / self.MANIFEST_FILENAME
            if not manifest_path.is_file():
                if self._logger:
                    self._logger.debug(
                        "Skipping plugin directory without manifest",
                        path=str(entry),
                    )
                continue
            manifest = self.load_manifest(entry)
            discovered.append(manifest)

        if self._logger:
            self._logger.info(
                "Plugin discovery complete",
                count=len(discovered),
                plugins=[m.name for m in discovered],
            )
        return discovered

    def load_manifest(self, plugin_dir: Path) -> PluginManifest:
        """Load and validate ``manifest.yaml`` from a plugin directory."""
        manifest_path = plugin_dir / self.MANIFEST_FILENAME
        if not manifest_path.is_file():
            raise PluginManifestNotFoundError(str(manifest_path))

        data = self._yaml_loader.load_file(manifest_path)
        self._validate_manifest_data(data, str(plugin_dir))
        manifest = PluginManifest.from_mapping(data, plugin_dir.resolve())

        if manifest.name in self._manifests:
            raise PluginManifestValidationError(
                f"Duplicate plugin name: {manifest.name}",
                str(plugin_dir),
                [f"Plugin name already registered: {manifest.name}"],
            )

        self._manifests[manifest.name] = manifest
        return manifest

    def get(self, name: str) -> PluginManifest:
        """Return a registered manifest by plugin name."""
        if name not in self._manifests:
            raise PluginNotFoundError(name)
        return self._manifests[name]

    def list_plugins(self) -> list[PluginManifest]:
        """Return all registered plugin manifests sorted by name."""
        return [self._manifests[name] for name in sorted(self._manifests)]

    def list_playbook_paths(self) -> list[Path]:
        """Return absolute paths to all declared playbook entry points."""
        paths: list[Path] = []
        for manifest in self.list_plugins():
            paths.extend(manifest.resolve_playbook_paths())
        return paths

    def list_playbook_paths_for(self, plugin_name: str) -> list[Path]:
        """Return playbook entry paths for a single plugin."""
        return self.get(plugin_name).resolve_playbook_paths()

    def is_registered(self, name: str) -> bool:
        """Return whether a plugin name is registered."""
        return name in self._manifests

    def clear(self) -> None:
        """Remove all registered manifests. Intended for tests."""
        self._manifests.clear()

    def _validate_manifest_data(self, data: JsonDict, plugin_path: str) -> None:
        """Validate required manifest fields and value constraints."""
        errors: list[str] = []

        for field in self._REQUIRED_FIELDS:
            value = data.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append(f"Missing required field: {field}")

        plugin_type = data.get("plugin_type")
        if plugin_type is not None:
            try:
                PluginType(str(plugin_type))
            except ValueError:
                errors.append(f"Invalid plugin_type: {plugin_type!r}")

        entry_points = data.get("entry_points")
        if entry_points is not None and not isinstance(entry_points, dict):
            errors.append("entry_points must be a mapping")

        if errors:
            raise PluginManifestValidationError(
                "Plugin manifest validation failed",
                plugin_path,
                errors,
            )
