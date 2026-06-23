"""Tests for the Genesys Cloud Parser Framework (GVOM)."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from model.genesys_objects import (
    Agent,
    ArchitectFlow,
    ByocCloudTrunk,
    ByocPremisesTrunk,
    Campaign,
    DataAction,
    Division,
    EdgeDevice,
    Flow,
    GenesysOrganization,
    PresenceDefinition,
    Queue,
    QueueMember,
    RecordingPolicy,
    Skill,
)
from parser.parser_context import ParserContext
from parser.parser_engine import ParserEngine
from parser.parser_registry import ParserRegistry
from plugins.genesys.parser import register_genesys_parsers
from plugins.genesys.parser.cloud._evidence import (
    FORMAT_CSV,
    FORMAT_JSON,
    FORMAT_TXT,
    FORMAT_YAML,
    dedupe_records,
    detect_evidence_format,
    parse_csv_records,
    parse_genesys_evidence,
    parse_json_records,
    parse_txt_records,
    parse_yaml_records,
)
from plugins.genesys.parser.cloud.agents_export import GenesysAgentsExportParser
from plugins.genesys.parser.cloud.edge_devices_export import GenesysEdgeDevicesExportParser
from plugins.genesys.parser.cloud.organization_export import GenesysOrganizationExportParser
from plugins.genesys.parser.cloud.queues_export import GenesysQueuesExportParser
from topology.relationship_builder import RelationshipBuilder
from topology.relationship_types import RelationshipType
from topology.topology_builder import TopologyBuilder

REPO_ROOT = Path(__file__).resolve().parents[1]
HEALTHY_DIR = REPO_ROOT / "examples" / "sample_evidence" / "genesys" / "healthy"
FAILURE_DIR = REPO_ROOT / "examples" / "sample_evidence" / "genesys" / "failure"
MIXED_DIR = REPO_ROOT / "examples" / "sample_evidence" / "genesys" / "mixed"


@pytest.fixture
def genesys_context() -> ParserContext:
    return ParserContext(
        vendor="genesys",
        case_id="CASE-gc-001",
        evidence_id="EVD-gc-001",
        platform="Genesys Cloud",
        hostname="acme.mypurecloud.com",
    )


@pytest.fixture
def genesys_registry() -> ParserRegistry:
    registry = ParserRegistry()
    register_genesys_parsers(registry)
    yield registry
    registry.clear()


@pytest.fixture
def genesys_engine(genesys_registry: ParserRegistry) -> ParserEngine:
    return ParserEngine(registry=genesys_registry)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class TestEvidenceParsing:
    def test_detect_csv_format(self) -> None:
        assert detect_evidence_format(_read(HEALTHY_DIR / "queues_export.csv")) == FORMAT_CSV

    def test_detect_json_format(self) -> None:
        assert detect_evidence_format(_read(HEALTHY_DIR / "users_export.json")) == FORMAT_JSON

    def test_detect_yaml_format(self) -> None:
        assert detect_evidence_format(_read(HEALTHY_DIR / "presence_export.yaml")) == FORMAT_YAML

    def test_detect_txt_format(self) -> None:
        assert detect_evidence_format(_read(HEALTHY_DIR / "agents_export.txt")) == FORMAT_TXT

    def test_parse_csv_records(self) -> None:
        records = parse_csv_records(_read(HEALTHY_DIR / "queues_export.csv"))
        assert records[0]["queue_id"] == "queue-100"

    def test_parse_json_records(self) -> None:
        records = parse_json_records(_read(HEALTHY_DIR / "users_export.json"))
        assert records[0]["user_id"] == "user-001"

    def test_parse_yaml_records(self) -> None:
        records = parse_yaml_records(_read(HEALTHY_DIR / "presence_export.yaml"))
        assert records[0]["presence_id"] == "pres-01"

    def test_parse_txt_records(self) -> None:
        records = parse_txt_records(_read(HEALTHY_DIR / "agents_export.txt"))
        assert records[0]["agent_id"] == "agent-001"

    def test_parse_genesys_evidence_csv(self) -> None:
        fmt, records = parse_genesys_evidence(_read(HEALTHY_DIR / "campaigns_export.csv"))
        assert fmt == FORMAT_CSV
        assert records[0]["campaign_id"] == "camp-700"

    def test_parse_genesys_evidence_json(self) -> None:
        fmt, records = parse_genesys_evidence(_read(HEALTHY_DIR / "edge_devices_export.json"))
        assert fmt == FORMAT_JSON
        assert records[0]["edge_id"] == "edge-900"

    def test_dedupe_records_keeps_last(self) -> None:
        records = [
            {"queue_id": "queue-100", "state": "Active"},
            {"queue_id": "queue-100", "state": "Unavailable"},
        ]
        deduped, warnings = dedupe_records(records, "queue_id")
        assert len(deduped) == 1
        assert deduped[0]["state"] == "Unavailable"
        assert warnings


class TestParserRegistry:
    def test_registers_fifteen_genesys_parsers(self, genesys_registry: ParserRegistry) -> None:
        commands = genesys_registry.list_commands("genesys")
        assert len(commands) == 15

    def test_lookup_queues_export(self, genesys_registry: ParserRegistry) -> None:
        parser = genesys_registry.get_parser("genesys", "queues-export")
        assert parser.command == "queues-export"

    def test_engine_runs_registered_parser(
        self,
        genesys_engine: ParserEngine,
        genesys_context: ParserContext,
    ) -> None:
        result = genesys_engine.parse(
            _read(HEALTHY_DIR / "queues_export.csv"),
            genesys_context,
            command="queues-export",
        )
        assert result.is_valid
        assert result.confidence > 0


class TestAllParsers:
    @pytest.mark.parametrize(
        ("command", "sample", "expected_type"),
        [
            ("organization-export", "organization_export.csv", "genesys_organization"),
            ("users-export", "users_export.json", "genesys_agent"),
            ("queues-export", "queues_export.csv", "genesys_queue"),
            ("queue-members-export", "queue_members_export.csv", "genesys_queue_member"),
            ("agents-export", "agents_export.txt", "genesys_agent"),
            ("presence-export", "presence_export.yaml", "genesys_presence_definition"),
            ("flows-export", "flows_export.csv", "genesys_flow"),
            ("architect-export", "architect_export.json", "genesys_architect_flow"),
            ("data-actions-export", "data_actions_export.csv", "genesys_data_action"),
            ("byoc-cloud-trunks-export", "byoc_cloud_trunks_export.txt", "genesys_byoc_cloud_trunk"),
            ("byoc-premises-trunks-export", "byoc_premises_trunks_export.csv", "genesys_byoc_premises_trunk"),
            ("edge-devices-export", "edge_devices_export.json", "genesys_edge_device"),
            ("recording-policies-export", "recording_policies_export.yaml", "genesys_recording_policy"),
            ("campaigns-export", "campaigns_export.csv", "genesys_campaign"),
            ("skills-export", "skills_export.json", "genesys_skill"),
        ],
    )
    def test_parser_produces_voice_objects(
        self,
        genesys_engine: ParserEngine,
        genesys_context: ParserContext,
        command: str,
        sample: str,
        expected_type: str,
    ) -> None:
        result = genesys_engine.parse(_read(HEALTHY_DIR / sample), genesys_context, command=command)
        assert result.is_valid, result.errors
        assert result.voice_objects
        assert result.voice_objects[0].object_type == expected_type


class TestInvalidSchema:
    def test_invalid_json_raises_error(self, genesys_context: ParserContext) -> None:
        parser = GenesysQueuesExportParser()
        result = parser.parse("{not-json", genesys_context)
        assert not result.is_valid
        assert result.errors

    def test_missing_required_identity(self, genesys_context: ParserContext) -> None:
        parser = GenesysQueuesExportParser()
        result = parser.parse("Queue Name: Sales\nState: Active\n", genesys_context)
        assert not result.is_valid

    def test_empty_evidence_invalid(self, genesys_context: ParserContext) -> None:
        parser = GenesysAgentsExportParser()
        result = parser.parse("", genesys_context)
        assert not result.is_valid


class TestFindings:
    def test_queue_unavailable_finding(self, genesys_context: ParserContext) -> None:
        parser = GenesysQueuesExportParser()
        result = parser.parse(_read(FAILURE_DIR / "queues_unavailable.csv"), genesys_context)
        signals = {finding.signal for finding in result.findings}
        assert "queue_unavailable" in signals

    def test_edge_offline_finding(self, genesys_context: ParserContext) -> None:
        parser = GenesysEdgeDevicesExportParser()
        result = parser.parse(_read(FAILURE_DIR / "edge_offline.txt"), genesys_context)
        signals = {finding.signal for finding in result.findings}
        assert "edge_offline" in signals

    def test_byoc_cloud_trunk_failure_finding(self, genesys_context: ParserContext) -> None:
        from plugins.genesys.parser.cloud.byoc_cloud_trunks_export import GenesysByocCloudTrunksExportParser

        parser = GenesysByocCloudTrunksExportParser()
        result = parser.parse(_read(FAILURE_DIR / "byoc_cloud_trunk_failure.txt"), genesys_context)
        signals = {finding.signal for finding in result.findings}
        assert "byoc_cloud_trunk_failure" in signals
        assert "sip_options_failure" in signals

    def test_agent_not_logged_in_finding(self, genesys_context: ParserContext) -> None:
        parser = GenesysAgentsExportParser()
        result = parser.parse(_read(FAILURE_DIR / "agents_offline.txt"), genesys_context)
        signals = {finding.signal for finding in result.findings}
        assert "agent_not_logged_in" in signals


class TestTopologyIntegration:
    def _build_topology_objects(self, genesys_context: ParserContext) -> list:
        engine = ParserEngine(registry=ParserRegistry())
        register_genesys_parsers(engine.registry)
        samples = (
            ("organization-export", "organization_export.csv"),
            ("queues-export", "queues_export.csv"),
            ("queue-members-export", "queue_members_export.csv"),
            ("agents-export", "agents_export.txt"),
            ("flows-export", "flows_export.csv"),
            ("architect-export", "architect_export.json"),
            ("data-actions-export", "data_actions_export.csv"),
            ("campaigns-export", "campaigns_export.csv"),
            ("byoc-premises-trunks-export", "byoc_premises_trunks_export.csv"),
            ("edge-devices-export", "edge_devices_export.json"),
            ("skills-export", "skills_export.json"),
            ("recording-policies-export", "recording_policies_export.yaml"),
        )
        objects = []
        for command, sample in samples:
            result = engine.parse(_read(HEALTHY_DIR / sample), genesys_context, command=command)
            objects.extend(result.voice_objects)
        return objects

    def test_topology_builder_partitions_genesys_objects(
        self,
        genesys_context: ParserContext,
    ) -> None:
        objects = self._build_topology_objects(genesys_context)
        topology = TopologyBuilder().build(objects)
        assert len(topology.genesys_organizations) >= 1
        assert len(topology.genesys_queues) >= 2
        assert len(topology.genesys_agents) >= 1
        assert len(topology.genesys_flows) >= 2
        assert len(topology.genesys_trunks) >= 1
        assert len(topology.genesys_edges) == 1
        assert len(topology.genesys_campaigns) == 1
        assert len(topology.genesys_skills) == 1
        assert len(topology.genesys_recordings) == 1
        assert topology.object_count >= 12

    def test_topology_all_objects_includes_genesys(
        self,
        genesys_context: ParserContext,
    ) -> None:
        objects = self._build_topology_objects(genesys_context)
        topology = TopologyBuilder().build(objects)
        types = {obj.object_type for obj in topology.all_objects()}
        assert "genesys_queue" in types
        assert "genesys_edge_device" in types

    def test_relationship_builder_links_agent_to_queue(
        self,
        genesys_context: ParserContext,
    ) -> None:
        objects = self._build_topology_objects(genesys_context)
        relationships = RelationshipBuilder().build(objects)
        agent = next(obj for obj in objects if isinstance(obj, Agent) and obj.queue_id)
        queue = next(obj for obj in objects if isinstance(obj, Queue))
        assert any(
            rel.source_object_id == agent.id
            and rel.target_object_id == queue.id
            and rel.relationship_type == RelationshipType.ROUTES_TO.value
            for rel in relationships
        )

    def test_relationship_builder_links_queue_to_member(
        self,
        genesys_context: ParserContext,
    ) -> None:
        objects = self._build_topology_objects(genesys_context)
        relationships = RelationshipBuilder().build(objects)
        member = next(obj for obj in objects if isinstance(obj, QueueMember))
        queue = next(obj for obj in objects if isinstance(obj, Queue))
        assert any(
            rel.source_object_id == queue.id
            and rel.target_object_id == member.id
            and rel.relationship_type == RelationshipType.PROVIDES.value
            for rel in relationships
        )

    def test_relationship_builder_links_flow_to_queue(
        self,
        genesys_context: ParserContext,
    ) -> None:
        objects = self._build_topology_objects(genesys_context)
        relationships = RelationshipBuilder().build(objects)
        flow = next(obj for obj in objects if isinstance(obj, Flow))
        queue = next(obj for obj in objects if isinstance(obj, Queue))
        assert any(
            rel.source_object_id == flow.id and rel.target_object_id == queue.id
            for rel in relationships
        )

    def test_relationship_builder_links_architect_flow_to_data_action(
        self,
        genesys_context: ParserContext,
    ) -> None:
        objects = self._build_topology_objects(genesys_context)
        relationships = RelationshipBuilder().build(objects)
        architect = next(obj for obj in objects if isinstance(obj, ArchitectFlow))
        data_action = next(obj for obj in objects if isinstance(obj, DataAction))
        assert any(
            rel.source_object_id == architect.id and rel.target_object_id == data_action.id
            for rel in relationships
        )

    def test_relationship_builder_links_campaign_to_queue(
        self,
        genesys_context: ParserContext,
    ) -> None:
        objects = self._build_topology_objects(genesys_context)
        relationships = RelationshipBuilder().build(objects)
        campaign = next(obj for obj in objects if isinstance(obj, Campaign))
        queue = next(obj for obj in objects if isinstance(obj, Queue))
        assert any(
            rel.source_object_id == campaign.id and rel.target_object_id == queue.id
            for rel in relationships
        )

    def test_relationship_builder_links_trunk_to_edge(
        self,
        genesys_context: ParserContext,
    ) -> None:
        objects = self._build_topology_objects(genesys_context)
        relationships = RelationshipBuilder().build(objects)
        trunk = next(obj for obj in objects if isinstance(obj, ByocPremisesTrunk))
        edge = next(obj for obj in objects if isinstance(obj, EdgeDevice))
        assert any(
            rel.source_object_id == trunk.id
            and rel.target_object_id == edge.id
            and rel.relationship_type == RelationshipType.CONNECTS_TO.value
            for rel in relationships
        )

    def test_relationship_builder_links_edge_to_organization(
        self,
        genesys_context: ParserContext,
    ) -> None:
        objects = self._build_topology_objects(genesys_context)
        relationships = RelationshipBuilder().build(objects)
        edge = next(obj for obj in objects if isinstance(obj, EdgeDevice))
        organization = next(obj for obj in objects if isinstance(obj, GenesysOrganization))
        assert any(
            rel.source_object_id == edge.id
            and rel.target_object_id == organization.id
            and rel.relationship_type == RelationshipType.HOSTED_ON.value
            for rel in relationships
        )


class TestGvomImmutability:
    def test_queue_is_frozen(self, genesys_context: ParserContext) -> None:
        parser = GenesysQueuesExportParser()
        result = parser.parse(_read(HEALTHY_DIR / "queues_export.csv"), genesys_context)
        queue = result.voice_objects[0]
        assert isinstance(queue, Queue)
        with pytest.raises(FrozenInstanceError):
            queue.state = "Down"  # type: ignore[misc]

    def test_organization_is_frozen(self, genesys_context: ParserContext) -> None:
        parser = GenesysOrganizationExportParser()
        result = parser.parse(_read(HEALTHY_DIR / "organization_export.csv"), genesys_context)
        organization = result.voice_objects[0]
        assert isinstance(organization, GenesysOrganization)
        with pytest.raises(FrozenInstanceError):
            organization.domain = "other.example.com"  # type: ignore[misc]

    def test_edge_device_is_frozen(self, genesys_context: ParserContext) -> None:
        parser = GenesysEdgeDevicesExportParser()
        result = parser.parse(_read(HEALTHY_DIR / "edge_devices_export.json"), genesys_context)
        edge = result.voice_objects[0]
        assert isinstance(edge, EdgeDevice)
        with pytest.raises(FrozenInstanceError):
            edge.state = "Offline"  # type: ignore[misc]


class TestSerialization:
    def test_queue_metadata_round_trip(self, genesys_context: ParserContext) -> None:
        parser = GenesysQueuesExportParser()
        result = parser.parse(_read(HEALTHY_DIR / "queues_export.csv"), genesys_context)
        queue = result.voice_objects[0]
        payload = {
            "id": queue.id,
            "object_type": queue.object_type,
            "queue_id": queue.queue_id,
            "metadata": queue.metadata,
        }
        assert json.loads(json.dumps(payload))["object_type"] == "genesys_queue"

    def test_parser_result_structured_data_serializable(self, genesys_context: ParserContext) -> None:
        parser = GenesysQueuesExportParser()
        result = parser.parse(_read(HEALTHY_DIR / "queues_export.csv"), genesys_context)
        json.dumps(result.structured_data)

    def test_recording_policy_object_fields(self, genesys_context: ParserContext) -> None:
        from plugins.genesys.parser.cloud.recording_policies_export import (
            GenesysRecordingPoliciesExportParser,
        )

        parser = GenesysRecordingPoliciesExportParser()
        result = parser.parse(_read(HEALTHY_DIR / "recording_policies_export.yaml"), genesys_context)
        policy = result.voice_objects[0]
        assert isinstance(policy, RecordingPolicy)
        assert policy.policy_name == "Sales Recording"

    def test_skill_object_fields(self, genesys_engine: ParserEngine, genesys_context: ParserContext) -> None:
        result = genesys_engine.parse(
            _read(HEALTHY_DIR / "skills_export.json"),
            genesys_context,
            command="skills-export",
        )
        skill = result.voice_objects[0]
        assert isinstance(skill, Skill)
        assert skill.skill_name == "Spanish"

    def test_presence_definition_object_fields(self, genesys_context: ParserContext) -> None:
        from plugins.genesys.parser.cloud.presence_export import GenesysPresenceExportParser

        parser = GenesysPresenceExportParser()
        result = parser.parse(_read(HEALTHY_DIR / "presence_export.yaml"), genesys_context)
        presence = result.voice_objects[0]
        assert isinstance(presence, PresenceDefinition)
        assert presence.presence_name == "Available"

    def test_byoc_cloud_trunk_object_fields(self, genesys_context: ParserContext) -> None:
        from plugins.genesys.parser.cloud.byoc_cloud_trunks_export import (
            GenesysByocCloudTrunksExportParser,
        )

        parser = GenesysByocCloudTrunksExportParser()
        result = parser.parse(_read(HEALTHY_DIR / "byoc_cloud_trunks_export.txt"), genesys_context)
        trunk = result.voice_objects[0]
        assert isinstance(trunk, ByocCloudTrunk)
        assert trunk.sip_options_status == "Success"

    def test_default_parser_engine_registers_genesys(self) -> None:
        from runtime.parser_bootstrap import build_default_parser_engine

        engine = build_default_parser_engine()
        assert engine is not None
        assert engine.registry.has_parser("genesys", "queues-export")

    def test_mixed_bundle_exists(self) -> None:
        assert (MIXED_DIR / "topology_bundle.json").exists()

    def test_twenty_gvom_object_types_defined(self) -> None:
        from model import genesys_objects as gvom
        from model.voice_graph import VoiceObject

        frozen_types = [
            name
            for name in dir(gvom)
            if not name.startswith("_")
            and isinstance(getattr(gvom, name), type)
            and issubclass(getattr(gvom, name), VoiceObject)
            and getattr(gvom, name) is not VoiceObject
        ]
        assert len(frozen_types) == 20

    def test_division_from_organization_export(self, genesys_context: ParserContext) -> None:
        raw = "Organization ID: org-100\nOrganization Name: Acme\nDivision ID: div-01\nDivision Name: Sales\n"
        parser = GenesysOrganizationExportParser()
        result = parser.parse(raw, genesys_context)
        divisions = [obj for obj in result.voice_objects if isinstance(obj, Division)]
        assert divisions
        assert divisions[0].division_id == "div-01"
