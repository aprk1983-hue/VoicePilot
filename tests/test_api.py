"""Tests for the VoicePilot Enterprise REST API (FastAPI)."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.dependencies import get_voicepilot_service
from api.main import create_app
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.evidence_collection import submit_evidence
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry
from runtime.runtime_engine import RuntimeEngine
from runtime.scenario_runner import (
    VP_CUBE_0001_PLAYBOOK_ID,
    default_scenarios_root,
    run_scenario_to_correlation,
)
from runtime.verification_engine import RESULT_PASSED, VerificationResultSubmission
from services import VoicePilotService
from shared.config import RuntimeConfig

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_ROOT = REPO_ROOT / "plugins"
PLAYBOOK_ID = VP_CUBE_0001_PLAYBOOK_ID
SCENARIOS_ROOT = default_scenarios_root(PLAYBOOK_ID, repo_root=REPO_ROOT)
SAMPLE_EVIDENCE = (
    REPO_ROOT / "examples" / "sample_evidence" / "parser" / "show_sip_ua_status_disabled.txt"
)

OPENAPI_PATHS = [
    "/health",
    "/version",
    "/dashboard/summary",
    "/cases",
    "/cases/{case_id}",
    "/cases/{case_id}/evidence",
    "/cases/{case_id}/investigate",
    "/cases/{case_id}/status",
    "/brain/start",
    "/brain/{session_id}",
    "/brain/{session_id}/timeline",
    "/cases/{case_id}/report",
    "/cases/{case_id}/executive",
    "/cases/{case_id}/engineering",
    "/cases/{case_id}/cab",
    "/cases/{case_id}/change-package",
    "/validate",
]


@pytest.fixture
def runtime_engine() -> RuntimeEngine:
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
    return engine


@pytest.fixture
def service(runtime_engine: RuntimeEngine) -> VoicePilotService:
    svc = VoicePilotService(runtime_engine=runtime_engine)
    svc._started = True
    return svc


@pytest.fixture
def client(service: VoicePilotService) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_voicepilot_service] = lambda: service
    return TestClient(app)


@pytest.fixture
def case_id(service: VoicePilotService) -> str:
    return service.create_case(PLAYBOOK_ID).case_id


@pytest.fixture
def correlated_case(service: VoicePilotService) -> str:
    scenario_dir = SCENARIOS_ROOT / "provider_503"
    runtime = service.runtime
    _, case_id = run_scenario_to_correlation(scenario_dir, runtime=runtime)
    return case_id


@pytest.fixture
def investigated_case(service: VoicePilotService, correlated_case: str) -> str:
    service.investigate_case(correlated_case)
    return correlated_case


@pytest.fixture
def closed_case(service: VoicePilotService) -> str:
    scenario_dir = SCENARIOS_ROOT / "provider_503"
    runtime = service.runtime
    _, case_id = run_scenario_to_correlation(scenario_dir, runtime=runtime)
    service.generate_recommendation(case_id)
    checklist = runtime.generate_verification_checklist(case_id)
    assert checklist is not None
    submissions = [
        VerificationResultSubmission(
            verification_id=item.verification_id,
            status=RESULT_PASSED,
        )
        for item in checklist.items
    ]
    runtime.submit_verification(case_id, submissions)
    runtime.close_case_with_learning(case_id)
    return case_id


def _assert_envelope(response) -> dict:
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["request_id"]
    assert body["timestamp"]
    assert "data" in body
    return body["data"]


def _assert_error(response, status_code: int, error_code: str | None = None) -> dict:
    assert response.status_code == status_code
    body = response.json()
    assert body["success"] is False
    assert body["error"]
    assert body["message"]
    assert body["request_id"]
    assert body["timestamp"]
    if error_code:
        assert body["error"] == error_code
    return body


class TestHealthEndpoints:
    def test_health_returns_ok(self, client: TestClient) -> None:
        data = _assert_envelope(client.get("/health"))
        assert data["status"] == "ok"
        assert data["service"] == "voicepilot-api"

    def test_health_includes_request_id_header(self, client: TestClient) -> None:
        response = client.get("/health", headers={"X-Request-ID": "req-health-1"})
        assert response.headers.get("X-Request-ID") == "req-health-1"


class TestVersionEndpoint:
    def test_version_returns_metadata(self, client: TestClient) -> None:
        data = _assert_envelope(client.get("/version"))
        assert data["name"] == "voicepilot"
        assert data["version"]
        assert data["api_version"] == "v1"


class TestDashboardEndpoints:
    def test_dashboard_summary_returns_metrics(self, client: TestClient) -> None:
        data = _assert_envelope(client.get("/dashboard/summary"))
        assert data["api_status"] == "ok"
        assert data["platform_name"] == "voicepilot"
        assert data["total_cases"] == 0
        assert data["supported_playbook_count"] >= 5
        assert "read_only_notice" in data
        assert isinstance(data["supported_playbooks"], list)

    def test_dashboard_reflects_created_cases(self, client: TestClient) -> None:
        client.post("/cases", json={"playbook_id": PLAYBOOK_ID})
        client.post("/cases", json={"playbook_id": PLAYBOOK_ID})
        data = _assert_envelope(client.get("/dashboard/summary"))
        assert data["total_cases"] == 2
        assert data["cases_by_playbook"].get(PLAYBOOK_ID) == 2

    def test_dashboard_summary_schema_fields(self, client: TestClient) -> None:
        data = _assert_envelope(client.get("/dashboard/summary"))
        for field in (
            "api_status",
            "platform_version",
            "total_findings",
            "total_hypotheses",
            "total_recommendations",
            "knowledge_asset_count",
            "cases_by_state",
            "cases_by_playbook",
        ):
            assert field in data


class TestCaseEndpoints:
    def test_create_case(self, client: TestClient) -> None:
        response = client.post("/cases", json={"playbook_id": PLAYBOOK_ID})
        data = _assert_envelope(response)
        assert data["playbook_id"] == PLAYBOOK_ID
        assert data["case_id"].startswith("CASE-")
        assert data["state"] == "INTAKE"

    def test_create_case_invalid_playbook_returns_404(self, client: TestClient) -> None:
        _assert_error(
            client.post("/cases", json={"playbook_id": "VP-MISSING-0001"}),
            404,
            "playbook_not_found",
        )

    def test_create_case_missing_playbook_returns_422(self, client: TestClient) -> None:
        _assert_error(client.post("/cases", json={}), 422, "validation_error")

    def test_list_cases(self, client: TestClient, case_id: str) -> None:
        data = _assert_envelope(client.get("/cases"))
        assert isinstance(data, list)
        assert any(item["case_id"] == case_id for item in data)

    def test_get_case(self, client: TestClient, case_id: str) -> None:
        data = _assert_envelope(client.get(f"/cases/{case_id}"))
        assert data["case_id"] == case_id

    def test_get_case_not_found(self, client: TestClient) -> None:
        _assert_error(client.get("/cases/CASE-missing"), 404, "case_not_found")

    def test_delete_case(self, client: TestClient, case_id: str) -> None:
        data = _assert_envelope(client.delete(f"/cases/{case_id}"))
        assert data["deleted"] is True
        _assert_error(client.get(f"/cases/{case_id}"), 404, "case_not_found")

    def test_delete_case_not_found(self, client: TestClient) -> None:
        _assert_error(client.delete("/cases/CASE-missing"), 404, "case_not_found")


class TestEvidenceEndpoints:
    def test_upload_evidence(self, client: TestClient, case_id: str) -> None:
        raw_text = SAMPLE_EVIDENCE.read_text(encoding="utf-8")
        response = client.post(
            f"/cases/{case_id}/evidence",
            json={"command": "show sip-ua status", "content": raw_text},
        )
        data = _assert_envelope(response)
        assert data["accepted"] is True
        assert data["command"] == "show sip-ua status"
        assert data["evidence_id"].startswith("EVD-")

    def test_upload_evidence_case_not_found(self, client: TestClient) -> None:
        _assert_error(
            client.post(
                "/cases/CASE-missing/evidence",
                json={"command": "show sip-ua status", "content": "sample"},
            ),
            404,
            "case_not_found",
        )

    def test_upload_evidence_validation_error(self, client: TestClient, case_id: str) -> None:
        _assert_error(
            client.post(f"/cases/{case_id}/evidence", json={"command": "", "content": ""}),
            422,
            "validation_error",
        )


class TestInvestigationEndpoints:
    def test_investigate_case(self, client: TestClient, correlated_case: str) -> None:
        data = _assert_envelope(client.post(f"/cases/{correlated_case}/investigate"))
        assert data["case_id"] == correlated_case
        assert data["analysis"]["finding_count"] > 0
        assert data["discovery"]["request_count"] >= 0
        assert data["quality"]["overall_score"] >= 0
        assert data["recommendation"]["recommendation_count"] >= 1
        assert data["change_package"]["package_id"]

    def test_investigate_case_not_found(self, client: TestClient) -> None:
        _assert_error(
            client.post("/cases/CASE-missing/investigate"),
            404,
            "case_not_found",
        )

    def test_get_investigation_status(self, client: TestClient, investigated_case: str) -> None:
        data = _assert_envelope(client.get(f"/cases/{investigated_case}/status"))
        assert data["case_id"] == investigated_case
        assert data["top_hypothesis"]
        assert data["confidence"] is not None

    def test_get_investigation_status_not_found(self, client: TestClient) -> None:
        _assert_error(client.get("/cases/CASE-missing/status"), 404, "case_not_found")


class TestBrainEndpoints:
    def test_start_brain_session(self, client: TestClient) -> None:
        data = _assert_envelope(client.post("/brain/start", json={"playbook_id": PLAYBOOK_ID}))
        assert data["session_id"].startswith("BRN-")
        assert data["playbook_id"] == PLAYBOOK_ID

    def test_start_brain_invalid_playbook(self, client: TestClient) -> None:
        _assert_error(
            client.post("/brain/start", json={"playbook_id": "VP-MISSING-0001"}),
            404,
            "playbook_not_found",
        )

    def test_get_brain_session(self, client: TestClient) -> None:
        started = _assert_envelope(
            client.post("/brain/start", json={"playbook_id": PLAYBOOK_ID})
        )
        data = _assert_envelope(client.get(f"/brain/{started['session_id']}"))
        assert data["session_id"] == started["session_id"]

    def test_get_brain_session_not_found(self, client: TestClient) -> None:
        _assert_error(client.get("/brain/BRN-missing"), 404, "brain_session_not_found")

    def test_get_brain_timeline(self, client: TestClient) -> None:
        started = _assert_envelope(
            client.post("/brain/start", json={"playbook_id": PLAYBOOK_ID})
        )
        data = _assert_envelope(client.get(f"/brain/{started['session_id']}/timeline"))
        assert data["session_id"] == started["session_id"]
        assert "Investigation Replay" in data["markdown"]

    def test_start_brain_validation_error(self, client: TestClient) -> None:
        _assert_error(client.post("/brain/start", json={}), 422, "validation_error")


class TestReportEndpoints:
    @pytest.mark.parametrize(
        ("path_suffix", "report_type"),
        [
            ("report", "LEGACY"),
            ("executive", "EXECUTIVE"),
            ("engineering", "ENGINEERING"),
            ("cab", "CAB"),
        ],
    )
    def test_report_endpoints(
        self,
        client: TestClient,
        closed_case: str,
        path_suffix: str,
        report_type: str,
    ) -> None:
        data = _assert_envelope(client.get(f"/cases/{closed_case}/{path_suffix}"))
        assert data["case_id"] == closed_case
        assert data["report_type"] == report_type
        assert "VoicePilot" in data["markdown"]

    def test_report_case_not_found(self, client: TestClient) -> None:
        _assert_error(client.get("/cases/CASE-missing/engineering"), 404, "case_not_found")


class TestChangePackageEndpoint:
    def test_get_change_package(self, client: TestClient, investigated_case: str) -> None:
        data = _assert_envelope(client.get(f"/cases/{investigated_case}/change-package"))
        assert data["case_id"] == investigated_case
        assert data["risk_level"]
        assert "Advisory" in data["markdown"] or "VP-" in data["markdown"]

    def test_change_package_case_not_found(self, client: TestClient) -> None:
        _assert_error(
            client.get("/cases/CASE-missing/change-package"),
            404,
            "case_not_found",
        )


class TestValidationEndpoint:
    def test_validate_single_playbook(self, client: TestClient) -> None:
        response = client.post("/validate", json={"playbook_id": PLAYBOOK_ID})
        data = _assert_envelope(response)
        assert data["playbook_id"] == PLAYBOOK_ID
        assert data["total_scenarios"] == 5
        assert data["failed_count"] == 0
        assert data["accuracy_percent"] == 100.0

    def test_validate_invalid_playbook(self, client: TestClient) -> None:
        _assert_error(
            client.post("/validate", json={"playbook_id": "VP-MISSING-0001"}),
            404,
            "playbook_not_found",
        )


class TestOpenAPI:
    def test_openapi_schema_available(self, client: TestClient) -> None:
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "VoicePilot Enterprise API"
        assert schema["paths"]

    @pytest.mark.parametrize("path", OPENAPI_PATHS)
    def test_openapi_declares_endpoint(self, client: TestClient, path: str) -> None:
        schema = client.get("/openapi.json").json()
        assert path in schema["paths"]

    def test_swagger_ui_available(self, client: TestClient) -> None:
        assert client.get("/docs").status_code == 200

    def test_redoc_available(self, client: TestClient) -> None:
        assert client.get("/redoc").status_code == 200

    @pytest.mark.parametrize(
        "tag",
        ["Health", "Cases", "Evidence", "Investigation", "Brain", "Reports", "Change Package", "Validation"],
    )
    def test_openapi_tags_present(self, client: TestClient, tag: str) -> None:
        schema = client.get("/openapi.json").json()
        tag_names = {item["name"] for item in schema.get("tags", [])}
        operation_tags = {
            tag_name
            for path_item in schema["paths"].values()
            for operation in path_item.values()
            if isinstance(operation, dict)
            for tag_name in operation.get("tags", [])
        }
        assert tag in tag_names or tag in operation_tags


class TestResponseSchemas:
    def test_case_response_fields(self, client: TestClient, case_id: str) -> None:
        data = _assert_envelope(client.get(f"/cases/{case_id}"))
        for field in (
            "case_id",
            "playbook_id",
            "state",
            "finding_count",
            "hypothesis_count",
            "recommendation_count",
        ):
            assert field in data

    def test_investigation_response_nested_fields(
        self,
        client: TestClient,
        correlated_case: str,
    ) -> None:
        data = _assert_envelope(client.post(f"/cases/{correlated_case}/investigate"))
        for section in ("analysis", "discovery", "quality", "recommendation", "change_package"):
            assert section in data

    def test_error_response_schema_on_404(self, client: TestClient) -> None:
        body = _assert_error(client.get("/cases/CASE-missing"), 404)
        assert set(body.keys()) >= {"success", "error", "message", "request_id", "timestamp"}

    def test_validation_error_includes_details(self, client: TestClient) -> None:
        body = _assert_error(client.post("/cases", json={}), 422)
        assert "details" in body


class TestApiArchitecture:
    @pytest.mark.parametrize(
        "module_name",
        [
            "api.routers.cases",
            "api.routers.evidence",
            "api.routers.investigation",
            "api.routers.brain",
            "api.routers.reports",
            "api.routers.change_package",
            "api.routers.validation",
        ],
    )
    def test_routers_do_not_import_runtime_engine(self, module_name: str) -> None:
        import importlib

        module = importlib.import_module(module_name)
        source = inspect.getsource(module)
        assert "RuntimeEngine" not in source
        assert "HypothesisEngine" not in source

    def test_routers_delegate_to_voicepilot_service(self) -> None:
        import importlib

        cases = importlib.import_module("api.routers.cases")
        source = inspect.getsource(cases)
        assert "VoicePilotService" in source
        assert "service.create_case" in source


class TestServiceIntegration:
    def test_evidence_then_status_via_api(self, client: TestClient, case_id: str) -> None:
        raw_text = SAMPLE_EVIDENCE.read_text(encoding="utf-8")
        client.post(
            f"/cases/{case_id}/evidence",
            json={"command": "show sip-ua status", "content": raw_text},
        )
        data = _assert_envelope(client.get(f"/cases/{case_id}/status"))
        assert data["state"] in {"INTAKE", "DISCOVERY", "COLLECTION", "ANALYSIS"}

    def test_delete_removes_case_from_service(
        self,
        client: TestClient,
        service: VoicePilotService,
        case_id: str,
    ) -> None:
        client.delete(f"/cases/{case_id}")
        assert service.list_cases() == [] or case_id not in {
            item.case_id for item in service.list_cases()
        }
