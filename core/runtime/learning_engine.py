"""Deterministic learning capture and case closure."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from domain.enums import InvestigationState
from domain.models import Case, Hypothesis, LearningRecord, Recommendation
from runtime.recommendation_engine import ACTION_LIKELY_ROOT_CAUSE
from runtime.verification_engine import RESULT_PASSED

FINAL_OUTCOME_VERIFIED = "verified_and_closed"


@dataclass(frozen=True)
class LearningClosureSummary:
    """Result of closing a case with a learning record."""

    case_id: str
    state: InvestigationState
    learning_record_id: str
    root_cause: str
    confidence: float
    message: str


class LearningEngine:
    """v1 structured learning record generator without model training."""

    def create_learning_record(self, case: Case) -> LearningRecord:
        """Build a learning record from a verified case in LEARNING state."""
        top_hypothesis = _top_hypothesis(case)
        recommendation = _likely_root_cause_recommendation(case)
        if top_hypothesis is None:
            top_hypothesis = _fallback_hypothesis(case)
        if recommendation is None and case.recommendations:
            recommendation = case.recommendations[-1]

        root_cause = (
            recommendation.likely_root_cause
            if recommendation and recommendation.likely_root_cause
            else top_hypothesis.title
        )
        confidence = (
            recommendation.confidence
            if recommendation and recommendation.confidence is not None
            else top_hypothesis.confidence
        )

        finding_ids = [finding.finding_id for finding in case.analysis_findings]
        finding_signals = [finding.signal for finding in case.analysis_findings]

        return LearningRecord.create(
            case_id=case.case_id,
            playbook_id=case.playbook_id,
            symptom=case.symptom.summary,
            root_cause=root_cause,
            confidence=confidence,
            evidence_summary=_format_evidence_summary(finding_signals, finding_ids),
            resolution_summary=_format_resolution_summary(recommendation, top_hypothesis),
            verification_summary=_format_verification_summary(case),
            lessons_learned=_build_lessons_learned(case, top_hypothesis, recommendation),
            reusable_pattern=_build_reusable_pattern(case, top_hypothesis),
            final_outcome=FINAL_OUTCOME_VERIFIED,
            hypothesis_id=top_hypothesis.hypothesis_id,
            recommendation_id=recommendation.recommendation_id if recommendation else None,
            evidence_finding_ids=finding_ids,
        )


def build_learning_closure_summary(
    case: Case,
    learning_record: LearningRecord,
) -> LearningClosureSummary:
    """Build a closure summary after learning capture."""
    return LearningClosureSummary(
        case_id=case.case_id,
        state=case.status,
        learning_record_id=learning_record.learning_record_id,
        root_cause=learning_record.root_cause,
        confidence=learning_record.confidence,
        message="Case closed.\nLearning record created.",
    )


def format_learning_closure_summary(summary: LearningClosureSummary) -> str:
    """Format case closure output for terminal display."""
    lines = [
        summary.message,
        f"Learning Record: {summary.learning_record_id}",
        f"Root cause: {summary.root_cause}",
        f"Confidence: {int(summary.confidence)}%",
    ]
    return "\n".join(lines)


def _top_hypothesis(case: Case) -> Hypothesis | None:
    if not case.hypotheses:
        return None
    return min(case.hypotheses, key=lambda hypothesis: hypothesis.rank or 999)


def _fallback_hypothesis(case: Case) -> Hypothesis:
    return Hypothesis.create(
        case_id=case.case_id,
        title="Unknown root cause",
        confidence=0.0,
        supporting_finding_ids=[],
        rank=1,
    )


def _likely_root_cause_recommendation(case: Case) -> Recommendation | None:
    for recommendation in reversed(case.recommendations):
        if recommendation.action_type == ACTION_LIKELY_ROOT_CAUSE:
            return recommendation
    return None


def _format_evidence_summary(signals: list[str], finding_ids: list[str]) -> str:
    if signals:
        return ", ".join(signals)
    if finding_ids:
        return ", ".join(finding_ids)
    return "No structured findings captured"


def _format_resolution_summary(
    recommendation: Recommendation | None,
    hypothesis: Hypothesis,
) -> str:
    if recommendation and recommendation.recommended_actions:
        return "; ".join(recommendation.recommended_actions)
    if hypothesis.next_best_action:
        return hypothesis.next_best_action
    return "Resolution actions not recorded"


def _format_verification_summary(case: Case) -> str:
    if not case.verifications:
        return "No verification steps recorded"

    passed = [step for step in case.verifications if step.result_status == RESULT_PASSED]
    summaries = [
        f"{step.step_name}: {step.description} ({step.result_status})"
        for step in case.verifications
        if step.result_status
    ]
    return f"{len(passed)}/{len(case.verifications)} passed — " + "; ".join(summaries)


def _build_lessons_learned(
    case: Case,
    hypothesis: Hypothesis,
    recommendation: Recommendation | None,
) -> str:
    playbook = case.playbook_id or "unknown-playbook"
    action_hint = ""
    if recommendation and recommendation.recommended_actions:
        action_hint = f" Next focus: {recommendation.recommended_actions[0]}."
    elif hypothesis.next_best_action:
        action_hint = f" Next focus: {hypothesis.next_best_action}."
    return (
        f"Playbook {playbook} investigation verified '{hypothesis.title}'. "
        f"Always collect correlated CLI evidence and verification before closure.{action_hint}"
    )


def _build_reusable_pattern(case: Case, hypothesis: Hypothesis) -> str:
    playbook = case.playbook_id or "UNKNOWN"
    category = hypothesis.category or hypothesis.title.lower().replace(" ", "_")
    return f"{playbook}:{category}"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
