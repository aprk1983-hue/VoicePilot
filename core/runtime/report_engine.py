"""Deterministic incident report generation from closed cases."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domain.enums import InvestigationState
from domain.models import Case, CorrelationResult, Hypothesis, Recommendation
from runtime.analysis_engine import (
    format_finding_source_label,
    summarize_structured_data,
)
from runtime.recommendation_engine import ACTION_LIKELY_ROOT_CAUSE
from runtime.verification_engine import RESULT_PASSED

VERIFICATION_OUTCOME_PASSED = "all_steps_passed"
VERIFICATION_OUTCOME_PARTIAL = "partial"
VERIFICATION_OUTCOME_NONE = "not_recorded"


@dataclass(frozen=True)
class ReportFinding:
    """Evidence finding included in an incident report."""

    signal: str
    command: str
    detail: str | None
    source: str | None = None
    structured_summary: str | None = None


@dataclass(frozen=True)
class ReportCorrelation:
    """Correlation result included in an incident report."""

    rule_id: str
    correlation_type: str
    confidence_delta: float
    explanation: str
    evidence_names: tuple[str, ...]


@dataclass(frozen=True)
class ReportVerification:
    """Verification step included in an incident report."""

    step_name: str
    description: str
    result_status: str | None
    notes: str | None


@dataclass(frozen=True)
class ReportTimelineEntry:
    """Chronological event included in an incident report."""

    sequence: int
    timestamp: str
    event_type: str
    summary: str


@dataclass(frozen=True)
class IncidentReport:
    """Structured incident report for a closed investigation."""

    case_id: str
    playbook_id: str | None
    final_state: InvestigationState
    symptom: str
    top_hypothesis_title: str | None
    top_hypothesis_id: str | None
    confidence: float | None
    findings: tuple[ReportFinding, ...]
    correlations: tuple[ReportCorrelation, ...]
    recommendation_summary: str | None
    recommendation_actions: tuple[str, ...]
    verification_outcome: str | None
    verifications: tuple[ReportVerification, ...]
    learning_record_id: str | None
    learning_root_cause: str | None
    learning_reusable_pattern: str | None
    learning_lessons: str | None
    timeline: tuple[ReportTimelineEntry, ...]
    closed_at: str | None


class ReportEngine:
    """v1 deterministic incident report generator."""

    def generate(self, case: Case) -> IncidentReport:
        """Build an incident report from a closed case."""
        return build_incident_report(case)


def build_incident_report(case: Case) -> IncidentReport:
    """Build a structured incident report from a closed case."""
    top_hypothesis = _top_hypothesis(case)
    recommendation = _likely_root_cause_recommendation(case)
    learning = case.learning_record

    confidence = _resolve_confidence(top_hypothesis, recommendation, learning)
    top_title = (
        learning.root_cause
        if learning
        else (
            recommendation.likely_root_cause
            if recommendation and recommendation.likely_root_cause
            else top_hypothesis.title if top_hypothesis else None
        )
    )
    top_id = (
        learning.hypothesis_id
        if learning and learning.hypothesis_id
        else top_hypothesis.hypothesis_id if top_hypothesis else None
    )

    return IncidentReport(
        case_id=case.case_id,
        playbook_id=case.playbook_id,
        final_state=case.status,
        symptom=case.symptom.summary,
        top_hypothesis_title=top_title,
        top_hypothesis_id=top_id,
        confidence=confidence,
        findings=tuple(
            ReportFinding(
                signal=finding.signal,
                command=finding.command,
                detail=finding.detail,
                source=format_finding_source_label(finding.metadata),
                structured_summary=summarize_structured_data(finding.metadata),
            )
            for finding in case.analysis_findings
        ),
        correlations=tuple(_build_report_correlations(case.correlation_results)),
        recommendation_summary=_format_recommendation_summary(recommendation),
        recommendation_actions=tuple(recommendation.recommended_actions) if recommendation else (),
        verification_outcome=_verification_outcome(case),
        verifications=tuple(
            ReportVerification(
                step_name=step.step_name,
                description=step.description,
                result_status=step.result_status,
                notes=step.notes,
            )
            for step in case.verifications
        ),
        learning_record_id=learning.learning_record_id if learning else None,
        learning_root_cause=learning.root_cause if learning else None,
        learning_reusable_pattern=learning.reusable_pattern if learning else None,
        learning_lessons=learning.lessons_learned if learning else None,
        timeline=_build_timeline(case),
        closed_at=_format_timestamp(case.closed_at),
    )


def format_incident_report(report: IncidentReport) -> str:
    """Format an incident report as readable Markdown."""
    lines = [
        "# VoicePilot Incident Report",
        "",
        "## Case Overview",
        "",
        f"- **Case ID:** {report.case_id}",
        f"- **Playbook ID:** {report.playbook_id or 'unknown'}",
        f"- **Final State:** {report.final_state.value}",
        f"- **Closed At:** {report.closed_at or 'not recorded'}",
        "",
        "## Symptom",
        "",
        report.symptom,
        "",
        "## Root Cause Assessment",
        "",
    ]

    if report.top_hypothesis_title:
        lines.append(f"- **Top Hypothesis:** {report.top_hypothesis_title}")
    if report.top_hypothesis_id:
        lines.append(f"- **Hypothesis ID:** {report.top_hypothesis_id}")
    if report.confidence is not None:
        lines.append(f"- **Confidence:** {int(report.confidence)}%")

    lines.extend(["", "## Evidence Findings", ""])
    if report.findings:
        for finding in report.findings:
            detail = f" — {finding.detail}" if finding.detail else ""
            source = f" ({finding.source})" if finding.source else ""
            structured = (
                f" — structured: {finding.structured_summary}"
                if finding.structured_summary
                else ""
            )
            lines.append(
                f"- `{finding.command}`: **{finding.signal}**{source}{detail}{structured}"
            )
    else:
        lines.append("_No analysis findings recorded._")

    lines.extend(["", "## Correlation Reasoning", ""])
    if report.correlations:
        for correlation in report.correlations:
            impact = _format_confidence_impact(correlation.confidence_delta)
            lines.append(
                f"- **{correlation.rule_id}** — {correlation.correlation_type}{impact}"
            )
            lines.append(f"  {correlation.explanation}")
            if correlation.evidence_names:
                evidence = ", ".join(correlation.evidence_names)
                lines.append(f"  Evidence: {evidence}")
    else:
        lines.append("_No correlation results recorded._")

    lines.extend(["", "## Recommendation", ""])
    if report.recommendation_summary:
        lines.append(report.recommendation_summary)
    else:
        lines.append("_No recommendation recorded._")

    if report.recommendation_actions:
        lines.append("")
        lines.append("**Recommended Actions:**")
        for action in report.recommendation_actions:
            lines.append(f"- {action}")

    lines.extend(["", "## Verification", ""])
    if report.verification_outcome:
        lines.append(f"- **Outcome:** {report.verification_outcome.replace('_', ' ')}")
    if report.verifications:
        for step in report.verifications:
            status = step.result_status or "pending"
            note = f" ({step.notes})" if step.notes else ""
            lines.append(f"- {step.step_name}: {step.description} — **{status}**{note}")
    else:
        lines.append("_No verification steps recorded._")

    lines.extend(["", "## Learning Record", ""])
    if report.learning_record_id:
        lines.append(f"- **Learning Record ID:** {report.learning_record_id}")
        if report.learning_root_cause:
            lines.append(f"- **Root Cause:** {report.learning_root_cause}")
        if report.learning_reusable_pattern:
            lines.append(f"- **Reusable Pattern:** {report.learning_reusable_pattern}")
        if report.learning_lessons:
            lines.append(f"- **Lessons Learned:** {report.learning_lessons}")
    else:
        lines.append("_No learning record attached._")

    lines.extend(["", "## Timeline", ""])
    if report.timeline:
        for entry in report.timeline:
            lines.append(
                f"{entry.sequence}. [{entry.timestamp}] {entry.event_type}: {entry.summary}"
            )
    else:
        lines.append("_No timeline events recorded._")

    return "\n".join(lines)


def _build_report_correlations(
    correlations: list[CorrelationResult],
) -> list[ReportCorrelation]:
    return [
        ReportCorrelation(
            rule_id=correlation.rule_id,
            correlation_type=correlation.correlation_type,
            confidence_delta=correlation.confidence_delta,
            explanation=correlation.explanation,
            evidence_names=tuple(correlation.finding_codes),
        )
        for correlation in correlations
    ]


def _format_confidence_impact(delta: float) -> str:
    if delta == 0.0:
        return ""
    value = int(delta)
    sign = "+" if value > 0 else ""
    return f", {sign}{value} confidence"


def _top_hypothesis(case: Case) -> Hypothesis | None:
    if not case.hypotheses:
        return None
    return min(case.hypotheses, key=lambda hypothesis: hypothesis.rank or 999)


def _likely_root_cause_recommendation(case: Case) -> Recommendation | None:
    for recommendation in reversed(case.recommendations):
        if recommendation.action_type == ACTION_LIKELY_ROOT_CAUSE:
            return recommendation
    return None


def _resolve_confidence(
    hypothesis: Hypothesis | None,
    recommendation: Recommendation | None,
    learning,
) -> float | None:
    if learning is not None:
        return learning.confidence
    if recommendation and recommendation.confidence is not None:
        return recommendation.confidence
    if hypothesis is not None:
        return hypothesis.confidence
    return None


def _format_recommendation_summary(recommendation: Recommendation | None) -> str | None:
    if recommendation is None:
        return None
    parts = [recommendation.description]
    if recommendation.likely_root_cause:
        parts.append(f"Likely root cause: {recommendation.likely_root_cause}")
    if recommendation.rationale:
        parts.append(recommendation.rationale)
    return " ".join(part for part in parts if part)


def _verification_outcome(case: Case) -> str | None:
    if not case.verifications:
        return None
    statuses = [step.result_status for step in case.verifications if step.result_status]
    if not statuses:
        return VERIFICATION_OUTCOME_NONE
    if all(status == RESULT_PASSED for status in statuses):
        return VERIFICATION_OUTCOME_PASSED
    return VERIFICATION_OUTCOME_PARTIAL


def _build_timeline(case: Case) -> tuple[ReportTimelineEntry, ...]:
    entries: list[ReportTimelineEntry] = []
    metadata_timeline = case.metadata.get("timeline", {})
    if isinstance(metadata_timeline, dict):
        onset = metadata_timeline.get("onset")
        if onset:
            entries.append(
                ReportTimelineEntry(
                    sequence=0,
                    timestamp="intake",
                    event_type="symptom_onset",
                    summary=f"Symptom onset recorded: {onset}",
                )
            )

    for event in sorted(case.timeline_events, key=lambda item: item.sequence):
        entries.append(
            ReportTimelineEntry(
                sequence=event.sequence,
                timestamp=_format_timestamp(event.timestamp) or "unknown",
                event_type=event.event_type,
                summary=event.summary,
            )
        )
    return tuple(entries)


def _format_timestamp(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()
