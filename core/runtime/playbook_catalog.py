"""Loads playbooks discovered via PluginRegistry into a searchable catalog."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from domain.interfaces import LoggerPort
from domain.models import Playbook
from runtime.exceptions import (
    PlaybookCatalogLoadError,
    PlaybookIdNotFoundError,
    PlaybookNotFoundError,
    PlaybookValidationError,
    PluginNotFoundError,
)
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry


@dataclass(frozen=True)
class CatalogEntry:
    """A playbook loaded into the catalog with plugin provenance."""

    playbook: Playbook
    plugin_name: str
    source_path: Path


class PlaybookCatalog:
    """Discovers plugin playbook paths and loads them via ``PlaybookLoader``.

    Playbooks are indexed by playbook ID and plugin name for runtime lookup.
    """

    def __init__(
        self,
        plugin_registry: PluginRegistry,
        playbook_loader: PlaybookLoader,
        logger: LoggerPort | None = None,
    ) -> None:
        self._plugin_registry = plugin_registry
        self._playbook_loader = playbook_loader
        self._logger = logger
        self._entries_by_id: dict[str, CatalogEntry] = {}
        self._entries_by_plugin: dict[str, list[CatalogEntry]] = {}

    @property
    def plugin_registry(self) -> PluginRegistry:
        """Underlying plugin registry."""
        return self._plugin_registry

    @property
    def playbook_loader(self) -> PlaybookLoader:
        """Underlying playbook loader."""
        return self._playbook_loader

    def load_all(self, discover_plugins: bool = True) -> list[Playbook]:
        """Discover plugin playbooks and load all entry points into the catalog.

        Args:
            discover_plugins: When ``True``, call ``PluginRegistry.discover()`` if
                no plugins are registered yet.

        Returns:
            List of loaded ``Playbook`` objects.

        Raises:
            PlaybookCatalogLoadError: If a declared playbook file fails to load.
            PluginNotFoundError: Propagated when resolving an unknown plugin.
        """
        if discover_plugins and not self._plugin_registry.list_plugins():
            self._plugin_registry.discover()

        loaded: list[Playbook] = []
        for manifest in self._plugin_registry.list_plugins():
            plugin_name = manifest.name
            for path in manifest.resolve_playbook_paths():
                entry = self._load_entry(plugin_name, path)
                loaded.append(entry.playbook)

        if self._logger:
            self._logger.info(
                "Playbook catalog loaded",
                count=len(loaded),
                playbook_ids=sorted(self._entries_by_id),
            )
        return loaded

    def get(self, playbook_id: str) -> Playbook:
        """Return a cataloged playbook by DSL metadata ID.

        Raises:
            PlaybookIdNotFoundError: If the playbook ID is not in the catalog.
        """
        entry = self._entries_by_id.get(playbook_id)
        if entry is None:
            raise PlaybookIdNotFoundError(playbook_id)
        return entry.playbook

    def get_entry(self, playbook_id: str) -> CatalogEntry:
        """Return catalog entry including plugin name and source path."""
        entry = self._entries_by_id.get(playbook_id)
        if entry is None:
            raise PlaybookIdNotFoundError(playbook_id)
        return entry

    def list_all(self) -> list[Playbook]:
        """Return all cataloged playbooks sorted by playbook ID."""
        return [self._entries_by_id[pid].playbook for pid in sorted(self._entries_by_id)]

    def list_for_plugin(self, plugin_name: str) -> list[Playbook]:
        """Return playbooks loaded from a specific plugin.

        Raises:
            PluginNotFoundError: If the plugin is not registered.
        """
        if not self._plugin_registry.is_registered(plugin_name):
            raise PluginNotFoundError(plugin_name)
        return [entry.playbook for entry in self._entries_by_plugin.get(plugin_name, [])]

    def list_entries_for_plugin(self, plugin_name: str) -> list[CatalogEntry]:
        """Return catalog entries for a plugin including source paths."""
        if not self._plugin_registry.is_registered(plugin_name):
            raise PluginNotFoundError(plugin_name)
        return list(self._entries_by_plugin.get(plugin_name, []))

    def is_loaded(self, playbook_id: str) -> bool:
        """Return whether ``playbook_id`` is present in the catalog."""
        return playbook_id in self._entries_by_id

    def clear(self) -> None:
        """Remove all catalog entries. Intended for tests."""
        self._entries_by_id.clear()
        self._entries_by_plugin.clear()

    def _load_entry(self, plugin_name: str, path: Path) -> CatalogEntry:
        """Load a single playbook file and register it in the catalog."""
        try:
            playbook = self._playbook_loader.load(path)
        except (PlaybookNotFoundError, PlaybookValidationError) as exc:
            raise PlaybookCatalogLoadError(plugin_name, str(path), str(exc)) from exc

        if playbook.playbook_id in self._entries_by_id:
            existing = self._entries_by_id[playbook.playbook_id]
            raise PlaybookCatalogLoadError(
                plugin_name,
                str(path),
                (
                    f"Duplicate playbook ID {playbook.playbook_id!r} "
                    f"already loaded from plugin {existing.plugin_name!r}"
                ),
            )

        entry = CatalogEntry(
            playbook=playbook,
            plugin_name=plugin_name,
            source_path=path.resolve(),
        )
        self._register(entry)
        return entry

    def _register(self, entry: CatalogEntry) -> None:
        """Index a catalog entry by playbook ID and plugin name."""
        playbook_id = entry.playbook.playbook_id
        self._entries_by_id[playbook_id] = entry
        self._entries_by_plugin.setdefault(entry.plugin_name, []).append(entry)
