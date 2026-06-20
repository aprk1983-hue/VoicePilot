"""Investigation quality Markdown reporting."""

from __future__ import annotations

from investigation_quality.quality_models import InvestigationQualityReport, QualityMetricResult


def format_investigation_quality_markdown(report: InvestigationQualityReport) -> str:
    """Format an investigation quality report as Markdown."""
    lines = [
        "# Investigation Quality Report",
        "",
        "Overall Score",
        "",
        f"{report.overall_score}/100",
        "",
        "Overall Status",
        "",
        report.overall_status,
        "",
        "Ready for Recommendation",
        "",
        "Yes" if report.ready_for_recommendation else "No",
        "",
        "Ready for Case Closure",
        "",
        "Yes" if report.ready_for_case_closure else "No",
        "",
        "--------------------------------",
        "",
        "## Metrics",
        "",
    ]

    if not report.metric_results:
        lines.append("_No quality metrics evaluated._")
        lines.append("")
        return "\n".join(lines)

    for index, metric in enumerate(report.metric_results, start=1):
        if index > 1:
            lines.extend(["", "--------------------------------", ""])
        lines.extend(_format_metric_section(metric))

    return "\n".join(lines).rstrip() + "\n"


def format_investigation_quality_report_section(report: InvestigationQualityReport) -> list[str]:
    """Format investigation quality for inclusion in an incident report."""
    lines = [
        "",
        "## Investigation Quality",
        "",
        f"- **Overall Score:** {report.overall_score}/100",
        f"- **Overall Status:** {report.overall_status}",
        f"- **Ready for Recommendation:** {'Yes' if report.ready_for_recommendation else 'No'}",
        f"- **Ready for Case Closure:** {'Yes' if report.ready_for_case_closure else 'No'}",
        "",
    ]

    if not report.metric_results:
        lines.append("_No quality metrics evaluated._")
        return lines

    for metric in report.metric_results:
        title = metric.metric_name.replace("_", " ").title()
        lines.extend(
            [
                f"### {title}",
                "",
                f"- **Score:** {metric.score}/{metric.max_score}",
                f"- **Status:** {metric.status}",
                f"- **Summary:** {metric.summary}",
                "",
                "**Recommendations:**",
            ]
        )
        if metric.recommendations:
            for recommendation in metric.recommendations:
                lines.append(f"- {recommendation}")
        else:
            lines.append("- _None_")
        lines.append("")

    return lines


def _format_metric_section(metric: QualityMetricResult) -> list[str]:
    title = metric.metric_name.replace("_", " ").title()
    lines = [
        f"### {title}",
        "",
        "Score",
        "",
        f"{metric.score}/{metric.max_score}",
        "",
        "Status",
        "",
        metric.status,
        "",
        "Summary",
        "",
        metric.summary,
        "",
        "Recommendations",
        "",
    ]
    if metric.recommendations:
        for recommendation in metric.recommendations:
            lines.append(f"- {recommendation}")
    else:
        lines.append("_None_")
    return lines
