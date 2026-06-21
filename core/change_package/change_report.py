"""Markdown formatter for Engineering Change Packages."""

from __future__ import annotations

from change_package.change_models import EngineeringChangePackage, RecommendedChange, VerificationStep


def format_change_package_markdown(package: EngineeringChangePackage) -> str:
    """Format a change package as a Markdown document for engineer/CAB review."""
    sections = [
        "# VoicePilot Engineering Change Package",
        "",
        f"**Package ID:** {package.package_id}",
        f"**Case ID:** {package.case_id}",
        f"**Playbook:** {package.playbook_id or '(none)'}",
        f"**Generated:** {package.generated_at.isoformat()}",
        "",
        "## Read-Only Notice",
        "",
        package.read_only_notice,
        "",
        "## Executive Summary",
        "",
        package.executive_summary,
        "",
        "## Root Cause",
        "",
        package.root_cause or "_Not determined — insufficient recommendation confidence._",
        "",
        "## Confidence",
        "",
        f"{int(package.confidence)}%",
        "",
        "## Evidence Reviewed",
        "",
        _bullet_list(package.evidence_reviewed, empty="_No evidence recorded._"),
        "",
        "## Affected Components",
        "",
        _bullet_list(package.affected_components, empty="_To be confirmed by engineer._"),
        "",
        "## Recommended Changes",
        "",
        _format_recommended_changes(package.recommended_changes),
        "",
        "## Configuration Examples",
        "",
        _format_code_blocks(package.configuration_examples, empty="_No configuration examples — collect additional evidence._"),
        "",
        "## Rollback Examples",
        "",
        _format_code_blocks(package.rollback_examples, empty="_No rollback examples — define during change planning._"),
        "",
        "## Risk Assessment",
        "",
        f"**Level:** {package.risk_level.value}",
        "",
        package.risk_summary,
        "",
        "## Prerequisites",
        "",
        _bullet_list(package.prerequisites),
        "",
        "## Assumptions",
        "",
        _bullet_list(package.assumptions),
        "",
        "## Verification Steps",
        "",
        _format_verification_steps(package.verification_steps),
        "",
        "## Post-Change Validation",
        "",
        _bullet_list(package.post_change_validation, empty="_Define after recommended changes are approved._"),
        "",
        "## Related Knowledge Assets",
        "",
        _bullet_list(package.related_knowledge_assets, empty="_No matched knowledge assets._"),
        "",
        "## Vendor References",
        "",
        _bullet_list(package.vendor_references, empty="_Confirm vendor documentation during review._"),
        "",
        "## Approvals",
        "",
        _format_approvals(package),
        "",
        "## Engineer Notes",
        "",
        _bullet_list(package.engineer_notes),
        "",
    ]
    return "\n".join(sections)


def _bullet_list(items: tuple[str, ...], *, empty: str = "_None._") -> str:
    if not items:
        return empty
    return "\n".join(f"- {item}" for item in items)


def _format_recommended_changes(changes: tuple[RecommendedChange, ...]) -> str:
    if not changes:
        return "_No recommended changes — insufficient investigation confidence._"
    blocks: list[str] = []
    for index, change in enumerate(changes, start=1):
        blocks.extend(
            [
                f"### {index}. {change.title}",
                "",
                f"**Risk:** {change.risk_level.value}",
                "",
                f"**Reason:** {change.reason}",
                "",
                f"**Current state:** {change.current_state}",
                "",
                f"**Recommended state:** {change.recommended_state}",
                "",
                "**Impacted objects:**",
                _bullet_list(change.impacted_objects),
                "",
            ]
        )
    return "\n".join(blocks).rstrip()


def _format_code_blocks(examples: tuple[str, ...], *, empty: str) -> str:
    if not examples:
        return empty
    blocks: list[str] = []
    for index, example in enumerate(examples, start=1):
        blocks.extend([f"### Example {index}", "", "```text", example.rstrip(), "```", ""])
    return "\n".join(blocks).rstrip()


def _format_verification_steps(steps: tuple[VerificationStep, ...]) -> str:
    if not steps:
        return "_No verification steps — define after changes are approved._"
    lines: list[str] = []
    for index, step in enumerate(steps, start=1):
        required = "required" if step.required else "optional"
        lines.extend(
            [
                f"### Step {index} ({required})",
                "",
                f"**Command / check:** `{step.command}`",
                "",
                f"**Purpose:** {step.purpose}",
                "",
                f"**Expected result:** {step.expected_result}",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def _format_approvals(package: EngineeringChangePackage) -> str:
    lines: list[str] = []
    for section in package.approval_sections:
        required = "required" if section.required else "optional"
        lines.extend(
            [
                f"### {section.name} ({required})",
                "",
                section.placeholder,
                "",
            ]
        )
    return "\n".join(lines).rstrip()
