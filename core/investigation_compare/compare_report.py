"""Markdown formatter for investigation comparison reports."""

from __future__ import annotations

from investigation_compare.compare_models import InvestigationComparison


def format_comparison_markdown(comparison: InvestigationComparison) -> str:
    """Format an investigation comparison as Markdown."""
    lines = [
        "# Investigation Comparison",
        "",
        f"**Comparison ID:** {comparison.comparison_id}",
        f"**Generated:** {comparison.generated_at.isoformat()}",
        f"**Before Case:** {comparison.before_case_id}",
        f"**After Case:** {comparison.after_case_id}",
        "",
        "## Executive Summary",
        "",
        comparison.summary,
        "",
        "## Overall Status",
        "",
        comparison.status.value,
        "",
        "## Health",
        "",
        f"- **Before:** {_score_text(comparison.health_score_before)}",
        f"- **After:** {_score_text(comparison.health_score_after)}",
        f"- **Delta:** {_delta_text(comparison.health_score_before, comparison.health_score_after, higher_is_better=True)}",
        "",
        "## Confidence",
        "",
        f"- **Before:** {_percent_text(comparison.confidence_before)}",
        f"- **After:** {_percent_text(comparison.confidence_after)}",
        f"- **Delta:** {_delta_text(comparison.confidence_before, comparison.confidence_after, higher_is_better=True)}",
        "",
        "## Investigation Quality",
        "",
        f"- **Before:** {_score_text(comparison.quality_before)}",
        f"- **After:** {_score_text(comparison.quality_after)}",
        f"- **Delta:** {_delta_text(comparison.quality_before, comparison.quality_after, higher_is_better=True)}",
        "",
        "## Findings Resolved",
        "",
        _bullet_list(comparison.resolved_findings, empty="_None._"),
        "",
        "## Findings Remaining",
        "",
        _bullet_list(comparison.remaining_findings, empty="_None._"),
        "",
        "## New Findings",
        "",
        _bullet_list(comparison.new_findings, empty="_None._"),
        "",
        "## Verification",
        "",
        comparison.verification_status,
        "",
        "## Improvement Metrics",
        "",
        _format_metrics(comparison),
        "",
        "## Overall Result",
        "",
        comparison.status.value,
        "",
        "## Read-Only Notice",
        "",
        comparison.read_only_notice,
        "",
    ]
    return "\n".join(lines)


def _bullet_list(items: tuple[str, ...], *, empty: str) -> str:
    if not items:
        return empty
    return "\n".join(f"- {item}" for item in items)


def _score_text(value: int | None) -> str:
    if value is None:
        return "N/A"
    return f"{value}/100"


def _percent_text(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{int(value)}%"


def _delta_text(before: int | float | None, after: int | float | None, *, higher_is_better: bool) -> str:
    if before is None or after is None:
        return "N/A"
    delta = after - before
    if delta == 0:
        return "0 (unchanged)"
    direction = "improved" if (delta > 0) == higher_is_better else "regressed"
    sign = "+" if delta > 0 else ""
    if isinstance(before, float) or isinstance(after, float):
        return f"{sign}{delta:.1f} ({direction})"
    return f"{sign}{delta} ({direction})"


def _format_metrics(comparison: InvestigationComparison) -> str:
    if not comparison.improvement_metrics:
        return "_No metric deltas recorded._"
    lines: list[str] = []
    for metric in comparison.improvement_metrics:
        trend = "improved" if metric.improved else "unchanged/regressed"
        lines.append(
            f"- **{metric.name}:** {metric.before_value} → {metric.after_value} "
            f"({metric.delta}, {trend})"
        )
    return "\n".join(lines)
