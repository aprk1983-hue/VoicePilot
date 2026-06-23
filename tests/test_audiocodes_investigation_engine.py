"""Tests for AudioCodes SBC investigation engine (Sprint 13.4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from change_package import EngineeringChangePackageEngine, READ_ONLY_NOTICE, format_change_package_markdown
from change_package.change_engine import VP_AUDIOCODES_0001_CHANGE_TEMPLATES
from cli.voicepilot_cli import build_runtime_engine, main
from discovery.planner_bootstrap import default_discovery_registry
from health.health_engine import HealthEngine
from health.health_models import HealthStatus
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from investigation_quality.quality_engine import InvestigationQualityEngine
from model.audiocodes_objects import License, ProxySet
from parser.parser_context import ParserContext
from runtime.analysis_engine import FINDING_SOURCE_PARSER
from runtime.audiocodes_investigation import (
    AUDIOCODES_EVIDENCE_FILES,
    AUDIOCODES_INTAKE_ANSWERS,
    HYP_GATEWAY,
    HYP_HA_SYNC,
    HYP_IP_GROUP,
    HYP_LICENSE,
    HYP_MEDIA_REALM,
    HYP_ONE_WAY_AUDIO,
    HYP_PROVIDER_UNAVAILABLE,
    HYP_PROXY_SET,
    HYP_ROUTING,
    HYP_SIP_OPTIONS,
    HYP_TLS_CERTIFICATE,
    VP_AUDIOCODES_0001_ACTION_PLANS,
    VP_AUDIOCODES_0001_CORRELATION_RULES,
    VP_AUDIOCODES_0001_PLAYBOOK_ID,
    VP_AUDIOCODES_0001_RULES,
)
from runtime.evidence_collection import initialize_evidence_collection, submit_evidence
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
PLAYBOOK_ID = VP_AUDIOCODES_0001_PLAYBOOK_ID
SCENARIOS_ROOT = default_scenarios_root(PLAYBOOK_ID, repo_root=REPO_ROOT)

_AUDIOCODES_DEFAULTS = {
    "vendor": "audiocodes",
    "platform": "AudioCodes SBC",
    "hostname": "sbc-lab-01.example.com",
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
        vendor="audiocodes",
        case_id="CASE-audiocodes-test",
        evidence_id="EVD-audiocodes-test",
        platform="AudioCodes SBC",
        hostname="sbc-lab-01.example.com",
    )


class TestAudioCodesPlaybook:
    def test_playbook_loads_from_catalog(self, runtime_engine: RuntimeEngine) -> None:
        playbook = runtime_engine.playbook_catalog.get(PLAYBOOK_ID)
        assert playbook.playbook_id == PLAYBOOK_ID
        assert playbook.title == "AudioCodes SBC Investigation"

    def test_intake_summary_lists_required_commands(self, runtime_engine: RuntimeEngine) -> None:
        turn = runtime_engine.start_investigation(PLAYBOOK_ID)
        for answer in AUDIOCODES_INTAKE_ANSWERS:
            turn = runtime_engine.submit_answer(turn.case_id, turn.question_id, answer)
        case = runtime_engine.case_manager.load_case(turn.case_id)
        playbook = runtime_engine.playbook_catalog.get(PLAYBOOK_ID)
        summary = build_intake_summary(case, playbook)
        assert summary.next_required_commands == [command for command, _ in AUDIOCODES_EVIDENCE_FILES]


class TestAudioCodesParsers:
    def test_sip_options_parser_extracts_failure(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "sip_options_failed" / "show_sip_options.txt").read_text()
        result = parser_engine.parse(sample, parser_context, command="show sip-options")
        assert "sip_options_failure" in {finding.signal for finding in result.findings}

    def test_sip_options_parser_extracts_provider_503(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "provider_503" / "show_sip_options.txt").read_text()
        result = parser_engine.parse(sample, parser_context, command="show sip-options")
        signals = {finding.signal for finding in result.findings}
        assert "provider_503" in signals

    def test_proxy_set_parser_extracts_unavailable(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "proxy_set_unavailable" / "show_proxy_set.txt").read_text()
        result = parser_engine.parse(sample, parser_context, command="show proxy-set")
        signals = {finding.signal for finding in result.findings}
        assert "proxy_set_unavailable" in signals
        assert any(isinstance(obj, ProxySet) for obj in result.voice_objects)

    def test_ip_group_parser_extracts_disabled(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "ip_group_disabled" / "show_ip_group.txt").read_text()
        result = parser_engine.parse(sample, parser_context, command="show ip-group")
        assert "ip_group_disabled" in {finding.signal for finding in result.findings}

    def test_routing_table_parser_extracts_issue(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "routing_rule_missing" / "show_routing_table.txt").read_text()
        result = parser_engine.parse(sample, parser_context, command="show routing-table")
        assert "routing_table_issue" in {finding.signal for finding in result.findings}

    def test_certificates_parser_extracts_expired(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "tls_certificate_expired" / "show_certificates.txt").read_text()
        result = parser_engine.parse(sample, parser_context, command="show certificates")
        assert "tls_certificate_expired" in {finding.signal for finding in result.findings}

    def test_media_realm_parser_extracts_failure(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "media_realm_down" / "show_media_realm.txt").read_text()
        result = parser_engine.parse(sample, parser_context, command="show media-realm")
        assert "media_realm_failure" in {finding.signal for finding in result.findings}

    def test_media_realm_parser_extracts_one_way_audio(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "rtp_one_way_audio" / "show_media_realm.txt").read_text()
        result = parser_engine.parse(sample, parser_context, command="show media-realm")
        assert "rtp_one_way_audio" in {finding.signal for finding in result.findings}

    def test_licenses_parser_extracts_exhausted(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "session_license_exhausted" / "show_licenses.txt").read_text()
        result = parser_engine.parse(sample, parser_context, command="show licenses")
        assert "session_license_exhausted" in {finding.signal for finding in result.findings}

    def test_ha_status_parser_extracts_sync_failure(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (SCENARIOS_ROOT / "ha_sync_failure" / "show_ha_status.txt").read_text()
        result = parser_engine.parse(sample, parser_context, command="show ha-status")
        signals = {finding.signal for finding in result.findings}
        assert "standby_synchronization_failure" in signals
        assert "ha_failover" in signals

    def test_voip_status_parser_extracts_dns_failure(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (
            "show voip status\n"
            "Device Name: SBC-LAB-01\n"
            "Device Status: Active\n"
            "DNS Resolution: Failed\n"
        )
        result = parser_engine.parse(sample, parser_context, command="show voip status")
        assert "dns_resolution_failure" in {finding.signal for finding in result.findings}

    def test_tls_context_parser_extracts_srtp_mismatch(
        self, parser_engine, parser_context: ParserContext
    ) -> None:
        sample = (
            "show tls-context\n"
            "Context Name: TLS_CTX_1\n"
            "TLS Version: TLS1.2\n"
            "Certificate Name: SBC_CERT\n"
            "Status: Active\n"
            "Media Security Profile: SRTP_PROFILE\n"
            "SRTP Mode: Mismatch\n"
        )
        result = parser_engine.parse(sample, parser_context, command="show tls-context")
        assert "srtp_mismatch" in {finding.signal for finding in result.findings}


class TestAudioCodesAnalysisIntegration:
    def test_analysis_uses_parser_findings(self, runtime_engine: RuntimeEngine) -> None:
        scenario_dir = SCENARIOS_ROOT / "sip_options_failed"
        turn = runtime_engine.start_investigation(PLAYBOOK_ID)
        for answer in AUDIOCODES_INTAKE_ANSWERS:
            turn = runtime_engine.submit_answer(turn.case_id, turn.question_id, answer)
        case = runtime_engine.case_manager.load_case(turn.case_id)
        playbook = runtime_engine.playbook_catalog.get(PLAYBOOK_ID)
        initialize_evidence_collection(case, runtime_engine.case_manager, playbook)
        submit_evidence(
            case,
            runtime_engine.case_manager,
            "show sip-options",
            (scenario_dir / "show_sip_options.txt").read_text(encoding="utf-8"),
        )
        runtime_engine.analyze_case(case.case_id)
        case = runtime_engine.case_manager.load_case(case.case_id)
        parser_findings = [
            finding
            for finding in case.analysis_findings
            if (finding.metadata or {}).get("source") == FINDING_SOURCE_PARSER
        ]
        assert parser_findings
        assert any(finding.signal == "sip_options_failure" for finding in parser_findings)


class TestAudioCodesHypotheses:
    @pytest.mark.parametrize("rule", VP_AUDIOCODES_0001_RULES, ids=lambda rule: rule.rule_id)
    def test_hypothesis_rule_has_required_signals(self, rule) -> None:
        assert rule.required_signals
        assert rule.confidence >= 80.0

    @pytest.mark.parametrize(
        ("scenario", "expected_title"),
        [
            ("sip_options_failed", HYP_SIP_OPTIONS),
            ("provider_503", HYP_PROVIDER_UNAVAILABLE),
            ("proxy_set_unavailable", HYP_PROXY_SET),
            ("ip_group_disabled", HYP_IP_GROUP),
            ("routing_rule_missing", HYP_ROUTING),
            ("tls_certificate_expired", HYP_TLS_CERTIFICATE),
            ("media_realm_down", HYP_MEDIA_REALM),
            ("rtp_one_way_audio", HYP_ONE_WAY_AUDIO),
            ("session_license_exhausted", HYP_LICENSE),
            ("ha_sync_failure", HYP_HA_SYNC),
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

    def test_audiocodes_rules_cover_fifteen_hypotheses(self) -> None:
        assert len(VP_AUDIOCODES_0001_RULES) == 15


class TestAudioCodesActionPlans:
    @pytest.mark.parametrize("rule_id", [rule.rule_id for rule in VP_AUDIOCODES_0001_RULES])
    def test_action_plan_exists(self, rule_id: str) -> None:
        assert rule_id in VP_AUDIOCODES_0001_ACTION_PLANS
        plan = VP_AUDIOCODES_0001_ACTION_PLANS[rule_id]
        assert plan.recommended_actions
        assert any("VP-AUDIOCODES-SBC-RB-" in action for action in plan.recommended_actions)

    @pytest.mark.parametrize("rule_id", sorted(VP_AUDIOCODES_0001_CHANGE_TEMPLATES))
    def test_change_template_exists(self, rule_id: str) -> None:
        template = VP_AUDIOCODES_0001_CHANGE_TEMPLATES[rule_id]
        assert template.current_state
        assert template.recommended_state
        assert any(ref.startswith("VP-AUDIOCODES-SBC-") for ref in template.vendor_references)


class TestAudioCodesCorrelation:
    @pytest.mark.parametrize("rule_id", [rule.rule_id for rule in VP_AUDIOCODES_0001_CORRELATION_RULES])
    def test_correlation_rule_exists(self, rule_id: str) -> None:
        assert rule_id in {rule.rule_id for rule in VP_AUDIOCODES_0001_CORRELATION_RULES}

    def test_ha_correlation_boosts_confidence(self) -> None:
        scenario_dir = SCENARIOS_ROOT / "ha_sync_failure"
        runtime, case_id = run_scenario_to_correlation(scenario_dir, playbook_id=PLAYBOOK_ID)
        try:
            runtime.correlate_case(case_id)
            case = runtime.case_manager.load_case(case_id)
            top = min(case.hypotheses, key=lambda item: item.rank or 999)
            assert top.title == HYP_HA_SYNC
            assert top.confidence >= 98.0
        finally:
            runtime.shutdown()

    def test_license_correlation_boosts_confidence(self) -> None:
        scenario_dir = SCENARIOS_ROOT / "session_license_exhausted"
        runtime, case_id = run_scenario_to_correlation(scenario_dir, playbook_id=PLAYBOOK_ID)
        try:
            runtime.correlate_case(case_id)
            case = runtime.case_manager.load_case(case_id)
            top = min(case.hypotheses, key=lambda item: item.rank or 999)
            assert top.title == HYP_LICENSE
            assert top.confidence >= 98.0
        finally:
            runtime.shutdown()


class TestAudioCodesDiscoveryPlanner:
    @pytest.mark.parametrize(
        "rule_id",
        [
            "audiocodes_voip_status_missing",
            "audiocodes_sip_options_missing",
            "audiocodes_proxy_set_missing",
            "audiocodes_ip_group_missing",
            "audiocodes_routing_table_missing",
            "audiocodes_media_realm_missing",
            "audiocodes_tls_context_missing",
            "audiocodes_certificates_missing",
            "audiocodes_ha_status_missing",
            "audiocodes_licenses_missing",
        ],
    )
    def test_audiocodes_discovery_rules_registered(self, rule_id: str) -> None:
        registry = default_discovery_registry()
        rule_ids = {rule.id for rule in registry.all_rules()}
        assert rule_id in rule_ids

    def test_discovery_plan_requests_missing_sip_options(self, runtime_engine: RuntimeEngine) -> None:
        turn = runtime_engine.start_investigation(PLAYBOOK_ID)
        for answer in AUDIOCODES_INTAKE_ANSWERS:
            turn = runtime_engine.submit_answer(turn.case_id, turn.question_id, answer)
        case = runtime_engine.case_manager.load_case(turn.case_id)
        playbook = runtime_engine.playbook_catalog.get(PLAYBOOK_ID)
        initialize_evidence_collection(case, runtime_engine.case_manager, playbook)
        plan = runtime_engine.plan_discovery(turn.case_id)
        commands = {request.command for request in plan.requests}
        assert "show sip-options" in commands


class TestAudioCodesInvestigationQuality:
    def test_quality_scores_complete_audiocodes_scenario(self) -> None:
        scenario_dir = SCENARIOS_ROOT / "proxy_set_unavailable"
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


class TestAudioCodesRecommendations:
    def test_recommendation_references_audiocodes_runbooks(self, runtime_engine: RuntimeEngine) -> None:
        _, case_id = run_scenario_to_correlation(
            SCENARIOS_ROOT / "proxy_set_unavailable",
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
        assert "VP-AUDIOCODES-SBC" in text or HYP_PROXY_SET in (recommendation.likely_root_cause or "")

    def test_gateway_hypothesis_action_plan_references_provider_runbook(self) -> None:
        plan = VP_AUDIOCODES_0001_ACTION_PLANS["HYP-AUDIOCODES-GATEWAY"]
        assert any("VP-AUDIOCODES-SBC-RB-008" in action for action in plan.recommended_actions)
        assert any("VP-AUDIOCODES-SBC-VG-008" in step for step in plan.verification_steps)


class TestAudioCodesChangePackage:
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
            assert "Advisory" in markdown or "VP-AUDIOCODES-SBC" in markdown
        finally:
            runtime.shutdown()

    def test_change_engine_generates_package(self) -> None:
        runtime, case_id = run_scenario_to_correlation(
            SCENARIOS_ROOT / "routing_rule_missing",
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
            SCENARIOS_ROOT / "ip_group_disabled",
            playbook_id=PLAYBOOK_ID,
        )
        try:
            runtime.generate_recommendation(case_id)
            package = runtime.generate_change_package(case_id)
            assert any(ref.startswith("VP-AUDIOCODES-SBC-") for ref in package.vendor_references)
        finally:
            runtime.shutdown()


class TestAudioCodesHealthIntegration:
    def test_health_evaluation_on_audiocodes_topology(self) -> None:
        license_obj = License.create(
            **_AUDIOCODES_DEFAULTS,
            license_type="Session",
            sessions_total=100,
            sessions_used=100,
            metadata={"session_license_exhausted": True},
        )
        topology = TopologyBuilder().build([license_obj])
        report = HealthEngine().evaluate_topology(topology)
        audiocodes_failures = [
            result
            for result in report.results
            if result.object_type.startswith("audiocodes_") and result.status == HealthStatus.FAIL
        ]
        assert audiocodes_failures


class TestAudioCodesEnterpriseReports:
    def test_executive_report_from_scenario(self, tmp_path: Path) -> None:
        assert (
            main(
                [
                    "report-scenario",
                    PLAYBOOK_ID,
                    "--scenario",
                    "sip_options_failed",
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
        assert HYP_SIP_OPTIONS in content


class TestAudioCodesCli:
    def test_investigate_vp_audiocodes_0001_starts(self) -> None:
        runtime = build_runtime_engine(PLUGINS_ROOT)
        try:
            runtime.start()
            turn = runtime.start_investigation(PLAYBOOK_ID)
            case = runtime.case_manager.load_case(turn.case_id)
            assert case.playbook_id == PLAYBOOK_ID
        finally:
            runtime.shutdown()

    def test_scenarios_vp_audiocodes_0001(self) -> None:
        assert main(["scenarios", PLAYBOOK_ID]) == 0

    def test_plan_scenario(self) -> None:
        assert main(["plan-scenario", PLAYBOOK_ID, "--scenario", "routing_rule_missing"]) == 0

    def test_quality_scenario(self) -> None:
        assert main(["quality-scenario", PLAYBOOK_ID, "--scenario", "routing_rule_missing"]) == 0

    def test_change_package_scenario(self, tmp_path: Path) -> None:
        output = tmp_path / "change.md"
        assert (
            main(
                [
                    "change-package-scenario",
                    PLAYBOOK_ID,
                    "--scenario",
                    "tls_certificate_expired",
                    "--output",
                    str(output),
                ]
            )
            == 0
        )
        assert READ_ONLY_NOTICE in output.read_text(encoding="utf-8")

    def test_validate_vp_audiocodes_0001(self) -> None:
        assert main(["validate", PLAYBOOK_ID]) == 0
