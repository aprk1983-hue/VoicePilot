"""VoicePilot CLI v1 — terminal intake investigation."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from domain.enums import InvestigationState
from domain.models import InvestigationTurn
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.exceptions import PlaybookIdNotFoundError
from runtime.runtime_engine import RuntimeEngine
from shared.config import RuntimeConfig

REPO_ROOT = Path(__file__).resolve().parents[1]

InputProvider = Callable[[], str]
OutputWriter = Callable[[str], None]


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


def run_investigation(
    playbook_id: str,
    input_provider: InputProvider,
    output_writer: OutputWriter,
    *,
    plugins_root: Path | None = None,
    engine: RuntimeEngine | None = None,
) -> int:
    """Run the intake investigation loop.

    Args:
        playbook_id: Cataloged playbook ID (e.g. ``VP-CUBE-0001``).
        input_provider: Callable returning the next user answer.
        output_writer: Callable receiving output lines.
        plugins_root: Optional plugins directory override.
        engine: Optional pre-built runtime engine for tests.

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
