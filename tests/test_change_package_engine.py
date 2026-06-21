"""Tests for the Engineering Change Package engine."""

from __future__ import annotations

import dataclasses
import inspect
from pathlib import Path

import pytest

from change_package import (
    EngineeringChangePackage,
    EngineeringChangePackageEngine,
    READ_ONLY_NOTICE,
    format_change_package_markdown,
)
from domain.models import Case
from cli.voicepilot_cli import (
    main,
    run_change_package_case,
    run_change_package_scenario,
)
from domain.enums import Severity
from domain.value_objects import AffectedScope, PlatformRef, SymptomSummary
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry
from runtime.runtime_engine import RuntimeEngine
from runtime.scenario_runner import (
    VP_CUBE_0001_PLAYBOOK_ID,
    default_scenarios_root,
    run_scenario_to_correlation,
)
from services import VoicePilotService
from shared.config import RuntimeConfig

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_ROOT = REPO_ROOT / "plugins"
PLAYBOOK_ID = VP_CUBE_0001_PLAYBOOK_ID
SCENARIOS_ROOT = default_scenarios_root(PLAYBOOK_ID, repo_root=REPO_ROOT)

FORBIDDEN_EXECUTION_PHRASES = (
    "auto-remediation",
    "auto remediation",
    "push configuration to",
    "will execute configuration",
    "reload device",
    "save configuration to",
)


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
    yield engine
    engine.shutdown()


@pytest.fixture
def sip_ua_case() -> tuple[RuntimeEngine, str]:
    scenario_dir = SCENARIOS_ROOT / "sip_ua_disabled"
    runtime, case_id = run_scenario_to_correlation(scenario_dir)
    runtime.generate_recommendation(case_id)
    try:
        yield runtime, case_id
    finally:
        runtime.shutdown()


class TestChangePackageModels:
    def test_package_model_is_immutable(self) -> None:
        engine = EngineeringChangePackageEngine(knowledge_engine=None)
        case = Case.create(
            title="Test",
            symptom=SymptomSummary(summary="test"),
            severity=Severity.MEDIUM,
            business_impact="test",
            affected_scope=AffectedScope(),
            platform=PlatformRef(vendor="Cisco", products=("CUBE",)),
        )
        package = engine.generate_for_case(case)
        with pytest.raises(dataclasses.FrozenInstanceError):
            package.title = "changed"  # type: ignore[misc]


class TestChangePackageEngine:
    def test_engine_generates_package_from_sip_ua_disabled_case(self, sip_ua_case) -> None:
        runtime, case_id = sip_ua_case
        case = runtime.case_manager.load_case(case_id)
        engine = EngineeringChangePackageEngine(knowledge_engine=None)
        package = engine.generate_for_case(case)

        assert package.case_id == case_id
        assert package.root_cause is not None
        assert "SIP" in package.root_cause or "sip" in package.root_cause.lower()
        assert package.recommended_changes

    def test_read_only_notice_always_present(self, sip_ua_case) -> None:
        _, case_id = sip_ua_case
        runtime, _ = sip_ua_case
        package = runtime.generate_change_package(case_id)

        assert package.read_only_notice == READ_ONLY_NOTICE
        markdown = format_change_package_markdown(package)
        assert READ_ONLY_NOTICE in markdown
        assert "## Read-Only Notice" in markdown

    def test_recommended_change_includes_config_and_rollback_examples(self, sip_ua_case) -> None:
        runtime, case_id = sip_ua_case
        package = runtime.generate_change_package(case_id)

        assert package.configuration_examples
        assert package.rollback_examples
        change = package.recommended_changes[0]
        assert change.config_example
        assert change.rollback_example
        assert "Example configuration for engineer review" in change.config_example

    def test_verification_steps_included(self, sip_ua_case) -> None:
        runtime, case_id = sip_ua_case
        package = runtime.generate_change_package(case_id)

        assert package.verification_steps
        assert all(step.expected_result for step in package.verification_steps)

    def test_risk_level_assigned(self, sip_ua_case) -> None:
        runtime, case_id = sip_ua_case
        package = runtime.generate_change_package(case_id)

        assert package.risk_level.value in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        assert package.risk_summary

    def test_missing_recommendation_handled_gracefully(self) -> None:
        engine = EngineeringChangePackageEngine(knowledge_engine=None)
        case = Case.create(
            title="Empty case",
            symptom=SymptomSummary(summary="No evidence"),
            severity=Severity.MEDIUM,
            business_impact="test",
            affected_scope=AffectedScope(),
            platform=PlatformRef(vendor="Cisco", products=("CUBE",)),
        )
        package = engine.generate_for_case(case)

        assert "Insufficient" in package.executive_summary
        assert not package.recommended_changes
        assert package.read_only_notice == READ_ONLY_NOTICE

    def test_markdown_report_contains_all_major_sections(self, sip_ua_case) -> None:
        runtime, case_id = sip_ua_case
        package = runtime.generate_change_package(case_id)
        markdown = format_change_package_markdown(package)

        for section in (
            "# VoicePilot Engineering Change Package",
            "## Read-Only Notice",
            "## Executive Summary",
            "## Root Cause",
            "## Confidence",
            "## Evidence Reviewed",
            "## Affected Components",
            "## Recommended Changes",
            "## Configuration Examples",
            "## Rollback Examples",
            "## Risk Assessment",
            "## Prerequisites",
            "## Assumptions",
            "## Verification Steps",
            "## Post-Change Validation",
            "## Related Knowledge Assets",
            "## Vendor References",
            "## Approvals",
            "## Engineer Notes",
        ):
            assert section in markdown

    def test_no_execution_or_auto_remediation_language(self, sip_ua_case) -> None:
        runtime, case_id = sip_ua_case
        package = runtime.generate_change_package(case_id)
        markdown = format_change_package_markdown(package).lower()

        body = markdown.replace(READ_ONLY_NOTICE.lower(), "")
        for phrase in FORBIDDEN_EXECUTION_PHRASES:
            assert phrase not in body

        engine_source = inspect.getsource(EngineeringChangePackageEngine)
        for phrase in ("push_config", "execute_config", "auto_remediat", "reload_device"):
            assert phrase not in engine_source


class TestChangePackageIntegration:
    def test_runtime_engine_stores_and_returns_package(self, sip_ua_case) -> None:
        runtime, case_id = sip_ua_case
        package = runtime.generate_change_package(case_id)
        case = runtime.case_manager.load_case(case_id)

        assert case.change_package is not None
        assert case.change_package.package_id == package.package_id

    def test_voicepilot_service_returns_dto(self, sip_ua_case) -> None:
        runtime, case_id = sip_ua_case
        service = VoicePilotService(runtime_engine=runtime)
        result = service.generate_change_package(case_id)

        assert result.case_id == case_id
        assert result.package_id
        assert result.risk_level
        assert result.title
        assert "# VoicePilot Engineering Change Package" in result.markdown


class TestChangePackageCli:
    def test_cli_change_package_scenario(self, tmp_path: Path) -> None:
        output_path = tmp_path / "change_package.md"
        assert (
            main(
                [
                    "change-package-scenario",
                    PLAYBOOK_ID,
                    "--scenario",
                    "sip_ua_disabled",
                    "--output",
                    str(output_path),
                ]
            )
            == 0
        )
        assert output_path.is_file()
        content = output_path.read_text(encoding="utf-8")
        assert READ_ONLY_NOTICE in content
        assert "## Recommended Changes" in content

    def test_run_change_package_scenario_writes_output_file(self, tmp_path: Path) -> None:
        output_path = tmp_path / "pkg.md"
        output: list[str] = []
        code = run_change_package_scenario(
            PLAYBOOK_ID,
            output.append,
            scenario_id="sip_ua_disabled",
            output_path=output_path,
            repo_root=REPO_ROOT,
        )
        assert code == 0
        assert output_path.exists()
        assert "Engineering Change Package" in output_path.read_text(encoding="utf-8")

    def test_run_change_package_case_not_found(self) -> None:
        output: list[str] = []
        code = run_change_package_case("CASE-does-not-exist", output.append)
        assert code == 1
        assert "Case not found" in "\n".join(output)
