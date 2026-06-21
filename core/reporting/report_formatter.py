"""Markdown assembly for enterprise reports."""

from __future__ import annotations

from datetime import datetime

from reporting.report_models import READ_ONLY_NOTICE, BaseReport, ReportType


def format_report_header(
    *,
    case_id: str,
    playbook_id: str | None,
    report_type: ReportType,
    generated_at: datetime,
    title: str,
) -> str:
    """Return standard report metadata header."""
    return "\n".join(
        [
            f"# {title}" if not title.startswith("#") else title.split("\n", 1)[0],
            "",
            f"**Generated:** {generated_at.isoformat()}",
            f"**Case ID:** {case_id}",
            f"**Playbook:** {playbook_id or '(none)'}",
            f"**Report Type:** {report_type.value}",
            "",
            "## Read-Only Notice",
            "",
            READ_ONLY_NOTICE,
            "",
        ]
    )


def assemble_report_markdown(
    *,
    case_id: str,
    playbook_id: str | None,
    report_type: ReportType,
    generated_at: datetime,
    title: str,
    body: str,
) -> str:
    """Combine metadata header with audience-specific body."""
    if body.startswith("#"):
        lines = body.split("\n")
        body_without_title = "\n".join(lines[1:]).lstrip("\n")
        header = format_report_header(
            case_id=case_id,
            playbook_id=playbook_id,
            report_type=report_type,
            generated_at=generated_at,
            title=lines[0].lstrip("# ").strip(),
        )
        return header + body_without_title

    header = format_report_header(
        case_id=case_id,
        playbook_id=playbook_id,
        report_type=report_type,
        generated_at=generated_at,
        title=title,
    )
    return header + body


def terminal_summary(report: BaseReport) -> str:
    """Return a short terminal summary for CLI output."""
    return "\n".join(
        [
            f"Report ID:   {report.report_id}",
            f"Case ID:     {report.case_id}",
            f"Type:        {report.report_type.value}",
            f"Title:       {report.title}",
            f"Summary:     {report.summary}",
        ]
    )
