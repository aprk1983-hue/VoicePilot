"""Deterministic validation rules for enterprise scenario checks."""

from __future__ import annotations

import re

from change_package.change_models import EngineeringChangePackage
from domain.models import Case, Recommendation
from engineering_knowledge.knowledge_models import KnowledgeReport
from health.health_report import HealthReport
from investigation_quality.quality_models import InvestigationQualityReport
from runtime.scenario_runner import root_cause_matches
from validation.validation_models import ScenarioExpectation, ValidationMetrics

_ASSET_ID_PATTERN = re.compile(r"VP-[A-Z0-9-]+-(?:RB|VG|REF)-\d+")


def evaluate_expectations(
    expectation: ScenarioExpectation,
  *,
    actual_root_cause: str | None,
    confidence: float,
    case: Case,
    health_report: HealthReport | None,
    knowledge_report: KnowledgeReport | None,
    quality_report: InvestigationQualityReport | None,
    change_package: EngineeringChangePackage | None,
    report_markdown: str | None,
    metrics: ValidationMetrics,
) -> tuple[bool, tuple[str, ...]]:
    """Compare investigation artifacts against scenario expectations."""
    failures: list[str] = []

    if actual_root_cause is None:
        failures.append("No top hypothesis generated")
    elif not root_cause_matches(
        actual_root_cause,
        {
            "expected_root_cause": expectation.expected_root_cause,
            "expected_root_cause_aliases": list(expectation.expected_root_cause_aliases),
        },
    ):
        failures.append(
            f"Root cause mismatch: expected {expectation.expected_root_cause!r}, "
            f"got {actual_root_cause!r}"
        )

    if confidence < expectation.min_confidence:
        failures.append(
            f"Confidence {confidence:.1f}% below minimum {expectation.min_confidence:.1f}%"
        )

    if expectation.require_recommendation and not case.recommendations:
        failures.append("Missing recommendation")

    if expectation.require_report:
        if not report_markdown or not report_markdown.strip():
            failures.append("Missing report output")

    if expectation.require_change_package:
        if change_package is None:
            failures.append("Missing change package")
        elif not change_package.recommended_changes and not change_package.root_cause:
            failures.append("Change package has no advisory content")

    if expectation.expected_health_status is not None and health_report is not None:
        actual_status = _health_status_label(health_report)
        if actual_status != expectation.expected_health_status.upper():
            failures.append(
                f"Health status {actual_status!r} != expected "
                f"{expectation.expected_health_status.upper()!r}"
            )

    if expectation.min_health_score is not None:
        if metrics.health_score is None:
            failures.append("Health score unavailable")
        elif metrics.health_score < expectation.min_health_score:
            failures.append(
                f"Health score {metrics.health_score} below minimum "
                f"{expectation.min_health_score}"
            )

    if expectation.min_quality_score is not None:
        if metrics.investigation_quality_score is None:
            failures.append("Investigation quality score unavailable")
        elif metrics.investigation_quality_score < expectation.min_quality_score:
            failures.append(
                f"Quality score {metrics.investigation_quality_score} below minimum "
                f"{expectation.min_quality_score}"
            )

    finding_signals = {finding.signal for finding in case.analysis_findings}
    for signal in expectation.expected_critical_findings:
        if signal not in finding_signals:
            failures.append(f"Missing critical finding signal: {signal}")

    if expectation.expected_knowledge_ids and knowledge_report is not None:
        matched_ids = {match.knowledge_id for match in knowledge_report.matches}
        for knowledge_id in expectation.expected_knowledge_ids:
            if knowledge_id not in matched_ids:
                failures.append(f"Missing expected knowledge ID: {knowledge_id}")

    searchable_text = _searchable_investigation_text(case, change_package)
    for runbook_id in expectation.expected_runbook_ids:
        if runbook_id not in searchable_text:
            failures.append(f"Missing expected runbook ID: {runbook_id}")

    for verification_id in expectation.expected_verification_ids:
        if verification_id not in searchable_text:
            failures.append(f"Missing expected verification ID: {verification_id}")

    return (not failures, tuple(failures))


def _health_status_label(health_report: HealthReport) -> str:
    if health_report.fail_count > 0:
        return "FAIL"
    if health_report.warn_count > 0:
        return "WARN"
    return "PASS"


def _searchable_investigation_text(
    case: Case,
    change_package: EngineeringChangePackage | None,
) -> str:
    parts: list[str] = []
    for recommendation in case.recommendations:
        parts.extend(_recommendation_text_parts(recommendation))
    if change_package is not None:
        parts.append(change_package.executive_summary)
        parts.extend(change_package.related_knowledge_assets)
        parts.extend(change_package.vendor_references)
        for step in change_package.verification_steps:
            parts.append(step.expected_result)
            parts.append(step.purpose)
    return "\n".join(part for part in parts if part)


def _recommendation_text_parts(recommendation: Recommendation) -> list[str]:
    return [
        recommendation.description,
        recommendation.rationale,
        recommendation.likely_root_cause or "",
        *list(recommendation.recommended_actions or []),
        *list(recommendation.verification_steps or []),
        *list(recommendation.rollback_steps or []),
        recommendation.command or "",
    ]


def extract_asset_ids(text: str) -> tuple[str, ...]:
    """Return engineering asset IDs found in advisory text."""
    return tuple(sorted(set(_ASSET_ID_PATTERN.findall(text))))
