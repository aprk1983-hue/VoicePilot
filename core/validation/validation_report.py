"""Markdown formatting for enterprise validation suites."""

from __future__ import annotations

from validation.validation_models import ValidationResult, ValidationSuite


def format_validation_report(suite: ValidationSuite) -> str:
    """Render a validation suite as Markdown."""
    summary = suite.summary
    lines = [
        "# VoicePilot Validation Report",
        "",
        f"Generated: {suite.generated_at.isoformat()}",
        "",
        "## Summary",
        "",
    ]

    if summary.playbook_id:
        lines.append(f"- **Playbook:** {summary.playbook_id}")
    else:
        lines.append("- **Playbook:** All supported playbooks")

    lines.extend(
        [
            f"- **Scenarios:** {summary.total_scenarios}",
            f"- **Passed:** {summary.passed_count}",
            f"- **Failed:** {summary.failed_count}",
            f"- **Accuracy:** {summary.accuracy_percent:.1f}%",
            f"- **Average Confidence:** {summary.average_confidence:.1f}%",
        ]
    )

    if summary.average_quality is not None:
        lines.append(f"- **Average Quality:** {summary.average_quality:.1f}")

    lines.extend(
        [
            f"- **Total Execution Time:** {summary.total_execution_time_ms:.0f} ms",
            f"- **Average Execution Time:** {summary.average_execution_time_ms:.0f} ms",
        ]
    )

    if summary.fastest_scenario_id is not None:
        lines.append(
            f"- **Fastest Scenario:** {summary.fastest_scenario_id} "
            f"({summary.fastest_execution_time_ms:.0f} ms)"
        )
    if summary.slowest_scenario_id is not None:
        lines.append(
            f"- **Slowest Scenario:** {summary.slowest_scenario_id} "
            f"({summary.slowest_execution_time_ms:.0f} ms)"
        )

    lines.extend(["", "## Scenario Results", ""])
    lines.append(_scenario_table(suite.results))
    lines.extend(["", "## Performance", ""])
    lines.append(_performance_table(suite.results))
    return "\n".join(lines)


def format_validation_summary_line(suite: ValidationSuite) -> str:
    """Return a one-line CLI summary."""
    summary = suite.summary
    scope = summary.playbook_id or "ALL"
    return (
        f"Validation {scope}: {summary.total_scenarios} total, "
        f"{summary.passed_count} passed, {summary.failed_count} failed "
        f"({summary.accuracy_percent:.1f}% accuracy)"
    )


def _scenario_table(results: tuple[ValidationResult, ...]) -> str:
    header = (
        "| Scenario | Playbook | Status | Root Cause | Confidence | Quality |"
    )
    separator = "| --- | --- | --- | --- | --- | --- |"
    rows = [header, separator]
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        quality = (
            str(result.metrics.investigation_quality_score)
            if result.metrics.investigation_quality_score is not None
            else "-"
        )
        root_cause = result.actual_root_cause or "(none)"
        rows.append(
            "| "
            f"{result.scenario_id} | {result.playbook_id} | {status} | "
            f"{root_cause} | {int(result.metrics.confidence)}% | {quality} |"
        )
    return "\n".join(rows)


def _performance_table(results: tuple[ValidationResult, ...]) -> str:
    header = (
        "| Scenario | Execution (ms) | Health | Knowledge | Report (bytes) | Topology | Discovery |"
    )
    separator = "| --- | --- | --- | --- | --- | --- | --- |"
    rows = [header, separator]
    for result in results:
        metrics = result.metrics
        health = str(metrics.health_score) if metrics.health_score is not None else "-"
        rows.append(
            "| "
            f"{result.scenario_id} | {metrics.execution_time_ms:.0f} | {health} | "
            f"{metrics.knowledge_match_count} | {metrics.report_size_bytes} | "
            f"{metrics.topology_object_count} | {metrics.discovery_command_count} |"
        )
    return "\n".join(rows)
