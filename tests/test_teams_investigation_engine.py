"""Tests for Microsoft Teams investigation engine (Sprint 12.4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from change_package import EngineeringChangePackageEngine, READ_ONLY_NOTICE, format_change_package_markdown
from cli.voicepilot_cli import build_runtime_engine, main
from discovery.planner_bootstrap import default_discovery_registry
from health.health_engine import HealthEngine
from health.health_models import HealthStatus
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from investigation_quality.quality_engine import InvestigationQualityEngine
from model.teams_objects import TeamsPstnGateway, TeamsUser
from parser.parser_context import ParserContext
from runtime.analysis_engine import FINDING_SOURCE_PARSER
from runtime.evidence_collection import initialize_evidence_collection, submit_evidence
from runtime.intake_summary import build_intake_summary
from runtime.parser_bootstrap import build_default_parser_engine
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry
from runtime.runtime_engine import RuntimeEngine
from runtime.scenario_runner import default_scenarios_root, run_scenario_to_correlation
from runtime.teams_investigation import (
    HYP_EMERGENCY_CALLING,
    HYP_SBC_UNREACHABLE,
    HYP_TEAMS_PHONE_LICENSE,
    TEAMS_EVIDENCE_FILES,
    TEAMS_INTAKE_ANSWERS,
    VP_TEAMS_0001_ACTION_PLANS,
    VP_TEAMS_0001_CORRELATION_RULES,
    VP_TEAMS_0001_PLAYBOOK_ID,
    VP_TEAMS_0001_RULES,
)
from change_package.change_engine import VP_TEAMS_0001_CHANGE_TEMPLATES
from shared.config import RuntimeConfig
from topology.topology_builder import TopologyBuilder

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS_ROOT = REPO_ROOT / "plugins"
PLAYBOOK_ID = VP_TEAMS_0001_PLAYBOOK_ID
SCENARIOS_ROOT = default_scenarios_root(PLAYBOOK_ID, repo_root=REPO_ROOT)

_TEAMS_DEFAULTS = {
    "vendor": "microsoft",
    "platform": "Teams Phone",
    "hostname": "contoso.onmicrosoft.com",
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
        pytest.skip("Parser pack not available")
    return engine


@pytest.fixture
def parser_context() -> ParserContext:
    return ParserContext(
        vendor="microsoft",
        case_id="CASE-teams-test",
        evidence_id="EVD-teams-test",
        platform="Teams Phone",
        hostname="contoso.onmicrosoft.com",
    )


class TestTeamsPlaybook:
    def test_playbook_loads_from_catalog(self, runtime_engine: RuntimeEngine) -> None:
        playbook = runtime_engine.playbook_catalog.get(PLAYBOOK_ID)
        assert playbook.playbook_id == PLAYBOOK_ID
        assert playbook.title == "Microsoft Teams Phone Investigation"

    def test_intake_summary_lists_required_commands(self, runtime_engine: RuntimeEngine) -> None:
        turn = runtime_engine.start_investigation(PLAYBOOK_ID)
        for answer in TEAMS_INTAKE_ANSWERS:
            turn = runtime_engine.submit_answer(turn.case_id, turn.question_id, answer)
        case = runtime_engine.case_manager.load_case(turn.case_id)
        playbook = runtime_engine.playbook_catalog.get(PLAYBOOK_ID)
        summary = build_intake_summary(case, playbook)
        assert summary.next_required_commands == [command for command, _ in TEAMS_EVIDENCE_FILES]


class TestTeamsParsers:
    def test_online_user_parser_extracts_license_missing(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "teams_phone_license_missing" / "get_csonlineuser.txt").read_text()
        result = parser_engine.parse(sample, parser_context, command="get-csonlineuser")
        signals = {finding.signal for finding in result.findings}
        assert "teams_phone_license_missing" in signals
        assert any(isinstance(obj, TeamsUser) for obj in result.voice_objects)

    def test_pstn_gateway_parser_extracts_sbc_unreachable(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "direct_routing_sbc_unreachable" / "get_csonlinepstngateway.txt").read_text()
        result = parser_engine.parse(sample, parser_context, command="get-csonlinepstngateway")
        signals = {finding.signal for finding in result.findings}
        assert "direct_routing_sbc_unreachable" in signals
        assert any(isinstance(obj, TeamsPstnGateway) for obj in result.voice_objects)

    def test_pstn_gateway_parser_extracts_tls_expired(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "tls_certificate_expired" / "get_csonlinepstngateway.txt").read_text()
        result = parser_engine.parse(sample, parser_context, command="get-csonlinepstngateway")
        assert "tls_certificate_expired" in {finding.signal for finding in result.findings}

    def test_pstn_gateway_parser_extracts_sip_options_failed(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "sip_options_failed" / "get_csonlinepstngateway.txt").read_text()
        result = parser_engine.parse(sample, parser_context, command="get-csonlinepstngateway")
        assert "sip_options_failure" in {finding.signal for finding in result.findings}

    def test_voice_routing_policy_parser_extracts_pstn_usage_missing(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "pstn_usage_missing" / "get_csonlinevoiceroutingpolicy.txt").read_text()
        result = parser_engine.parse(sample, parser_context, command="get-csonlinevoiceroutingpolicy")
        assert "pstn_usage_missing" in {finding.signal for finding in result.findings}

    def test_voice_route_parser_extracts_voice_route_missing(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "voice_route_missing" / "get_csonlinevoiceroute.txt").read_text()
        result = parser_engine.parse(sample, parser_context, command="get-csonlinevoiceroute")
        signals = {finding.signal for finding in result.findings}
        assert "voice_route_missing" in signals


class TestTeamsAnalysisIntegration:
    def test_analysis_uses_parser_findings(self, runtime_engine: RuntimeEngine) -> None:
        scenario_dir = SCENARIOS_ROOT / "teams_phone_license_missing"
        turn = runtime_engine.start_investigation(PLAYBOOK_ID)
        for answer in TEAMS_INTAKE_ANSWERS:
            turn = runtime_engine.submit_answer(turn.case_id, turn.question_id, answer)
        case = runtime_engine.case_manager.load_case(turn.case_id)
        playbook = runtime_engine.playbook_catalog.get(PLAYBOOK_ID)
        initialize_evidence_collection(case, runtime_engine.case_manager, playbook)
        submit_evidence(
            case,
            runtime_engine.case_manager,
            "get-csonlineuser",
            (scenario_dir / "get_csonlineuser.txt").read_text(encoding="utf-8"),
        )
        runtime_engine.analyze_case(case.case_id)
        case = runtime_engine.case_manager.load_case(case.case_id)
        parser_findings = [
            finding
            for finding in case.analysis_findings
            if (finding.metadata or {}).get("source") == FINDING_SOURCE_PARSER
        ]
        assert parser_findings
        assert any(finding.signal == "teams_phone_license_missing" for finding in parser_findings)


class TestTeamsHypotheses:
    @pytest.mark.parametrize("rule", VP_TEAMS_0001_RULES, ids=lambda rule: rule.rule_id)
    def test_hypothesis_rule_has_required_signals(self, rule) -> None:
        assert rule.required_signals
        assert rule.confidence >= 80.0

    @pytest.mark.parametrize(
        ("scenario", "expected_title"),
        [
            ("teams_phone_license_missing", HYP_TEAMS_PHONE_LICENSE),
            ("enterprise_voice_disabled", "Enterprise Voice disabled"),
            ("phone_number_not_assigned", "Phone number not assigned"),
            ("voice_routing_policy_missing", "Voice Routing Policy missing"),
            ("pstn_usage_missing", "PSTN Usage missing"),
            ("voice_route_missing", "Voice Route missing"),
            ("direct_routing_sbc_unreachable", HYP_SBC_UNREACHABLE),
            ("tls_certificate_expired", "TLS certificate expired"),
            ("sip_options_failed", "SIP OPTIONS failed"),
            ("emergency_calling_configuration", HYP_EMERGENCY_CALLING),
            ("resource_account_issue", "Resource Account issue"),
        ],
    )
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

    def test_teams_rules_cover_eleven_hypotheses(self) -> None:
        assert len(VP_TEAMS_0001_RULES) == 11


class TestTeamsActionPlans:
    @pytest.mark.parametrize("rule_id", [rule.rule_id for rule in VP_TEAMS_0001_RULES])
    def test_action_plan_exists(self, rule_id: str) -> None:
        assert rule_id in VP_TEAMS_0001_ACTION_PLANS

    @pytest.mark.parametrize("rule_id", sorted(VP_TEAMS_0001_CHANGE_TEMPLATES))
    def test_change_template_exists(self, rule_id: str) -> None:
        template = VP_TEAMS_0001_CHANGE_TEMPLATES[rule_id]
        assert template.current_state
        assert template.recommended_state


class TestTeamsCorrelation:
    @pytest.mark.parametrize("rule_id", [rule.rule_id for rule in VP_TEAMS_0001_CORRELATION_RULES])
    def test_correlation_rule_exists(self, rule_id: str) -> None:
        assert rule_id in {rule.rule_id for rule in VP_TEAMS_0001_CORRELATION_RULES}

    def test_license_correlation_boosts_confidence(self) -> None:
        scenario_dir = SCENARIOS_ROOT / "teams_phone_license_missing"
        runtime, case_id = run_scenario_to_correlation(scenario_dir, playbook_id=PLAYBOOK_ID)
        try:
            runtime.correlate_case(case_id)
            case = runtime.case_manager.load_case(case_id)
            top = min(case.hypotheses, key=lambda item: item.rank or 999)
            assert top.title == HYP_TEAMS_PHONE_LICENSE
            assert top.confidence >= 98.0
        finally:
            runtime.shutdown()


class TestTeamsDiscoveryPlanner:
    def test_teams_discovery_rules_registered(self) -> None:
        registry = default_discovery_registry()
        rule_ids = {rule.id for rule in registry.all_rules()}
        assert "teams_online_user_missing" in rule_ids
        assert "teams_pstn_gateway_missing" in rule_ids

    def test_discovery_plan_requests_missing_user_export(self, runtime_engine: RuntimeEngine) -> None:
        turn = runtime_engine.start_investigation(PLAYBOOK_ID)
        for answer in TEAMS_INTAKE_ANSWERS:
            turn = runtime_engine.submit_answer(turn.case_id, turn.question_id, answer)
        case = runtime_engine.case_manager.load_case(turn.case_id)
        playbook = runtime_engine.playbook_catalog.get(PLAYBOOK_ID)
        initialize_evidence_collection(case, runtime_engine.case_manager, playbook)
        plan = runtime_engine.plan_discovery(turn.case_id)
        commands = {request.command for request in plan.requests}
        assert "get-csonlineuser" in commands


class TestTeamsInvestigationQuality:
    def test_quality_scores_complete_teams_scenario(self) -> None:
        scenario_dir = SCENARIOS_ROOT / "direct_routing_sbc_unreachable"
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


class TestTeamsRecommendations:
    def test_recommendation_references_teams_runbooks(self, runtime_engine: RuntimeEngine) -> None:
        _, case_id = run_scenario_to_correlation(
            SCENARIOS_ROOT / "direct_routing_sbc_unreachable",
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
        assert "VP-MS-TEAMS" in text or HYP_SBC_UNREACHABLE in (recommendation.likely_root_cause or "")


class TestTeamsChangePackage:
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
            assert "Advisory" in markdown or "VP-MS-TEAMS" in markdown
        finally:
            runtime.shutdown()

    def test_change_engine_generates_package(self) -> None:
        runtime, case_id = run_scenario_to_correlation(
            SCENARIOS_ROOT / "emergency_calling_configuration",
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


class TestTeamsHealthIntegration:
    def test_health_evaluation_on_teams_topology(self) -> None:
        user = TeamsUser.create(
            **_TEAMS_DEFAULTS,
            user_principal_name="user@contoso.com",
            enterprise_voice_enabled=False,
            metadata={"teams_phone_license_missing": True},
        )
        topology = TopologyBuilder().build([user])
        report = HealthEngine().evaluate_topology(topology)
        teams_failures = [
            result for result in report.results if result.object_type.startswith("teams_") and result.status == HealthStatus.FAIL
        ]
        assert teams_failures


class TestTeamsEnterpriseReports:
    def test_executive_report_from_scenario(self, tmp_path: Path) -> None:
        assert (
            main(
                [
                    "report-scenario",
                    PLAYBOOK_ID,
                    "--scenario",
                    "teams_phone_license_missing",
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
        assert HYP_TEAMS_PHONE_LICENSE in content


class TestTeamsCli:
    def test_investigate_vp_teams_0001_starts(self) -> None:
        runtime = build_runtime_engine(PLUGINS_ROOT)
        try:
            runtime.start()
            turn = runtime.start_investigation(PLAYBOOK_ID)
            case = runtime.case_manager.load_case(turn.case_id)
            assert case.playbook_id == PLAYBOOK_ID
        finally:
            runtime.shutdown()

    def test_scenarios_vp_teams_0001(self) -> None:
        assert main(["scenarios", PLAYBOOK_ID]) == 0

    def test_plan_scenario(self) -> None:
        assert main(["plan-scenario", PLAYBOOK_ID, "--scenario", "pstn_usage_missing"]) == 0

    def test_quality_scenario(self) -> None:
        assert main(["quality-scenario", PLAYBOOK_ID, "--scenario", "pstn_usage_missing"]) == 0

    def test_change_package_scenario(self, tmp_path: Path) -> None:
        output = tmp_path / "change.md"
        assert (
            main(
                [
                    "change-package-scenario",
                    PLAYBOOK_ID,
                    "--scenario",
                    "direct_routing_sbc_unreachable",
                    "--output",
                    str(output),
                ]
            )
            == 0
        )
        assert READ_ONLY_NOTICE in output.read_text(encoding="utf-8")
