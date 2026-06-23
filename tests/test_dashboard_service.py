"""Tests for VoicePilotService dashboard summary."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry
from runtime.runtime_engine import RuntimeEngine
from runtime.scenario_runner import VP_CUBE_0001_PLAYBOOK_ID
from services import VoicePilotService
from shared.config import RuntimeConfig

PLUGINS_ROOT = Path(__file__).resolve().parents[1] / "plugins"
PLAYBOOK_ID = VP_CUBE_0001_PLAYBOOK_ID


@pytest.fixture
def service() -> VoicePilotService:
    registry = PluginRegistry(plugins_root=PLUGINS_ROOT)
    loader = PlaybookLoader(repository=FilesystemPlaybookRepository(YamlLoader()))
    catalog = PlaybookCatalog(plugin_registry=registry, playbook_loader=loader)
    catalog.load_all()
    engine = RuntimeEngine(
        config=RuntimeConfig(playbooks_path=PLUGINS_ROOT),
        case_repository=InMemoryCaseRepository(),
        playbook_repository=FilesystemPlaybookRepository(YamlLoader()),
        plugin_registry=registry,
        playbook_catalog=catalog,
    )
    engine.start()
    svc = VoicePilotService(runtime_engine=engine)
    svc._started = True
    return svc


class TestDashboardService:
    def test_get_dashboard_summary_empty(self, service: VoicePilotService) -> None:
        summary = service.get_dashboard_summary()
        assert summary.api_status == "ok"
        assert summary.total_cases == 0
        assert summary.supported_playbook_count >= 5
        assert summary.read_only_notice

    def test_get_dashboard_summary_with_cases(self, service: VoicePilotService) -> None:
        service.create_case(PLAYBOOK_ID)
        service.create_case(PLAYBOOK_ID)
        summary = service.get_dashboard_summary()
        assert summary.total_cases == 2
        assert dict(summary.cases_by_playbook).get(PLAYBOOK_ID) == 2
        assert summary.knowledge_asset_count > 0
