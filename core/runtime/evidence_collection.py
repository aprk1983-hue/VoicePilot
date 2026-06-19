"""Deterministic CLI evidence collection flow."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import uuid4

from domain.enums import InvestigationState
from domain.models import Case, Evidence, EvidenceRequest, EvidenceSubmission, Playbook, TimelineEvent
from runtime.intake_summary import build_intake_summary
from shared.constants import ID_PREFIX_TIMELINE

if TYPE_CHECKING:
    from runtime.case_manager import CaseManager
    from runtime.decision_log_engine import DecisionLogEngine


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_timeline_id() -> str:
    return f"{ID_PREFIX_TIMELINE}{uuid4().hex[:12]}"


def initialize_evidence_collection(
    case: Case,
    case_manager: CaseManager,
    playbook: Playbook | None = None,
) -> EvidenceRequest | None:
    """Initialize required commands from intake summary and enter COLLECTION."""
    summary = build_intake_summary(case, playbook)
    commands = summary.next_required_commands
    if not commands:
        return None

    case.metadata["evidence_collection"] = {
        "required_commands": list(commands),
        "collected_commands": [],
    }
    case_manager.save_case(case)

    if case.status == InvestigationState.DISCOVERY:
        case_manager.transition_state(case.case_id, InvestigationState.COLLECTION)

    case = case_manager.load_case(case.case_id)
    return get_next_evidence_request(case)


def get_next_evidence_request(case: Case) -> EvidenceRequest | None:
    """Return the next command that still needs pasted output."""
    collection = case.metadata.get("evidence_collection")
    if not collection:
        return None

    required: list[str] = collection.get("required_commands", [])
    collected: set[str] = set(collection.get("collected_commands", []))

    for index, command in enumerate(required, start=1):
        if command not in collected:
            return EvidenceRequest(
                case_id=case.case_id,
                command=command,
                sequence=len(collected) + 1,
                total=len(required),
            )
    return None


def submit_evidence(
    case: Case,
    case_manager: CaseManager,
    command: str,
    raw_text: str,
    *,
    decision_log: DecisionLogEngine | None = None,
) -> EvidenceSubmission:
    """Save pasted CLI output as case evidence and advance collection state."""
    evidence = Evidence.create_cli_paste(case.case_id, command, raw_text)
    case.evidence.append(evidence)

    if decision_log is not None:
        decision_log.append_evidence_collected(case, evidence=evidence, command=command)

    collection = case.metadata.setdefault("evidence_collection", {})
    collected: list[str] = collection.setdefault("collected_commands", [])
    if command not in collected:
        collected.append(command)

    case.timeline_events.append(
        TimelineEvent(
            event_id=_new_timeline_id(),
            case_id=case.case_id,
            sequence=len(case.timeline_events) + 1,
            timestamp=_utc_now(),
            event_type="evidence_collected",
            source_engine="evidence-collection",
            summary=f"Collected CLI evidence for: {command}",
            related_entity_ids={"evidence_id": evidence.evidence_id, "command": command},
        )
    )
    case_manager.save_case(case)

    submission = EvidenceSubmission(
        case_id=case.case_id,
        command=command,
        source_type="cli_paste",
        raw_text=raw_text,
        collected_at=evidence.collected_at,
        evidence_id=evidence.evidence_id,
    )

    if get_next_evidence_request(case) is None:
        complete_evidence_collection(case, case_manager)

    return submission


def complete_evidence_collection(case: Case, case_manager: CaseManager) -> None:
    """Transition to ANALYSIS when all required evidence is collected."""
    if case.status == InvestigationState.COLLECTION:
        case_manager.transition_state(case.case_id, InvestigationState.ANALYSIS)


def evidence_collection_complete(case: Case) -> bool:
    """Return whether all required commands have been collected."""
    return get_next_evidence_request(case) is None and bool(
        case.metadata.get("evidence_collection")
    )


def format_evidence_request(request: EvidenceRequest) -> str:
    """Format an evidence request prompt for terminal output."""
    return "\n".join(
        [
            "Please provide command output:",
            request.command,
        ]
    )
