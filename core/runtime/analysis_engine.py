"""Deterministic lightweight analysis of collected CLI evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from domain.enums import InvestigationState
from domain.models import AnalysisFinding, Case, Evidence

Analyzer = Callable[[str], list[str]]

SIP_UA_STATUS_COMMAND = "show sip-ua status"
DIAL_PEER_SUMMARY_COMMAND = "show dial-peer voice summary"
CCSIP_DEBUG_COMMAND = "debug ccsip messages"

SIP_CODE_PATTERNS: tuple[tuple[str, str], ...] = (
    ("404 Not Found", "sip_404_detected"),
    ("403 Forbidden", "sip_403_detected"),
    ("408 Request Timeout", "sip_408_detected"),
    ("488 Not Acceptable Here", "sip_488_detected"),
    ("503 Service Unavailable", "sip_503_detected"),
)

COMMAND_ANALYZERS: dict[str, Analyzer] = {}


@dataclass(frozen=True)
class AnalysisSummary:
    """Result of analyzing collected evidence for a case."""

    case_id: str
    state: InvestigationState
    findings: tuple[str, ...]


class AnalysisEngine:
    """v1 deterministic pattern matcher for pasted CLI evidence."""

    def analyze(self, case: Case) -> list[AnalysisFinding]:
        """Analyze all collected evidence and return findings."""
        findings: list[AnalysisFinding] = []
        seen_signals: set[str] = set()

        for evidence in case.evidence:
            if not evidence.raw_text:
                continue

            command = _normalize_command(evidence.source.command or "")
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
                    )
                )
                evidence.parser_finding_ids.append(findings[-1].finding_id)

        return findings


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
        findings=tuple(finding.signal for finding in findings),
    )


def format_analysis_summary(summary: AnalysisSummary) -> str:
    """Format analysis results for terminal output."""
    lines = [
        "Analysis complete. Next phase: HYPOTHESIS.",
        "Findings:",
    ]
    if summary.findings:
        lines.extend(f"- {signal}" for signal in summary.findings)
    else:
        lines.append("- (none)")
    return "\n".join(lines)


def _normalize_command(command: str) -> str:
    return " ".join(command.strip().lower().split())


def _register_analyzers() -> None:
    COMMAND_ANALYZERS[SIP_UA_STATUS_COMMAND] = analyze_sip_ua_status
    COMMAND_ANALYZERS[DIAL_PEER_SUMMARY_COMMAND] = analyze_dial_peer_summary
    COMMAND_ANALYZERS[CCSIP_DEBUG_COMMAND] = analyze_ccsip_debug


_register_analyzers()
