"""Audience-specific report templates for the Enterprise Reporting Engine."""

from __future__ import annotations

from dataclasses import dataclass

from reporting.report_models import READ_ONLY_NOTICE, ReportType


@dataclass(frozen=True)
class CaseReportContext:
    """Read-only snapshot of investigation outputs for report formatting."""

    case_id: str
    playbook_id: str | None
    case_status: str
    symptom: str
    business_impact: str
    root_cause: str | None
    confidence: float | None
    resolution_summary: str | None
    recommendation_summary: str | None
    recommendation_actions: tuple[str, ...]
    verification_steps: tuple[str, ...]
    rollback_steps: tuple[str, ...]
    finding_signals: tuple[str, ...]
    affected_services: tuple[str, ...]
    incident_markdown: str | None
    health_score: int | None
    health_status: str | None
    health_recommendations: tuple[str, ...]
    quality_score: int | None
    quality_status: str | None
    ready_for_recommendation: bool | None
    knowledge_matches: tuple[str, ...]
    change_summary: str | None
    change_risk: str | None
    change_rollback: tuple[str, ...]
    change_verification: tuple[str, ...]
    change_approvals: tuple[str, ...]
    prevention: str
    next_actions: tuple[str, ...]
    future_monitoring: tuple[str, ...]


_CUSTOMER_TERM_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("SIP-UA", "voice signaling service"),
    ("sip-ua", "voice signaling service"),
    ("dial-peer", "call routing rule"),
    ("DialPeer", "call routing rule"),
    ("CUBE", "voice gateway"),
    ("show sip-ua status", "signaling status review"),
    ("show dial-peer voice summary", "routing configuration review"),
    ("show run | sec voice service voip", "voice service configuration review"),
    ("debug ccsip messages", "signaling trace review"),
    ("CLI", "technical review"),
    ("codec", "audio format"),
    ("SDP", "media negotiation"),
)


def build_executive_body(context: CaseReportContext) -> tuple[str, str, str]:
    """Return title, summary, and markdown body for an executive report."""
    title = f"Executive Incident Report — {context.case_id}"
    summary = (
        f"{context.symptom}. "
        f"Root cause: {context.root_cause or 'under investigation'}. "
        f"Confidence: {_confidence_text(context.confidence)}."
    )
    lines = [
        "# Executive Incident Report",
        "",
        "## Incident",
        "",
        context.symptom,
        "",
        "## Status",
        "",
        context.case_status,
        "",
        "## Business Impact",
        "",
        context.business_impact,
        "",
        "## Affected Services",
        "",
        _bullet_list(context.affected_services, empty="Voice services under review."),
        "",
        "## Root Cause",
        "",
        context.root_cause or "Under investigation — additional evidence may be required.",
        "",
        "## Resolution",
        "",
        context.resolution_summary
        or context.recommendation_summary
        or "Resolution pending engineer validation.",
        "",
        "## Risk",
        "",
        context.change_risk or _executive_risk(context.confidence),
        "",
        "## Confidence",
        "",
        _confidence_text(context.confidence),
        "",
        "## Prevention",
        "",
        context.prevention,
        "",
        "## Next Actions",
        "",
        _bullet_list(context.next_actions, empty="Continue monitoring and validate remediation."),
    ]
    return title, summary, "\n".join(lines)


def build_customer_body(context: CaseReportContext) -> tuple[str, str, str]:
    """Return title, summary, and markdown body for a customer report."""
    title = f"Customer Incident Summary — {context.case_id}"
    incident_summary = _sanitize_customer_text(
        context.symptom
        + (
            f" Investigation identified: {_sanitize_customer_text(context.root_cause)}."
            if context.root_cause
            else ""
        )
    )
    summary = _sanitize_customer_text(
        f"Service impact: {context.business_impact}. Status: {context.case_status}."
    )
    lines = [
        "# Customer Incident Summary",
        "",
        "## Issue",
        "",
        incident_summary,
        "",
        "## Impact",
        "",
        _sanitize_customer_text(context.business_impact),
        "",
        "## Resolution",
        "",
        _sanitize_customer_text(
            context.resolution_summary
            or context.recommendation_summary
            or "Our team is working to restore normal service."
        ),
        "",
        "## Verification",
        "",
        _sanitize_customer_text(
            "; ".join(context.verification_steps)
            if context.verification_steps
            else "Service validation is in progress."
        ),
        "",
        "## Status",
        "",
        context.case_status,
    ]
    return title, summary, "\n".join(lines)


def build_cab_body(context: CaseReportContext) -> tuple[str, str, str]:
    """Return title, summary, and markdown body for a CAB report."""
    title = f"Change Advisory Report — {context.case_id}"
    change_summary = context.change_summary or context.recommendation_summary or context.symptom
    summary = (
        f"Proposed change review for {context.case_id}. "
        f"Reason: {context.root_cause or 'investigation finding'}."
    )
    lines = [
        "# Change Advisory Report",
        "",
        "## Summary",
        "",
        change_summary,
        "",
        "## Reason",
        "",
        context.root_cause or context.recommendation_summary or context.symptom,
        "",
        "## Affected Components",
        "",
        _bullet_list(context.affected_services, empty="To be confirmed during CAB review."),
        "",
        "## Risk",
        "",
        context.change_risk or _executive_risk(context.confidence),
        "",
        "## Rollback",
        "",
        _bullet_list(context.change_rollback or context.rollback_steps, empty="Define rollback during change planning."),
        "",
        "## Verification",
        "",
        _bullet_list(context.change_verification or context.verification_steps, empty="Define verification during change planning."),
        "",
        "## Approvals",
        "",
        _bullet_list(
            context.change_approvals
            or (
                "Technical Reviewer",
                "Change Manager",
                "CAB Approval",
                "Implementation Engineer",
            ),
            empty="CAB approval required.",
        ),
        "",
        "## Implementation Window",
        "",
        "Schedule during approved maintenance window after CAB sign-off.",
    ]
    return title, summary, "\n".join(lines)


def build_engineering_body(context: CaseReportContext) -> tuple[str, str, str]:
    """Return title, summary, and markdown body for an engineering report."""
    title = f"Engineering Incident Report — {context.case_id}"
    summary = (
        f"Engineering report for {context.case_id}. "
        f"Root cause: {context.root_cause or 'see detailed sections'}."
    )
    body = context.incident_markdown or "_No engineering report content available._"
    if not body.startswith("#"):
        body = "\n".join(["# VoicePilot Incident Report", "", body])
    return title, summary, body


def build_operations_body(context: CaseReportContext) -> tuple[str, str, str]:
    """Return title, summary, and markdown body for an operations report."""
    title = f"Operations Report — {context.case_id}"
    summary = (
        f"Operations summary for {context.case_id}. "
        f"Health: {context.health_status or 'N/A'}. "
        f"Quality: {context.quality_status or 'N/A'}."
    )
    lines = [
        "# Operations Report",
        "",
        "## Health Score",
        "",
        _health_score_text(context.health_score, context.health_status),
        "",
        "## Investigation Quality",
        "",
        _quality_score_text(context.quality_score, context.quality_status, context.ready_for_recommendation),
        "",
        "## Knowledge Matches",
        "",
        _bullet_list(context.knowledge_matches, empty="No engineering knowledge assets matched."),
        "",
        "## Open Findings",
        "",
        _bullet_list(context.finding_signals, empty="No open findings recorded."),
        "",
        "## Recommendations",
        "",
        _bullet_list(context.recommendation_actions, empty="No recommendations recorded."),
        "",
        "## Future Monitoring",
        "",
        _bullet_list(context.future_monitoring, empty="Continue standard voice platform monitoring."),
    ]
    return title, summary, "\n".join(lines)


def _bullet_list(items: tuple[str, ...], *, empty: str) -> str:
    if not items:
        return empty
    return "\n".join(f"- {item}" for item in items)


def _confidence_text(confidence: float | None) -> str:
    if confidence is None:
        return "Not available"
    return f"{int(confidence)}%"


def _executive_risk(confidence: float | None) -> str:
    if confidence is None or confidence < 50:
        return "Low — investigation incomplete"
    if confidence >= 85:
        return "Medium — validated root cause with recommended remediation"
    return "Low — additional validation recommended before change"


def _health_score_text(score: int | None, status: str | None) -> str:
    if score is None:
        return "Health evaluation not available for this case."
    status_text = status or "UNKNOWN"
    return f"Overall health score: {score}/100 ({status_text})"


def _quality_score_text(
    score: int | None,
    status: str | None,
    ready_for_recommendation: bool | None,
) -> str:
    if score is None:
        return "Investigation quality not evaluated."
    ready = (
        "ready for recommendation"
        if ready_for_recommendation
        else "not ready for recommendation"
    )
    return f"Overall quality: {score}/100 ({status or 'UNKNOWN'}) — {ready}"


def _sanitize_customer_text(value: str | None) -> str:
    if not value:
        return ""
    text = value
    for source, replacement in _CUSTOMER_TERM_REPLACEMENTS:
        text = text.replace(source, replacement)
    return text
