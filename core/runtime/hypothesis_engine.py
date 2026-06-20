"""Deterministic hypothesis generation from analysis findings."""

from __future__ import annotations

from dataclasses import dataclass

from domain.enums import HypothesisStatus, InvestigationState
from domain.models import AnalysisFinding, Case, Hypothesis

VP_CUBE_0001_PLAYBOOK_ID = "VP-CUBE-0001"
INSUFFICIENT_EVIDENCE_TITLE = "Insufficient evidence to rank root cause"
INSUFFICIENT_EVIDENCE_CONFIDENCE = 25.0


@dataclass(frozen=True)
class HypothesisRule:
    """Deterministic mapping from finding signals to a hypothesis."""

    rule_id: str
    title: str
    confidence: float
    required_signals: frozenset[str]
    supporting_signals: frozenset[str]
    explanation: str
    next_best_action: str
    forbidden_signals: frozenset[str] = frozenset()


@dataclass(frozen=True)
class HypothesisSummaryItem:
    """Serializable hypothesis result for CLI and API consumers."""

    hypothesis_id: str
    title: str
    confidence: float
    supporting_signals: tuple[str, ...]
    explanation: str
    next_best_action: str
    rank: int


@dataclass(frozen=True)
class HypothesisSummary:
    """Result of generating ranked hypotheses for a case."""

    case_id: str
    state: InvestigationState
    hypotheses: tuple[HypothesisSummaryItem, ...]


VP_CUBE_0001_RULES: tuple[HypothesisRule, ...] = (
    HypothesisRule(
        rule_id="HYP-404-ROUTING",
        title="Routing / dial-peer issue",
        confidence=70.0,
        required_signals=frozenset({"sip_404_detected", "dial_peer_config_present"}),
        supporting_signals=frozenset({"sip_404_detected", "dial_peer_config_present"}),
        explanation="SIP 404 with dial-peer configuration present suggests local routing or dial-peer mismatch.",
        next_best_action="Validate dial-peer match and translation for the failing destination.",
    ),
    HypothesisRule(
        rule_id="HYP-404-MISSING",
        title="Missing or unmatched outbound dial-peer",
        confidence=82.0,
        required_signals=frozenset({"sip_404_detected"}),
        supporting_signals=frozenset({"sip_404_detected"}),
        forbidden_signals=frozenset({"dial_peer_config_present"}),
        explanation="SIP 404 without dial-peer evidence suggests no matching outbound dial-peer.",
        next_best_action="Review outbound dial-peer coverage for the failing number class.",
    ),
    HypothesisRule(
        rule_id="HYP-503-PROVIDER",
        title="Provider or SIP trunk service issue",
        confidence=75.0,
        required_signals=frozenset({"sip_503_detected", "sip_trace_present"}),
        supporting_signals=frozenset({"sip_503_detected", "sip_trace_present"}),
        explanation="SIP 503 with trace present points to provider or trunk service rejection.",
        next_best_action="Verify provider status and SIP trunk health.",
    ),
    HypothesisRule(
        rule_id="HYP-488-CODEC",
        title="Codec / SDP negotiation issue",
        confidence=82.0,
        required_signals=frozenset({"sip_488_detected"}),
        supporting_signals=frozenset({"sip_488_detected"}),
        explanation="SIP 488 indicates media negotiation failure between endpoints.",
        next_best_action="Compare codec and SDP offer/answer on CUBE and provider trunk.",
    ),
    HypothesisRule(
        rule_id="HYP-408-NETWORK",
        title="Network timeout / firewall / provider no response",
        confidence=76.0,
        required_signals=frozenset({"sip_408_detected"}),
        supporting_signals=frozenset({"sip_408_detected"}),
        explanation="SIP 408 suggests timeout along the signaling path or from the provider.",
        next_best_action="Check firewall, routing, DNS, and provider reachability for the trunk.",
    ),
    HypothesisRule(
        rule_id="HYP-403-PROVIDER-REJECT",
        title="Provider rejection / caller ID / authorization issue",
        confidence=74.0,
        required_signals=frozenset({"sip_403_detected"}),
        supporting_signals=frozenset({"sip_403_detected"}),
        explanation="SIP 403 indicates provider-side rejection or authorization policy enforcement.",
        next_best_action="Validate caller ID presentation and provider authorization policy.",
    ),
    HypothesisRule(
        rule_id="HYP-DIAL-PEER-DOWN",
        title="Outbound dial peer administratively down/out of service",
        confidence=86.0,
        required_signals=frozenset({"dial_peer_down"}),
        supporting_signals=frozenset({"dial_peer_down", "dial_peer_out_of_service"}),
        explanation=(
            "Outbound dial-peer summary shows administratively down or out-of-service peers."
        ),
        next_best_action=(
            "Remove shutdown on outbound dial-peers and verify peer operational state."
        ),
    ),
    HypothesisRule(
        rule_id="HYP-SIP-UA-DISABLED",
        title="CUBE SIP user agent disabled",
        confidence=90.0,
        required_signals=frozenset({"sip_ua_disabled"}),
        supporting_signals=frozenset({"sip_ua_disabled"}),
        explanation="SIP user agent is disabled on CUBE, blocking outbound SIP processing.",
        next_best_action="Enable SIP-UA and confirm provider trunk registration.",
    ),
    HypothesisRule(
        rule_id="HYP-REG-ISSUE",
        title="SIP registration/trunk availability issue",
        confidence=86.0,
        required_signals=frozenset({"sip_registration_issue"}),
        supporting_signals=frozenset({"sip_registration_issue"}),
        explanation="SIP registration or trunk availability problem detected on CUBE.",
        next_best_action="Inspect show sip-ua status and restore provider registration.",
    ),
)


class HypothesisEngine:
    """v1 deterministic hypothesis generator from analysis findings."""

    def generate(self, case: Case) -> list[Hypothesis]:
        """Create ranked hypotheses from case findings."""
        if not case.analysis_findings:
            return [_insufficient_evidence_hypothesis(case)]

        if case.playbook_id != VP_CUBE_0001_PLAYBOOK_ID:
            return [_insufficient_evidence_hypothesis(case)]

        signals = {finding.signal for finding in case.analysis_findings}
        finding_ids_by_signal = _finding_ids_by_signal(case.analysis_findings)
        hypotheses: list[Hypothesis] = []

        for rule in VP_CUBE_0001_RULES:
            if not _rule_matches(rule, signals):
                continue
            hypotheses.append(_build_hypothesis(case.case_id, rule, finding_ids_by_signal))

        if not hypotheses:
            return [_insufficient_evidence_hypothesis(case)]

        hypotheses.sort(key=lambda item: (-item.confidence, item.title))
        for rank, hypothesis in enumerate(hypotheses, start=1):
            hypothesis.rank = rank
            hypothesis.status = _status_for_confidence(hypothesis.confidence)

        return hypotheses


def build_hypothesis_summary(case: Case, hypotheses: list[Hypothesis]) -> HypothesisSummary:
    """Build a summary object from generated hypotheses."""
    signal_map = _finding_ids_to_signals(case.analysis_findings)
    items = tuple(
        HypothesisSummaryItem(
            hypothesis_id=hypothesis.hypothesis_id,
            title=hypothesis.title,
            confidence=hypothesis.confidence,
            supporting_signals=tuple(
                signal_map[finding_id]
                for finding_id in hypothesis.supporting_finding_ids
                if finding_id in signal_map
            ),
            explanation=hypothesis.explanation or "",
            next_best_action=hypothesis.next_best_action or "",
            rank=hypothesis.rank or 0,
        )
        for hypothesis in hypotheses
    )
    return HypothesisSummary(case_id=case.case_id, state=case.status, hypotheses=items)


def format_hypothesis_summary(summary: HypothesisSummary) -> str:
    """Format hypothesis results for terminal output."""
    lines = [
        "Hypothesis generation complete. Next phase: INVESTIGATION.",
        "Hypotheses:",
    ]
    if not summary.hypotheses:
        lines.append("- (none)")
        return "\n".join(lines)

    for item in summary.hypotheses:
        lines.append(f"- {item.title} — {int(item.confidence)}%")
        if item.supporting_signals:
            evidence = ", ".join(item.supporting_signals)
            lines.append(f"  Evidence: {evidence}")
        if item.next_best_action:
            lines.append(f"  Next action: {item.next_best_action}")

    return "\n".join(lines)


def _rule_matches(rule: HypothesisRule, signals: set[str]) -> bool:
    if not rule.required_signals.issubset(signals):
        return False
    return not rule.forbidden_signals.intersection(signals)


def _build_hypothesis(
    case_id: str,
    rule: HypothesisRule,
    finding_ids_by_signal: dict[str, str],
) -> Hypothesis:
    supporting_finding_ids = [
        finding_ids_by_signal[signal]
        for signal in rule.supporting_signals
        if signal in finding_ids_by_signal
    ]
    return Hypothesis.create(
        case_id=case_id,
        title=rule.title,
        confidence=rule.confidence,
        supporting_finding_ids=supporting_finding_ids,
        explanation=rule.explanation,
        next_best_action=rule.next_best_action,
        category=rule.rule_id,
    )


def _insufficient_evidence_hypothesis(case: Case) -> Hypothesis:
    return Hypothesis.create(
        case_id=case.case_id,
        title=INSUFFICIENT_EVIDENCE_TITLE,
        confidence=INSUFFICIENT_EVIDENCE_CONFIDENCE,
        supporting_finding_ids=[],
        explanation="Not enough structured findings are available to rank a root cause.",
        next_best_action="Collect additional CLI evidence and re-run analysis.",
        rank=1,
        status=HypothesisStatus.CANDIDATE,
        category="insufficient-evidence",
    )


def _finding_ids_by_signal(findings: list[AnalysisFinding]) -> dict[str, str]:
    return {finding.signal: finding.finding_id for finding in findings}


def _finding_ids_to_signals(findings: list[AnalysisFinding]) -> dict[str, str]:
    return {finding.finding_id: finding.signal for finding in findings}


def _status_for_confidence(confidence: float) -> HypothesisStatus:
    """Keep hypotheses as candidates in v1; do not auto-confirm root cause."""
    return HypothesisStatus.CANDIDATE
