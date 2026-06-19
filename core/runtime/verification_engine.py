"""Deterministic verification checklist and result handling."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from domain.enums import InvestigationState
from domain.models import Case, Recommendation, Verification
from runtime.recommendation_engine import ACTION_LIKELY_ROOT_CAUSE

RESULT_PASSED = "passed"
RESULT_FAILED = "failed"
RESULT_NOT_TESTED = "not_tested"

OUTCOME_COMPLETE = "complete"
OUTCOME_FAILED = "failed"
OUTCOME_SKIPPED = "skipped"


@dataclass(frozen=True)
class VerificationChecklistItem:
    """A single verification step presented to the engineer."""

    verification_id: str
    step_number: int
    description: str
    required: bool


@dataclass(frozen=True)
class VerificationChecklist:
    """Checklist generated from a likely root cause recommendation."""

    case_id: str
    likely_root_cause: str
    items: tuple[VerificationChecklistItem, ...]


@dataclass(frozen=True)
class VerificationResultSubmission:
    """Engineer-submitted result for one verification step."""

    verification_id: str
    status: str
    notes: str = ""


@dataclass(frozen=True)
class VerificationSummary:
    """Outcome of submitting verification results."""

    case_id: str
    state: InvestigationState
    outcome: str
    message: str


class VerificationEngine:
    """v1 verification checklist generator and result evaluator."""

    def generate_checklist(self, case: Case) -> VerificationChecklist | None:
        """Create a verification checklist when resolution has a likely root cause."""
        if case.status != InvestigationState.RESOLUTION:
            return None

        recommendation = _likely_root_cause_recommendation(case)
        if recommendation is None:
            return None

        if not recommendation.verification_steps:
            return None

        if not case.verifications:
            for index, step in enumerate(recommendation.verification_steps, start=1):
                case.verifications.append(
                    Verification.create(
                        case_id=case.case_id,
                        step_name=f"VER-{index:03d}",
                        description=step,
                    )
                )

        items = tuple(
            VerificationChecklistItem(
                verification_id=verification.verification_id,
                step_number=index,
                description=verification.description,
                required=verification.required,
            )
            for index, verification in enumerate(case.verifications, start=1)
        )
        return VerificationChecklist(
            case_id=case.case_id,
            likely_root_cause=recommendation.likely_root_cause or recommendation.description,
            items=items,
        )

    def should_start_verification(self, case: Case) -> bool:
        """Return whether verification should begin for the case."""
        if case.status != InvestigationState.RESOLUTION:
            return False
        recommendation = _latest_recommendation(case)
        if recommendation is None:
            return False
        return recommendation.action_type == ACTION_LIKELY_ROOT_CAUSE

    def apply_results(
        self,
        case: Case,
        submissions: list[VerificationResultSubmission],
        *,
        actor: str = "engineer",
    ) -> VerificationSummary:
        """Apply engineer verification results and determine next lifecycle state."""
        submission_map = {item.verification_id: item for item in submissions}
        now = _utc_now()

        for verification in case.verifications:
            submission = submission_map.get(verification.verification_id)
            if submission is None:
                continue
            status = _normalize_status(submission.status)
            verification.result_status = status
            verification.notes = submission.notes or None
            verification.actual_result = submission.notes or status
            verification.executed_at = now
            verification.executed_by = actor
            verification.passed = status == RESULT_PASSED

        required_steps = [step for step in case.verifications if step.required]
        any_failed = any(step.result_status == RESULT_FAILED for step in required_steps)
        all_passed = bool(required_steps) and all(
            step.result_status == RESULT_PASSED for step in required_steps
        )

        if any_failed:
            case.metadata["verification_note"] = (
                "Root cause not verified. Returning to investigation for additional evidence."
            )
            return VerificationSummary(
                case_id=case.case_id,
                state=case.status,
                outcome=OUTCOME_FAILED,
                message="Verification failed. Returning to INVESTIGATION.",
            )

        if all_passed:
            return VerificationSummary(
                case_id=case.case_id,
                state=case.status,
                outcome=OUTCOME_COMPLETE,
                message="Verification complete. Next phase: LEARNING.",
            )

        return VerificationSummary(
            case_id=case.case_id,
            state=case.status,
            outcome=OUTCOME_SKIPPED,
            message="Verification incomplete. Required steps are not all marked passed.",
        )


def format_verification_checklist(checklist: VerificationChecklist) -> str:
    """Format a verification checklist for terminal output."""
    lines = [
        "Verification Checklist:",
        f"Likely root cause: {checklist.likely_root_cause}",
        "",
    ]
    for item in checklist.items:
        required = "required" if item.required else "optional"
        lines.append(f"[{item.step_number}] {item.description} ({required})")
    lines.append("")
    lines.append("Mark each step: passed / failed / not_tested")
    return "\n".join(lines)


def format_verification_summary(summary: VerificationSummary) -> str:
    """Format verification outcome for terminal output."""
    return summary.message


def _likely_root_cause_recommendation(case: Case) -> Recommendation | None:
    recommendation = _latest_recommendation(case)
    if recommendation is None:
        return None
    if recommendation.action_type != ACTION_LIKELY_ROOT_CAUSE:
        return None
    return recommendation


def _latest_recommendation(case: Case) -> Recommendation | None:
    if not case.recommendations:
        return None
    return case.recommendations[-1]


def _normalize_status(status: str) -> str:
    normalized = status.strip().lower().replace(" ", "_")
    if normalized in {RESULT_PASSED, RESULT_FAILED, RESULT_NOT_TESTED}:
        return normalized
    if normalized in {"pass", "yes", "y"}:
        return RESULT_PASSED
    if normalized in {"fail", "no", "n"}:
        return RESULT_FAILED
    return RESULT_NOT_TESTED


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
