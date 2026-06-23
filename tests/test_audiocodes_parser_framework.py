"""Tests for the AudioCodes SBC Parser Framework."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from model.audiocodes_objects import (
    Certificate,
    HACluster,
    IPGroup,
    License,
    MediaRealm,
    ProxySet,
    RoutingRule,
    SBCDevice,
    SIPInterface,
    SIPMessagePolicy,
    TLSContext,
)
from parser.parser_context import ParserContext
from parser.parser_engine import ParserEngine
from parser.parser_registry import ParserRegistry
from plugins.audiocodes.parser import register_audiocodes_parsers
from plugins.audiocodes.parser.sbc._evidence import (
    FORMAT_INI,
    FORMAT_TXT,
    FORMAT_XML,
    dedupe_records,
    detect_evidence_format,
    parse_audiocodes_evidence,
    parse_ini_records,
    parse_txt_records,
    parse_xml_records,
)
from plugins.audiocodes.parser.sbc.show_certificates import AudioCodesShowCertificatesParser
from plugins.audiocodes.parser.sbc.show_ip_group import AudioCodesShowIpGroupParser
from plugins.audiocodes.parser.sbc.show_proxy_set import AudioCodesShowProxySetParser
from plugins.audiocodes.parser.sbc.show_sip_interface import AudioCodesShowSipInterfaceParser
from topology.relationship_builder import RelationshipBuilder
from topology.topology_builder import TopologyBuilder

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = REPO_ROOT / "examples" / "sample_evidence" / "audiocodes"


@pytest.fixture
def audiocodes_context() -> ParserContext:
    return ParserContext(
        vendor="audiocodes",
        case_id="CASE-ac-001",
        evidence_id="EVD-ac-001",
        platform="Mediant SBC",
        hostname="sbc-lab-01.example.com",
    )


@pytest.fixture
def audiocodes_registry() -> ParserRegistry:
    registry = ParserRegistry()
    register_audiocodes_parsers(registry)
    yield registry
    registry.clear()


@pytest.fixture
def audiocodes_engine(audiocodes_registry: ParserRegistry) -> ParserEngine:
    return ParserEngine(registry=audiocodes_registry)


def _read_sample(name: str) -> str:
    return (SAMPLE_DIR / name).read_text(encoding="utf-8")


class TestEvidenceParsing:
    def test_detect_txt_format(self) -> None:
        assert detect_evidence_format(_read_sample("show_sip_interface.txt")) == FORMAT_TXT

    def test_detect_ini_format(self) -> None:
        assert detect_evidence_format(_read_sample("show_sip_interface.ini")) == FORMAT_INI

    def test_detect_xml_format(self) -> None:
        assert detect_evidence_format(_read_sample("show_sip_interface.xml")) == FORMAT_XML

    def test_parse_txt_records(self) -> None:
        records = parse_txt_records(_read_sample("show_proxy_set.txt"))
        assert records[0]["proxy_set_name"] == "PROVIDER_PS"

    def test_parse_ini_records(self) -> None:
        records = parse_ini_records(_read_sample("show_sip_interface.ini"))
        assert records[0]["interface_name"] == "SIP_TRUNK_1"

    def test_parse_xml_records(self) -> None:
        records = parse_xml_records(_read_sample("show_sip_interface.xml"))
        assert records[0]["interface_name"] == "SIP_TRUNK_1"

    def test_parse_audiocodes_evidence_txt(self) -> None:
        fmt, records = parse_audiocodes_evidence(_read_sample("show_ip_group.txt"))
        assert fmt == FORMAT_TXT
        assert records[0]["ip_group_name"] == "TO_PROVIDER"

    def test_parse_audiocodes_evidence_ini(self) -> None:
        fmt, records = parse_audiocodes_evidence(_read_sample("show_sip_interface.ini"))
        assert fmt == FORMAT_INI
        assert records[0]["transport"] == "TLS"

    def test_parse_audiocodes_evidence_xml(self) -> None:
        fmt, records = parse_audiocodes_evidence(_read_sample("show_sip_interface.xml"))
        assert fmt == FORMAT_XML
        assert records[0]["media_realm"] == "MR_INTERNAL"

    def test_dedupe_records_keeps_last(self) -> None:
        records = [
            {"name": "SIP_TRUNK_1", "state": "Active"},
            {"name": "SIP_TRUNK_1", "state": "Down"},
        ]
        deduped, warnings = dedupe_records(records, "name")
        assert len(deduped) == 1
        assert deduped[0]["state"] == "Down"
        assert warnings


class TestShowSipInterfaceParser:
    @pytest.fixture
    def parser(self) -> AudioCodesShowSipInterfaceParser:
        return AudioCodesShowSipInterfaceParser()

    def test_detects_txt_sample(self, parser: AudioCodesShowSipInterfaceParser) -> None:
        assert parser.detect(_read_sample("show_sip_interface.txt"))

    def test_parses_txt_sample(
        self,
        parser: AudioCodesShowSipInterfaceParser,
        audiocodes_context: ParserContext,
    ) -> None:
        result = parser.parse(_read_sample("show_sip_interface.txt"), audiocodes_context)
        assert result.is_valid
        assert isinstance(result.voice_objects[0], SIPInterface)
        assert result.voice_objects[0].transport == "TLS"

    def test_parses_ini_sample(
        self,
        parser: AudioCodesShowSipInterfaceParser,
        audiocodes_context: ParserContext,
    ) -> None:
        result = parser.parse(_read_sample("show_sip_interface.ini"), audiocodes_context)
        assert result.is_valid
        assert result.structured_data["format"] == FORMAT_INI

    def test_parses_xml_sample(
        self,
        parser: AudioCodesShowSipInterfaceParser,
        audiocodes_context: ParserContext,
    ) -> None:
        result = parser.parse(_read_sample("show_sip_interface.xml"), audiocodes_context)
        assert result.is_valid
        assert result.structured_data["format"] == FORMAT_XML

    def test_voice_object_provenance(
        self,
        parser: AudioCodesShowSipInterfaceParser,
        audiocodes_context: ParserContext,
    ) -> None:
        result = parser.parse(_read_sample("show_sip_interface.txt"), audiocodes_context)
        sip_interface = result.voice_objects[0]
        assert sip_interface.source_parser == "audiocodes_show_sip_interface"
        assert sip_interface.source_command == "show sip-interface"
        assert sip_interface.vendor == "audiocodes"

    def test_invalid_empty_output(
        self,
        parser: AudioCodesShowSipInterfaceParser,
        audiocodes_context: ParserContext,
    ) -> None:
        result = parser.parse("", audiocodes_context)
        assert not result.is_valid


class TestParserRegistry:
    def test_registers_twelve_audiocodes_parsers(self, audiocodes_registry: ParserRegistry) -> None:
        commands = audiocodes_registry.list_commands("audiocodes")
        assert len(commands) == 12

    def test_lookup_show_ip_group(self, audiocodes_registry: ParserRegistry) -> None:
        parser = audiocodes_registry.get_parser("audiocodes", "show ip-group")
        assert parser.command == "show ip-group"

    def test_engine_runs_registered_parser(
        self,
        audiocodes_engine: ParserEngine,
        audiocodes_context: ParserContext,
    ) -> None:
        result = audiocodes_engine.parse(
            _read_sample("show_proxy_set.txt"),
            audiocodes_context,
            command="show proxy-set",
        )
        assert result.is_valid
        assert result.confidence > 0


class TestAdditionalAudioCodesParsers:
    @pytest.mark.parametrize(
        ("command", "sample", "expected_type"),
        [
            ("show configuration", "show_configuration.txt", "audiocodes_sbc_device"),
            ("show voip status", "show_voip_status.txt", "audiocodes_sbc_device"),
            ("show sip-interface", "show_sip_interface.txt", "audiocodes_sip_interface"),
            ("show proxy-set", "show_proxy_set.txt", "audiocodes_proxy_set"),
            ("show ip-group", "show_ip_group.txt", "audiocodes_ip_group"),
            ("show routing-table", "show_routing_table.txt", "audiocodes_routing_rule"),
            ("show tls-context", "show_tls_context.txt", "audiocodes_tls_context"),
            ("show certificates", "show_certificates.txt", "audiocodes_certificate"),
            ("show media-realm", "show_media_realm.txt", "audiocodes_media_realm"),
            ("show licenses", "show_licenses.txt", "audiocodes_license"),
            ("show ha-status", "show_ha_status.txt", "audiocodes_ha_cluster"),
            ("show sip-options", "show_sip_options.txt", "audiocodes_sip_message_policy"),
        ],
    )
    def test_parser_produces_voice_objects(
        self,
        audiocodes_engine: ParserEngine,
        audiocodes_context: ParserContext,
        command: str,
        sample: str,
        expected_type: str,
    ) -> None:
        result = audiocodes_engine.parse(_read_sample(sample), audiocodes_context, command=command)
        assert result.is_valid, result.errors
        assert result.voice_objects
        assert result.voice_objects[0].object_type == expected_type


class TestInvalidSchema:
    def test_invalid_xml_raises_error(self, audiocodes_context: ParserContext) -> None:
        parser = AudioCodesShowSipInterfaceParser()
        result = parser.parse("<not-closed", audiocodes_context)
        assert not result.is_valid
        assert result.errors

    def test_missing_required_identity(self, audiocodes_context: ParserContext) -> None:
        parser = AudioCodesShowIpGroupParser()
        result = parser.parse("State: Active\n", audiocodes_context)
        assert not result.is_valid

    def test_proxy_set_missing_identity(self, audiocodes_context: ParserContext) -> None:
        parser = AudioCodesShowProxySetParser()
        result = parser.parse("State: Active\n", audiocodes_context)
        assert not result.is_valid


class TestTopologyIntegration:
    def _build_topology_objects(self, audiocodes_context: ParserContext) -> list:
        engine = ParserEngine(registry=ParserRegistry())
        register_audiocodes_parsers(engine.registry)
        samples = (
            ("show sip-interface", "show_sip_interface.txt"),
            ("show proxy-set", "show_proxy_set.txt"),
            ("show ip-group", "show_ip_group.txt"),
            ("show routing-table", "show_routing_table.txt"),
            ("show tls-context", "show_tls_context.txt"),
            ("show certificates", "show_certificates.txt"),
            ("show media-realm", "show_media_realm.txt"),
        )
        objects = []
        for command, sample in samples:
            result = engine.parse(_read_sample(sample), audiocodes_context, command=command)
            objects.extend(result.voice_objects)
        return objects

    def test_topology_builder_partitions_audiocodes_objects(
        self,
        audiocodes_context: ParserContext,
    ) -> None:
        objects = self._build_topology_objects(audiocodes_context)
        topology = TopologyBuilder().build(objects)
        assert len(topology.audiocodes_sip_interfaces) == 1
        assert len(topology.audiocodes_proxy_sets) == 1
        assert len(topology.audiocodes_ip_groups) == 1
        assert len(topology.audiocodes_routing_rules) == 1
        assert topology.object_count >= 7

    def test_topology_all_objects_includes_audiocodes(
        self,
        audiocodes_context: ParserContext,
    ) -> None:
        objects = self._build_topology_objects(audiocodes_context)
        topology = TopologyBuilder().build(objects)
        types = {obj.object_type for obj in topology.all_objects()}
        assert "audiocodes_sip_interface" in types
        assert "audiocodes_ip_group" in types

    def test_relationship_builder_links_ip_group_to_proxy_set(
        self,
        audiocodes_context: ParserContext,
    ) -> None:
        objects = self._build_topology_objects(audiocodes_context)
        relationships = RelationshipBuilder().build(objects)
        ip_group = next(obj for obj in objects if isinstance(obj, IPGroup))
        proxy_set = next(obj for obj in objects if isinstance(obj, ProxySet))
        assert any(
            rel.source_object_id == ip_group.id and rel.target_object_id == proxy_set.id
            for rel in relationships
        )

    def test_relationship_builder_links_routing_rule_to_ip_group(
        self,
        audiocodes_context: ParserContext,
    ) -> None:
        objects = self._build_topology_objects(audiocodes_context)
        relationships = RelationshipBuilder().build(objects)
        rule = next(obj for obj in objects if isinstance(obj, RoutingRule))
        ip_group = next(obj for obj in objects if isinstance(obj, IPGroup))
        assert any(
            rel.source_object_id == rule.id and rel.target_object_id == ip_group.id
            for rel in relationships
        )


class TestFindings:
    def test_sip_interface_down_finding(self, audiocodes_context: ParserContext) -> None:
        parser = AudioCodesShowSipInterfaceParser()
        result = parser.parse(_read_sample("show_sip_interface_down.txt"), audiocodes_context)
        signals = {finding.signal for finding in result.findings}
        assert "sip_interface_down" in signals

    def test_tls_certificate_expired_finding(self, audiocodes_context: ParserContext) -> None:
        parser = AudioCodesShowCertificatesParser()
        result = parser.parse(_read_sample("show_certificates_expired.txt"), audiocodes_context)
        signals = {finding.signal for finding in result.findings}
        assert "tls_certificate_expired" in signals

    def test_session_license_exhausted_finding(self, audiocodes_context: ParserContext) -> None:
        from plugins.audiocodes.parser.sbc.show_licenses import AudioCodesShowLicensesParser

        parser = AudioCodesShowLicensesParser()
        result = parser.parse(_read_sample("show_licenses_exhausted.txt"), audiocodes_context)
        signals = {finding.signal for finding in result.findings}
        assert "session_license_exhausted" in signals

    def test_sip_options_failure_finding(self, audiocodes_context: ParserContext) -> None:
        from plugins.audiocodes.parser.sbc.show_sip_options import AudioCodesShowSipOptionsParser

        parser = AudioCodesShowSipOptionsParser()
        raw = "Policy Name: OPTIONS\nOptions Enabled: False\nOptions Status: Failed\n"
        result = parser.parse(raw, audiocodes_context)
        signals = {finding.signal for finding in result.findings}
        assert "sip_options_failure" in signals


class TestAvomImmutability:
    def test_sbc_device_is_frozen(self, audiocodes_context: ParserContext) -> None:
        from plugins.audiocodes.parser.sbc.show_voip_status import AudioCodesShowVoipStatusParser

        parser = AudioCodesShowVoipStatusParser()
        result = parser.parse(_read_sample("show_voip_status.txt"), audiocodes_context)
        device = result.voice_objects[0]
        assert isinstance(device, SBCDevice)
        with pytest.raises(FrozenInstanceError):
            device.device_status = "Down"  # type: ignore[misc]

    def test_certificate_is_frozen(self, audiocodes_context: ParserContext) -> None:
        parser = AudioCodesShowCertificatesParser()
        result = parser.parse(_read_sample("show_certificates.txt"), audiocodes_context)
        certificate = result.voice_objects[0]
        assert isinstance(certificate, Certificate)
        with pytest.raises(FrozenInstanceError):
            certificate.status = "Expired"  # type: ignore[misc]


class TestSerialization:
    def test_sip_interface_metadata_round_trip(self, audiocodes_context: ParserContext) -> None:
        parser = AudioCodesShowSipInterfaceParser()
        result = parser.parse(_read_sample("show_sip_interface.txt"), audiocodes_context)
        sip_interface = result.voice_objects[0]
        payload = {
            "id": sip_interface.id,
            "object_type": sip_interface.object_type,
            "interface_name": sip_interface.interface_name,
            "metadata": sip_interface.metadata,
        }
        assert json.loads(json.dumps(payload))["object_type"] == "audiocodes_sip_interface"

    def test_parser_result_structured_data_serializable(self, audiocodes_context: ParserContext) -> None:
        parser = AudioCodesShowSipInterfaceParser()
        result = parser.parse(_read_sample("show_sip_interface.txt"), audiocodes_context)
        json.dumps(result.structured_data)

    def test_ha_cluster_object_fields(self, audiocodes_context: ParserContext) -> None:
        from plugins.audiocodes.parser.sbc.show_ha_status import AudioCodesShowHaStatusParser

        parser = AudioCodesShowHaStatusParser()
        result = parser.parse(_read_sample("show_ha_status.txt"), audiocodes_context)
        cluster = result.voice_objects[0]
        assert isinstance(cluster, HACluster)
        assert cluster.sync_state == "Synchronized"

    def test_sip_message_policy_object_fields(self, audiocodes_context: ParserContext) -> None:
        from plugins.audiocodes.parser.sbc.show_sip_options import AudioCodesShowSipOptionsParser

        parser = AudioCodesShowSipOptionsParser()
        result = parser.parse(_read_sample("show_sip_options.txt"), audiocodes_context)
        policy = result.voice_objects[0]
        assert isinstance(policy, SIPMessagePolicy)
        assert policy.options_enabled is True

    def test_media_realm_object_fields(self, audiocodes_context: ParserContext) -> None:
        from plugins.audiocodes.parser.sbc.show_media_realm import AudioCodesShowMediaRealmParser

        parser = AudioCodesShowMediaRealmParser()
        result = parser.parse(_read_sample("show_media_realm.txt"), audiocodes_context)
        realm = result.voice_objects[0]
        assert isinstance(realm, MediaRealm)
        assert realm.port_range == "6000-6499"

    def test_license_object_fields(self, audiocodes_context: ParserContext) -> None:
        from plugins.audiocodes.parser.sbc.show_licenses import AudioCodesShowLicensesParser

        parser = AudioCodesShowLicensesParser()
        result = parser.parse(_read_sample("show_licenses.txt"), audiocodes_context)
        license_obj = result.voice_objects[0]
        assert isinstance(license_obj, License)
        assert license_obj.sessions_total == 500

    def test_tls_context_object_fields(self, audiocodes_context: ParserContext) -> None:
        from plugins.audiocodes.parser.sbc.show_tls_context import AudioCodesShowTlsContextParser

        parser = AudioCodesShowTlsContextParser()
        result = parser.parse(_read_sample("show_tls_context.txt"), audiocodes_context)
        tls_context = result.voice_objects[0]
        assert isinstance(tls_context, TLSContext)
        assert tls_context.certificate_name == "SBC_CERT"

    def test_default_parser_engine_registers_audiocodes(self) -> None:
        from runtime.parser_bootstrap import build_default_parser_engine

        engine = build_default_parser_engine()
        assert engine is not None
        assert engine.registry.has_parser("audiocodes", "show ip-group")
