"""Vendor-neutral correlation engine for reinforcing and contradicting findings."""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.enums import HypothesisStatus, InvestigationState
from domain.models import Case, CorrelationResult, Hypothesis
from runtime.exceptions import InvalidInvestigationStateError

# Finding codes produced by parsers and analysis fallback.
FINDING_SIP_UA_DISABLED = "sip_ua_disabled"
FINDING_SIP_UA_ENABLED = "sip_ua_enabled"
FINDING_SIP_UA_DISABLED_BY_CONFIG = "sip_ua_disabled_by_config"
FINDING_SIP_503_DETECTED = "sip_503_detected"
FINDING_SIP_REGISTRATION_ISSUE = "sip_registration_issue"
FINDING_SIP_404_DETECTED = "sip_404_detected"
FINDING_DIAL_PEER_SUMMARY_MISSING_OR_EMPTY = "dial_peer_summary_missing_or_empty"
FINDING_SIP_488_DETECTED = "sip_488_detected"

# Hypothesis titles (must match hypothesis engine).
HYP_SIP_UA_DISABLED_TITLE = "CUBE SIP user agent disabled"
HYP_PROVIDER_TITLE = "Provider or SIP trunk service issue"
HYP_MISSING_DIAL_PEER_TITLE = "Missing or unmatched outbound dial-peer"
HYP_CODEC_TITLE = "Codec / SDP negotiation issue"
HYP_DIAL_PEER_DOWN_TITLE = "Outbound dial peer administratively down/out of service"
FINDING_DIAL_PEER_DOWN = "dial_peer_down"
FINDING_DIAL_PEER_CONFIG_PRESENT = "dial_peer_config_present"
FINDING_SIP_TRACE_PRESENT = "sip_trace_present"

CORRELATION_TYPE_REINFORCEMENT = "reinforcement"
CORRELATION_TYPE_CONTRADICTION = "contradiction"
CORRELATION_TYPE_SIGNAL = "signal"

MAX_CONFIDENCE = 98.0
MIN_CONFIDENCE = 0.0


@dataclass(frozen=True)
class CorrelationRule:
    """Declarative correlation rule evaluated against finding codes."""

    rule_id: str
    correlation_type: str
    required_codes: frozenset[str]
    hypothesis_title: str | None
    confidence_delta: float
    explanation: str
    apply_max_cap: bool = False


VP_CUBE_0001_CORRELATION_RULES: tuple[CorrelationRule, ...] = (
    CorrelationRule(
        rule_id="sip_ua_disabled_confirmed",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset(
            {FINDING_SIP_UA_DISABLED, FINDING_SIP_UA_DISABLED_BY_CONFIG}
        ),
        hypothesis_title=HYP_SIP_UA_DISABLED_TITLE,
        confidence_delta=8.0,
        explanation=(
            "Operational status and running configuration both indicate SIP-UA is disabled."
        ),
        apply_max_cap=True,
    ),
    CorrelationRule(
        rule_id="sip_ua_status_config_mismatch",
        correlation_type=CORRELATION_TYPE_CONTRADICTION,
        required_codes=frozenset(
            {FINDING_SIP_UA_ENABLED, FINDING_SIP_UA_DISABLED_BY_CONFIG}
        ),
        hypothesis_title=HYP_SIP_UA_DISABLED_TITLE,
        confidence_delta=-10.0,
        explanation=(
            "Operational status says enabled, but config suggests disabled. "
            "More evidence required."
        ),
    ),
    CorrelationRule(
        rule_id="provider_or_trunk_unavailable",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset(
            {FINDING_SIP_503_DETECTED, FINDING_SIP_REGISTRATION_ISSUE}
        ),
        hypothesis_title=HYP_PROVIDER_TITLE,
        confidence_delta=10.0,
        explanation=(
            "SIP 503 responses and registration issues reinforce a provider or trunk outage."
        ),
    ),
    CorrelationRule(
        rule_id="routing_evidence_missing_dial_peer",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset(
            {
                FINDING_SIP_404_DETECTED,
                FINDING_DIAL_PEER_SUMMARY_MISSING_OR_EMPTY,
            }
        ),
        hypothesis_title=HYP_MISSING_DIAL_PEER_TITLE,
        confidence_delta=10.0,
        explanation=(
            "SIP 404 responses with missing or empty dial-peer summary reinforce routing gaps."
        ),
    ),
    CorrelationRule(
        rule_id="codec_negotiation_failure_signal",
        correlation_type=CORRELATION_TYPE_SIGNAL,
        required_codes=frozenset({FINDING_SIP_488_DETECTED}),
        hypothesis_title=HYP_CODEC_TITLE,
        confidence_delta=0.0,
        explanation=(
            "SIP 488 indicates codec negotiation failure; SDP details are required to confirm."
        ),
    ),
    CorrelationRule(
        rule_id="provider_503_healthy_cube",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset(
            {
                FINDING_SIP_503_DETECTED,
                FINDING_SIP_TRACE_PRESENT,
                FINDING_SIP_UA_ENABLED,
                FINDING_DIAL_PEER_CONFIG_PRESENT,
            }
        ),
        hypothesis_title=HYP_PROVIDER_TITLE,
        confidence_delta=12.0,
        explanation=(
            "SIP 503 with healthy CUBE dial-plan and SIP-UA points to provider or trunk issue."
        ),
    ),
    CorrelationRule(
        rule_id="dial_peer_down_routing_failure",
        correlation_type=CORRELATION_TYPE_REINFORCEMENT,
        required_codes=frozenset(
            {FINDING_SIP_404_DETECTED, FINDING_DIAL_PEER_DOWN}
        ),
        hypothesis_title=HYP_DIAL_PEER_DOWN_TITLE,
        confidence_delta=5.0,
        explanation=(
            "SIP 404 with administratively down dial-peers reinforces local peer availability issue."
        ),
    ),
)


@dataclass
class CorrelationSummary:
    """Result of correlating findings for a case."""

    case_id: str
    correlations: list[CorrelationResult] = field(default_factory=list)
    hypotheses_updated: int = 0

    @property
    def correlation_count(self) -> int:
        return len(self.correlations)


class CorrelationEngine:
    """Correlate analysis findings and adjust hypothesis confidence."""

    def __init__(self, rules: tuple[CorrelationRule, ...] | None = None) -> None:
        self._rules = rules if rules is not None else VP_CUBE_0001_CORRELATION_RULES

    def correlate(self, case: Case) -> CorrelationSummary:
        if case.status not in (
            InvestigationState.HYPOTHESIS,
            InvestigationState.INVESTIGATION,
        ):
            raise InvalidInvestigationStateError(
                case.case_id,
                "HYPOTHESIS or INVESTIGATION",
                case.status.value,
            )
        if not case.hypotheses:
            raise InvalidInvestigationStateError(
                case.case_id,
                "hypotheses present",
                "no hypotheses",
            )

        rules = _rules_for_playbook(case.playbook_id, self._rules)
        finding_codes = _collect_finding_codes(case)
        correlations: list[CorrelationResult] = []
        hypotheses_updated = 0

        for rule in rules:
            if not rule.required_codes.issubset(finding_codes):
                continue

            hypothesis = (
                _find_hypothesis_by_title(case.hypotheses, rule.hypothesis_title)
                if rule.hypothesis_title
                else None
            )
            applied_delta = 0.0
            if hypothesis is not None and rule.confidence_delta != 0.0:
                applied_delta = _apply_confidence_delta(
                    hypothesis,
                    rule.confidence_delta,
                    apply_max_cap=rule.apply_max_cap,
                )
                if applied_delta != 0.0:
                    hypotheses_updated += 1

            correlations.append(
                CorrelationResult.create(
                    case.case_id,
                    rule.correlation_type,
                    rule.rule_id,
                    rule.explanation,
                    finding_codes=sorted(rule.required_codes),
                    confidence_delta=applied_delta if hypothesis else rule.confidence_delta,
                    hypothesis_id=hypothesis.hypothesis_id if hypothesis else None,
                )
            )

        if hypotheses_updated:
            _rerank_hypotheses(case.hypotheses)

        case.correlation_results = correlations
        return CorrelationSummary(
            case_id=case.case_id,
            correlations=correlations,
            hypotheses_updated=hypotheses_updated,
        )


def _collect_finding_codes(case: Case) -> set[str]:
    return {finding.signal for finding in case.analysis_findings}


def _rules_for_playbook(
    playbook_id: str | None,
    default_rules: tuple[CorrelationRule, ...],
) -> tuple[CorrelationRule, ...]:
    from runtime.cucm_investigation import VP_CUCM_0001_CORRELATION_RULES, VP_CUCM_0001_PLAYBOOK_ID
    from runtime.audiocodes_investigation import (
        VP_AUDIOCODES_0001_CORRELATION_RULES,
        VP_AUDIOCODES_0001_PLAYBOOK_ID,
    )
    from runtime.teams_investigation import VP_TEAMS_0001_CORRELATION_RULES, VP_TEAMS_0001_PLAYBOOK_ID

    if playbook_id == VP_CUCM_0001_PLAYBOOK_ID:
        return VP_CUCM_0001_CORRELATION_RULES
    if playbook_id == VP_TEAMS_0001_PLAYBOOK_ID:
        return VP_TEAMS_0001_CORRELATION_RULES
    if playbook_id == VP_AUDIOCODES_0001_PLAYBOOK_ID:
        return VP_AUDIOCODES_0001_CORRELATION_RULES
    return default_rules


def _find_hypothesis_by_title(
    hypotheses: list[Hypothesis], title: str | None
) -> Hypothesis | None:
    if title is None:
        return None
    for hypothesis in hypotheses:
        if hypothesis.title == title:
            return hypothesis
    return None


def _apply_confidence_delta(
    hypothesis: Hypothesis,
    delta: float,
    *,
    apply_max_cap: bool = False,
) -> float:
    if hypothesis.status == HypothesisStatus.ELIMINATED:
        return 0.0

    previous = hypothesis.confidence
    updated = previous + delta
    if apply_max_cap:
        updated = min(updated, MAX_CONFIDENCE)
    updated = max(MIN_CONFIDENCE, min(MAX_CONFIDENCE, updated))
    applied = updated - previous
    if applied == 0.0:
        return 0.0

    hypothesis.confidence = updated
    return applied


def _rerank_hypotheses(hypotheses: list[Hypothesis]) -> None:
    ranked = sorted(
        hypotheses,
        key=lambda item: (-item.confidence, item.title),
    )
    for index, hypothesis in enumerate(ranked, start=1):
        hypothesis.rank = index


def format_correlation_summary(summary: CorrelationSummary) -> str:
    """Format correlation results for terminal output."""
    lines = [
        "Correlation complete.",
        "Correlations:",
    ]
    if not summary.correlations:
        lines.append("- (none)")
        return "\n".join(lines)

    for correlation in summary.correlations:
        if correlation.confidence_delta:
            delta = int(correlation.confidence_delta)
            sign = "+" if delta > 0 else ""
            lines.append(f"- {correlation.rule_id} ({sign}{delta} confidence)")
        else:
            lines.append(f"- {correlation.rule_id}")

    return "\n".join(lines)


def build_correlation_summary(
    case: Case, correlations: list[CorrelationResult]
) -> CorrelationSummary:
    """Build a summary object from correlation results."""
    return CorrelationSummary(
        case_id=case.case_id,
        correlations=list(correlations),
        hypotheses_updated=sum(
            1
            for item in correlations
            if item.confidence_delta != 0.0 and item.hypothesis_id
        ),
    )
