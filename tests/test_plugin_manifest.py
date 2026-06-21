"""Tests for plugin manifest parsing."""

from __future__ import annotations

from pathlib import Path

import pytest

from sdk.plugin_manifest import PluginManifest
from sdk.plugin_types import PluginType

MANIFEST_PATH = Path(__file__).resolve().parents[1] / "plugins" / "cisco" / "manifest.yaml"


@pytest.fixture
def manifest_data() -> dict:
    if not MANIFEST_PATH.exists():
        pytest.skip("Cisco manifest not found")
    import yaml

    data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


class TestPluginManifest:
    def test_cisco_manifest_parses(self, manifest_data: dict) -> None:
        root = MANIFEST_PATH.parent
        manifest = PluginManifest.from_mapping(manifest_data, root)
        assert manifest.name == "cisco"
        assert manifest.display_name == "Cisco Voice Plugin"
        assert manifest.version == "0.1.0"
        assert manifest.plugin_type == PluginType.VENDOR
        assert "cube_playbooks" in manifest.capabilities
        assert "cucm_playbooks" in manifest.capabilities
        assert "Cisco CUBE" in manifest.supported_platforms

    def test_resolve_playbook_paths(self, manifest_data: dict) -> None:
        root = MANIFEST_PATH.parent
        manifest = PluginManifest.from_mapping(manifest_data, root)
        paths = manifest.resolve_playbook_paths()
        path_names = {path.name for path in paths}
        assert len(paths) == 2
        assert "vp-cube-0001-outbound-calls-fail.vpb.yaml" in path_names
        assert "vp-cucm-0001-cisco-cucm-investigation.vpb.yaml" in path_names
        assert all(path.exists() for path in paths)
