"""Brain status and investigation replay reporting."""

from __future__ import annotations

from brain.brain_context import BrainContext
from brain.brain_models import BrainReplayStep, BrainSession, BrainStage


_STAGE_LABELS: dict[BrainStage, str] = {
    BrainStage.INITIALIZING: "Brain Started",
    BrainStage.WAITING_FOR_EVIDENCE: "Waiting for Evidence",
    BrainStage.PARSING: "Parsing Evidence",
    BrainStage.ANALYZING: "Analysis Completed",
    BrainStage.CORRELATING: "Correlation Completed",
    BrainStage.DISCOVERY_PLANNING: "Discovery Plan Generated",
    BrainStage.QUALITY_EVALUATION: "Investigation Quality Updated",
    BrainStage.RECOMMENDING: "Recommendation Generated",
    BrainStage.VERIFYING: "Verification Complete",
    BrainStage.LEARNING: "Learning Record Created",
    BrainStage.COMPLETE: "Investigation Closed",
    BrainStage.FAILED: "Investigation Failed",
}

_NEXT_ENGINE: dict[BrainStage, str] = {
    BrainStage.INITIALIZING: "RuntimeEngine",
    BrainStage.WAITING_FOR_EVIDENCE: "Evidence Collection",
    BrainStage.PARSING: "Parser Engine",
    BrainStage.ANALYZING: "Analysis Engine",
    BrainStage.CORRELATING: "Correlation Engine",
    BrainStage.DISCOVERY_PLANNING: "Discovery Planner",
    BrainStage.QUALITY_EVALUATION: "Investigation Quality Framework",
    BrainStage.RECOMMENDING: "Recommendation Engine",
    BrainStage.VERIFYING: "Verification Engine",
    BrainStage.LEARNING: "Learning Engine",
    BrainStage.COMPLETE: "None",
    BrainStage.FAILED: "None",
}


def format_brain_status(
    session: BrainSession,
    context: BrainContext,
) -> str:
    """Format a Brain status report for terminal output."""
    top_hypothesis = context.top_hypothesis
    lines = [
        "Brain Status",
        "",
        f"Session:            {session.session_id}",
        f"Case:               {session.case_id}",
        f"Playbook:           {session.playbook}",
        f"Current Stage:      {session.current_stage.value}",
        f"Confidence:         {_format_optional_float(session.current_confidence)}",
        f"Quality Score:      {_format_optional_int(session.current_quality_score)}",
        f"Current Hypothesis: {top_hypothesis.title if top_hypothesis else '(none)'}",
        f"Next Expected Engine: {_NEXT_ENGINE.get(session.current_stage, 'Unknown')}",
        f"Completed:          {'Yes' if session.completed else 'No'}",
        f"Failed:             {'Yes' if session.failed else 'No'}",
    ]
    return "\n".join(lines)


def format_brain_replay(session: BrainSession, context: BrainContext) -> str:
    """Format an investigation replay timeline."""
    steps = build_investigation_replay(session, context)
    lines = [
        "Investigation Replay",
        "",
        f"Session: {session.session_id}",
        f"Case:    {session.case_id}",
        "",
    ]
    if not steps:
        lines.append("_No replay steps recorded._")
        return "\n".join(lines)

    for index, step in enumerate(steps):
        timestamp = step.timestamp.strftime("%H:%M")
        lines.append(timestamp)
        lines.append(step.label)
        if index < len(steps) - 1:
            lines.append("")
            lines.append("↓")
            lines.append("")
    return "\n".join(lines)


def build_investigation_replay(
    session: BrainSession,
    context: BrainContext,
) -> tuple[BrainReplayStep, ...]:
    """Build replay steps from Brain journey and decision log entries."""
    steps: list[BrainReplayStep] = []

    for entry in session.journey:
        steps.append(
            BrainReplayStep(
                timestamp=entry.timestamp,
                label=_STAGE_LABELS.get(entry.stage, entry.summary),
                source="brain",
            )
        )

    decision_by_id = {entry.entry_id: entry for entry in context.decision_log}
    for entry_id in session.decision_log_ids:
        decision = decision_by_id.get(entry_id)
        if decision is None:
            continue
        steps.append(
            BrainReplayStep(
                timestamp=decision.timestamp,
                label=decision.title,
                source="decision_log",
            )
        )

    steps.sort(key=lambda item: item.timestamp)
    return tuple(steps)


def format_brain_session_list(sessions: tuple[BrainSession, ...]) -> str:
    """Format a list of Brain sessions."""
    lines = ["Brain Sessions", ""]
    if not sessions:
        lines.append("_No Brain sessions registered._")
        return "\n".join(lines)

    for session in sessions:
        lines.append(
            f"- {session.session_id} | {session.playbook} | "
            f"{session.current_stage.value} | case={session.case_id}"
        )
    return "\n".join(lines)


def _format_optional_float(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{int(value)}%"


def _format_optional_int(value: int | None) -> str:
    if value is None:
        return "n/a"
    return f"{value}/100"
