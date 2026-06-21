"""Tests for Cisco CUCM investigation engine (Sprint 11.3)."""

from __future__ import annotations

from pathlib import Path

import pytest

from change_package import EngineeringChangePackageEngine, READ_ONLY_NOTICE, format_change_package_markdown
from cli.voicepilot_cli import build_runtime_engine, main
from health.health_engine import HealthEngine
from health.health_models import HealthStatus
from health.builtin_rules import register_builtin_rules
from health.health_rule_registry import HealthRuleRegistry
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from model.cucm_objects import CUCMNode, Phone, SIPTrunk
from parser.parser_context import ParserContext
from runtime.analysis_engine import FINDING_SOURCE_PARSER
from runtime.cucm_investigation import (
    HYP_PHONE_REGISTRATION,
    HYP_SIP_TRUNK,
    VP_CUCM_0001_CORRELATION_RULES,
    VP_CUCM_0001_PLAYBOOK_ID,
    VP_CUCM_0001_RULES,
)
from runtime.evidence_collection import initialize_evidence_collection, submit_evidence
from runtime.parser_bootstrap import build_default_parser_engine
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry
from runtime.runtime_engine import RuntimeEngine
from runtime.scenario_runner import default_scenarios_root, run_scenario_to_correlation
from shared.config import RuntimeConfig
from topology.relationship_builder import RelationshipBuilder
from topology.relationship_types import RelationshipType
from topology.topology_builder import TopologyBuilder

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_ROOT = REPO_ROOT / "plugins"
PLAYBOOK_ID = VP_CUCM_0001_PLAYBOOK_ID
SCENARIOS_ROOT = default_scenarios_root(PLAYBOOK_ID, repo_root=REPO_ROOT)
CUCM_INTAKE_ANSWERS = [
    "yes",
    "2026-06-19",
    "phone registration and call routing failure",
    "hq site users",
    "yes",
]
_CUCM_OBJECT_DEFAULTS = {
    "vendor": "cisco",
    "platform": "CUCM",
    "hostname": "cucm-pub",
    "source_parser": "test",
    "source_command": "test",
    "source_evidence_id": "EVD-test",
}


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
def parser_engine():
    engine = build_default_parser_engine()
    if engine is None:
        pytest.skip("Cisco parser pack not available")
    return engine


@pytest.fixture
def parser_context() -> ParserContext:
    return ParserContext(
        vendor="cisco",
        case_id="CASE-cucm-test",
        evidence_id="EVD-cucm-test",
        device_id="DEV-cucm-pub",
        platform="CUCM",
        ios_version="14.0",
        hostname="cucm-pub",
    )


class TestCucmPlaybook:
    def test_playbook_loads_from_catalog(self, runtime_engine: RuntimeEngine) -> None:
        playbook = runtime_engine.playbook_catalog.get(PLAYBOOK_ID)
        assert playbook.playbook_id == PLAYBOOK_ID
        assert playbook.title == "Cisco CUCM Investigation"


class TestCucmParsers:
    def test_risdb_parser_extracts_phone_not_registered(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "phone_not_registered" / "show_risdb_query_phone.txt").read_text()
        result = parser_engine.parse(sample, parser_context, command="show risdb query phone")
        signals = {finding.signal for finding in result.findings}
        assert "phone_not_registered" in signals
        phone_objects = [obj for obj in result.voice_objects if isinstance(obj, Phone)]
        assert phone_objects
        assert any(phone.registered is False for phone in phone_objects)

    def test_sip_trunk_parser_extracts_trunk_down(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "sip_trunk_down" / "show_sip_trunk.txt").read_text()
        result = parser_engine.parse(sample, parser_context, command="show sip trunk")
        signals = {finding.signal for finding in result.findings}
        assert "sip_trunk_down" in signals
        assert any(isinstance(obj, SIPTrunk) for obj in result.voice_objects)

    def test_dbreplication_parser_extracts_unhealthy(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "db_replication" / "utils_dbreplication_runtimestate.txt").read_text()
        result = parser_engine.parse(
            sample, parser_context, command="utils dbreplication runtimestate"
        )
        signals = {finding.signal for finding in result.findings}
        assert "db_replication_unhealthy" in signals


class TestCucmAnalysisIntegration:
    def test_analysis_uses_parser_findings(self, runtime_engine: RuntimeEngine) -> None:
        scenario_dir = SCENARIOS_ROOT / "phone_not_registered"
        turn = runtime_engine.start_investigation(PLAYBOOK_ID)
        for answer in CUCM_INTAKE_ANSWERS:
            turn = runtime_engine.submit_answer(turn.case_id, turn.question_id, answer)
        case = runtime_engine.case_manager.load_case(turn.case_id)
        playbook = runtime_engine.playbook_catalog.get(PLAYBOOK_ID)
        initialize_evidence_collection(case, runtime_engine.case_manager, playbook)
        case = runtime_engine.case_manager.load_case(case.case_id)

        submit_evidence(
            case,
            runtime_engine.case_manager,
            "show risdb query phone",
            (scenario_dir / "show_risdb_query_phone.txt").read_text(encoding="utf-8"),
        )
        case = runtime_engine.case_manager.load_case(case.case_id)
        runtime_engine.analyze_case(case.case_id)
        case = runtime_engine.case_manager.load_case(case.case_id)

        parser_findings = [
            finding
            for finding in case.analysis_findings
            if (finding.metadata or {}).get("source") == FINDING_SOURCE_PARSER
        ]
        assert parser_findings
        assert any(finding.signal == "phone_not_registered" for finding in parser_findings)
        assert any(isinstance(obj, Phone) for obj in case.voice_objects)


class TestCucmHypotheses:
    def test_phone_registration_hypothesis_generated(self, runtime_engine: RuntimeEngine) -> None:
        scenario_dir = SCENARIOS_ROOT / "phone_not_registered"
        _, case_id = run_scenario_to_correlation(
            scenario_dir, playbook_id=PLAYBOOK_ID, runtime=runtime_engine
        )
        case = runtime_engine.case_manager.load_case(case_id)
        titles = {hypothesis.title for hypothesis in case.hypotheses}
        assert HYP_PHONE_REGISTRATION in titles

    def test_cucm_rules_cover_ten_hypotheses(self) -> None:
        assert len(VP_CUCM_0001_RULES) == 10


class TestCucmCorrelation:
    def test_replication_phone_correlation_rule_exists(self) -> None:
        rule_ids = {rule.rule_id for rule in VP_CUCM_0001_CORRELATION_RULES}
        assert "replication_phone_registration" in rule_ids

    def test_callmanager_correlation_boosts_confidence(self) -> None:
        scenario_dir = SCENARIOS_ROOT / "callmanager_service_down"
        runtime, case_id = run_scenario_to_correlation(scenario_dir, playbook_id=PLAYBOOK_ID)
        try:
            runtime.correlate_case(case_id)
            case = runtime.case_manager.load_case(case_id)
            top = min(case.hypotheses, key=lambda item: item.rank or 999)
            assert "CallManager" in top.title
            assert top.confidence >= 94.0
        finally:
            runtime.shutdown()


class TestCucmTopology:
    def test_cucm_relationships_built(self) -> None:
        phone = Phone.create(**_CUCM_OBJECT_DEFAULTS, name="SEP0011111111", registered=False)
        node = CUCMNode.create(**_CUCM_OBJECT_DEFAULTS, name="cucm-pub", role="publisher")
        trunk = SIPTrunk.create(**_CUCM_OBJECT_DEFAULTS, name="SIP-ITSP-01", status="down")
        builder = RelationshipBuilder()
        relationships = builder.build([phone, node, trunk])
        assert any(rel.relationship_type == RelationshipType.REGISTERED_TO for rel in relationships)

    def test_topology_builder_includes_cucm_objects(self) -> None:
        phone = Phone.create(**_CUCM_OBJECT_DEFAULTS, name="SEP0011111111", registered=False)
        node = CUCMNode.create(**_CUCM_OBJECT_DEFAULTS, name="cucm-pub", role="publisher")
        topology = TopologyBuilder().build([phone, node])
        assert topology.relationships


class TestCucmHealth:
    def test_phone_not_registered_rule_fails(self) -> None:
        phone = Phone.create(**_CUCM_OBJECT_DEFAULTS, name="SEP0011111111", registered=False)
        topology = TopologyBuilder().build([phone])
        results = HealthEngine().evaluate_object(phone, topology)
        failing = [result for result in results if result.status == HealthStatus.FAIL]
        assert any(result.rule_id == "phone_not_registered" for result in failing)

    def test_cucm_health_rules_registered(self) -> None:
        registry = HealthRuleRegistry()
        register_builtin_rules(registry)
        rule_ids = {rule.id for rule in registry.all_rules()}
        cucm_rules = {
            "phone_not_registered",
            "db_replication_unhealthy",
            "callmanager_service_stopped",
            "tftp_service_stopped",
            "certificate_expired",
            "sip_trunk_down",
            "ris_unavailable",
            "route_pattern_missing",
            "css_missing",
            "partition_missing",
        }
        assert cucm_rules.issubset(rule_ids)


class TestCucmRecommendations:
    def test_recommendation_references_cucm_runbooks(self, runtime_engine: RuntimeEngine) -> None:
        scenario_dir = SCENARIOS_ROOT / "sip_trunk_down"
        _, case_id = run_scenario_to_correlation(
            scenario_dir, playbook_id=PLAYBOOK_ID, runtime=runtime_engine
        )
        runtime_engine.generate_recommendation(case_id)
        case = runtime_engine.case_manager.load_case(case_id)
        assert case.recommendations
        recommendation = case.recommendations[-1]
        text = " ".join(
            filter(
                None,
                [
                    recommendation.rationale,
                    recommendation.likely_root_cause,
                    " ".join(recommendation.recommended_actions or ()),
                ],
            )
        )
        assert "VP-CISCO-CUCM" in text or HYP_SIP_TRUNK in (recommendation.likely_root_cause or "")


class TestCucmChangePackage:
    def test_change_package_for_phone_not_registered(self) -> None:
        scenario_dir = SCENARIOS_ROOT / "phone_not_registered"
        runtime, case_id = run_scenario_to_correlation(scenario_dir, playbook_id=PLAYBOOK_ID)
        try:
            runtime.generate_recommendation(case_id)
            package = runtime.generate_change_package(case_id)
            assert package.read_only_notice == READ_ONLY_NOTICE
            assert package.recommended_changes or package.root_cause
            markdown = format_change_package_markdown(package)
            assert "VP-CISCO-CUCM" in markdown or "registration" in markdown.lower()
        finally:
            runtime.shutdown()


class TestCucmCli:
    def test_investigate_vp_cucm_0001_starts(self) -> None:
        runtime = build_runtime_engine(PLUGINS_ROOT)
        try:
            runtime.start()
            turn = runtime.start_investigation(PLAYBOOK_ID)
            assert turn.case_id
            case = runtime.case_manager.load_case(turn.case_id)
            assert case.playbook_id == PLAYBOOK_ID
        finally:
            runtime.shutdown()

    def test_scenarios_vp_cucm_0001(self) -> None:
        assert main(["scenarios", PLAYBOOK_ID]) == 0

    def test_report_scenario_executive(self, tmp_path: Path) -> None:
        output = tmp_path / "report.md"
        assert (
            main(
                [
                    "report-scenario",
                    PLAYBOOK_ID,
                    "--scenario",
                    "phone_not_registered",
                    "--type",
                    "executive",
                    "--output",
                    str(output),
                ]
            )
            == 0
        )
        assert output.is_file()
        assert "VoicePilot" in output.read_text(encoding="utf-8")

    def test_change_package_scenario(self, tmp_path: Path) -> None:
        output = tmp_path / "change.md"
        assert (
            main(
                [
                    "change-package-scenario",
                    PLAYBOOK_ID,
                    "--scenario",
                    "phone_not_registered",
                    "--output",
                    str(output),
                ]
            )
            == 0
        )
        assert READ_ONLY_NOTICE in output.read_text(encoding="utf-8")
