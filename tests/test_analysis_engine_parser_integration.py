"""Tests for parser framework integration with AnalysisEngine."""

from __future__ import annotations

from pathlib import Path

import pytest

from domain.enums import InvestigationState
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.analysis_engine import AnalysisEngine, FINDING_SOURCE_PARSER, FINDING_SOURCE_V1
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


def _case_with_evidence(
    runtime_engine: RuntimeEngine,
    *,
    sip_ua_text: str,
    voip_config_text: str = "voice service voip\n sip\n",
    debug_text: str = "SIP/2.0 503 Service Unavailable",
) -> str:
    turn = runtime_engine.start_investigation(PLAYBOOK_ID)
    for answer in INTAKE_ANSWERS:
        turn = runtime_engine.submit_answer(turn.case_id, turn.question_id, answer)
    case = runtime_engine.case_manager.load_case(turn.case_id)
    playbook = runtime_engine.playbook_catalog.get(PLAYBOOK_ID)
    initialize_evidence_collection(case, runtime_engine.case_manager, playbook)
    case = runtime_engine.case_manager.load_case(case.case_id)

    submit_evidence(
        case,
        runtime_engine.case_manager,
        "show dial-peer voice summary",
        "dial-peer 1 voip up\n destination-pattern 9T",
    )
    case = runtime_engine.case_manager.load_case(case.case_id)
    submit_evidence(
        case,
        runtime_engine.case_manager,
        "show sip-ua status",
        sip_ua_text,
    )
    case = runtime_engine.case_manager.load_case(case.case_id)
    submit_evidence(
        case,
        runtime_engine.case_manager,
        "show run | sec voice service voip",
        voip_config_text,
    )
    case = runtime_engine.case_manager.load_case(case.case_id)
    submit_evidence(
        case,
        runtime_engine.case_manager,
        "debug ccsip messages",
        debug_text,
    )
    return case.case_id


class TestAnalysisEngineParserIntegration:
    def test_disabled_sip_ua_uses_parser_findings(
        self,
        parser_engine,
    ) -> None:
        from domain.enums import Severity
        from domain.models import Case, Evidence
        from domain.value_objects import AffectedScope, EvidenceQuality, EvidenceSource, PlatformRef, SymptomSummary

        raw = (SAMPLE_DIR / "show_sip_ua_status_disabled.txt").read_text(encoding="utf-8")
        case = Case.create(
            title="Parser integration",
            symptom=SymptomSummary(summary="outbound calls fail"),
            severity=Severity.HIGH,
            business_impact="test",
            affected_scope=AffectedScope(),
            platform=PlatformRef(vendor="cisco", products=("CUBE",)),
            playbook_id=PLAYBOOK_ID,
        )
        case.status = InvestigationState.ANALYSIS
        evidence = Evidence(
            evidence_id="EVD-test",
            case_id=case.case_id,
            type="cli_output",
            title="CLI paste",
            source=EvidenceSource(
                origin="cli_paste",
                collector="engineer",
                command="show sip-ua status",
            ),
            collected_at=case.opened_at,
            quality=EvidenceQuality(
                completeness=1.0,
                freshness=1.0,
                reliability=1.0,
                parseability=1.0,
                overall=1.0,
            ),
            raw_text=raw,
        )
        case.evidence.append(evidence)

        findings = AnalysisEngine(parser_engine=parser_engine).analyze(case)
        signals = {finding.signal for finding in findings}
        sip_finding = next(f for f in findings if f.signal == "sip_ua_disabled")

        assert "sip_ua_disabled" in signals
        assert sip_finding.metadata is not None
        assert sip_finding.metadata["source"] == FINDING_SOURCE_PARSER
        assert sip_finding.metadata["structured_data"]["sip_ua_enabled"] is False
        assert "related_voice_object_ids" in sip_finding.metadata
        assert len(sip_finding.metadata["related_voice_object_ids"]) == 1
        assert sip_finding.metadata["related_voice_object_ids"][0].startswith("VOBJ-")

    def test_debug_ccsip_uses_parser_for_503(
        self,
        parser_engine,
    ) -> None:
        from domain.enums import Severity
        from domain.models import Case, Evidence
        from domain.value_objects import AffectedScope, EvidenceQuality, EvidenceSource, PlatformRef, SymptomSummary

        raw = (SAMPLE_DIR / "debug_ccsip_503.txt").read_text(encoding="utf-8")
        case = Case.create(
            title="Parser integration",
            symptom=SymptomSummary(summary="outbound calls fail"),
            severity=Severity.HIGH,
            business_impact="test",
            affected_scope=AffectedScope(),
            platform=PlatformRef(vendor="cisco", products=("CUBE",)),
            playbook_id=PLAYBOOK_ID,
        )
        case.status = InvestigationState.ANALYSIS
        evidence = Evidence(
            evidence_id="EVD-debug",
            case_id=case.case_id,
            type="cli_output",
            title="CLI paste",
            source=EvidenceSource(
                origin="cli_paste",
                collector="engineer",
                command="debug ccsip messages",
            ),
            collected_at=case.opened_at,
            quality=EvidenceQuality(
                completeness=1.0,
                freshness=1.0,
                reliability=1.0,
                parseability=1.0,
                overall=1.0,
            ),
            raw_text=raw,
        )
        case.evidence.append(evidence)

        findings = AnalysisEngine(parser_engine=parser_engine).analyze(case)
        debug_finding = next(f for f in findings if f.signal == "sip_503_detected")

        assert debug_finding.metadata is not None
        assert debug_finding.metadata["source"] == FINDING_SOURCE_PARSER
        assert 503 in debug_finding.metadata["structured_data"]["response_codes"]

    def test_analyze_case_stores_parser_generated_findings(
        self,
        runtime_engine: RuntimeEngine,
    ) -> None:
        disabled = (SAMPLE_DIR / "show_sip_ua_status_disabled.txt").read_text(encoding="utf-8")
        case_id = _case_with_evidence(runtime_engine, sip_ua_text=disabled)

        runtime_engine.analyze_case(case_id)
        case = runtime_engine.case_manager.load_case(case_id)
        signals = {finding.signal for finding in case.analysis_findings}

        assert "sip_ua_disabled" in signals
        assert "sip_503_detected" in signals

        sip_finding = next(f for f in case.analysis_findings if f.signal == "sip_ua_disabled")
        assert sip_finding.metadata is not None
        assert sip_finding.metadata["source"] == FINDING_SOURCE_PARSER
        assert sip_finding.metadata["structured_data"]["sip_ua_enabled"] is False
        assert "related_voice_object_ids" in sip_finding.metadata
        assert sip_finding.metadata["related_voice_object_ids"]

        debug_finding = next(f for f in case.analysis_findings if f.signal == "sip_503_detected")
        assert debug_finding.metadata is not None
        assert debug_finding.metadata["source"] == FINDING_SOURCE_PARSER

    def test_v1_fallback_when_parser_engine_not_configured(self) -> None:
        from domain.enums import Severity
        from domain.models import Case, Evidence
        from domain.value_objects import AffectedScope, EvidenceQuality, EvidenceSource, PlatformRef, SymptomSummary

        case = Case.create(
            title="V1 only",
            symptom=SymptomSummary(summary="outbound calls fail"),
            severity=Severity.HIGH,
            business_impact="test",
            affected_scope=AffectedScope(),
            platform=PlatformRef(vendor="cisco", products=("CUBE",)),
        )
        case.status = InvestigationState.ANALYSIS
        evidence = Evidence(
            evidence_id="EVD-v1",
            case_id=case.case_id,
            type="cli_output",
            title="CLI paste",
            source=EvidenceSource(
                origin="cli_paste",
                collector="engineer",
                command="show sip-ua status",
            ),
            collected_at=case.opened_at,
            quality=EvidenceQuality(
                completeness=1.0,
                freshness=1.0,
                reliability=1.0,
                parseability=1.0,
                overall=1.0,
            ),
            raw_text="SIP-UA Status: disabled",
        )
        case.evidence.append(evidence)

        findings = AnalysisEngine(parser_engine=None).analyze(case)

        assert any(finding.signal == "sip_ua_disabled" for finding in findings)
        assert all(finding.metadata and finding.metadata["source"] == FINDING_SOURCE_V1 for finding in findings)

    def test_voice_service_parser_links_voice_object_ids(
        self,
        parser_engine,
    ) -> None:
        from domain.enums import Severity
        from domain.models import Case, Evidence
        from domain.value_objects import AffectedScope, EvidenceQuality, EvidenceSource, PlatformRef, SymptomSummary

        raw = (SAMPLE_DIR / "show_run_voice_service_voip_disabled.txt").read_text(encoding="utf-8")
        case = Case.create(
            title="Voice service CVOM integration",
            symptom=SymptomSummary(summary="outbound calls fail"),
            severity=Severity.HIGH,
            business_impact="test",
            affected_scope=AffectedScope(),
            platform=PlatformRef(vendor="cisco", products=("CUBE",)),
            playbook_id=PLAYBOOK_ID,
        )
        case.status = InvestigationState.ANALYSIS
        case.evidence.append(
            Evidence(
                evidence_id="EVD-voip-config",
                case_id=case.case_id,
                type="cli_output",
                title="CLI paste",
                source=EvidenceSource(
                    origin="cli_paste",
                    collector="engineer",
                    command="show run | sec voice service voip",
                ),
                collected_at=case.opened_at,
                quality=EvidenceQuality(
                    completeness=1.0,
                    freshness=1.0,
                    reliability=1.0,
                    parseability=1.0,
                    overall=1.0,
                ),
                raw_text=raw,
            )
        )

        findings = AnalysisEngine(parser_engine=parser_engine).analyze(case)
        disabled_finding = next(f for f in findings if f.signal == "sip_ua_disabled_by_config")

        assert disabled_finding.metadata is not None
        assert disabled_finding.metadata["source"] == FINDING_SOURCE_PARSER
        assert disabled_finding.metadata["parser_id"] == "cisco_show_run_voice_service_voip"
        assert "related_voice_object_ids" in disabled_finding.metadata
        assert len(disabled_finding.metadata["related_voice_object_ids"]) == 1

    def test_dial_peer_parser_links_voice_object_ids(
        self,
        parser_engine,
    ) -> None:
        from domain.enums import Severity
        from domain.models import Case, Evidence
        from domain.value_objects import AffectedScope, EvidenceQuality, EvidenceSource, PlatformRef, SymptomSummary

        raw = (SAMPLE_DIR / "show_dial_peer_voice_summary_normal.txt").read_text(encoding="utf-8")
        case = Case.create(
            title="Dial-peer CVOM integration",
            symptom=SymptomSummary(summary="outbound calls fail"),
            severity=Severity.HIGH,
            business_impact="test",
            affected_scope=AffectedScope(),
            platform=PlatformRef(vendor="cisco", products=("CUBE",)),
            playbook_id=PLAYBOOK_ID,
        )
        case.status = InvestigationState.ANALYSIS
        case.evidence.append(
            Evidence(
                evidence_id="EVD-dial-peer-cvom",
                case_id=case.case_id,
                type="cli_output",
                title="CLI paste",
                source=EvidenceSource(
                    origin="cli_paste",
                    collector="engineer",
                    command="show dial-peer voice summary",
                ),
                collected_at=case.opened_at,
                quality=EvidenceQuality(
                    completeness=1.0,
                    freshness=1.0,
                    reliability=1.0,
                    parseability=1.0,
                    overall=1.0,
                ),
                raw_text=raw,
            )
        )

        findings = AnalysisEngine(parser_engine=parser_engine).analyze(case)
        config_finding = next(f for f in findings if f.signal == "dial_peer_config_present")

        assert config_finding.metadata is not None
        assert config_finding.metadata["source"] == FINDING_SOURCE_PARSER
        assert config_finding.metadata["parser_id"] == "cisco_show_dial_peer_voice_summary"
        assert "related_voice_object_ids" in config_finding.metadata
        assert len(config_finding.metadata["related_voice_object_ids"]) == 2
