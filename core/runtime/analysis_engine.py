"""Deterministic lightweight analysis of collected CLI evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from domain.enums import InvestigationState
from domain.models import AnalysisFinding, Case, Evidence
from parser.parser_context import ParserContext
from parser.parser_engine import ParserEngine
from parser.parser_exceptions import VoicePilotParserError
from parser.parser_result import ParserResult
from shared.types import JsonDict

Analyzer = Callable[[str], list[str]]

SIP_UA_STATUS_COMMAND = "show sip-ua status"
DIAL_PEER_SUMMARY_COMMAND = "show dial-peer voice summary"
CCSIP_DEBUG_COMMAND = "debug ccsip messages"
SHOW_RUN_VOICE_SERVICE_VOIP_COMMAND = "show run | sec voice service voip"

SIP_CODE_PATTERNS: tuple[tuple[str, str], ...] = (
    ("404 Not Found", "sip_404_detected"),
    ("403 Forbidden", "sip_403_detected"),
    ("408 Request Timeout", "sip_408_detected"),
    ("488 Not Acceptable Here", "sip_488_detected"),
    ("503 Service Unavailable", "sip_503_detected"),
)

COMMAND_ANALYZERS: dict[str, Analyzer] = {}
FINDING_SOURCE_PARSER = "parser"
FINDING_SOURCE_V1 = "v1_pattern_match"

PARSER_ID_BY_COMMAND: dict[str, str] = {
    SIP_UA_STATUS_COMMAND: "cisco_show_sip_ua_status",
    DIAL_PEER_SUMMARY_COMMAND: "cisco_show_dial_peer_voice_summary",
    CCSIP_DEBUG_COMMAND: "cisco_debug_ccsip_messages",
    SHOW_RUN_VOICE_SERVICE_VOIP_COMMAND: "cisco_show_run_voice_service_voip",
}


@dataclass(frozen=True)
class AnalysisSummaryFinding:
    """Serializable analysis finding for CLI and runtime consumers."""

    signal: str
    source_label: str


@dataclass(frozen=True)
class AnalysisSummary:
    """Result of analyzing collected evidence for a case."""

    case_id: str
    state: InvestigationState
    findings: tuple[AnalysisSummaryFinding, ...]


class AnalysisEngine:
    """Deterministic evidence analysis with parser-first and v1 pattern fallback."""

    def __init__(self, parser_engine: ParserEngine | None = None) -> None:
        self._parser_engine = parser_engine

    def analyze(self, case: Case) -> list[AnalysisFinding]:
        """Analyze all collected evidence and return findings."""
        findings: list[AnalysisFinding] = []
        seen_signals: set[str] = set()

        for evidence in case.evidence:
            if not evidence.raw_text:
                continue

            command = _normalize_command(evidence.source.command or "")
            parser_findings = self._analyze_with_parser(case, evidence, command)
            if parser_findings is not None:
                self._append_findings(
                    findings,
                    parser_findings,
                    seen_signals,
                    evidence,
                )
                continue

            analyzer = COMMAND_ANALYZERS.get(command)
            if analyzer is None:
                continue

            for signal in analyzer(evidence.raw_text):
                if signal in seen_signals:
                    continue
                seen_signals.add(signal)
                findings.append(
                    AnalysisFinding.create(
                        case_id=case.case_id,
                        evidence_id=evidence.evidence_id,
                        command=command,
                        signal=signal,
                        metadata={"source": FINDING_SOURCE_V1},
                    )
                )
                evidence.parser_finding_ids.append(findings[-1].finding_id)

        return findings

    def _analyze_with_parser(
        self,
        case: Case,
        evidence: Evidence,
        command: str,
    ) -> list[AnalysisFinding] | None:
        """Try parser-based analysis. Return None to fall back to v1 patterns."""
        if self._parser_engine is None or not command:
            return None

        vendor = _resolve_vendor(case)
        if not self._parser_engine.registry.has_parser(vendor, command):
            return None

        context = _build_parser_context(case, evidence, vendor)
        try:
            result = self._parser_engine.parse(
                evidence.raw_text or "",
                context,
                command=command,
            )
        except VoicePilotParserError:
            return None

        if not result.is_valid:
            return None

        return _findings_from_parser_result(case, evidence, command, result)

    def _append_findings(
        self,
        findings: list[AnalysisFinding],
        new_findings: list[AnalysisFinding],
        seen_signals: set[str],
        evidence: Evidence,
    ) -> None:
        for finding in new_findings:
            if finding.signal in seen_signals:
                continue
            seen_signals.add(finding.signal)
            findings.append(finding)
            evidence.parser_finding_ids.append(finding.finding_id)


def analyze_sip_ua_status(text: str) -> list[str]:
    """Detect simple SIP-UA status patterns."""
    findings: list[str] = []
    lower = text.lower()

    if "sip-ua status: enabled" in lower or "sip user agent status: enabled" in lower:
        findings.append("sip_ua_enabled")
    if re.search(r"\bdisabled\b", lower):
        findings.append("sip_ua_disabled")
    if "registrar" in lower or re.search(r"\bregistered\b", lower):
        findings.append("sip_registration_present")
    if "unregistered" in lower or re.search(r"\bfailed\b", lower):
        findings.append("sip_registration_issue")

    return findings


def analyze_dial_peer_summary(text: str) -> list[str]:
    """Detect simple dial-peer summary patterns."""
    findings: list[str] = []
    stripped = text.strip()
    lower = text.lower()

    if len(stripped) < 10:
        findings.append("dial_peer_summary_missing_or_empty")

    if any(token in lower for token in ("dial-peer", "peer tag", "destination-pattern")):
        findings.append("dial_peer_config_present")
    if "down" in lower or "out of service" in lower:
        findings.append("dial_peer_down")

    return findings


def analyze_ccsip_debug(text: str) -> list[str]:
    """Detect SIP response codes and trace markers in debug output."""
    findings: list[str] = []
    lower = text.lower()

    for pattern, signal in SIP_CODE_PATTERNS:
        if pattern in text:
            findings.append(signal)

    if "from:" in lower and "to:" in lower and "call-id:" in lower:
        findings.append("sip_trace_present")

    return findings


def build_analysis_summary(case: Case, findings: list[AnalysisFinding]) -> AnalysisSummary:
    """Build a summary object from case state and findings."""
    return AnalysisSummary(
        case_id=case.case_id,
        state=case.status,
        findings=tuple(
            AnalysisSummaryFinding(
                signal=finding.signal,
                source_label=format_finding_source_label(finding.metadata),
            )
            for finding in findings
        ),
    )


def format_finding_source_label(metadata: JsonDict | None) -> str:
    """Format a human-readable finding source label."""
    if not metadata:
        return FINDING_SOURCE_V1
    if metadata.get("source") == FINDING_SOURCE_PARSER:
        parser_id = metadata.get("parser_id")
        if isinstance(parser_id, str) and parser_id:
            return f"parser:{parser_id}"
        return FINDING_SOURCE_PARSER
    return FINDING_SOURCE_V1


def summarize_structured_data(metadata: JsonDict | None) -> str | None:
    """Build a short readable summary of parser structured data."""
    if not metadata or metadata.get("source") != FINDING_SOURCE_PARSER:
        return None

    structured_data = metadata.get("structured_data")
    if not isinstance(structured_data, dict):
        return None

    parts: list[str] = []
    if structured_data.get("sip_ua_enabled") is not None:
        parts.append(f"sip_ua_enabled={structured_data['sip_ua_enabled']}")
    if structured_data.get("sip_ua_disabled_by_config") is not None:
        parts.append(
            f"sip_ua_disabled_by_config={structured_data['sip_ua_disabled_by_config']}"
        )
    if structured_data.get("registration_state"):
        parts.append(f"registration_state={structured_data['registration_state']}")
    if structured_data.get("response_codes"):
        parts.append(f"response_codes={structured_data['response_codes']}")
    if structured_data.get("dial_peer_count") is not None:
        parts.append(f"dial_peer_count={structured_data['dial_peer_count']}")
    if structured_data.get("voip_dial_peer_count") is not None:
        parts.append(f"voip_dial_peer_count={structured_data['voip_dial_peer_count']}")
    if structured_data.get("down_dial_peer_count"):
        parts.append(f"down_dial_peer_count={structured_data['down_dial_peer_count']}")

    return ", ".join(parts) if parts else None


def format_analysis_summary(summary: AnalysisSummary) -> str:
    """Format analysis results for terminal output."""
    lines = [
        "Analysis complete. Next phase: HYPOTHESIS.",
        "Findings:",
    ]
    if summary.findings:
        for finding in summary.findings:
            lines.append(f"- {finding.signal} ({finding.source_label})")
    else:
        lines.append("- (none)")
    return "\n".join(lines)


def _normalize_command(command: str) -> str:
    return " ".join(command.strip().lower().split())


def _resolve_vendor(case: Case) -> str:
    return case.platform.vendor.strip().lower()


def _build_parser_context(case: Case, evidence: Evidence, vendor: str) -> ParserContext:
    platform = case.platform.products[0] if case.platform.products else None
    return ParserContext(
        vendor=vendor,
        case_id=case.case_id,
        evidence_id=evidence.evidence_id,
        device_id=evidence.source.device_id,
        platform=platform,
        hostname=None,
        collection_timestamp=evidence.collected_at,
    )


def _findings_from_parser_result(
    case: Case,
    evidence: Evidence,
    command: str,
    result: ParserResult,
) -> list[AnalysisFinding]:
    findings: list[AnalysisFinding] = []
    for parser_finding in result.findings:
        findings.append(
            AnalysisFinding.create(
                case_id=case.case_id,
                evidence_id=evidence.evidence_id,
                command=command,
                signal=parser_finding.signal,
                detail=parser_finding.detail,
                metadata=_parser_finding_metadata(result, parser_finding.signal, command),
            )
        )
    return findings


def _parser_finding_metadata(result: ParserResult, signal: str, command: str) -> JsonDict:
    normalized_command = _normalize_command(command)
    voice_object_ids = [obj.id for obj in result.voice_objects]
    metadata: JsonDict = {
        "source": FINDING_SOURCE_PARSER,
        "parser_id": PARSER_ID_BY_COMMAND.get(normalized_command),
        "parser_version": result.parser_version,
        "parser_confidence": result.confidence,
        "signal": signal,
        "structured_data": dict(result.structured_data),
        "parser_metadata": dict(result.metadata),
        "parser_warnings": list(result.warnings),
    }
    if voice_object_ids:
        metadata["related_voice_object_ids"] = voice_object_ids
    return metadata


def _register_analyzers() -> None:
    COMMAND_ANALYZERS[SIP_UA_STATUS_COMMAND] = analyze_sip_ua_status
    COMMAND_ANALYZERS[DIAL_PEER_SUMMARY_COMMAND] = analyze_dial_peer_summary
    COMMAND_ANALYZERS[CCSIP_DEBUG_COMMAND] = analyze_ccsip_debug


_register_analyzers()
