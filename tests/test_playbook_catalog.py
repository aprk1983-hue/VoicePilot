"""Tests for PlaybookCatalog."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.filesystem import FilesystemPlaybookRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.event_bus import EventBus
from runtime.exceptions import (
    PlaybookCatalogLoadError,
    PlaybookIdNotFoundError,
    PluginNotFoundError,
)
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry

PLUGINS_ROOT = Path(__file__).resolve().parents[1] / "plugins"


@pytest.fixture
def plugin_registry() -> PluginRegistry:
    registry = PluginRegistry(plugins_root=PLUGINS_ROOT)
    yield registry
    registry.clear()


@pytest.fixture
def playbook_catalog(plugin_registry: PluginRegistry, event_bus: EventBus) -> PlaybookCatalog:
    loader = PlaybookLoader(
        repository=FilesystemPlaybookRepository(YamlLoader()),
        event_bus=event_bus,
    )
    catalog = PlaybookCatalog(plugin_registry=plugin_registry, playbook_loader=loader)
    yield catalog
    catalog.clear()


class TestPlaybookCatalog:
    def test_loads_cisco_playbook_from_plugin_registry(
        self, playbook_catalog: PlaybookCatalog
    ) -> None:
        playbooks = playbook_catalog.load_all()
        assert len(playbooks) >= 1
        assert any(pb.playbook_id == "VP-CUBE-0001" for pb in playbooks)

    def test_lookup_vp_cube_0001(self, playbook_catalog: PlaybookCatalog) -> None:
        playbook_catalog.load_all()
        playbook = playbook_catalog.get("VP-CUBE-0001")
        assert playbook.title == "Outbound Calls Fail"
        assert playbook.version == "1.0.0"

    def test_list_playbooks_by_plugin_cisco(self, playbook_catalog: PlaybookCatalog) -> None:
        playbook_catalog.load_all()
        cisco_playbooks = playbook_catalog.list_for_plugin("cisco")
        playbook_ids = {entry.playbook_id for entry in cisco_playbooks}
        assert "VP-CUBE-0001" in playbook_ids
        assert "VP-CUCM-0001" in playbook_ids

    def test_unknown_playbook_id_raises(self, playbook_catalog: PlaybookCatalog) -> None:
        playbook_catalog.load_all()
        with pytest.raises(PlaybookIdNotFoundError):
            playbook_catalog.get("VP-UNKNOWN-9999")

    def test_unknown_plugin_raises(self, playbook_catalog: PlaybookCatalog) -> None:
        playbook_catalog.load_all()
        with pytest.raises(PluginNotFoundError):
            playbook_catalog.list_for_plugin("nonexistent-plugin")

    def test_get_entry_includes_plugin_and_path(self, playbook_catalog: PlaybookCatalog) -> None:
        playbook_catalog.load_all()
        entry = playbook_catalog.get_entry("VP-CUBE-0001")
        assert entry.plugin_name == "cisco"
        assert entry.source_path.name == "vp-cube-0001-outbound-calls-fail.vpb.yaml"
        assert entry.source_path.exists()

    def test_invalid_playbook_raises_catalog_load_error(
        self, tmp_path: Path, event_bus: EventBus
    ) -> None:
        plugin_dir = tmp_path / "bad-playbooks"
        plugin_dir.mkdir()
        playbooks_dir = plugin_dir / "playbooks"
        playbooks_dir.mkdir()
        bad_playbook = playbooks_dir / "bad.vpb.yaml"
        bad_playbook.write_text("foo: bar\n", encoding="utf-8")
        (plugin_dir / "manifest.yaml").write_text(
            """
name: bad-playbooks
display_name: Bad Playbooks
version: 0.1.0
vendor: Test
plugin_type: custom
entry_points:
  playbooks:
    - playbooks/bad.vpb.yaml
""".strip(),
            encoding="utf-8",
        )

        registry = PluginRegistry(plugins_root=tmp_path)
        loader = PlaybookLoader(
            repository=FilesystemPlaybookRepository(YamlLoader()),
            event_bus=event_bus,
        )
        catalog = PlaybookCatalog(plugin_registry=registry, playbook_loader=loader)

        with pytest.raises(PlaybookCatalogLoadError) as exc_info:
            catalog.load_all()
        assert exc_info.value.plugin_name == "bad-playbooks"

    def test_uses_plugin_registry_paths_not_hardcoded(
        self, playbook_catalog: PlaybookCatalog, plugin_registry: PluginRegistry
    ) -> None:
        plugin_registry.discover()
        expected_paths = set(plugin_registry.list_playbook_paths_for("cisco"))
        playbook_catalog.load_all(discover_plugins=False)
        actual_paths = {
            entry.source_path for entry in playbook_catalog.list_entries_for_plugin("cisco")
        }
        assert actual_paths == expected_paths
