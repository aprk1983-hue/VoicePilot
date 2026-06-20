"""Discovery plan Markdown reporting."""

from __future__ import annotations

from discovery.planner_models import DiscoveryPlan


def format_discovery_plan_markdown(plan: DiscoveryPlan) -> str:
    """Format a discovery plan as Markdown."""
    lines = [
        "# Discovery Plan",
        "",
        "Current Confidence",
        "",
        f"{_format_percent(plan.current_confidence)}",
        "",
        "Estimated Final Confidence",
        "",
        f"{_format_percent(plan.estimated_final_confidence)}",
        "",
        "Remaining Uncertainty",
        "",
        f"{_format_percent(plan.remaining_uncertainty)}",
        "",
        "--------------------------------",
        "",
        "## Recommended Evidence",
        "",
    ]

    if not plan.requests:
        lines.append("_No additional evidence recommended._")
        lines.append("")
        return "\n".join(lines)

    for index, request in enumerate(plan.requests, start=1):
        lines.extend(
            [
                f"{index}.",
                "",
                request.command,
                "",
                "Priority",
                "",
                request.priority.value,
                "",
                "Estimated Gain",
                "",
                f"{_format_percent(request.estimated_confidence_gain)}",
                "",
                "Reason",
                "",
                request.reason,
                "",
                "Estimated Time",
                "",
                _format_minutes(request.estimated_minutes),
                "",
            ]
        )
        if index < len(plan.requests):
            lines.append("--------------------------------")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _format_percent(value: float) -> str:
    if float(value).is_integer():
        return f"{int(value)}%"
    return f"{value:.1f}%"


def _format_minutes(minutes: int) -> str:
    suffix = "minute" if minutes == 1 else "minutes"
    return f"{minutes} {suffix}"
