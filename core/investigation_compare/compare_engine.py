"""Investigation Comparison Engine — deterministic before/after analysis."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from configuration.snapshot_models import ConfigurationSnapshot
from domain.models import Case
from investigation_compare.compare_models import (
    ComparisonStatus,
    FindingComparison,
    ImprovementMetric,
    InvestigationComparison,
    InvestigationSnapshot,
)
from runtime.recommendation_engine import ACTION_LIKELY_ROOT_CAUSE
from runtime.report_engine import build_incident_report
from runtime.verification_engine import RESULT_PASSED

_CRITICAL_FINDING_SIGNALS = frozenset(
    {
        "sip_ua_disabled",
        "sip_ua_disabled_by_config",
        "sip_503_detected",
        "sip_488_detected",
        "sip_404_detected",
        "sip_403_detected",
        "sip_408_detected",
        "dial_peer_down",
        "dial_peer_out_of_service",
        "dial_peer_summary_missing_or_empty",
        "sip_registration_issue",
    }
)


class InvestigationComparisonEngine:
    """Compare existing investigation outputs without diagnosing or recommending."""

    def compare_cases(self, before_case: Case, after_case: Case) -> InvestigationComparison:
        """Compare two investigation cases using existing engine outputs."""
        return self._compare(
            snapshot_from_case(before_case),
            snapshot_from_case(after_case),
            before_case_id=before_case.case_id,
            after_case_id=after_case.case_id,
        )

    def compare_snapshots(
        self,
        before_snapshot: InvestigationSnapshot | ConfigurationSnapshot,
        after_snapshot: InvestigationSnapshot | ConfigurationSnapshot,
    ) -> InvestigationComparison:
        """Compare two investigation or configuration snapshots."""
        before = _coerce_snapshot(before_snapshot)
        after = _coerce_snapshot(after_snapshot)
        return self._compare(
            before,
            after,
            before_case_id=before.source_id,
            after_case_id=after.source_id,
        )

    def generate_summary(self, comparison: InvestigationComparison) -> str:
        """Return a short executive summary for a comparison."""
        return comparison.summary

    def _compare(
        self,
        before: InvestigationSnapshot,
        after: InvestigationSnapshot,
        *,
        before_case_id: str,
        after_case_id: str,
    ) -> InvestigationComparison:
        before_findings = set(before.finding_signals)
        after_findings = set(after.finding_signals)
        before_critical = set(before.critical_findings)
        after_critical = set(after.critical_findings)

        resolved = tuple(sorted(before_critical - after_critical))
        remaining = tuple(sorted(after_critical))
        new_findings = tuple(sorted(after_critical - before_critical))

        metrics = _build_metrics(before, after)
        status = _determine_status(metrics, before_critical, after_critical)
        summary = _build_summary(
            status,
            before_case_id,
            after_case_id,
            resolved=resolved,
            remaining=remaining,
            new_findings=new_findings,
        )

        finding_comparisons = tuple(
            sorted(
                (
                    FindingComparison(
                        finding=signal,
                        before=signal in before_findings,
                        after=signal in after_findings,
                        resolved=signal in before_critical and signal not in after_critical,
                    )
                    for signal in before_findings.union(after_findings)
                ),
                key=lambda item: item.finding,
            )
        )

        return InvestigationComparison(
            comparison_id=_new_comparison_id(),
            generated_at=datetime.now(timezone.utc),
            before_case_id=before_case_id,
            after_case_id=after_case_id,
            status=status,
            summary=summary,
            health_score_before=before.health_score,
            health_score_after=after.health_score,
            confidence_before=before.confidence,
            confidence_after=after.confidence,
            quality_before=before.quality_score,
            quality_after=after.quality_score,
            knowledge_matches_before=before.knowledge_matches,
            knowledge_matches_after=after.knowledge_matches,
            critical_findings_before=before.critical_findings,
            critical_findings_after=after.critical_findings,
            resolved_findings=resolved,
            remaining_findings=remaining,
            new_findings=new_findings,
            verification_status=_verification_summary(before, after),
            improvement_metrics=metrics,
            finding_comparisons=finding_comparisons,
        )


def snapshot_from_case(case: Case) -> InvestigationSnapshot:
    """Extract comparison metrics from an existing case without new analysis."""
    incident = build_incident_report(case)
    quality = case.investigation_quality_report
    signals = tuple(sorted({finding.signal for finding in case.analysis_findings}))
    critical = tuple(sorted(signal for signal in signals if signal in _CRITICAL_FINDING_SIGNALS))

    return InvestigationSnapshot(
        source_id=case.case_id,
        health_score=incident.health_assessment.overall_score
        if incident.health_assessment.available
        else None,
        confidence=incident.confidence,
        quality_score=quality.overall_score if quality else None,
        knowledge_matches=_knowledge_matches_from_case(case),
        critical_findings=critical,
        finding_signals=signals,
        verification_status=_verification_status(case),
    )


def snapshot_from_configuration(configuration: ConfigurationSnapshot) -> InvestigationSnapshot:
    """Extract comparison metrics from an existing configuration snapshot."""
    health = configuration.health_report
    critical = tuple(
        sorted(
            result.rule_id
            for result in health.results
            if result.status.value.upper() in {"FAIL", "WARN"}
        )
    )
    knowledge = tuple(match.pack_id for match in configuration.knowledge_report.matched_packs)
    return InvestigationSnapshot(
        source_id=configuration.snapshot_id,
        health_score=health.overall_score,
        confidence=None,
        quality_score=None,
        knowledge_matches=knowledge,
        critical_findings=critical,
        finding_signals=critical,
        verification_status=None,
    )


def _coerce_snapshot(value: InvestigationSnapshot | ConfigurationSnapshot) -> InvestigationSnapshot:
    if isinstance(value, InvestigationSnapshot):
        return value
    return snapshot_from_configuration(value)


def _knowledge_matches_from_case(case: Case) -> tuple[str, ...]:
    if not case.analysis_findings:
        return ()
    try:
        from engineering_knowledge import default_engineering_knowledge_engine

        report = default_engineering_knowledge_engine().evaluate_case(case)
        return tuple(match.knowledge_id for match in report.matches)
    except Exception:
        return ()


def _verification_status(case: Case) -> str | None:
    if not case.verifications:
        return None
    statuses = [step.result_status for step in case.verifications if step.result_status]
    if not statuses:
        return "not_recorded"
    if all(status == RESULT_PASSED for status in statuses):
        return "all_steps_passed"
    return "partial"


def _build_metrics(before: InvestigationSnapshot, after: InvestigationSnapshot) -> tuple[ImprovementMetric, ...]:
    metrics: list[ImprovementMetric] = []
    metrics.append(_metric("Health Score", before.health_score, after.health_score, higher_is_better=True))
    metrics.append(_metric("Confidence", before.confidence, after.confidence, higher_is_better=True))
    metrics.append(_metric("Investigation Quality", before.quality_score, after.quality_score, higher_is_better=True))
    metrics.append(
        _metric(
            "Critical Findings Count",
            len(before.critical_findings),
            len(after.critical_findings),
            higher_is_better=False,
        )
    )
    metrics.append(
        _metric(
            "Knowledge Matches",
            len(before.knowledge_matches),
            len(after.knowledge_matches),
            higher_is_better=True,
            allow_equal=True,
        )
    )
    return tuple(metrics)


def _metric(
    name: str,
    before_value: int | float | None,
    after_value: int | float | None,
    *,
    higher_is_better: bool,
    allow_equal: bool = False,
) -> ImprovementMetric:
    before_text = _value_text(before_value)
    after_text = _value_text(after_value)
    if before_value is None or after_value is None:
        return ImprovementMetric(
            name=name,
            before_value=before_text,
            after_value=after_text,
            delta="N/A",
            improved=False,
        )

    delta = after_value - before_value
    if delta == 0:
        improved = allow_equal
        delta_text = "0"
    elif higher_is_better:
        improved = delta > 0
        delta_text = f"{delta:+g}"
    else:
        improved = delta < 0
        delta_text = f"{delta:+g}"

    return ImprovementMetric(
        name=name,
        before_value=before_text,
        after_value=after_text,
        delta=delta_text,
        improved=improved,
    )


def _value_text(value: int | float | None) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


_STATUS_METRIC_NAMES = frozenset(
    {"Health Score", "Investigation Quality", "Critical Findings Count"}
)


def _determine_status(
    metrics: tuple[ImprovementMetric, ...],
    before_critical: set[str],
    after_critical: set[str],
) -> ComparisonStatus:
    comparable = [
        metric
        for metric in metrics
        if metric.name in _STATUS_METRIC_NAMES and metric.delta != "N/A"
    ]
    improvements = sum(
        1 for metric in comparable if metric.improved and metric.delta not in {"0", "+0", "-0"}
    )
    regressions = sum(
        1
        for metric in comparable
        if not metric.improved and metric.delta not in {"0", "+0", "-0", "N/A"}
    )

    finding_improved = len(after_critical) < len(before_critical)
    finding_regressed = len(after_critical) > len(before_critical)
    new_critical = after_critical - before_critical

    if finding_regressed or new_critical:
        if finding_improved or improvements > 0:
            return ComparisonStatus.PARTIAL
        return ComparisonStatus.REGRESSED
    if (finding_improved or improvements > 0) and regressions == 0:
        return ComparisonStatus.IMPROVED
    if improvements == 0 and regressions == 0 and not finding_improved:
        return ComparisonStatus.UNCHANGED
    return ComparisonStatus.PARTIAL


def _build_summary(
    status: ComparisonStatus,
    before_case_id: str,
    after_case_id: str,
    *,
    resolved: tuple[str, ...],
    remaining: tuple[str, ...],
    new_findings: tuple[str, ...],
) -> str:
    parts = [
        f"Comparison of {before_case_id} → {after_case_id} is {status.value}.",
    ]
    if resolved:
        parts.append(f"Resolved findings: {', '.join(resolved)}.")
    if remaining:
        parts.append(f"Remaining critical findings: {', '.join(remaining)}.")
    if new_findings:
        parts.append(f"New findings: {', '.join(new_findings)}.")
    return " ".join(parts)


def _verification_summary(before: InvestigationSnapshot, after: InvestigationSnapshot) -> str:
    before_status = before.verification_status or "not_recorded"
    after_status = after.verification_status or "not_recorded"
    return f"Before: {before_status}; After: {after_status}"


def _new_comparison_id() -> str:
    return f"CMP-{uuid4().hex[:12]}"
