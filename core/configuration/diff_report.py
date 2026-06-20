"""Human-readable configuration diff reports."""

from __future__ import annotations

from configuration.diff_models import DiffRiskLevel, ObjectDiff, SnapshotDiff

_SEVERITY_SECTIONS = (
    DiffRiskLevel.CRITICAL.value.upper(),
    DiffRiskLevel.HIGH.value.upper(),
    DiffRiskLevel.MEDIUM.value.upper(),
    DiffRiskLevel.LOW.value.upper(),
)


def format_diff_report_markdown(diff: SnapshotDiff) -> str:
    """Format a configuration diff as readable Markdown."""
    lines = [
        "## Configuration Diff",
        "",
        f"Before: {diff.before_snapshot_id}",
        f"After: {diff.after_snapshot_id}",
        "",
        f"Risk Level: {diff.risk_level.upper()}",
        "",
        diff.summary,
        "",
    ]

    grouped = _group_by_severity(diff)
    for section in _SEVERITY_SECTIONS:
        entries = grouped.get(section, ())
        lines.append(f"{section}:")
        if entries:
            for entry in entries:
                lines.append(f"- {entry.summary}")
        else:
            lines.append("- _None_")
        lines.append("")

    lines.append(f"Unchanged objects: {diff.unchanged_count}")
    return "\n".join(lines).rstrip()


def _group_by_severity(diff: SnapshotDiff) -> dict[str, tuple[ObjectDiff, ...]]:
    entries = [*diff.added, *diff.removed, *diff.modified]
    grouped: dict[str, list[ObjectDiff]] = {section: [] for section in _SEVERITY_SECTIONS}
    for entry in sorted(entries, key=lambda item: (item.severity, item.object_id)):
        section = entry.severity.upper()
        if section in grouped:
            grouped[section].append(entry)
    return {section: tuple(items) for section, items in grouped.items()}
