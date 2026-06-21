"""Investigation session Markdown reporting."""

from __future__ import annotations

from investigation.session_models import InvestigationSession, SessionJourneyEntry


def format_investigation_journey_markdown(session: InvestigationSession) -> str:
    """Format a session journey as standalone Markdown."""
    lines = [
        "# Investigation Journey",
        "",
        f"**Session:** {session.session_id}",
        f"**Case:** {session.case_id}",
        f"**Playbook:** {session.playbook_id}",
        f"**Status:** {session.status.value}",
        "",
        "## Steps",
        "",
    ]
    lines.extend(_format_journey_entries(session.journey))
    return "\n".join(lines).rstrip() + "\n"


def format_investigation_journey_report_section(
    *,
    available: bool,
    session_id: str | None = None,
    journey: tuple[SessionJourneyEntry, ...] = (),
) -> list[str]:
    """Format investigation journey for inclusion in an incident report."""
    lines = ["", "## Investigation Journey", ""]
    if not available:
        lines.append("_No investigation session recorded._")
        return lines

    if session_id:
        lines.append(f"- **Session ID:** {session_id}")
    lines.append(f"- **Steps:** {len(journey)}")
    lines.append("")
    lines.append("**Journey:**")
    if journey:
        for entry in journey:
            lines.append(
                f"{entry.sequence}. `{entry.action.value}` "
                f"({entry.case_state.value}) — {entry.summary}"
            )
    else:
        lines.append("_No journey steps recorded._")
    lines.append("")
    return lines


def journey_from_case_metadata(metadata: dict) -> tuple[SessionJourneyEntry, ...]:
    """Rebuild journey entries stored on a case."""
    session_data = metadata.get("investigation_session")
    if not isinstance(session_data, dict):
        return ()

    raw_journey = session_data.get("journey", [])
    if not isinstance(raw_journey, list):
        return ()

    entries: list[SessionJourneyEntry] = []
    from datetime import datetime

    from domain.enums import InvestigationState
    from investigation.session_models import SessionActionType

    for item in raw_journey:
        if not isinstance(item, dict):
            continue
        timestamp_raw = item.get("timestamp")
        timestamp = (
            datetime.fromisoformat(timestamp_raw)
            if isinstance(timestamp_raw, str)
            else datetime.now()
        )
        entries.append(
            SessionJourneyEntry(
                sequence=int(item.get("sequence", len(entries) + 1)),
                timestamp=timestamp,
                action=SessionActionType(str(item.get("action", "intake_question"))),
                case_state=InvestigationState(str(item.get("case_state", "INTAKE"))),
                summary=str(item.get("summary", "")),
            )
        )
    return tuple(entries)
