"""Brain status and investigation replay reporting."""

from __future__ import annotations

from brain.brain_context import BrainContext
from brain.brain_models import BrainAdvanceResult, BrainReplayStep, BrainSession, BrainStage
from runtime.intake_summary import VP_CUBE_0001_ALL_FAIL_EVIDENCE, VP_CUBE_0001_PLAYBOOK_ID


_STAGE_LABELS: dict[BrainStage, str] = {
    BrainStage.INITIALIZING: "Session started",
    BrainStage.WAITING_FOR_EVIDENCE: "Waiting for Evidence",
    BrainStage.PARSING: "Parsing Evidence",
    BrainStage.ANALYZING: "Analysis completed",
    BrainStage.CORRELATING: "Correlation completed",
    BrainStage.DISCOVERY_PLANNING: "Discovery plan generated",
    BrainStage.QUALITY_EVALUATION: "Investigation quality evaluated",
    BrainStage.RECOMMENDING: "Recommendation generated",
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


def _collected_commands(context: BrainContext) -> set[str]:
    commands: set[str] = set()
    for item in context.case.evidence:
        if item.source.command:
            commands.add(item.source.command)
    collection = context.case.metadata.get("evidence_collection", {})
    commands.update(collection.get("collected_commands", []))
    return commands


def get_next_requested_evidence(session: BrainSession, context: BrainContext) -> str | None:
    """Return the next CLI command Brain is waiting for, if known."""
    if session.completed or session.failed:
        return None

    collected = _collected_commands(context)
    if context.discovery_plan and context.discovery_plan.next_best_command:
        if context.discovery_plan.next_best_command not in collected:
            return context.discovery_plan.next_best_command

    if session.playbook == VP_CUBE_0001_PLAYBOOK_ID:
        for command in VP_CUBE_0001_ALL_FAIL_EVIDENCE:
            if command not in collected:
                return command

    return None


def format_brain_status(
    session: BrainSession,
    context: BrainContext,
) -> str:
    """Format a Brain status report for terminal output."""
    top_hypothesis = context.top_hypothesis
    next_evidence = get_next_requested_evidence(session, context)
    lines = [
        "Brain Status",
        "",
        f"Session:                {session.session_id}",
        f"Case:                   {session.case_id}",
        f"Playbook:               {session.playbook}",
        f"Current Stage:          {session.current_stage.value}",
        f"Confidence:             {_format_optional_float(session.current_confidence)}",
        f"Quality Score:          {_format_optional_int(session.current_quality_score)}",
        f"Current Hypothesis:     {top_hypothesis.title if top_hypothesis else '(none)'}",
        f"Next Expected Engine:   {_NEXT_ENGINE.get(session.current_stage, 'Unknown')}",
        f"Next Requested Evidence: {next_evidence or '(none)'}",
        f"Completed:              {'Yes' if session.completed else 'No'}",
        f"Failed:                 {'Yes' if session.failed else 'No'}",
    ]
    return "\n".join(lines)


def format_brain_start_summary(
    session: BrainSession,
    context: BrainContext,
) -> str:
    """Format the summary printed after ``brain start``."""
    next_evidence = get_next_requested_evidence(session, context)
    lines = [
        "Brain session started",
        "",
        f"Session ID:             {session.session_id}",
        f"Case ID:                {session.case_id}",
        f"Playbook:               {session.playbook}",
        f"Current Stage:          {session.current_stage.value}",
        f"Next Expected Engine:   {_NEXT_ENGINE.get(session.current_stage, 'Unknown')}",
        f"Next Requested Evidence: {next_evidence or '(none)'}",
    ]
    return "\n".join(lines)


def format_brain_upload_summary(
    session: BrainSession,
    *,
    command: str,
    file_path: str,
) -> str:
    """Format the summary printed after ``brain upload``."""
    return "\n".join(
        [
            "Evidence uploaded",
            "",
            f"Session:       {session.session_id}",
            f"Command:       {command}",
            f"File:          {file_path}",
            f"Current Stage: {session.current_stage.value}",
        ]
    )


def format_brain_next_summary(
    session: BrainSession,
    context: BrainContext,
    result: BrainAdvanceResult,
) -> str:
    """Format the summary printed after ``brain next``."""
    top_hypothesis = context.top_hypothesis
    next_evidence = get_next_requested_evidence(session, context)
    recommendation = context.recommendations[0] if context.recommendations else None
    lines = [
        "Brain advanced",
        "",
        f"Current Stage:              {session.current_stage.value}",
        f"Current Confidence:         {_format_optional_float(session.current_confidence)}",
        f"Investigation Quality Score: {_format_optional_int(session.current_quality_score)}",
        f"Top Hypothesis:             {top_hypothesis.title if top_hypothesis else '(none)'}",
    ]
    if next_evidence and session.current_stage == BrainStage.WAITING_FOR_EVIDENCE:
        lines.append(f"Next Requested Evidence:    {next_evidence}")
    elif recommendation is not None:
        lines.append(f"Recommendation Ready:       {recommendation.title}")
    else:
        lines.append("Next Requested Evidence:    (none)")

    if result.messages:
        lines.append("")
        lines.extend(result.messages)

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
                label=_journey_replay_label(entry),
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
    lines = [
        "Brain Sessions",
        "",
        "Session | Case | Playbook | Stage | Confidence | Quality | Completed",
        "",
    ]
    if not sessions:
        lines.append("_No Brain sessions registered._")
        return "\n".join(lines)

    for session in sessions:
        lines.append(
            f"{session.session_id} | {session.case_id} | {session.playbook} | "
            f"{session.current_stage.value} | "
            f"{_format_optional_float(session.current_confidence)} | "
            f"{_format_optional_int(session.current_quality_score)} | "
            f"{'Yes' if session.completed else 'No'}"
        )
    return "\n".join(lines)


def _journey_replay_label(entry) -> str:
    if entry.summary.startswith("Evidence uploaded:"):
        return entry.summary
    if entry.summary.startswith("Waiting for evidence:"):
        return entry.summary
    if entry.summary in {
        "Brain session started",
        "Hypothesis generated",
        "Analysis completed",
        "Correlation completed",
        "Discovery plan generated",
        "Investigation quality evaluated",
        "Recommendation generated",
    }:
        return entry.summary
    return _STAGE_LABELS.get(entry.stage, entry.summary)


def _format_optional_float(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{int(value)}%"


def _format_optional_int(value: int | None) -> str:
    if value is None:
        return "n/a"
    return f"{value}/100"
