"""Tests for PluginRegistry."""

from __future__ import annotations

from pathlib import Path

import pytest

from runtime.exceptions import (
    PluginManifestNotFoundError,
    PluginManifestValidationError,
    PluginNotFoundError,
)
from runtime.plugin_registry import PluginRegistry
from sdk.plugin_types import PluginType

PLUGINS_ROOT = Path(__file__).resolve().parents[1] / "plugins"


@pytest.fixture
def registry() -> PluginRegistry:
    reg = PluginRegistry(plugins_root=PLUGINS_ROOT)
    yield reg
    reg.clear()


class TestPluginRegistry:
    def test_discovers_cisco_plugin(self, registry: PluginRegistry) -> None:
        manifests = registry.discover()
        names = [m.name for m in manifests]
        assert "cisco" in names

    def test_loads_manifest_fields_correctly(self, registry: PluginRegistry) -> None:
        registry.discover()
        manifest = registry.get("cisco")
        assert manifest.display_name == "Cisco Voice Plugin"
        assert manifest.version == "0.1.0"
        assert manifest.vendor == "VoicePilot"
        assert manifest.plugin_type == PluginType.VENDOR
        assert "cube_playbooks" in manifest.capabilities
        assert "Cisco CUBE" in manifest.supported_platforms

    def test_returns_playbook_entry_paths(self, registry: PluginRegistry) -> None:
        registry.discover()
        paths = registry.list_playbook_paths()
        assert len(paths) >= 1
        assert any(p.name == "vp-cube-0001-outbound-calls-fail.vpb.yaml" for p in paths)
        assert all(p.is_absolute() for p in paths)

    def test_lookup_by_plugin_name(self, registry: PluginRegistry) -> None:
        registry.discover()
        assert registry.is_registered("cisco")
        cisco_paths = registry.list_playbook_paths_for("cisco")
        assert len(cisco_paths) == 1

    def test_lookup_missing_plugin_raises(self, registry: PluginRegistry) -> None:
        registry.discover()
        with pytest.raises(PluginNotFoundError):
            registry.get("nonexistent-plugin")

    def test_missing_manifest_is_skipped_on_discover(self, tmp_path: Path) -> None:
        (tmp_path / "empty-plugin").mkdir()
        registry = PluginRegistry(plugins_root=tmp_path)
        assert registry.discover() == []

    def test_missing_manifest_raises_on_explicit_load(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / "no-manifest"
        plugin_dir.mkdir()
        registry = PluginRegistry(plugins_root=tmp_path)
        with pytest.raises(PluginManifestNotFoundError):
            registry.load_manifest(plugin_dir)

    def test_invalid_manifest_raises(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / "bad-plugin"
        plugin_dir.mkdir()
        (plugin_dir / "manifest.yaml").write_text(
            "name: bad\nversion: 0.1.0\n",
            encoding="utf-8",
        )
        registry = PluginRegistry(plugins_root=tmp_path)
        with pytest.raises(PluginManifestValidationError) as exc_info:
            registry.load_manifest(plugin_dir)
        assert any("display_name" in err for err in exc_info.value.errors)

    def test_duplicate_plugin_name_raises(self, tmp_path: Path) -> None:
        for name in ("plugin-a", "plugin-b"):
            plugin_dir = tmp_path / name
            plugin_dir.mkdir()
            (plugin_dir / "manifest.yaml").write_text(
                f"""
name: duplicate
display_name: Duplicate Plugin
version: 0.1.0
vendor: Test
plugin_type: custom
""".strip(),
                encoding="utf-8",
            )
        registry = PluginRegistry(plugins_root=tmp_path)
        registry.load_manifest(tmp_path / "plugin-a")
        with pytest.raises(PluginManifestValidationError):
            registry.load_manifest(tmp_path / "plugin-b")
