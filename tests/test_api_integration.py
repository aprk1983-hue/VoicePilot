"""API integration tests for enterprise dashboard workflow."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.dependencies import get_voicepilot_service
from api.main import create_app
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry
from runtime.runtime_engine import RuntimeEngine
from runtime.scenario_runner import VP_CUBE_0001_PLAYBOOK_ID
from services import VoicePilotService
from shared.config import RuntimeConfig

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_ROOT = REPO_ROOT / "plugins"
PLAYBOOK_ID = VP_CUBE_0001_PLAYBOOK_ID
SAMPLE_EVIDENCE = (
    REPO_ROOT / "examples" / "sample_evidence" / "parser" / "show_sip_ua_status_disabled.txt"
)


@pytest.fixture
def client() -> TestClient:
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
    service = VoicePilotService(runtime_engine=engine)
    service._started = True
    app = create_app()
    app.dependency_overrides[get_voicepilot_service] = lambda: service
    return TestClient(app)


class TestDashboardIntegration:
    def test_dashboard_to_case_workflow(self, client: TestClient) -> None:
        initial = client.get("/dashboard/summary").json()["data"]
        assert initial["total_cases"] == 0

        created = client.post("/cases", json={"playbook_id": PLAYBOOK_ID}).json()["data"]
        case_id = created["case_id"]

        dashboard = client.get("/dashboard/summary").json()["data"]
        assert dashboard["total_cases"] == 1

        client.post(
            f"/cases/{case_id}/evidence",
            json={
                "command": "show sip-ua status",
                "content": SAMPLE_EVIDENCE.read_text(encoding="utf-8"),
            },
        )

        status = client.get(f"/cases/{case_id}/status").json()["data"]
        assert status["case_id"] == case_id

    def test_dashboard_openapi_includes_summary(self, client: TestClient) -> None:
        schema = client.get("/openapi.json").json()
        assert "/dashboard/summary" in schema["paths"]
