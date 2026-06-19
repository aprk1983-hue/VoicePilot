"""VoicePilot CLI v1 — terminal intake investigation and evidence collection."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from domain.enums import InvestigationState
from domain.models import InvestigationTurn
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.analysis_engine import format_analysis_summary
from runtime.evidence_collection import (
    format_evidence_request,
    get_next_evidence_request,
    initialize_evidence_collection,
    submit_evidence,
)
from runtime.exceptions import PlaybookIdNotFoundError
from runtime.intake_summary import write_intake_summary
from runtime.runtime_engine import RuntimeEngine
from shared.config import RuntimeConfig

REPO_ROOT = Path(__file__).resolve().parents[1]

InputProvider = Callable[[], str]
OutputWriter = Callable[[str], None]
END_MARKER = "END"


def default_plugins_root() -> Path:
    """Return the default plugins directory for the VoicePilot repo."""
    return REPO_ROOT / "plugins"


def build_runtime_engine(plugins_root: Path | None = None) -> RuntimeEngine:
    """Construct a runtime engine wired to plugin playbooks."""
    root = plugins_root or default_plugins_root()
    return RuntimeEngine(
        config=RuntimeConfig(playbooks_path=root),
        case_repository=InMemoryCaseRepository(),
        playbook_repository=FilesystemPlaybookRepository(YamlLoader()),
    )


def write_case_header(turn: InvestigationTurn, output_writer: OutputWriter) -> None:
    """Write case metadata lines to the output writer."""
    output_writer(f"Case:     {turn.case_id}")
    output_writer(f"State:    {turn.state.value}")
    output_writer(f"Playbook: {turn.context.get('playbook_id')}")


def format_question(turn: InvestigationTurn) -> str:
    """Format the active question for terminal output."""
    if not turn.question_id:
        return turn.prompt
    return f"[{turn.question_id}] {turn.prompt}"


def read_multiline_paste(input_provider: InputProvider, *, end_marker: str = END_MARKER) -> str:
    """Read pasted command output until ``end_marker`` on its own line."""
    lines: list[str] = []
    while True:
        line = input_provider()
        if line.strip() == end_marker:
            break
        lines.append(line)
    return "\n".join(lines)


def run_evidence_collection(
    case_id: str,
    runtime: RuntimeEngine,
    playbook_id: str,
    input_provider: InputProvider,
    output_writer: OutputWriter,
) -> int:
    """Collect required CLI evidence via multi-line paste."""
    case = runtime.case_manager.load_case(case_id)
    playbook = runtime.playbook_catalog.get(playbook_id)
    request = initialize_evidence_collection(case, runtime.case_manager, playbook)

    if request is None:
        return 0

    while request is not None:
        for line in format_evidence_request(request).splitlines():
            output_writer(line)
        output_writer(f"(paste output; type {END_MARKER} on its own line to finish)")

        raw_text = read_multiline_paste(input_provider)
        case = runtime.case_manager.load_case(case_id)
        submit_evidence(case, runtime.case_manager, request.command, raw_text)

        case = runtime.case_manager.load_case(case_id)
        request = get_next_evidence_request(case)
        if request is None:
            output_writer("Evidence collection complete. Next phase: ANALYSIS.")
            break

    return run_analysis(case_id, runtime, output_writer)


def run_analysis(
    case_id: str,
    runtime: RuntimeEngine,
    output_writer: OutputWriter,
) -> int:
    """Run deterministic analysis and print findings."""
    summary = runtime.analyze_case(case_id)
    for line in format_analysis_summary(summary).splitlines():
        output_writer(line)
    return 0


def run_investigation(
    playbook_id: str,
    input_provider: InputProvider,
    output_writer: OutputWriter,
    *,
    plugins_root: Path | None = None,
    engine: RuntimeEngine | None = None,
    collect_evidence: bool = True,
) -> int:
    """Run the intake investigation loop and optional evidence collection.

    Args:
        playbook_id: Cataloged playbook ID (e.g. ``VP-CUBE-0001``).
        input_provider: Callable returning the next user answer.
        output_writer: Callable receiving output lines.
        plugins_root: Optional plugins directory override.
        engine: Optional pre-built runtime engine for tests.
        collect_evidence: When ``True``, continue into evidence collection after intake.

    Returns:
        Process exit code (``0`` on success, ``1`` on playbook error).
    """
    runtime = engine or build_runtime_engine(plugins_root)

    try:
        runtime.start()
        turn = runtime.start_investigation(playbook_id)
    except PlaybookIdNotFoundError:
        output_writer(f"Error: Playbook not found: {playbook_id}")
        return 1

    output_writer("Investigation started")
    write_case_header(turn, output_writer)
    output_writer(format_question(turn))

    while (
        turn.state == InvestigationState.INTAKE
        and turn.next_action_type == "ask_question"
        and turn.question_id
    ):
        answer = input_provider().strip()
        turn = runtime.submit_answer(turn.case_id, turn.question_id, answer)

        if turn.state == InvestigationState.DISCOVERY:
            output_writer("Intake complete. Next phase: DISCOVERY.")
            case = runtime.case_manager.load_case(turn.case_id)
            playbook = runtime.playbook_catalog.get(playbook_id)
            write_intake_summary(case, output_writer, playbook=playbook)
            if collect_evidence:
                return run_evidence_collection(
                    turn.case_id,
                    runtime,
                    playbook_id,
                    input_provider,
                    output_writer,
                )
            return 0

        output_writer(format_question(turn))

    return 0


def cmd_investigate(args: argparse.Namespace) -> int:
    """Handle ``voicepilot investigate <playbook_id>``."""
    return run_investigation(
        args.playbook_id,
        input_provider=lambda: input("> "),
        output_writer=print,
        plugins_root=Path(args.plugins_root) if args.plugins_root else None,
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the VoicePilot argument parser."""
    parser = argparse.ArgumentParser(
        prog="voicepilot",
        description="VoicePilot — AI Voice Operations Engineer CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    investigate = subparsers.add_parser(
        "investigate",
        help="Start an investigation from a playbook ID",
    )
    investigate.add_argument(
        "playbook_id",
        help="Cataloged playbook ID (e.g. VP-CUBE-0001)",
    )
    investigate.add_argument(
        "--plugins-root",
        default=None,
        help="Override plugins directory (default: repo plugins/)",
    )
    investigate.set_defaults(func=cmd_investigate)

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
