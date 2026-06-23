"""Deterministic recommendation generation from ranked hypotheses."""

from __future__ import annotations

from dataclasses import dataclass

from domain.enums import InvestigationState
from domain.models import AnalysisFinding, Case, Hypothesis, Recommendation
from shared.constants import DEFAULT_CONFIDENCE_THRESHOLD

ACTION_LIKELY_ROOT_CAUSE = "likely_root_cause"
ACTION_NEXT_BEST = "next_best_action"


@dataclass(frozen=True)
class HypothesisActionPlan:
    """Evidence-first actions mapped to a hypothesis category."""

    recommended_actions: tuple[str, ...]
    verification_steps: tuple[str, ...]
    rollback_guidance: tuple[str, ...] = ()
    command: str | None = None
    requires_engineer_approval: bool = False


@dataclass(frozen=True)
class RecommendationSummary:
    """Serializable recommendation result for CLI and runtime consumers."""

    case_id: str
    state: InvestigationState
    recommendation_type: str
    likely_root_cause: str | None
    confidence: float
    evidence: tuple[str, ...]
    recommended_actions: tuple[str, ...]
    verification_steps: tuple[str, ...]
    rollback_guidance: tuple[str, ...]
    description: str


VP_CUBE_0001_ACTION_PLANS: dict[str, HypothesisActionPlan] = {
    "HYP-SIP-UA-DISABLED": HypothesisActionPlan(
        recommended_actions=(
            "Review voice service voip configuration on CUBE",
            "Enable SIP user agent if currently disabled",
        ),
        verification_steps=(
            "show sip-ua status reports SIP-UA enabled",
            "Provider trunk shows registered/UP",
            "Place controlled outbound test call",
        ),
        rollback_guidance=(
            "Restore previous voice service voip sip configuration from change record",
            "Confirm SIP-UA state matches pre-change baseline",
        ),
        command="show run | sec voice service voip",
        requires_engineer_approval=True,
    ),
    "HYP-REG-ISSUE": HypothesisActionPlan(
        recommended_actions=(
            "Verify show sip-ua status for provider registration state",
            "Confirm provider-side registration and trunk availability",
        ),
        verification_steps=(
            "show sip-ua status shows provider trunk registered",
            "Outbound test call succeeds to known-good destination",
        ),
        command="show sip-ua status",
    ),
    "HYP-503-PROVIDER": HypothesisActionPlan(
        recommended_actions=(
            "Check ITSP/service provider status and incident notices",
            "Send SIP OPTIONS toward provider and review response",
            "Review provider routing and trunk capacity policy",
        ),
        verification_steps=(
            "Provider trunk returns healthy SIP response to OPTIONS",
            "Outbound test call completes without 503",
        ),
        command="show sip-ua status",
    ),
    "HYP-488-CODEC": HypothesisActionPlan(
        recommended_actions=(
            "Review voice-class codec configuration on CUBE",
            "Compare provider-required codec list with CUBE offer",
        ),
        verification_steps=(
            "SDP offer/answer shows overlapping codec set",
            "Outbound test call negotiates media successfully",
        ),
        command="show run | sec voice class codec",
    ),
    "HYP-408-NETWORK": HypothesisActionPlan(
        recommended_actions=(
            "Collect packet capture on CUBE/provider path during failing call",
            "Review firewall and ACL logs for dropped SIP packets",
            "Validate DNS and routing to provider session target",
        ),
        verification_steps=(
            "Signaling path shows bidirectional SIP without timeout",
            "Outbound test call completes without 408",
        ),
    ),
    "HYP-403-PROVIDER-REJECT": HypothesisActionPlan(
        recommended_actions=(
            "Verify caller ID format matches provider provisioning",
            "Confirm authorization and CLIP/CLIR policy with provider",
        ),
        verification_steps=(
            "Provider accepts presented caller ID on test call",
            "Outbound call no longer returns 403",
        ),
        command="show run | sec voice service voip",
    ),
    "HYP-404-ROUTING": HypothesisActionPlan(
        recommended_actions=(
            "Collect show run | sec dial-peer for outbound peers",
            "Verify destination-pattern covers the failing destination",
            "Validate translation rules affecting called number",
        ),
        verification_steps=(
            "Matched dial-peer shown for failing destination in test call",
            "Outbound test call routes without local 404",
        ),
        command="show run | sec dial-peer",
    ),
    "HYP-DIAL-PEER-DOWN": HypothesisActionPlan(
        recommended_actions=(
            "Review show dial-peer voice summary for shutdown or out-of-service peers",
            "Remove shutdown from affected outbound dial-peers",
            "Verify dial-peer session target and provider reachability",
        ),
        verification_steps=(
            "Dial-peer summary shows outbound peers in UP state",
            "Outbound test call routes without local 404/503",
        ),
        command="show dial-peer voice summary",
        requires_engineer_approval=True,
    ),
    "HYP-404-MISSING": HypothesisActionPlan(
        recommended_actions=(
            "Collect show run | sec dial-peer for outbound peers",
            "Verify destination-pattern coverage for failing number class",
            "Add or correct outbound dial-peer if no match exists",
        ),
        verification_steps=(
            "Dial-peer summary shows matching outbound peer",
            "Outbound test call succeeds for affected destination class",
        ),
        command="show run | sec dial-peer",
        requires_engineer_approval=True,
    ),
    "insufficient-evidence": HypothesisActionPlan(
        recommended_actions=(
            "Collect additional CLI evidence for the active playbook",
            "Re-run analysis after pasting missing command outputs",
        ),
        verification_steps=(
            "Required evidence artifacts are present on the case",
            "Analysis findings support a ranked hypothesis",
        ),
    ),
}

DEFAULT_ACTION_PLAN = HypothesisActionPlan(
    recommended_actions=(
        "Collect additional evidence aligned with the top hypothesis",
        "Review collected findings before applying configuration changes",
    ),
    verification_steps=(
        "Repeat failing test call after evidence collection",
    ),
)


class RecommendationEngine:
    """v1 evidence-first recommendation generator."""

    def generate(self, case: Case) -> Recommendation:
        """Build a recommendation from the top ranked hypothesis."""
        top_hypothesis = _top_hypothesis(case)
        if top_hypothesis is None:
            return _insufficient_recommendation(case)

        plan = _plan_for_hypothesis(top_hypothesis, case)
        evidence = _evidence_for_hypothesis(case, top_hypothesis)
        confidence = top_hypothesis.confidence

        if confidence >= DEFAULT_CONFIDENCE_THRESHOLD:
            return Recommendation.create(
                case_id=case.case_id,
                action_type=ACTION_LIKELY_ROOT_CAUSE,
                description=f"Likely root cause identified: {top_hypothesis.title}",
                rationale=top_hypothesis.explanation or top_hypothesis.title,
                confidence=confidence,
                likely_root_cause=top_hypothesis.title,
                evidence_summary=evidence,
                recommended_actions=list(plan.recommended_actions),
                verification_steps=list(plan.verification_steps),
                rollback_steps=list(plan.rollback_guidance),
                hypothesis_id=top_hypothesis.hypothesis_id,
                command=plan.command,
                requires_engineer_approval=plan.requires_engineer_approval,
                information_gain=confidence / 100.0,
            )

        return Recommendation.create(
            case_id=case.case_id,
            action_type=ACTION_NEXT_BEST,
            description=(
                f"More evidence is needed before confirming root cause. "
                f"Top hypothesis: {top_hypothesis.title} ({int(confidence)}%)"
            ),
            rationale=top_hypothesis.explanation or top_hypothesis.title,
            confidence=confidence,
            evidence_summary=evidence,
            recommended_actions=list(plan.recommended_actions),
            verification_steps=list(plan.verification_steps),
            rollback_steps=list(plan.rollback_guidance),
            hypothesis_id=top_hypothesis.hypothesis_id,
            command=plan.command,
            requires_engineer_approval=plan.requires_engineer_approval,
            information_gain=confidence / 100.0,
        )


def build_recommendation_summary(
    case: Case,
    recommendation: Recommendation,
) -> RecommendationSummary:
    """Build a summary object from a stored recommendation."""
    return RecommendationSummary(
        case_id=case.case_id,
        state=case.status,
        recommendation_type=recommendation.action_type,
        likely_root_cause=recommendation.likely_root_cause,
        confidence=recommendation.confidence or 0.0,
        evidence=tuple(recommendation.evidence_summary),
        recommended_actions=tuple(recommendation.recommended_actions),
        verification_steps=tuple(recommendation.verification_steps),
        rollback_guidance=tuple(recommendation.rollback_steps),
        description=recommendation.description,
    )


def format_recommendation_summary(summary: RecommendationSummary) -> str:
    """Format recommendation output for terminal display."""
    lines: list[str] = []

    if summary.recommendation_type == ACTION_LIKELY_ROOT_CAUSE:
        lines.append("Likely Root Cause:")
        lines.append(f"  {summary.likely_root_cause}")
        lines.append(f"Confidence: {int(summary.confidence)}%")
    else:
        lines.append("Recommended Next Action:")
        lines.append(f"  {summary.description}")

    if summary.evidence:
        lines.append("Evidence:")
        for item in summary.evidence:
            lines.append(f"  - {item}")

    if summary.recommended_actions:
        lines.append("Recommended actions:")
        for action in summary.recommended_actions:
            lines.append(f"  - {action}")

    if summary.verification_steps:
        lines.append("Verification steps:")
        for step in summary.verification_steps:
            lines.append(f"  - {step}")

    if summary.rollback_guidance:
        lines.append("Rollback guidance:")
        for step in summary.rollback_guidance:
            lines.append(f"  - {step}")

    return "\n".join(lines)


def _top_hypothesis(case: Case) -> Hypothesis | None:
    if not case.hypotheses:
        return None
    return min(case.hypotheses, key=lambda hypothesis: hypothesis.rank or 999)


def _plan_for_hypothesis(hypothesis: Hypothesis, case: Case) -> HypothesisActionPlan:
    from runtime.cucm_investigation import VP_CUCM_0001_ACTION_PLANS, VP_CUCM_0001_PLAYBOOK_ID
    from runtime.audiocodes_investigation import (
        VP_AUDIOCODES_0001_ACTION_PLANS,
        VP_AUDIOCODES_0001_PLAYBOOK_ID,
    )
    from runtime.genesys_investigation import (
        VP_GENESYS_0001_ACTION_PLANS,
        VP_GENESYS_0001_PLAYBOOK_ID,
    )
    from runtime.teams_investigation import VP_TEAMS_0001_ACTION_PLANS, VP_TEAMS_0001_PLAYBOOK_ID

    category = hypothesis.category or ""
    if case.playbook_id == VP_CUCM_0001_PLAYBOOK_ID:
        return VP_CUCM_0001_ACTION_PLANS.get(category, DEFAULT_ACTION_PLAN)
    if case.playbook_id == VP_TEAMS_0001_PLAYBOOK_ID:
        return VP_TEAMS_0001_ACTION_PLANS.get(category, DEFAULT_ACTION_PLAN)
    if case.playbook_id == VP_AUDIOCODES_0001_PLAYBOOK_ID:
        return VP_AUDIOCODES_0001_ACTION_PLANS.get(category, DEFAULT_ACTION_PLAN)
    if case.playbook_id == VP_GENESYS_0001_PLAYBOOK_ID:
        return VP_GENESYS_0001_ACTION_PLANS.get(category, DEFAULT_ACTION_PLAN)
    return VP_CUBE_0001_ACTION_PLANS.get(category, DEFAULT_ACTION_PLAN)


def _evidence_for_hypothesis(case: Case, hypothesis: Hypothesis) -> list[str]:
    signal_map = {finding.finding_id: finding.signal for finding in case.analysis_findings}
    return [
        signal_map[finding_id]
        for finding_id in hypothesis.supporting_finding_ids
        if finding_id in signal_map
    ]


def _insufficient_recommendation(case: Case) -> Recommendation:
    plan = VP_CUBE_0001_ACTION_PLANS["insufficient-evidence"]
    return Recommendation.create(
        case_id=case.case_id,
        action_type=ACTION_NEXT_BEST,
        description="More evidence is needed before ranking a root cause.",
        rationale="No ranked hypothesis is available on the case.",
        confidence=0.0,
        recommended_actions=list(plan.recommended_actions),
        verification_steps=list(plan.verification_steps),
        information_gain=0.0,
    )
