"""Tests for attaching parser-produced CVOM objects to cases."""

from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from model.dial_peer import DialPeer
from model.sip_ua import SipUA
from model.voice_service import VoiceService
from runtime.analysis_engine import AnalysisEngine, attach_voice_objects_to_case
from runtime.evidence_collection import initialize_evidence_collection, submit_evidence
from runtime.parser_bootstrap import build_default_parser_engine
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry
from runtime.runtime_engine import RuntimeEngine
from shared.config import RuntimeConfig

PLUGINS_ROOT = Path(__file__).resolve().parents[1] / "plugins"
PLAYBOOK_ID = "VP-CUBE-0001"
INTAKE_ANSWERS = [
    "yes",
    "2026-06-10",
    "no changes",
    "all destinations",
    "yes",
]
SAMPLE_DIR = Path(__file__).resolve().parents[1] / "examples" / "sample_evidence" / "parser"


@pytest.fixture
def runtime_engine() -> RuntimeEngine:
    registry = PluginRegistry(plugins_root=PLUGINS_ROOT)
    loader = PlaybookLoader(
        repository=FilesystemPlaybookRepository(YamlLoader()),
    )
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
def parser_engine():
    engine = build_default_parser_engine()
    if engine is None:
        pytest.skip("Cisco parser pack not available")
    return engine


def _case_with_parser_evidence(runtime_engine: RuntimeEngine) -> str:
    turn = runtime_engine.start_investigation(PLAYBOOK_ID)
    for answer in INTAKE_ANSWERS:
        turn = runtime_engine.submit_answer(turn.case_id, turn.question_id, answer)
    case = runtime_engine.case_manager.load_case(turn.case_id)
    playbook = runtime_engine.playbook_catalog.get(PLAYBOOK_ID)
    initialize_evidence_collection(case, runtime_engine.case_manager, playbook)
    case = runtime_engine.case_manager.load_case(case.case_id)

    evidence_files = (
        ("show dial-peer voice summary", "show_dial_peer_voice_summary_normal.txt"),
        ("show sip-ua status", "show_sip_ua_status_disabled.txt"),
        ("show run | sec voice service voip", "show_run_voice_service_voip_disabled.txt"),
        ("debug ccsip messages", "debug_ccsip_503.txt"),
    )
    for command, filename in evidence_files:
        raw_text = (SAMPLE_DIR / filename).read_text(encoding="utf-8")
        submit_evidence(
            case,
            runtime_engine.case_manager,
            command,
            raw_text,
        )
        case = runtime_engine.case_manager.load_case(case.case_id)

    return case.case_id


class TestVoiceObjectCaseAttachment:
    def test_analysis_attaches_voice_objects_from_parsers(
        self,
        runtime_engine: RuntimeEngine,
        parser_engine,
    ) -> None:
        case_id = _case_with_parser_evidence(runtime_engine)
        case = runtime_engine.case_manager.load_case(case_id)

        AnalysisEngine(parser_engine=parser_engine).analyze(case)

        assert len(case.voice_objects) == 4
        dial_peers = [obj for obj in case.voice_objects if isinstance(obj, DialPeer)]
        sip_uas = [obj for obj in case.voice_objects if isinstance(obj, SipUA)]
        voice_services = [obj for obj in case.voice_objects if isinstance(obj, VoiceService)]
        assert len(dial_peers) == 2
        assert len(sip_uas) == 1
        assert len(voice_services) == 1

    def test_voice_objects_preserve_provenance(
        self,
        runtime_engine: RuntimeEngine,
        parser_engine,
    ) -> None:
        case_id = _case_with_parser_evidence(runtime_engine)
        case = runtime_engine.case_manager.load_case(case_id)

        AnalysisEngine(parser_engine=parser_engine).analyze(case)

        sip_ua = next(obj for obj in case.voice_objects if isinstance(obj, SipUA))
        assert sip_ua.source_parser == "cisco_show_sip_ua_status"
        assert sip_ua.source_command == "show sip-ua status"
        assert sip_ua.source_evidence_id

        dial_peer = next(
            obj
            for obj in case.voice_objects
            if isinstance(obj, DialPeer) and str(obj.tag) == "1"
        )
        assert dial_peer.source_parser == "cisco_show_dial_peer_voice_summary"
        assert dial_peer.source_command == "show dial-peer voice summary"
        assert dial_peer.destination_pattern == "9T"

    def test_duplicate_voice_object_ids_are_not_reattached(
        self,
        runtime_engine: RuntimeEngine,
        parser_engine,
    ) -> None:
        case_id = _case_with_parser_evidence(runtime_engine)
        case = runtime_engine.case_manager.load_case(case_id)
        engine = AnalysisEngine(parser_engine=parser_engine)

        engine.analyze(case)
        first_count = len(case.voice_objects)
        first_ids = {obj.id for obj in case.voice_objects}

        engine.analyze(case)
        second_count = len(case.voice_objects)
        second_ids = {obj.id for obj in case.voice_objects}

        assert first_count == 4
        assert second_count == 4
        assert len(first_ids) == 4
        assert len(second_ids) == 4

    def test_analyze_case_persists_voice_objects(
        self,
        runtime_engine: RuntimeEngine,
    ) -> None:
        case_id = _case_with_parser_evidence(runtime_engine)

        runtime_engine.analyze_case(case_id)
        case = runtime_engine.case_manager.load_case(case_id)

        assert len(case.voice_objects) == 4

    def test_attach_voice_objects_to_case_helper_deduplicates(self) -> None:
        from domain.enums import InvestigationState, Severity
        from domain.models import Case
        from domain.value_objects import AffectedScope, PlatformRef, SymptomSummary
        from model.voice_graph import base_object_fields

        case = Case(
            case_id="CASE-VO-ATTACH",
            title="test",
            status=InvestigationState.COLLECTION,
            severity=Severity.HIGH,
            business_impact="test",
            symptom=SymptomSummary(summary="test"),
            affected_scope=AffectedScope(),
            platform=PlatformRef(vendor="cisco"),
        )
        shared_fields = base_object_fields(
            object_type="sip_ua",
            vendor="cisco",
            platform="cube",
            hostname="cube-01",
            name="sip-ua",
            description="SIP user agent status",
            source_parser="cisco_show_sip_ua_status",
            source_command="show sip-ua status",
            source_evidence_id="EVID-1",
            confidence=95.0,
            object_id="VOBJ-fixed-id",
        )
        first = SipUA(**shared_fields)
        duplicate = SipUA(**shared_fields)
        different = SipUA.create(
            vendor="cisco",
            platform="cube",
            hostname="cube-01",
            source_parser="cisco_show_sip_ua_status",
            source_command="show sip-ua status",
            source_evidence_id="EVID-2",
            confidence=90.0,
        )

        attached = attach_voice_objects_to_case(case, [first, duplicate, different])

        assert attached == 2
        assert len(case.voice_objects) == 2
        assert {obj.id for obj in case.voice_objects} == {first.id, different.id}
