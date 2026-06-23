"""Tests for Genesys Cloud investigation engine (Sprint 14.4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from change_package import EngineeringChangePackageEngine, READ_ONLY_NOTICE, format_change_package_markdown
from change_package.change_engine import VP_GENESYS_0001_CHANGE_TEMPLATES
from cli.voicepilot_cli import build_runtime_engine, main
from discovery.planner_bootstrap import default_discovery_registry
from health.health_engine import HealthEngine
from health.health_models import HealthStatus
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from investigation_quality.quality_engine import InvestigationQualityEngine
from model.genesys_objects import EdgeDevice, Queue
from parser.parser_context import ParserContext
from runtime.analysis_engine import FINDING_SOURCE_PARSER
from runtime.evidence_collection import initialize_evidence_collection, submit_evidence
from runtime.genesys_investigation import (
    GENESYS_EVIDENCE_FILES,
    GENESYS_INTAKE_ANSWERS,
    HYP_AGENT_LOGIN,
    HYP_ARCHITECT_PUBLISH,
    HYP_BYOC_CLOUD,
    HYP_BYOC_PREMISES,
    HYP_DATA_ACTION,
    HYP_EDGE_OFFLINE,
    HYP_FLOW,
    HYP_MEDIA,
    HYP_OAUTH,
    HYP_QUEUE,
    HYP_SIP_OPTIONS,
    HYP_TLS_CERT,
    VP_GENESYS_0001_ACTION_PLANS,
    VP_GENESYS_0001_CORRELATION_RULES,
    VP_GENESYS_0001_PLAYBOOK_ID,
    VP_GENESYS_0001_RULES,
)
from runtime.intake_summary import build_intake_summary
from runtime.parser_bootstrap import build_default_parser_engine
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry
from runtime.runtime_engine import RuntimeEngine
from runtime.scenario_runner import default_scenarios_root, run_scenario_to_correlation
from shared.config import RuntimeConfig
from topology.topology_builder import TopologyBuilder

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_ROOT = REPO_ROOT / "plugins"
PLAYBOOK_ID = VP_GENESYS_0001_PLAYBOOK_ID
SCENARIOS_ROOT = default_scenarios_root(PLAYBOOK_ID, repo_root=REPO_ROOT)

_GENESYS_DEFAULTS = {
    "vendor": "genesys",
    "platform": "Genesys Cloud",
    "hostname": "genesys-lab.example.com",
    "source_parser": "test",
    "source_command": "test",
    "source_evidence_id": "EVD-test",
}

SCENARIO_HYPOTHESES = [
    ("oauth_failure", HYP_OAUTH),
    ("edge_offline", HYP_EDGE_OFFLINE),
    ("byoc_cloud_trunk_unavailable", HYP_BYOC_CLOUD),
    ("byoc_premises_edge_unavailable", HYP_BYOC_PREMISES),
    ("sip_options_failure", HYP_SIP_OPTIONS),
    ("tls_certificate_expired", HYP_TLS_CERT),
    ("queue_unavailable", HYP_QUEUE),
    ("agent_not_logged_in", HYP_AGENT_LOGIN),
    ("architect_flow_failure", HYP_FLOW),
    ("data_action_failure", HYP_DATA_ACTION),
    ("webrtc_media_failure", HYP_MEDIA),
    ("outbound_campaign_failure", "Outbound campaign failure"),
]

GENESYS_DISCOVERY_RULE_IDS = [
    "genesys_organization_export_missing",
    "genesys_users_export_missing",
    "genesys_queues_export_missing",
    "genesys_queue_members_export_missing",
    "genesys_agents_export_missing",
    "genesys_presence_export_missing",
    "genesys_flows_export_missing",
    "genesys_architect_export_missing",
    "genesys_data_actions_export_missing",
    "genesys_byoc_cloud_export_missing",
    "genesys_byoc_premises_export_missing",
    "genesys_edge_devices_export_missing",
    "genesys_recording_policies_export_missing",
    "genesys_campaigns_export_missing",
    "genesys_skills_export_missing",
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
    yield engine
    engine.shutdown()


@pytest.fixture
def parser_engine():
    engine = build_default_parser_engine()
    if engine is None:
        pytest.skip("Parser pack not available")
    return engine


@pytest.fixture
def parser_context() -> ParserContext:
    return ParserContext(
        vendor="genesys",
        case_id="CASE-genesys-test",
        evidence_id="EVD-genesys-test",
        platform="Genesys Cloud",
        hostname="genesys-lab.example.com",
    )


class TestGenesysPlaybook:
    def test_playbook_loads_from_catalog(self, runtime_engine: RuntimeEngine) -> None:
        playbook = runtime_engine.playbook_catalog.get(PLAYBOOK_ID)
        assert playbook.playbook_id == PLAYBOOK_ID
        assert playbook.title == "Genesys Cloud Investigation"

    def test_intake_summary_lists_required_commands(self, runtime_engine: RuntimeEngine) -> None:
        turn = runtime_engine.start_investigation(PLAYBOOK_ID)
        for answer in GENESYS_INTAKE_ANSWERS:
            turn = runtime_engine.submit_answer(turn.case_id, turn.question_id, answer)
        case = runtime_engine.case_manager.load_case(turn.case_id)
        playbook = runtime_engine.playbook_catalog.get(PLAYBOOK_ID)
        summary = build_intake_summary(case, playbook)
        assert summary.next_required_commands == [command for command, _ in GENESYS_EVIDENCE_FILES]


class TestGenesysParsers:
    def test_organization_parser_extracts_oauth_failure(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "oauth_failure" / "organization_export.csv").read_text()
        result = parser_engine.parse(sample, parser_context, command="organization-export")
        signals = {finding.signal for finding in result.findings}
        assert "oauth_failure" in signals
        assert "token_expired" in signals

    def test_edge_devices_parser_extracts_offline(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "edge_offline" / "edge_devices_export.json").read_text()
        result = parser_engine.parse(sample, parser_context, command="edge-devices-export")
        signals = {finding.signal for finding in result.findings}
        assert "edge_offline" in signals
        assert any(isinstance(obj, EdgeDevice) for obj in result.voice_objects)

    def test_byoc_cloud_parser_extracts_trunk_failure(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "byoc_cloud_trunk_unavailable" / "byoc_cloud_trunks_export.txt").read_text()
        result = parser_engine.parse(sample, parser_context, command="byoc-cloud-trunks-export")
        assert "byoc_cloud_trunk_failure" in {finding.signal for finding in result.findings}

    def test_byoc_cloud_parser_extracts_sip_options_failure(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "sip_options_failure" / "byoc_cloud_trunks_export.txt").read_text()
        result = parser_engine.parse(sample, parser_context, command="byoc-cloud-trunks-export")
        assert "sip_options_failure" in {finding.signal for finding in result.findings}

    def test_byoc_cloud_parser_extracts_tls_expired(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "tls_certificate_expired" / "byoc_cloud_trunks_export.txt").read_text()
        result = parser_engine.parse(sample, parser_context, command="byoc-cloud-trunks-export")
        signals = {finding.signal for finding in result.findings}
        assert "tls_certificate_expired" in signals
        assert "tls_negotiation_failure" in signals

    def test_queues_parser_extracts_unavailable(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "queue_unavailable" / "queues_export.csv").read_text()
        result = parser_engine.parse(sample, parser_context, command="queues-export")
        signals = {finding.signal for finding in result.findings}
        assert "queue_unavailable" in signals
        assert any(isinstance(obj, Queue) for obj in result.voice_objects)

    def test_agents_parser_extracts_not_logged_in(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "agent_not_logged_in" / "agents_export.txt").read_text()
        result = parser_engine.parse(sample, parser_context, command="agents-export")
        assert "agent_not_logged_in" in {finding.signal for finding in result.findings}

    def test_flows_parser_extracts_failure(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "architect_flow_failure" / "flows_export.csv").read_text()
        result = parser_engine.parse(sample, parser_context, command="flows-export")
        assert "call_flow_failure" in {finding.signal for finding in result.findings}

    def test_data_actions_parser_extracts_failure(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "data_action_failure" / "data_actions_export.csv").read_text()
        result = parser_engine.parse(sample, parser_context, command="data-actions-export")
        assert "data_action_failure" in {finding.signal for finding in result.findings}

    def test_organization_parser_extracts_media_webrtc_failure(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "webrtc_media_failure" / "organization_export.csv").read_text()
        result = parser_engine.parse(sample, parser_context, command="organization-export")
        signals = {finding.signal for finding in result.findings}
        assert "media_service_unavailable" in signals
        assert "webrtc_failure" in signals

    def test_campaigns_parser_extracts_failure(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "outbound_campaign_failure" / "campaigns_export.csv").read_text()
        result = parser_engine.parse(sample, parser_context, command="campaigns-export")
        assert "outbound_campaign_failure" in {finding.signal for finding in result.findings}


class TestGenesysAnalysisIntegration:
    def test_analysis_uses_parser_findings(self, runtime_engine: RuntimeEngine) -> None:
        scenario_dir = SCENARIOS_ROOT / "oauth_failure"
        turn = runtime_engine.start_investigation(PLAYBOOK_ID)
        for answer in GENESYS_INTAKE_ANSWERS:
            turn = runtime_engine.submit_answer(turn.case_id, turn.question_id, answer)
        case = runtime_engine.case_manager.load_case(turn.case_id)
        playbook = runtime_engine.playbook_catalog.get(PLAYBOOK_ID)
        initialize_evidence_collection(case, runtime_engine.case_manager, playbook)
        submit_evidence(
            case,
            runtime_engine.case_manager,
            "organization-export",
            (scenario_dir / "organization_export.csv").read_text(encoding="utf-8"),
        )
        runtime_engine.analyze_case(case.case_id)
        case = runtime_engine.case_manager.load_case(case.case_id)
        parser_findings = [
            finding
            for finding in case.analysis_findings
            if (finding.metadata or {}).get("source") == FINDING_SOURCE_PARSER
        ]
        assert parser_findings
        assert any(finding.signal == "oauth_failure" for finding in parser_findings)


class TestGenesysHypotheses:
    @pytest.mark.parametrize("rule", VP_GENESYS_0001_RULES, ids=lambda rule: rule.rule_id)
    def test_hypothesis_rule_has_required_signals(self, rule) -> None:
        assert rule.required_signals
        assert rule.confidence >= 80.0

    @pytest.mark.parametrize(("scenario", "expected_title"), SCENARIO_HYPOTHESES)
    def test_hypothesis_generated_for_scenario(
        self,
        runtime_engine: RuntimeEngine,
        scenario: str,
        expected_title: str,
    ) -> None:
        _, case_id = run_scenario_to_correlation(
            SCENARIOS_ROOT / scenario,
            playbook_id=PLAYBOOK_ID,
            runtime=runtime_engine,
        )
        case = runtime_engine.case_manager.load_case(case_id)
        titles = {hypothesis.title for hypothesis in case.hypotheses}
        assert expected_title in titles

    def test_genesys_rules_cover_twenty_seven_hypotheses(self) -> None:
        assert len(VP_GENESYS_0001_RULES) == 27


class TestGenesysActionPlans:
    @pytest.mark.parametrize("rule_id", [rule.rule_id for rule in VP_GENESYS_0001_RULES])
    def test_action_plan_exists(self, rule_id: str) -> None:
        assert rule_id in VP_GENESYS_0001_ACTION_PLANS
        plan = VP_GENESYS_0001_ACTION_PLANS[rule_id]
        assert plan.recommended_actions
        assert any("VP-GENESYS-CLOUD-RB-" in action for action in plan.recommended_actions)

    @pytest.mark.parametrize("rule_id", sorted(VP_GENESYS_0001_CHANGE_TEMPLATES))
    def test_change_template_exists(self, rule_id: str) -> None:
        template = VP_GENESYS_0001_CHANGE_TEMPLATES[rule_id]
        assert template.current_state
        assert template.recommended_state
        assert any(ref.startswith("VP-GENESYS-CLOUD-") for ref in template.vendor_references)


class TestGenesysCorrelation:
    @pytest.mark.parametrize("rule_id", [rule.rule_id for rule in VP_GENESYS_0001_CORRELATION_RULES])
    def test_correlation_rule_exists(self, rule_id: str) -> None:
        assert rule_id in {rule.rule_id for rule in VP_GENESYS_0001_CORRELATION_RULES}

    def test_oauth_correlation_boosts_confidence(self) -> None:
        scenario_dir = SCENARIOS_ROOT / "oauth_failure"
        runtime, case_id = run_scenario_to_correlation(scenario_dir, playbook_id=PLAYBOOK_ID)
        try:
            runtime.correlate_case(case_id)
            case = runtime.case_manager.load_case(case_id)
            top = min(case.hypotheses, key=lambda item: item.rank or 999)
            assert top.title == HYP_OAUTH
            assert top.confidence >= 98.0
        finally:
            runtime.shutdown()

    def test_byoc_premises_correlation_boosts_confidence(self) -> None:
        scenario_dir = SCENARIOS_ROOT / "byoc_premises_edge_unavailable"
        runtime, case_id = run_scenario_to_correlation(scenario_dir, playbook_id=PLAYBOOK_ID)
        try:
            runtime.correlate_case(case_id)
            case = runtime.case_manager.load_case(case_id)
            top = min(case.hypotheses, key=lambda item: item.rank or 999)
            assert top.title == HYP_BYOC_PREMISES
            assert top.confidence >= 98.0
        finally:
            runtime.shutdown()

    def test_tls_correlation_boosts_confidence(self) -> None:
        scenario_dir = SCENARIOS_ROOT / "tls_certificate_expired"
        runtime, case_id = run_scenario_to_correlation(scenario_dir, playbook_id=PLAYBOOK_ID)
        try:
            runtime.correlate_case(case_id)
            case = runtime.case_manager.load_case(case_id)
            top = min(case.hypotheses, key=lambda item: item.rank or 999)
            assert top.title == HYP_TLS_CERT
            assert top.confidence >= 98.0
        finally:
            runtime.shutdown()

    def test_architect_flow_correlation_boosts_flow_hypothesis(self) -> None:
        scenario_dir = SCENARIOS_ROOT / "architect_flow_failure"
        runtime, case_id = run_scenario_to_correlation(scenario_dir, playbook_id=PLAYBOOK_ID)
        try:
            runtime.correlate_case(case_id)
            case = runtime.case_manager.load_case(case_id)
            top = min(case.hypotheses, key=lambda item: item.rank or 999)
            assert top.title == HYP_FLOW
            assert top.confidence >= 98.0
        finally:
            runtime.shutdown()

    def test_data_action_correlation_boosts_confidence(self) -> None:
        scenario_dir = SCENARIOS_ROOT / "data_action_failure"
        runtime, case_id = run_scenario_to_correlation(scenario_dir, playbook_id=PLAYBOOK_ID)
        try:
            runtime.correlate_case(case_id)
            case = runtime.case_manager.load_case(case_id)
            top = min(case.hypotheses, key=lambda item: item.rank or 999)
            assert top.title == HYP_DATA_ACTION
            assert top.confidence >= 98.0
        finally:
            runtime.shutdown()


class TestGenesysDiscoveryPlanner:
    @pytest.mark.parametrize("rule_id", GENESYS_DISCOVERY_RULE_IDS)
    def test_genesys_discovery_rules_registered(self, rule_id: str) -> None:
        registry = default_discovery_registry()
        rule_ids = {rule.id for rule in registry.all_rules()}
        assert rule_id in rule_ids

    def test_discovery_plan_requests_missing_organization_export(
        self, runtime_engine: RuntimeEngine
    ) -> None:
        turn = runtime_engine.start_investigation(PLAYBOOK_ID)
        for answer in GENESYS_INTAKE_ANSWERS:
            turn = runtime_engine.submit_answer(turn.case_id, turn.question_id, answer)
        case = runtime_engine.case_manager.load_case(turn.case_id)
        playbook = runtime_engine.playbook_catalog.get(PLAYBOOK_ID)
        initialize_evidence_collection(case, runtime_engine.case_manager, playbook)
        plan = runtime_engine.plan_discovery(turn.case_id)
        commands = {request.command for request in plan.requests}
        assert "organization-export" in commands


class TestGenesysInvestigationQuality:
    def test_quality_scores_complete_genesys_scenario(self) -> None:
        scenario_dir = SCENARIOS_ROOT / "queue_unavailable"
        runtime, case_id = run_scenario_to_correlation(scenario_dir, playbook_id=PLAYBOOK_ID)
        try:
            report = runtime.evaluate_investigation_quality(case_id)
            assert report.overall_score >= 75
            assert report.ready_for_recommendation
        finally:
            runtime.shutdown()

    def test_quality_engine_metric_registered(self) -> None:
        engine = InvestigationQualityEngine()
        assert engine.registry.all_metrics()


class TestGenesysRecommendations:
    def test_recommendation_references_genesys_runbooks(self, runtime_engine: RuntimeEngine) -> None:
        _, case_id = run_scenario_to_correlation(
            SCENARIOS_ROOT / "queue_unavailable",
            playbook_id=PLAYBOOK_ID,
            runtime=runtime_engine,
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
        assert "VP-GENESYS-CLOUD" in text or HYP_QUEUE in (recommendation.likely_root_cause or "")

    def test_oauth_hypothesis_action_plan_references_runbook(self) -> None:
        plan = VP_GENESYS_0001_ACTION_PLANS["HYP-GENESYS-OAUTH"]
        assert any("VP-GENESYS-CLOUD-RB-001" in action for action in plan.recommended_actions)
        assert any("VP-GENESYS-CLOUD-VG-001" in step for step in plan.verification_steps)


class TestGenesysChangePackage:
    def test_change_package_is_read_only_advisory(self) -> None:
        runtime, case_id = run_scenario_to_correlation(
            SCENARIOS_ROOT / "tls_certificate_expired",
            playbook_id=PLAYBOOK_ID,
        )
        try:
            runtime.generate_recommendation(case_id)
            package = runtime.generate_change_package(case_id)
            assert package.read_only_notice == READ_ONLY_NOTICE
            markdown = format_change_package_markdown(package)
            assert "Advisory" in markdown or "VP-GENESYS-CLOUD" in markdown
        finally:
            runtime.shutdown()

    def test_change_engine_generates_package(self) -> None:
        runtime, case_id = run_scenario_to_correlation(
            SCENARIOS_ROOT / "data_action_failure",
            playbook_id=PLAYBOOK_ID,
        )
        try:
            runtime.generate_recommendation(case_id)
            engine = EngineeringChangePackageEngine()
            case = runtime.case_manager.load_case(case_id)
            package = engine.generate_for_case(case)
            assert package.playbook_id == PLAYBOOK_ID
        finally:
            runtime.shutdown()

    def test_change_package_includes_vendor_references(self) -> None:
        runtime, case_id = run_scenario_to_correlation(
            SCENARIOS_ROOT / "agent_not_logged_in",
            playbook_id=PLAYBOOK_ID,
        )
        try:
            runtime.generate_recommendation(case_id)
            package = runtime.generate_change_package(case_id)
            assert any(ref.startswith("VP-GENESYS-CLOUD-") for ref in package.vendor_references)
        finally:
            runtime.shutdown()


class TestGenesysHealthIntegration:
    def test_health_evaluation_on_genesys_topology(self) -> None:
        queue = Queue.create(
            **_GENESYS_DEFAULTS,
            queue_id="queue-100",
            queue_name="Sales",
            state="Unavailable",
            metadata={"queue_unavailable": True},
        )
        topology = TopologyBuilder().build([queue])
        report = HealthEngine().evaluate_topology(topology)
        genesys_failures = [
            result
            for result in report.results
            if result.object_type.startswith("genesys_") and result.status == HealthStatus.FAIL
        ]
        assert genesys_failures


class TestGenesysEnterpriseReports:
    def test_executive_report_from_scenario(self, tmp_path: Path) -> None:
        assert (
            main(
                [
                    "report-scenario",
                    PLAYBOOK_ID,
                    "--scenario",
                    "oauth_failure",
                    "--type",
                    "executive",
                    "--output",
                    str(tmp_path / "report.md"),
                ]
            )
            == 0
        )
        content = (tmp_path / "report.md").read_text(encoding="utf-8")
        assert "VoicePilot" in content
        assert HYP_OAUTH in content


class TestGenesysCli:
    def test_investigate_vp_genesys_0001_starts(self) -> None:
        runtime = build_runtime_engine(PLUGINS_ROOT)
        try:
            runtime.start()
            turn = runtime.start_investigation(PLAYBOOK_ID)
            case = runtime.case_manager.load_case(turn.case_id)
            assert case.playbook_id == PLAYBOOK_ID
        finally:
            runtime.shutdown()

    def test_scenarios_vp_genesys_0001(self) -> None:
        assert main(["scenarios", PLAYBOOK_ID]) == 0

    def test_plan_scenario(self) -> None:
        assert main(["plan-scenario", PLAYBOOK_ID, "--scenario", "queue_unavailable"]) == 0

    def test_quality_scenario(self) -> None:
        assert main(["quality-scenario", PLAYBOOK_ID, "--scenario", "edge_offline"]) == 0

    def test_change_package_scenario(self, tmp_path: Path) -> None:
        output = tmp_path / "change.md"
        assert (
            main(
                [
                    "change-package-scenario",
                    PLAYBOOK_ID,
                    "--scenario",
                    "agent_not_logged_in",
                    "--output",
                    str(output),
                ]
            )
            == 0
        )
        assert READ_ONLY_NOTICE in output.read_text(encoding="utf-8")

    def test_validate_vp_genesys_0001(self) -> None:
        assert main(["validate", PLAYBOOK_ID]) == 0
