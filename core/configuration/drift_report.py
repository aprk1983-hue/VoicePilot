"""Human-readable baseline drift reports."""

from __future__ import annotations

from configuration.baseline_models import DriftReport
from configuration.diff_report import format_diff_report_markdown


def format_drift_report_markdown(report: DriftReport) -> str:
    """Format a drift report as readable Markdown."""
    lines = [
        "## Baseline Drift Report",
        "",
        f"Baseline: {report.baseline.baseline_id} ({report.baseline.label})",
        f"Baseline Snapshot: {report.baseline.snapshot_id}",
        f"Current Snapshot: {report.current_snapshot.snapshot_id}",
        f"Hostname: {report.current_snapshot.hostname}",
        "",
        f"Drift Status: {report.drift_status.value.upper()}",
        "",
        report.summary,
        "",
        "**Recommendations:**",
    ]

    for recommendation in report.recommendations:
        lines.append(f"- {recommendation}")

    lines.extend(["", format_diff_report_markdown(report.diff)])
    return "\n".join(lines)
