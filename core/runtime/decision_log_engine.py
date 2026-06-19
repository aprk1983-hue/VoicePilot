"""Append-only decision log for investigation audit trails."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from domain.enums import DecisionLogEntryType, InvestigationState
from domain.models import (
    AnalysisFinding,
    Case,
    CorrelationResult,
    DecisionLogEntry,
    Evidence,
    Hypothesis,
    LearningRecord,
    Recommendation,
    Verification,
)
from shared.constants import ID_PREFIX_DECISION_LOG
from shared.types import JsonDict

ENGINE_NAME = "decision-log-engine"
PARSER_ENGINE_NAME = "parser-engine"
ANALYSIS_ENGINE_NAME = "analysis-engine"
CORRELATION_ENGINE_NAME = "correlation-engine"
HYPOTHESIS_ENGINE_NAME = "hypothesis-engine"
RECOMMENDATION_ENGINE_NAME = "recommendation-engine"
VERIFICATION_ENGINE_NAME = "verification-engine"
LEARNING_ENGINE_NAME = "learning-engine"
RUNTIME_ENGINE_NAME = "runtime-engine"


class DecisionLogImmutableError(RuntimeError):
    """Raised when an attempt is made to mutate an existing decision log entry."""


class DecisionLogEngine:
    """Append-only audit log for investigation decisions."""

    def append(self, case: Case, entry: DecisionLogEntry) -> DecisionLogEntry:
        """Append a decision log entry. Existing entries are never modified."""
        _assert_append_only(case, entry)
        case.decision_log.append(entry)
        return entry

    def append_evidence_collected(
        self,
        case: Case,
        *,
        evidence: Evidence,
        command: str,
    ) -> DecisionLogEntry:
        return self.append(
            case,
            _build_entry(
                case,
                decision_type=DecisionLogEntryType.EVIDENCE_COLLECTED,
                title=f"Evidence collected: {command}",
                description=f"CLI evidence submitted for command `{command}`.",
                engine=RUNTIME_ENGINE_NAME,
                supporting_evidence=(evidence.evidence_id,),
                metadata={"command": command},
            ),
        )

    def append_parser_decision(
        self,
        case: Case,
        *,
        parser_name: str,
        parser_id: str | None,
        signal: str,
        evidence_id: str,
        command: str,
        finding_id: str | None = None,
    ) -> DecisionLogEntry:
        return self.append(
            case,
            _build_entry(
                case,
                decision_type=DecisionLogEntryType.PARSER_RESULT,
                title=parser_name,
                description=f"Detected {signal}",
                engine=PARSER_ENGINE_NAME,
                rule_name=parser_id,
                supporting_findings=(finding_id or signal,),
                supporting_evidence=(evidence_id,),
                metadata={"command": command, "signal": signal, "parser_id": parser_id},
            ),
        )

    def append_analysis_decision(
        self,
        case: Case,
        *,
        finding: AnalysisFinding,
    ) -> DecisionLogEntry:
        return self.append(
            case,
            _build_entry(
                case,
                decision_type=DecisionLogEntryType.ANALYSIS_RESULT,
                title="Analysis finding",
                description=f"Detected {finding.signal} from `{finding.command}`.",
                engine=ANALYSIS_ENGINE_NAME,
                supporting_findings=(finding.finding_id,),
                supporting_evidence=(finding.evidence_id,),
                metadata={"signal": finding.signal, "command": finding.command},
            ),
        )

    def append_hypothesis_created(
        self,
        case: Case,
        *,
        hypothesis: Hypothesis,
    ) -> DecisionLogEntry:
        return self.append(
            case,
            _build_entry(
                case,
                decision_type=DecisionLogEntryType.HYPOTHESIS_CREATED,
                title=hypothesis.title,
                description=hypothesis.explanation or "Hypothesis created from analysis findings.",
                engine=HYPOTHESIS_ENGINE_NAME,
                confidence_after=hypothesis.confidence,
                selected_hypothesis=hypothesis.hypothesis_id,
                supporting_findings=tuple(hypothesis.supporting_finding_ids),
                metadata={"rank": hypothesis.rank, "category": hypothesis.category},
            ),
        )

    def append_correlation_decision(
        self,
        case: Case,
        *,
        correlation: CorrelationResult,
        confidence_before: float | None = None,
        confidence_after: float | None = None,
    ) -> DecisionLogEntry:
        return self.append(
            case,
            _build_entry(
                case,
                decision_type=DecisionLogEntryType.CORRELATION,
                title=correlation.rule_id,
                description=correlation.explanation,
                engine=CORRELATION_ENGINE_NAME,
                rule_name=correlation.rule_id,
                confidence_before=confidence_before,
                confidence_after=confidence_after,
                confidence_delta=correlation.confidence_delta or None,
                trigger=correlation.correlation_type,
                supporting_correlations=(correlation.correlation_id,),
                supporting_findings=tuple(correlation.finding_codes),
                selected_hypothesis=correlation.hypothesis_id,
                metadata={"correlation_type": correlation.correlation_type},
            ),
        )

    def append_confidence_change(
        self,
        case: Case,
        *,
        hypothesis: Hypothesis,
        confidence_before: float,
        confidence_after: float,
        trigger: str,
        rule_name: str | None = None,
        correlation_id: str | None = None,
    ) -> DecisionLogEntry:
        delta = confidence_after - confidence_before
        decision_type = (
            DecisionLogEntryType.CONFIDENCE_INCREASED
            if delta > 0
            else DecisionLogEntryType.CONFIDENCE_DECREASED
        )
        return self.append(
            case,
            _build_entry(
                case,
                decision_type=decision_type,
                title=hypothesis.title,
                description=(
                    f"Confidence changed from {int(confidence_before)}% to "
                    f"{int(confidence_after)}% ({trigger})."
                ),
                engine=CORRELATION_ENGINE_NAME,
                rule_name=rule_name,
                confidence_before=confidence_before,
                confidence_after=confidence_after,
                confidence_delta=delta,
                trigger=trigger,
                selected_hypothesis=hypothesis.hypothesis_id,
                supporting_correlations=(correlation_id,) if correlation_id else (),
                metadata={"hypothesis_id": hypothesis.hypothesis_id},
            ),
        )

    def append_recommendation(
        self,
        case: Case,
        *,
        recommendation: Recommendation,
        selected_hypothesis: Hypothesis | None,
        rejected_hypotheses: list[Hypothesis],
    ) -> DecisionLogEntry:
        title = recommendation.likely_root_cause or recommendation.description
        if recommendation.action_type == "likely_root_cause":
            title = f"Likely Root Cause — {title}"
        return self.append(
            case,
            _build_entry(
                case,
                decision_type=DecisionLogEntryType.RECOMMENDATION_SELECTED,
                title=title,
                description=recommendation.rationale or recommendation.description,
                engine=RECOMMENDATION_ENGINE_NAME,
                confidence_after=recommendation.confidence,
                selected_hypothesis=(
                    selected_hypothesis.hypothesis_id if selected_hypothesis else None
                ),
                rejected_hypotheses=tuple(
                    hypothesis.title for hypothesis in rejected_hypotheses
                ),
                supporting_findings=tuple(
                    finding_id
                    for finding_id in (
                        selected_hypothesis.supporting_finding_ids
                        if selected_hypothesis
                        else []
                    )
                ),
                metadata={
                    "action_type": recommendation.action_type,
                    "recommendation_id": recommendation.recommendation_id,
                },
            ),
        )

    def append_verification(
        self,
        case: Case,
        *,
        verification: Verification,
        outcome: str,
    ) -> DecisionLogEntry:
        return self.append(
            case,
            _build_entry(
                case,
                decision_type=DecisionLogEntryType.VERIFICATION_COMPLETED,
                title=verification.step_name,
                description=f"{verification.description} — {outcome}",
                engine=VERIFICATION_ENGINE_NAME,
                metadata={
                    "verification_id": verification.verification_id,
                    "result_status": verification.result_status,
                    "passed": verification.passed,
                },
            ),
        )

    def append_learning(
        self,
        case: Case,
        *,
        learning_record: LearningRecord,
    ) -> DecisionLogEntry:
        return self.append(
            case,
            _build_entry(
                case,
                decision_type=DecisionLogEntryType.LEARNING_CREATED,
                title="Learning record created",
                description=learning_record.resolution_summary,
                engine=LEARNING_ENGINE_NAME,
                confidence_after=learning_record.confidence,
                selected_hypothesis=learning_record.hypothesis_id,
                supporting_findings=tuple(learning_record.evidence_finding_ids),
                metadata={"learning_record_id": learning_record.learning_record_id},
            ),
        )

    def append_case_closed(self, case: Case) -> DecisionLogEntry:
        return self.append(
            case,
            _build_entry(
                case,
                decision_type=DecisionLogEntryType.CASE_CLOSED,
                title="Case closed",
                description=case.resolution_summary or "Investigation closed with learning record.",
                engine=RUNTIME_ENGINE_NAME,
                selected_hypothesis=case.root_cause_id,
                metadata={"closed_at": _format_timestamp(case.closed_at)},
            ),
        )


def parser_display_name(parser_id: str | None) -> str:
    """Convert a parser identifier to a display class name."""
    if not parser_id:
        return "UnknownParser"
    return "".join(part.capitalize() for part in parser_id.split("_")) + "Parser"


def format_decision_timeline(entries: list[DecisionLogEntry]) -> str:
    """Format the complete decision log for terminal output."""
    if not entries:
        return "Decision log is empty."

    lines = ["Decision Timeline", ""]
    ordered = sorted(entries, key=lambda item: item.timestamp)

    for index, entry in enumerate(ordered):
        if index > 0:
            lines.append("")
            lines.append("↓")
            lines.append("")

        timestamp = entry.timestamp.strftime("%H:%M:%S")
        category = _timeline_category(entry)
        lines.append(timestamp)
        lines.append(category)
        lines.append(entry.title)

        if entry.description and entry.description != entry.title:
            lines.append(entry.description)

        if entry.confidence_before is not None and entry.confidence_after is not None:
            lines.append(
                f"Confidence: {int(entry.confidence_before)} → {int(entry.confidence_after)}"
            )
        elif entry.confidence_after is not None and entry.confidence_delta is None:
            lines.append(f"Confidence: {int(entry.confidence_after)}%")

        if entry.supporting_findings:
            names = _finding_labels(entry)
            if names:
                lines.append(f"Evidence: {', '.join(names)}")

        if entry.rejected_hypotheses:
            lines.append(f"Rejected: {', '.join(entry.rejected_hypotheses)}")

    return "\n".join(lines)


def _timeline_category(entry: DecisionLogEntry) -> str:
    mapping = {
        DecisionLogEntryType.PARSER_RESULT: "Parser",
        DecisionLogEntryType.ANALYSIS_RESULT: "Analysis",
        DecisionLogEntryType.CORRELATION: "Correlation",
        DecisionLogEntryType.HYPOTHESIS_CREATED: "Hypothesis",
        DecisionLogEntryType.HYPOTHESIS_REJECTED: "Hypothesis Rejected",
        DecisionLogEntryType.CONFIDENCE_INCREASED: "Confidence",
        DecisionLogEntryType.CONFIDENCE_DECREASED: "Confidence",
        DecisionLogEntryType.RECOMMENDATION_SELECTED: "Recommendation",
        DecisionLogEntryType.VERIFICATION_COMPLETED: "Verification",
        DecisionLogEntryType.LEARNING_CREATED: "Learning",
        DecisionLogEntryType.CASE_CLOSED: "Case Closed",
        DecisionLogEntryType.EVIDENCE_COLLECTED: "Evidence",
        DecisionLogEntryType.QUESTION_SELECTED: "Question",
    }
    label = mapping.get(entry.decision_type, entry.decision_type.value)
    if entry.rule_name and entry.decision_type == DecisionLogEntryType.CORRELATION:
        return f"{label} — Rule fired"
    return label


def _finding_labels(entry: DecisionLogEntry) -> list[str]:
    labels: list[str] = []
    for item in entry.supporting_findings:
        if item.startswith("FIND-"):
            signal = entry.metadata.get("signal")
            labels.append(signal if isinstance(signal, str) else item)
        else:
            labels.append(item)
    signal = entry.metadata.get("signal")
    if isinstance(signal, str) and signal not in labels:
        labels.append(signal)
    return labels


def _build_entry(case: Case, **kwargs) -> DecisionLogEntry:
    stage = case.status.value if isinstance(case.status, InvestigationState) else str(case.status)
    severity = case.severity.value if hasattr(case.severity, "value") else None
    return DecisionLogEntry(
        entry_id=_new_entry_id(),
        timestamp=_utc_now(),
        case_id=case.case_id,
        stage=stage,
        severity=severity,
        **kwargs,
    )


def _new_entry_id() -> str:
    return f"{ID_PREFIX_DECISION_LOG}{uuid4().hex[:12]}"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _format_timestamp(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _assert_append_only(case: Case, entry: DecisionLogEntry) -> None:
    for existing in case.decision_log:
        if existing.entry_id == entry.entry_id:
            raise DecisionLogImmutableError(
                f"Decision log entry {entry.entry_id} already exists; log is append-only."
            )
    frozen_probe = replace(entry)
    if frozen_probe != entry:
        raise DecisionLogImmutableError("Decision log entries must remain immutable after creation.")
