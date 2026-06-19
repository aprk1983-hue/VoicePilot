"""Deterministic intake summary builder for post-intake handoff."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from domain.enums import InvestigationState
from domain.models import Case, Playbook

VP_CUBE_0001_PLAYBOOK_ID = "VP-CUBE-0001"

VP_CUBE_0001_ALL_FAIL_EVIDENCE = [
    "show dial-peer voice summary",
    "show sip-ua status",
    "show run | sec voice service voip",
    "debug ccsip messages",
]

DEFAULT_STRATEGY = "Routing-first"
CHANGE_ROUTING_STRATEGY = "Change-first / Routing-first"


@dataclass(frozen=True)
class IntakeSummary:
    """Structured summary produced when intake completes."""

    case_id: str
    playbook_id: str
    current_state: InvestigationState
    known_facts: dict[str, Any]
    missing_evidence: list[str]
    recommended_strategy: str
    next_required_commands: list[str]


def build_intake_summary(case: Case, playbook: Playbook | None = None) -> IntakeSummary:
    """Build an intake summary from case intake answers and playbook rules."""
    playbook_id = case.playbook_id or ""
    known_facts = extract_known_facts(case)

    if playbook_id == VP_CUBE_0001_PLAYBOOK_ID:
        return _build_vp_cube_0001_summary(case, known_facts)

    return IntakeSummary(
        case_id=case.case_id,
        playbook_id=playbook_id,
        current_state=case.status,
        known_facts=known_facts,
        missing_evidence=[],
        recommended_strategy=DEFAULT_STRATEGY,
        next_required_commands=[],
    )


def extract_known_facts(case: Case) -> dict[str, Any]:
    """Collect intake answers stored on the case metadata."""
    facts: dict[str, Any] = dict(case.metadata.get("known_facts", {}))

    if "recent_changes" in case.metadata:
        facts["recent_changes"] = case.metadata["recent_changes"]

    timeline = case.metadata.get("timeline", {})
    if isinstance(timeline, dict) and "onset" in timeline:
        facts["onset"] = timeline["onset"]

    scope = case.metadata.get("affected_scope", {})
    if isinstance(scope, dict) and scope:
        if "destination_classes" in scope:
            facts["destination_classes"] = scope["destination_classes"]

    return facts


def format_intake_summary(summary: IntakeSummary) -> str:
    """Format an intake summary for terminal output."""
    lines = [
        "",
        "--- Intake Summary ---",
        f"Case ID:     {summary.case_id}",
        f"Playbook:    {summary.playbook_id}",
        f"State:       {summary.current_state.value}",
        "",
        "Known Facts:",
    ]

    if summary.known_facts:
        for key, value in summary.known_facts.items():
            lines.append(f"  {key}: {value}")
    else:
        lines.append("  (none)")

    lines.append("")
    lines.append("Missing Evidence:")
    if summary.missing_evidence:
        for item in summary.missing_evidence:
            lines.append(f"  - {item}")
    else:
        lines.append("  (none)")

    lines.extend(
        [
            "",
            f"Recommended Strategy:",
            f"  {summary.recommended_strategy}",
            "",
            "Next Required Commands:",
        ]
    )
    if summary.next_required_commands:
        for command in summary.next_required_commands:
            lines.append(f"  - {command}")
    else:
        lines.append("  (none)")

    return "\n".join(lines)


def write_intake_summary(
    case: Case,
    output_writer: Any,
    *,
    playbook: Playbook | None = None,
) -> IntakeSummary:
    """Build and write a formatted intake summary."""
    summary = build_intake_summary(case, playbook)
    for line in format_intake_summary(summary).splitlines():
        output_writer(line)
    return summary


def _build_vp_cube_0001_summary(
    case: Case,
    known_facts: dict[str, Any],
) -> IntakeSummary:
    """Apply VP-CUBE-0001 deterministic summary rules."""
    recommended_strategy = DEFAULT_STRATEGY
    missing_evidence: list[str] = []
    next_required_commands: list[str] = []

    if _worked_previously(known_facts.get("worked_previously")) and _has_recent_change(
        known_facts.get("recent_changes")
    ):
        recommended_strategy = CHANGE_ROUTING_STRATEGY

    if _all_outbound_calls_failing(known_facts.get("destination_classes")):
        missing_evidence = list(VP_CUBE_0001_ALL_FAIL_EVIDENCE)
        next_required_commands = list(VP_CUBE_0001_ALL_FAIL_EVIDENCE)

    return IntakeSummary(
        case_id=case.case_id,
        playbook_id=VP_CUBE_0001_PLAYBOOK_ID,
        current_state=case.status,
        known_facts=known_facts,
        missing_evidence=missing_evidence,
        recommended_strategy=recommended_strategy,
        next_required_commands=next_required_commands,
    )


def _worked_previously(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"yes", "true", "y", "1"}
    return False


def _has_recent_change(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if not normalized:
            return False
        negatives = {"no", "none", "no changes", "n/a", "nothing", "unknown"}
        return normalized not in negatives
    return bool(value)


def _all_outbound_calls_failing(value: Any) -> bool:
    if isinstance(value, str):
        normalized = value.strip().lower()
        return any(
            phrase in normalized
            for phrase in ("all", "every", "all destinations", "all outbound")
        )
    if isinstance(value, (list, tuple, set)):
        normalized = " ".join(str(item).lower() for item in value)
        return _all_outbound_calls_failing(normalized)
    return False
