"""Tests for the Microsoft Teams Parser Framework."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from model.teams_objects import (
    TeamsPstnGateway,
    TeamsUser,
    TeamsVoiceRoute,
    TeamsVoiceRoutingPolicy,
)
from parser.parser_context import ParserContext
from parser.parser_engine import ParserEngine
from parser.parser_registry import ParserRegistry
from plugins.microsoft.parser import register_microsoft_parsers
from plugins.microsoft.parser.teams._evidence import (
    FORMAT_CSV,
    FORMAT_JSON,
    FORMAT_LIST,
    dedupe_records,
    detect_evidence_format,
    parse_csv_records,
    parse_format_list_records,
    parse_json_records,
    parse_powershell_evidence,
)
from plugins.microsoft.parser.teams.get_csonlinepstngateway import MicrosoftGetCsOnlinePstnGatewayParser
from plugins.microsoft.parser.teams.get_csonlineuser import MicrosoftGetCsOnlineUserParser
from plugins.microsoft.parser.teams.get_csonlinevoiceroute import MicrosoftGetCsOnlineVoiceRouteParser
from plugins.microsoft.parser.teams.get_csonlinevoiceroutingpolicy import (
    MicrosoftGetCsOnlineVoiceRoutingPolicyParser,
)
from topology.relationship_builder import RelationshipBuilder
from topology.topology_builder import TopologyBuilder

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = REPO_ROOT / "examples" / "sample_evidence" / "teams"


@pytest.fixture
def teams_context() -> ParserContext:
    return ParserContext(
        vendor="microsoft",
        case_id="CASE-teams-001",
        evidence_id="EVD-teams-001",
        platform="Teams Phone",
        hostname="contoso.onmicrosoft.com",
    )


@pytest.fixture
def teams_registry() -> ParserRegistry:
    registry = ParserRegistry()
    register_microsoft_parsers(registry)
    yield registry
    registry.clear()


@pytest.fixture
def teams_engine(teams_registry: ParserRegistry) -> ParserEngine:
    return ParserEngine(registry=teams_registry)


def _read_sample(name: str) -> str:
    return (SAMPLE_DIR / name).read_text(encoding="utf-8")


class TestEvidenceParsing:
    def test_detect_format_list(self) -> None:
        raw = _read_sample("get_csonlineuser_format_list.txt")
        assert detect_evidence_format(raw) == FORMAT_LIST

    def test_detect_csv(self) -> None:
        raw = _read_sample("get_csonlineuser.csv")
        assert detect_evidence_format(raw) == FORMAT_CSV

    def test_detect_json(self) -> None:
        raw = _read_sample("get_csonlineuser.json")
        assert detect_evidence_format(raw) == FORMAT_JSON

    def test_parse_format_list_records(self) -> None:
        records = parse_format_list_records(_read_sample("get_csonlineuser_format_list.txt"))
        assert records[0]["user_principal_name"] == "user@contoso.com"
        assert records[0]["enterprise_voice_enabled"] == "True"

    def test_parse_csv_records(self) -> None:
        records = parse_csv_records(_read_sample("get_csonlineuser.csv"))
        assert records[0]["line_uri"] == "tel:+15551234567"

    def test_parse_json_records(self) -> None:
        records = parse_json_records(_read_sample("get_csonlineuser.json"))
        assert records[0]["enterprise_voice_enabled"] is True

    def test_parse_powershell_evidence_csv(self) -> None:
        fmt, records = parse_powershell_evidence(_read_sample("get_csonlinepstngateway.csv"))
        assert fmt == FORMAT_CSV
        assert records[0]["fqdn"] == "sbc.contoso.com"

    def test_dedupe_records_keeps_last(self) -> None:
        records = [
            {"user_principal_name": "user@contoso.com", "line_uri": "tel:+1"},
            {"user_principal_name": "user@contoso.com", "line_uri": "tel:+2"},
        ]
        deduped, warnings = dedupe_records(records, "user_principal_name")
        assert len(deduped) == 1
        assert deduped[0]["line_uri"] == "tel:+2"
        assert warnings


class TestGetCsOnlineUserParser:
    @pytest.fixture
    def parser(self) -> MicrosoftGetCsOnlineUserParser:
        return MicrosoftGetCsOnlineUserParser()

    def test_detects_format_list_sample(self, parser: MicrosoftGetCsOnlineUserParser) -> None:
        assert parser.detect(_read_sample("get_csonlineuser_format_list.txt"))

    def test_parses_csv_sample(self, parser: MicrosoftGetCsOnlineUserParser, teams_context: ParserContext) -> None:
        result = parser.parse(_read_sample("get_csonlineuser.csv"), teams_context)
        assert result.is_valid
        assert result.structured_data["record_count"] == 1
        assert result.findings

    def test_parses_json_sample(self, parser: MicrosoftGetCsOnlineUserParser, teams_context: ParserContext) -> None:
        result = parser.parse(_read_sample("get_csonlineuser.json"), teams_context)
        assert result.is_valid
        assert result.voice_objects
        user = result.voice_objects[0]
        assert isinstance(user, TeamsUser)
        assert user.enterprise_voice_enabled is True

    def test_invalid_empty_output(self, parser: MicrosoftGetCsOnlineUserParser, teams_context: ParserContext) -> None:
        result = parser.parse("", teams_context)
        assert not result.is_valid

    def test_duplicate_warning(self, parser: MicrosoftGetCsOnlineUserParser, teams_context: ParserContext) -> None:
        raw = (
            "UserPrincipalName,EnterpriseVoiceEnabled\n"
            "user@contoso.com,True\n"
            "user@contoso.com,False\n"
        )
        result = parser.parse(raw, teams_context)
        assert any("duplicate" in warning for warning in result.warnings)

    def test_voice_object_provenance(self, parser: MicrosoftGetCsOnlineUserParser, teams_context: ParserContext) -> None:
        result = parser.parse(_read_sample("get_csonlineuser_format_list.txt"), teams_context)
        user = result.voice_objects[0]
        assert user.source_parser == "microsoft_get_csonlineuser"
        assert user.source_command == "get-csonlineuser"
        assert user.vendor == "microsoft"


class TestParserRegistry:
    def test_registers_eleven_teams_parsers(self, teams_registry: ParserRegistry) -> None:
        commands = teams_registry.list_commands("microsoft")
        assert len(commands) == 11

    def test_lookup_get_csonlineuser(self, teams_registry: ParserRegistry) -> None:
        parser = teams_registry.get_parser("microsoft", "get-csonlineuser")
        assert parser.command == "get-csonlineuser"

    def test_engine_runs_registered_parser(
        self,
        teams_engine: ParserEngine,
        teams_context: ParserContext,
    ) -> None:
        result = teams_engine.parse(
            _read_sample("get_csonlineuser.json"),
            teams_context,
            command="get-csonlineuser",
        )
        assert result.is_valid
        assert result.confidence > 0


class TestAdditionalTeamsParsers:
    @pytest.mark.parametrize(
        ("command", "sample", "expected_type"),
        [
            ("get-csphonenumberassignment", "get_csphonenumberassignment.csv", "teams_phone_number"),
            ("get-csonlinevoiceroutingpolicy", "get_csonlinevoiceroutingpolicy_format_list.txt", "teams_voice_routing_policy"),
            ("get-csonlinevoiceroute", "get_csonlinevoiceroute.json", "teams_voice_route"),
            ("get-cstenantdialplan", "get_cstenantdialplan_format_list.txt", "teams_dial_plan"),
            ("get-csonlinepstngateway", "get_csonlinepstngateway.csv", "teams_pstn_gateway"),
            ("get-csonlinepstnusage", "get_csonlinepstnusage_format_list.txt", "teams_pstn_usage"),
            ("get-cscallqueue", "get_cscallqueue.json", "teams_call_queue"),
            ("get-csautoattendant", "get_csautoattendant.csv", "teams_auto_attendant"),
            ("get-csresourceaccount", "get_csresourceaccount_format_list.txt", "teams_resource_account"),
            ("get-csonlinelislocation", "get_csonlinelislocation.json", "teams_lis_location"),
        ],
    )
    def test_parser_produces_voice_objects(
        self,
        teams_engine: ParserEngine,
        teams_context: ParserContext,
        command: str,
        sample: str,
        expected_type: str,
    ) -> None:
        result = teams_engine.parse(_read_sample(sample), teams_context, command=command)
        assert result.is_valid, result.errors
        assert result.voice_objects
        assert result.voice_objects[0].object_type == expected_type


class TestInvalidSchema:
    def test_invalid_json_raises_error(self, teams_context: ParserContext) -> None:
        parser = MicrosoftGetCsOnlineUserParser()
        result = parser.parse("{not-json", teams_context)
        assert not result.is_valid
        assert result.errors

    def test_missing_required_identity(self, teams_context: ParserContext) -> None:
        parser = MicrosoftGetCsOnlineVoiceRoutingPolicyParser()
        result = parser.parse("Identity :\n", teams_context)
        assert not result.is_valid

    def test_pstn_gateway_missing_identity(self, teams_context: ParserContext) -> None:
        parser = MicrosoftGetCsOnlinePstnGatewayParser()
        result = parser.parse("Fqdn,Enabled\n,True\n", teams_context)
        assert not result.is_valid


class TestTopologyIntegration:
    def _build_topology_objects(self) -> list:
        context = ParserContext(
            vendor="microsoft",
            case_id="CASE-topology",
            evidence_id="EVD-topology",
            platform="Teams Phone",
            hostname="contoso.onmicrosoft.com",
        )
        user_parser = MicrosoftGetCsOnlineUserParser()
        policy_parser = MicrosoftGetCsOnlineVoiceRoutingPolicyParser()
        route_parser = MicrosoftGetCsOnlineVoiceRouteParser()
        gateway_parser = MicrosoftGetCsOnlinePstnGatewayParser()

        user_result = user_parser.parse(_read_sample("get_csonlineuser.json"), context)
        policy_result = policy_parser.parse(
            _read_sample("get_csonlinevoiceroutingpolicy_format_list.txt"),
            context,
        )
        route_result = route_parser.parse(_read_sample("get_csonlinevoiceroute.json"), context)
        gateway_result = gateway_parser.parse(_read_sample("get_csonlinepstngateway.csv"), context)

        return (
            *user_result.voice_objects,
            *policy_result.voice_objects,
            *route_result.voice_objects,
            *gateway_result.voice_objects,
        )

    def test_topology_builder_partitions_teams_objects(self) -> None:
        objects = self._build_topology_objects()
        topology = TopologyBuilder().build(list(objects))

        assert len(topology.teams_users) == 1
        assert len(topology.teams_voice_routing_policies) == 1
        assert len(topology.teams_voice_routes) == 1
        assert len(topology.teams_pstn_gateways) == 1
        assert topology.object_count == 4

    def test_topology_all_objects_includes_teams(self) -> None:
        objects = self._build_topology_objects()
        topology = TopologyBuilder().build(list(objects))
        types = {obj.object_type for obj in topology.all_objects()}
        assert "teams_user" in types
        assert "teams_pstn_gateway" in types

    def test_relationship_builder_links_user_to_policy(self) -> None:
        objects = self._build_topology_objects()
        relationships = RelationshipBuilder().build(list(objects))
        assert any(rel.relationship_type == "uses" for rel in relationships)

    def test_relationship_builder_links_route_to_gateway(self) -> None:
        objects = self._build_topology_objects()
        relationships = RelationshipBuilder().build(list(objects))
        route = next(obj for obj in objects if isinstance(obj, TeamsVoiceRoute))
        gateway = next(obj for obj in objects if isinstance(obj, TeamsPstnGateway))
        assert any(
            rel.source_object_id == route.id and rel.target_object_id == gateway.id
            for rel in relationships
        )


class TestSerialization:
    def test_teams_user_metadata_round_trip(self, teams_context: ParserContext) -> None:
        parser = MicrosoftGetCsOnlineUserParser()
        result = parser.parse(_read_sample("get_csonlineuser.json"), teams_context)
        user = result.voice_objects[0]
        payload = {
            "id": user.id,
            "object_type": user.object_type,
            "name": user.name,
            "line_uri": user.line_uri,
            "metadata": user.metadata,
        }
        assert json.loads(json.dumps(payload))["object_type"] == "teams_user"

    def test_parser_result_structured_data_serializable(self, teams_context: ParserContext) -> None:
        parser = MicrosoftGetCsOnlineVoiceRouteParser()
        result = parser.parse(_read_sample("get_csonlinevoiceroute.json"), teams_context)
        json.dumps(result.structured_data)

    def test_voice_routing_policy_pstn_usages_tuple(self, teams_context: ParserContext) -> None:
        parser = MicrosoftGetCsOnlineVoiceRoutingPolicyParser()
        result = parser.parse(
            _read_sample("get_csonlinevoiceroutingpolicy_format_list.txt"),
            teams_context,
        )
        policy = result.voice_objects[0]
        assert isinstance(policy, TeamsVoiceRoutingPolicy)
        assert policy.pstn_usages


class TestFindings:
    def test_enterprise_voice_disabled_finding(self, teams_context: ParserContext) -> None:
        parser = MicrosoftGetCsOnlineUserParser()
        raw = "UserPrincipalName,EnterpriseVoiceEnabled\nuser@contoso.com,False\n"
        result = parser.parse(raw, teams_context)
        signals = {finding.signal for finding in result.findings}
        assert "enterprise_voice_disabled" in signals

    def test_voice_routing_failure_finding(self, teams_context: ParserContext) -> None:
        parser = MicrosoftGetCsOnlineVoiceRouteParser()
        raw = "Identity,NumberPattern,OnlinePstnGatewayList\nRoute1,+1*,\n"
        result = parser.parse(raw, teams_context)
        signals = {finding.signal for finding in result.findings}
        assert "voice_routing_failure_pstn" in signals

    def test_emergency_calling_finding(self, teams_context: ParserContext) -> None:
        from plugins.microsoft.parser.teams.get_csonlinelislocation import (
            MicrosoftGetCsOnlineLisLocationParser,
        )

        parser = MicrosoftGetCsOnlineLisLocationParser()
        raw = "LocationId,CivicAddress,Location\nHQ,,\n"
        result = parser.parse(raw, teams_context)
        signals = {finding.signal for finding in result.findings}
        assert "emergency_calling_policy_missing" in signals
