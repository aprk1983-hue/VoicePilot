"""VoicePilot CLI v1 — terminal intake investigation and evidence collection."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path


def bootstrap_import_paths() -> Path:
    """Ensure repo, core, sdk, and plugins roots are importable."""
    repo_root = Path(__file__).resolve().parents[1]
    for path in (
        repo_root,
        repo_root / "core",
        repo_root / "sdk",
        repo_root / "plugins",
    ):
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
    return repo_root


REPO_ROOT = bootstrap_import_paths()

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
from runtime.decision_log_engine import format_decision_timeline
from runtime.exceptions import (
    CaseNotFoundError,
    PlaybookIdNotFoundError,
    QuestionNotFoundError,
    ScenarioNotFoundError,
    UnsupportedPlaybookScenarioError,
)
from runtime.intake_summary import write_intake_summary
from runtime.correlation_engine import format_correlation_summary
from runtime.hypothesis_engine import format_hypothesis_summary
from runtime.learning_engine import format_learning_closure_summary
from runtime.report_engine import format_incident_report
from runtime.recommendation_engine import format_recommendation_summary
from runtime.runtime_engine import RuntimeEngine
from services import VoicePilotService
from services.service_exceptions import ServiceCaseNotFoundError
from runtime.verification_engine import (
    OUTCOME_COMPLETE,
    VerificationResultSubmission,
    format_verification_checklist,
    format_verification_summary,
)
from health.health_engine import HealthEngine
from health.health_models import HealthResult, HealthStatus
from health.health_severity import HealthSeverity
from knowledge import KnowledgeEngine
from model.voice_graph import VoiceObject
from parser.parser_context import ParserContext
from runtime.knowledge_bootstrap import default_knowledge_engine
from runtime.parser_bootstrap import build_default_parser_engine
from discovery.planner_report import format_discovery_plan_markdown
from investigation_quality.quality_report import format_investigation_quality_markdown
from investigation.session_models import InvestigationSessionStatus, SessionActionType
from brain.brain_report import (
    build_investigation_replay,
    format_brain_next_summary,
    format_brain_replay,
    format_brain_session_list,
    format_brain_start_summary,
    format_brain_status,
    format_brain_upload_summary,
)
from brain.brain_exceptions import BrainSessionNotFoundError
from brain.brain_store import (
    BrainSessionStore,
    merge_brain_sessions,
    persist_brain_session,
    restore_brain_session_to_runtime,
)
from engineering_assets import EngineeringAssetNotFoundError
from engineering_knowledge import (
    asset_stats,
    default_engineering_knowledge_library,
    format_asset_details,
    reset_default_engineering_knowledge_engine,
    search_assets,
)
from runtime.intake_flow import build_investigation_turn, get_next_question_for_phase
from runtime.scenario_runner import (
    default_scenarios_root,
    format_scenario_markdown_report,
    format_scenario_summary,
    format_summary_table,
    resolve_scenario_dirs,
    run_playbook_scenarios,
    build_scenario_runtime_engine,
    run_scenario_for_comparison,
    resolve_comparison_after_scenario,
    run_scenario_to_correlation,
)
from change_package.change_report import format_change_package_markdown
from reporting.report_formatter import terminal_summary
from investigation_compare.compare_report import format_comparison_markdown
from investigation_compare.compare_models import READ_ONLY_NOTICE as COMPARE_READ_ONLY_NOTICE
from reporting.report_models import READ_ONLY_NOTICE, ReportType
from shared.config import RuntimeConfig
from topology.topology_builder import TopologyBuilder

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
        submit_evidence(
            case,
            runtime.case_manager,
            request.command,
            raw_text,
            decision_log=runtime.decision_log_engine,
        )

        case = runtime.case_manager.load_case(case_id)
        request = get_next_evidence_request(case)
        if request is None:
            output_writer("Evidence collection complete. Next phase: ANALYSIS.")
            break

    return run_analysis(case_id, runtime, input_provider, output_writer)


def run_analysis(
    case_id: str,
    runtime: RuntimeEngine,
    input_provider: InputProvider,
    output_writer: OutputWriter,
) -> int:
    """Run deterministic analysis and print findings."""
    summary = runtime.analyze_case(case_id)
    for line in format_analysis_summary(summary).splitlines():
        output_writer(line)
    return run_hypothesis_generation(case_id, runtime, input_provider, output_writer)


def run_hypothesis_generation(
    case_id: str,
    runtime: RuntimeEngine,
    input_provider: InputProvider,
    output_writer: OutputWriter,
) -> int:
    """Generate ranked hypotheses and print the summary."""
    summary = runtime.generate_hypotheses(case_id)
    for line in format_hypothesis_summary(summary).splitlines():
        output_writer(line)
    return run_correlation(case_id, runtime, input_provider, output_writer)


def run_correlation(
    case_id: str,
    runtime: RuntimeEngine,
    input_provider: InputProvider,
    output_writer: OutputWriter,
) -> int:
    """Correlate findings and print the summary."""
    summary = runtime.correlate_case(case_id)
    for line in format_correlation_summary(summary).splitlines():
        output_writer(line)
    return run_recommendation_generation(case_id, runtime, input_provider, output_writer)


def run_recommendation_generation(
    case_id: str,
    runtime: RuntimeEngine,
    input_provider: InputProvider,
    output_writer: OutputWriter,
) -> int:
    """Generate recommendation from top hypothesis and print the summary."""
    summary = runtime.generate_recommendation(case_id)
    for line in format_recommendation_summary(summary).splitlines():
        output_writer(line)

    case = runtime.case_manager.load_case(case_id)
    if case.status == InvestigationState.RESOLUTION:
        return run_verification(case_id, runtime, input_provider, output_writer)
    return 0


def run_verification(
    case_id: str,
    runtime: RuntimeEngine,
    input_provider: InputProvider,
    output_writer: OutputWriter,
) -> int:
    """Present verification checklist and collect engineer results."""
    checklist = runtime.generate_verification_checklist(case_id)
    if checklist is None:
        return 0

    for line in format_verification_checklist(checklist).splitlines():
        output_writer(line)

    submissions: list[VerificationResultSubmission] = []
    for item in checklist.items:
        output_writer(f"Step {item.step_number}: {item.description}")
        output_writer("Result (passed/failed/not_tested):")
        status = input_provider().strip()
        output_writer("Notes (optional):")
        notes = input_provider().strip()
        submissions.append(
            VerificationResultSubmission(
                verification_id=item.verification_id,
                status=status,
                notes=notes,
            )
        )

    summary = runtime.submit_verification(case_id, submissions)
    output_writer(format_verification_summary(summary))

    if summary.outcome == OUTCOME_COMPLETE:
        return run_case_closure(case_id, runtime, output_writer)
    return 0


def run_case_closure(
    case_id: str,
    runtime: RuntimeEngine,
    output_writer: OutputWriter,
) -> int:
    """Create learning record, close the case, and print the incident report."""
    closure = runtime.close_case_with_learning(case_id)
    for line in format_learning_closure_summary(closure).splitlines():
        output_writer(line)

    report = runtime.generate_report(case_id)
    output_writer("")
    output_writer("=== Incident Report ===")
    for line in format_incident_report(report).splitlines():
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
    """Run an interactive investigation session through the session engine."""
    runtime = engine or build_runtime_engine(plugins_root)

    try:
        runtime.start()
        session = runtime.start_investigation_session(playbook_id)
    except PlaybookIdNotFoundError:
        output_writer(f"Error: Playbook not found: {playbook_id}")
        return 1

    output_writer("Investigation started")
    output_writer(f"Session:  {session.session_id}")
    case = runtime.case_manager.load_case(session.case_id)
    question = get_next_question_for_phase(case, InvestigationState.INTAKE)
    turn = build_investigation_turn(case, question)
    write_case_header(turn, output_writer)

    while session.status not in {
        InvestigationSessionStatus.COMPLETED,
        InvestigationSessionStatus.FAILED,
    }:
        if (
            not collect_evidence
            and session.current_action == SessionActionType.DISCOVERY_PLANNING
        ):
            break

        if session.status == InvestigationSessionStatus.AWAITING_INPUT:
            result = runtime.continue_investigation_session(
                session.session_id,
                input_provider=input_provider,
            )
        else:
            result = runtime.continue_investigation_session(session.session_id)

        for message in result.messages:
            if message:
                for line in message.splitlines():
                    output_writer(line)
        session = result.session

    return 0


def run_session_status(
    session_id: str,
    output_writer: OutputWriter,
    *,
    plugins_root: Path | None = None,
    engine: RuntimeEngine | None = None,
) -> int:
    """Print the current status of an investigation session."""
    runtime = engine or build_runtime_engine(plugins_root)
    runtime.start()
    try:
        output_writer(runtime.format_investigation_session_status(session_id))
    except SessionNotFoundError:
        output_writer(f"Error: Session not found: {session_id}")
        return 1
    return 0


def run_continue_session(
    session_id: str,
    input_provider: InputProvider,
    output_writer: OutputWriter,
    *,
    plugins_root: Path | None = None,
    engine: RuntimeEngine | None = None,
) -> int:
    """Continue an investigation session from the next input boundary."""
    runtime = engine or build_runtime_engine(plugins_root)
    runtime.start()
    try:
        runtime.get_investigation_session(session_id)
    except SessionNotFoundError:
        output_writer(f"Error: Session not found: {session_id}")
        return 1

    session = runtime.get_investigation_session(session_id)
    while session.status not in {
        InvestigationSessionStatus.COMPLETED,
        InvestigationSessionStatus.FAILED,
    }:
        if session.status == InvestigationSessionStatus.AWAITING_INPUT:
            result = runtime.continue_investigation_session(
                session_id,
                input_provider=input_provider,
            )
        else:
            result = runtime.continue_investigation_session(session_id)

        for message in result.messages:
            if message:
                for line in message.splitlines():
                    output_writer(line)
        session = result.session

        if session.status == InvestigationSessionStatus.AWAITING_INPUT:
            break

    return 0


def run_brain_start(
    playbook_id: str,
    output_writer: OutputWriter,
    *,
    plugins_root: Path | None = None,
    engine: RuntimeEngine | None = None,
    session_store: BrainSessionStore | None = None,
) -> int:
    """Start a VoicePilot Brain session for a playbook."""
    runtime = engine or build_runtime_engine(plugins_root)
    store = session_store or BrainSessionStore()
    runtime.start()
    try:
        session = runtime.start_brain_session(playbook_id)
    except PlaybookIdNotFoundError:
        output_writer(f"Error: Playbook not found: {playbook_id}")
        return 1

    persist_brain_session(runtime, store, session.session_id)
    context = runtime.brain_engine.build_context(session.session_id)
    output_writer(format_brain_start_summary(session, context))
    return 0


def run_brain_upload(
    session_id: str,
    command: str,
    file_path: Path,
    output_writer: OutputWriter,
    *,
    plugins_root: Path | None = None,
    engine: RuntimeEngine | None = None,
    session_store: BrainSessionStore | None = None,
) -> int:
    """Upload CLI evidence for a Brain session."""
    runtime = engine or build_runtime_engine(plugins_root)
    store = session_store or BrainSessionStore()
    runtime.start()

    if not file_path.is_file():
        output_writer(f"Error: Evidence file not found: {file_path}")
        return 1

    try:
        restore_brain_session_to_runtime(runtime, store, session_id)
        raw_text = file_path.read_text(encoding="utf-8")
        session = runtime.upload_brain_evidence(session_id, command, raw_text)
    except BrainSessionNotFoundError:
        output_writer(f"Error: Brain session not found: {session_id}")
        return 1

    persist_brain_session(runtime, store, session_id)
    output_writer(format_brain_upload_summary(session, command=command, file_path=str(file_path)))
    return 0


def run_brain_next(
    session_id: str,
    output_writer: OutputWriter,
    *,
    plugins_root: Path | None = None,
    engine: RuntimeEngine | None = None,
    session_store: BrainSessionStore | None = None,
) -> int:
    """Advance a Brain session through the orchestrated pipeline."""
    runtime = engine or build_runtime_engine(plugins_root)
    store = session_store or BrainSessionStore()
    runtime.start()

    try:
        restore_brain_session_to_runtime(runtime, store, session_id)
        result = runtime.next_brain_session(session_id)
        session = result.session
        context = runtime.brain_engine.build_context(session_id)
    except BrainSessionNotFoundError:
        output_writer(f"Error: Brain session not found: {session_id}")
        return 1

    persist_brain_session(runtime, store, session_id)
    output_writer(format_brain_next_summary(session, context, result))
    return 0


def run_brain_status(
    session_id: str,
    output_writer: OutputWriter,
    *,
    plugins_root: Path | None = None,
    engine: RuntimeEngine | None = None,
    session_store: BrainSessionStore | None = None,
) -> int:
    """Print Brain session status."""
    runtime = engine or build_runtime_engine(plugins_root)
    store = session_store or BrainSessionStore()
    runtime.start()
    try:
        restore_brain_session_to_runtime(runtime, store, session_id)
        session = runtime.get_brain_session(session_id)
        context = runtime.brain_engine.build_context(session_id)
    except BrainSessionNotFoundError:
        output_writer(f"Error: Brain session not found: {session_id}")
        return 1

    output_writer(format_brain_status(session, context))
    return 0


def run_brain_replay(
    session_id: str,
    output_writer: OutputWriter,
    *,
    plugins_root: Path | None = None,
    engine: RuntimeEngine | None = None,
    session_store: BrainSessionStore | None = None,
) -> int:
    """Print Brain investigation replay."""
    runtime = engine or build_runtime_engine(plugins_root)
    store = session_store or BrainSessionStore()
    runtime.start()
    try:
        restore_brain_session_to_runtime(runtime, store, session_id)
        session = runtime.get_brain_session(session_id)
        context = runtime.brain_engine.build_context(session_id)
    except BrainSessionNotFoundError:
        output_writer(f"Error: Brain session not found: {session_id}")
        return 1

    output_writer(format_brain_replay(session, context))
    return 0


def run_brain_list(
    output_writer: OutputWriter,
    *,
    plugins_root: Path | None = None,
    engine: RuntimeEngine | None = None,
    session_store: BrainSessionStore | None = None,
) -> int:
    """List registered Brain sessions."""
    runtime = engine or build_runtime_engine(plugins_root)
    store = session_store or BrainSessionStore()
    runtime.start()
    sessions = merge_brain_sessions(runtime.list_brain_sessions(), store.list_sessions())
    output_writer(format_brain_session_list(sessions))
    return 0


def cmd_brain_start(args: argparse.Namespace) -> int:
    """Handle ``voicepilot brain start <playbook_id>``."""
    return run_brain_start(
        args.playbook_id,
        print,
        plugins_root=Path(args.plugins_root) if args.plugins_root else None,
    )


def cmd_brain_status(args: argparse.Namespace) -> int:
    """Handle ``voicepilot brain status <session_id>``."""
    return run_brain_status(
        args.session_id,
        print,
        plugins_root=Path(args.plugins_root) if args.plugins_root else None,
    )


def cmd_brain_replay(args: argparse.Namespace) -> int:
    """Handle ``voicepilot brain replay <session_id>``."""
    return run_brain_replay(
        args.session_id,
        print,
        plugins_root=Path(args.plugins_root) if args.plugins_root else None,
    )


def cmd_brain_list(args: argparse.Namespace) -> int:
    """Handle ``voicepilot brain list``."""
    return run_brain_list(
        print,
        plugins_root=Path(args.plugins_root) if args.plugins_root else None,
    )


def cmd_brain_upload(args: argparse.Namespace) -> int:
    """Handle ``voicepilot brain upload <session_id> <command> <file>``."""
    return run_brain_upload(
        args.session_id,
        args.command,
        Path(args.file),
        print,
        plugins_root=Path(args.plugins_root) if args.plugins_root else None,
    )


def cmd_brain_next(args: argparse.Namespace) -> int:
    """Handle ``voicepilot brain next <session_id>``."""
    return run_brain_next(
        args.session_id,
        print,
        plugins_root=Path(args.plugins_root) if args.plugins_root else None,
    )


def run_assets_search(
    query: str,
    output_writer: OutputWriter,
    *,
    library=None,
) -> int:
    """Search bundled engineering knowledge assets."""
    active_library = library or default_engineering_knowledge_library()
    results = search_assets(active_library, query)
    output_writer(f"Engineering Asset Search — {query!r}")
    output_writer("")
    if not results:
        output_writer("_No assets matched._")
        return 0
    for asset in results:
        output_writer(
            f"- {asset.asset_id} | {asset.asset_type.value} | {asset.title} | {asset.vendor}/{asset.product}"
        )
    return 0


def run_assets_show(
    asset_id: str,
    output_writer: OutputWriter,
    *,
    library=None,
) -> int:
    """Show one engineering knowledge asset."""
    active_library = library or default_engineering_knowledge_library()
    try:
        asset = active_library.asset_registry.get(asset_id)
    except EngineeringAssetNotFoundError:
        output_writer(f"Error: Asset not found: {asset_id}")
        return 1
    output_writer(format_asset_details(asset))
    return 0


def run_assets_stats(
    output_writer: OutputWriter,
    *,
    library=None,
) -> int:
    """Show engineering knowledge library statistics."""
    active_library = library or default_engineering_knowledge_library()
    stats = asset_stats(active_library)
    output_writer("Engineering Knowledge Library Stats")
    output_writer("")
    output_writer(f"Total Assets:            {stats['total_assets']}")
    output_writer(f"Knowledge Entries:       {stats['total_knowledge_entries']}")
    output_writer(f"Relationships:           {stats['total_relationships']}")
    output_writer("")
    output_writer("Asset Types:")
    for asset_type, count in sorted(stats["type_counts"].items()):
        output_writer(f"  {asset_type}: {count}")
    output_writer("")
    output_writer("Vendors:")
    for vendor, count in sorted(stats["vendor_counts"].items()):
        output_writer(f"  {vendor}: {count}")
    return 0


def cmd_assets_search(args: argparse.Namespace) -> int:
    """Handle ``voicepilot assets search <query>``."""
    return run_assets_search(args.query, print)


def cmd_assets_show(args: argparse.Namespace) -> int:
    """Handle ``voicepilot assets show <asset_id>``."""
    return run_assets_show(args.asset_id, print)


def cmd_assets_stats(args: argparse.Namespace) -> int:
    """Handle ``voicepilot assets stats``."""
    return run_assets_stats(print)


def cmd_decisions(args: argparse.Namespace) -> int:
    """Handle ``voicepilot decisions <case_id>``."""
    runtime = build_runtime_engine(
        Path(args.plugins_root) if args.plugins_root else None
    )
    runtime.start()
    try:
        case = runtime.case_manager.load_case(args.case_id)
    except CaseNotFoundError:
        print(f"Error: Case not found: {args.case_id}")
        return 1

    print(format_decision_timeline(case.decision_log))
    return 0


def cmd_investigate(args: argparse.Namespace) -> int:
    """Handle ``voicepilot investigate <playbook_id>``."""
    return run_investigation(
        args.playbook_id,
        input_provider=lambda: input("> "),
        output_writer=print,
        plugins_root=Path(args.plugins_root) if args.plugins_root else None,
    )


def cmd_status(args: argparse.Namespace) -> int:
    """Handle ``voicepilot status <session_id>``."""
    return run_session_status(
        args.session_id,
        print,
        plugins_root=Path(args.plugins_root) if args.plugins_root else None,
    )


def cmd_continue(args: argparse.Namespace) -> int:
    """Handle ``voicepilot continue <session_id>``."""
    return run_continue_session(
        args.session_id,
        input_provider=lambda: input("> "),
        output_writer=print,
        plugins_root=Path(args.plugins_root) if args.plugins_root else None,
    )


def default_samples_dir() -> Path:
    """Return the default parser sample evidence directory."""
    return REPO_ROOT / "examples" / "sample_evidence" / "parser"


def resolve_samples_dir(path: str | None) -> Path | None:
    """Resolve the samples directory from CLI input or default."""
    if path:
        resolved = Path(path)
        return resolved if resolved.is_dir() else None
    default = default_samples_dir()
    return default if default.is_dir() else None


def collect_voice_objects_from_samples(
    samples_dir: Path,
    *,
    parser_engine=None,
) -> tuple[VoiceObject, ...]:
    """Parse sample CLI files and collect canonical voice objects."""
    engine = parser_engine or build_default_parser_engine()
    if engine is None:
        return ()

    parsers = [
        engine.registry.get_parser("cisco", command)
        for command in engine.registry.list_commands("cisco")
    ]
    voice_objects: list[VoiceObject] = []

    for index, sample_path in enumerate(sorted(samples_dir.glob("*.txt")), start=1):
        raw_text = sample_path.read_text(encoding="utf-8")
        matched_parser = next(
            (parser for parser in parsers if parser.detect(raw_text)),
            None,
        )
        if matched_parser is None:
            continue

        context = ParserContext(
            vendor="cisco",
            case_id="CASE-HEALTH-CLI",
            evidence_id=f"EVD-health-{index:03d}",
            device_id="DEV-cube-01",
            platform="CUBE",
            ios_version="17.9.1",
            hostname="cube-edge-01",
            metadata={"sample_file": sample_path.name},
        )
        result = engine.parse(raw_text, context, command=matched_parser.command)
        voice_objects.extend(result.voice_objects)

    return tuple(voice_objects)


def format_health_cli_output(health_report, knowledge_report) -> str:
    """Format health and knowledge evaluation for terminal output."""
    status = _overall_health_status(health_report.fail_count, health_report.warn_count)
    lines = [
        "VoicePilot Health Assessment",
        "",
        f"Score: {health_report.overall_score}/100",
        f"Status: {status}",
        (
            "Counts: "
            f"PASS {health_report.pass_count} | "
            f"WARN {health_report.warn_count} | "
            f"FAIL {health_report.fail_count}"
        ),
        "",
        "Top Findings:",
    ]

    top_findings = _top_health_findings(health_report.results)
    if top_findings:
        for finding in top_findings:
            lines.append(
                f"- {finding.severity.value.upper()} {finding.status.value.upper()} — {finding.message}"
            )
            if finding.recommendation:
                lines.append(f"  Recommendation: {finding.recommendation}")
    else:
        lines.append("_No health findings recorded._")

    lines.extend(["", "Matched Knowledge:"])
    if knowledge_report.matched_packs:
        for match in knowledge_report.matched_packs:
            lines.append(f"- {match.pack_id} — {match.title}")
            if match.recommendations:
                lines.append(f"  Recommendation: {match.recommendations[0]}")
    else:
        lines.append("_No knowledge packs matched._")

    return "\n".join(lines)


def format_health_markdown_report(
    health_report,
    knowledge_report,
    *,
    samples_dir: Path,
    generated_at: datetime | None = None,
) -> str:
    """Format health and knowledge evaluation as a Markdown report."""
    status = _overall_health_status(health_report.fail_count, health_report.warn_count)
    timestamp = (generated_at or datetime.now(timezone.utc)).isoformat()
    lines = [
        "# VoicePilot Health Assessment",
        "",
        f"- **Score:** {health_report.overall_score}/100",
        f"- **Status:** {status}",
        (
            "- **Counts:** "
            f"PASS {health_report.pass_count} | "
            f"WARN {health_report.warn_count} | "
            f"FAIL {health_report.fail_count}"
        ),
        "",
        "## Top Findings",
        "",
    ]

    top_findings = _top_health_findings(health_report.results)
    if top_findings:
        for finding in top_findings:
            lines.append(
                f"- {finding.severity.value.upper()} {finding.status.value.upper()} — {finding.message}"
            )
            if finding.recommendation:
                lines.append(f"  - Recommendation: {finding.recommendation}")
    else:
        lines.append("_No health findings recorded._")

    lines.extend(["", "## Matched Knowledge", ""])
    if knowledge_report.matched_packs:
        for match in knowledge_report.matched_packs:
            lines.append(f"- **{match.pack_id}** — {match.title}")
            if match.recommendations:
                lines.append(f"  - Recommendation: {match.recommendations[0]}")
    else:
        lines.append("_No knowledge packs matched._")

    lines.extend(
        [
            "",
            "## Report Metadata",
            "",
            f"- **Generated:** {timestamp}",
            f"- **Samples:** {samples_dir}",
        ]
    )
    return "\n".join(lines)


def run_health_assessment(
    samples_dir: Path | None,
    output_writer: OutputWriter,
    *,
    parser_engine=None,
    health_engine: HealthEngine | None = None,
    knowledge_engine: KnowledgeEngine | None = None,
    output_path: Path | None = None,
    generated_at: datetime | None = None,
) -> int:
    """Run health and knowledge assessment against parser sample evidence."""
    if samples_dir is None or not samples_dir.is_dir():
        output_writer("Error: Sample evidence directory not found.")
        return 1

    engine = parser_engine or build_default_parser_engine()
    if engine is None:
        output_writer("Error: Cisco parser pack not available.")
        return 1

    voice_objects = collect_voice_objects_from_samples(
        samples_dir,
        parser_engine=engine,
    )
    if not voice_objects:
        output_writer("Error: No voice objects parsed from sample evidence.")
        return 1

    topology = TopologyBuilder().build(list(voice_objects))
    health_report = (health_engine or HealthEngine()).evaluate_topology(topology)
    knowledge_report = (knowledge_engine or default_knowledge_engine()).evaluate_topology(
        topology
    )

    for line in format_health_cli_output(health_report, knowledge_report).splitlines():
        output_writer(line)

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        markdown = format_health_markdown_report(
            health_report,
            knowledge_report,
            samples_dir=samples_dir,
            generated_at=generated_at,
        )
        output_path.write_text(markdown, encoding="utf-8")

    return 0


def cmd_health(args: argparse.Namespace) -> int:
    """Handle ``voicepilot health``."""
    samples_dir = resolve_samples_dir(args.samples)
    output_path = Path(args.output) if args.output else None
    return run_health_assessment(samples_dir, print, output_path=output_path)


def run_change_package_case(
    case_id: str,
    output_writer: OutputWriter,
    *,
    plugins_root: Path | None = None,
    output_path: Path | None = None,
) -> int:
    """Generate a read-only engineering change package for a case."""
    runtime = build_runtime_engine(plugins_root)
    runtime.start()
    try:
        package = runtime.generate_change_package(case_id)
        markdown = format_change_package_markdown(package)
        output_writer(markdown)
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown, encoding="utf-8")
            output_writer("")
            output_writer(f"Change package saved: {output_path}")
        return 0
    except CaseNotFoundError:
        output_writer(f"Error: Case not found: {case_id}")
        return 1
    finally:
        runtime.shutdown()


def run_change_package_scenario(
    playbook_id: str,
    output_writer: OutputWriter,
    *,
    scenario_id: str | None = None,
    output_path: Path | None = None,
    repo_root: Path | None = None,
) -> int:
    """Run a scenario through recommendation and generate a change package."""
    root = repo_root or REPO_ROOT
    try:
        scenario_dirs = resolve_scenario_dirs(
            playbook_id,
            scenario_id=scenario_id,
            repo_root=root,
        )
    except UnsupportedPlaybookScenarioError as exc:
        output_writer(str(exc))
        return 1
    except ScenarioNotFoundError as exc:
        output_writer(str(exc))
        return 1

    if not scenario_dirs:
        output_writer(
            f"No scenarios found under {default_scenarios_root(playbook_id, repo_root=root)}"
        )
        return 1
    if scenario_id is None and len(scenario_dirs) > 1:
        output_writer("Error: specify --scenario when multiple scenarios are available.")
        return 1

    scenario_dir = scenario_dirs[0]
    runtime, case_id = run_scenario_to_correlation(scenario_dir, playbook_id=playbook_id)
    try:
        runtime.generate_recommendation(case_id)
        package = runtime.generate_change_package(case_id)
        markdown = format_change_package_markdown(package)
        output_writer(markdown)
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown, encoding="utf-8")
            output_writer("")
            output_writer(f"Change package saved: {output_path}")
        return 0
    finally:
        runtime.shutdown()


def cmd_change_package(args: argparse.Namespace) -> int:
    """Handle ``voicepilot change-package <case_id>``."""
    plugins_root = Path(args.plugins_root) if args.plugins_root else None
    output_path = Path(args.output) if args.output else None
    return run_change_package_case(
        args.case_id,
        print,
        plugins_root=plugins_root,
        output_path=output_path,
    )


def cmd_change_package_scenario(args: argparse.Namespace) -> int:
    """Handle ``voicepilot change-package-scenario <playbook_id>``."""
    output_path = Path(args.output) if args.output else None
    return run_change_package_scenario(
        args.playbook_id,
        print,
        scenario_id=args.scenario,
        output_path=output_path,
    )


def _parse_report_type(value: str) -> ReportType:
    normalized = value.strip().upper()
    try:
        return ReportType(normalized)
    except ValueError as exc:
        valid = ", ".join(item.value.lower() for item in ReportType)
        raise argparse.ArgumentTypeError(f"Invalid report type {value!r}. Choose one of: {valid}") from exc


def run_report_case(
    case_id: str,
    output_writer: OutputWriter,
    *,
    report_type: ReportType = ReportType.ENGINEERING,
    plugins_root: Path | None = None,
    output_path: Path | None = None,
) -> int:
    """Generate an enterprise report for a case."""
    runtime = build_runtime_engine(plugins_root)
    runtime.start()
    try:
        report = runtime.generate_report(case_id, report_type)
        output_writer(terminal_summary(report))
        output_writer("")
        output_writer(report.markdown)
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report.markdown, encoding="utf-8")
            output_writer("")
            output_writer(f"Report saved: {output_path}")
        return 0
    except CaseNotFoundError:
        output_writer(f"Error: Case not found: {case_id}")
        return 1
    finally:
        runtime.shutdown()


def run_report_scenario(
    playbook_id: str,
    output_writer: OutputWriter,
    *,
    scenario_id: str,
    report_type: ReportType = ReportType.ENGINEERING,
    output_path: Path | None = None,
    repo_root: Path | None = None,
) -> int:
    """Run a scenario through recommendation and generate an enterprise report."""
    root = repo_root or REPO_ROOT
    try:
        scenario_dirs = resolve_scenario_dirs(
            playbook_id,
            scenario_id=scenario_id,
            repo_root=root,
        )
    except UnsupportedPlaybookScenarioError as exc:
        output_writer(str(exc))
        return 1
    except ScenarioNotFoundError as exc:
        output_writer(str(exc))
        return 1

    if not scenario_dirs:
        output_writer(
            f"No scenarios found under {default_scenarios_root(playbook_id, repo_root=root)}"
        )
        return 1

    scenario_dir = scenario_dirs[0]
    runtime, case_id = run_scenario_to_correlation(scenario_dir, playbook_id=playbook_id)
    try:
        runtime.generate_recommendation(case_id)
        report = runtime.generate_report(case_id, report_type)
        output_writer(terminal_summary(report))
        output_writer("")
        output_writer(report.markdown)
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report.markdown, encoding="utf-8")
            output_writer("")
            output_writer(f"Report saved: {output_path}")
        return 0
    finally:
        runtime.shutdown()


def cmd_report(args: argparse.Namespace) -> int:
    """Handle ``voicepilot report <case_id>``."""
    plugins_root = Path(args.plugins_root) if args.plugins_root else None
    output_path = Path(args.output) if args.output else None
    return run_report_case(
        args.case_id,
        print,
        report_type=args.type,
        plugins_root=plugins_root,
        output_path=output_path,
    )


def cmd_report_scenario(args: argparse.Namespace) -> int:
    """Handle ``voicepilot report-scenario <playbook_id>``."""
    output_path = Path(args.output) if args.output else None
    return run_report_scenario(
        args.playbook_id,
        print,
        scenario_id=args.scenario,
        report_type=args.type,
        output_path=output_path,
    )


def run_compare_cases(
    before_case_id: str,
    after_case_id: str,
    output_writer: OutputWriter,
    *,
    plugins_root: Path | None = None,
    output_path: Path | None = None,
) -> int:
    """Compare two in-memory cases and print a comparison report."""
    runtime = build_runtime_engine(plugins_root)
    runtime.start()
    try:
        comparison = runtime.compare_cases(before_case_id, after_case_id)
        markdown = format_comparison_markdown(comparison)
        output_writer(f"Comparison ID: {comparison.comparison_id}")
        output_writer(f"Status:        {comparison.status.value}")
        output_writer(f"Summary:       {comparison.summary}")
        output_writer("")
        output_writer(markdown)
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown, encoding="utf-8")
            output_writer("")
            output_writer(f"Comparison saved: {output_path}")
        return 0
    except CaseNotFoundError as exc:
        output_writer(f"Error: Case not found: {exc}")
        return 1
    finally:
        runtime.shutdown()


def run_compare_scenarios(
    playbook_id: str,
    before_scenario: str,
    output_writer: OutputWriter,
    *,
    after_scenario: str | None = None,
    output_path: Path | None = None,
    repo_root: Path | None = None,
) -> int:
    """Run before/after scenarios and compare investigation outputs."""
    root = repo_root or REPO_ROOT
    try:
        after = resolve_comparison_after_scenario(before_scenario, after_scenario)
        before_dirs = resolve_scenario_dirs(
            playbook_id,
            scenario_id=before_scenario,
            repo_root=root,
        )
        after_dirs = resolve_scenario_dirs(
            playbook_id,
            scenario_id=after,
            repo_root=root,
        )
    except UnsupportedPlaybookScenarioError as exc:
        output_writer(str(exc))
        return 1
    except ScenarioNotFoundError as exc:
        output_writer(str(exc))
        return 1
    except ValueError as exc:
        output_writer(str(exc))
        return 1

    runtime = build_scenario_runtime_engine()
    try:
        _, before_case_id = run_scenario_for_comparison(
            before_dirs[0],
            playbook_id=playbook_id,
            runtime=runtime,
        )
        _, after_case_id = run_scenario_for_comparison(
            after_dirs[0],
            playbook_id=playbook_id,
            runtime=runtime,
        )
        comparison = runtime.compare_cases(before_case_id, after_case_id)
        markdown = format_comparison_markdown(comparison)
        output_writer(f"Comparison ID: {comparison.comparison_id}")
        output_writer(f"Status:        {comparison.status.value}")
        output_writer(f"Summary:       {comparison.summary}")
        output_writer("")
        output_writer(markdown)
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown, encoding="utf-8")
            output_writer("")
            output_writer(f"Comparison saved: {output_path}")
        return 0
    finally:
        runtime.shutdown()


def cmd_compare(args: argparse.Namespace) -> int:
    """Handle ``voicepilot compare <before_case> <after_case>``."""
    plugins_root = Path(args.plugins_root) if args.plugins_root else None
    output_path = Path(args.output) if args.output else None
    return run_compare_cases(
        args.before_case_id,
        args.after_case_id,
        print,
        plugins_root=plugins_root,
        output_path=output_path,
    )


def cmd_compare_scenarios(args: argparse.Namespace) -> int:
    """Handle ``voicepilot compare-scenarios <playbook_id> <before> [after]``."""
    output_path = Path(args.output) if args.output else None
    after_scenario = args.after_scenario if hasattr(args, "after_scenario") else None
    return run_compare_scenarios(
        args.playbook_id,
        args.before_scenario,
        print,
        after_scenario=getattr(args, "after_scenario", None),
        output_path=output_path,
    )


def run_scenario_assessment(
    playbook_id: str,
    output_writer: OutputWriter,
    *,
    scenario_id: str | None = None,
    scenarios_root: Path | None = None,
    output_path: Path | None = None,
    generated_at: datetime | None = None,
    repo_root: Path | None = None,
    include_discovery: bool = False,
    include_quality: bool = False,
    include_change_package: bool = False,
) -> int:
    """Run scenario regression tests and optionally write a Markdown report."""
    root = repo_root or REPO_ROOT
    try:
        resolved_root = scenarios_root or default_scenarios_root(playbook_id, repo_root=root)
        results = run_playbook_scenarios(
            playbook_id,
            scenario_id=scenario_id,
            scenarios_root=scenarios_root,
            repo_root=root,
        )
    except UnsupportedPlaybookScenarioError as exc:
        output_writer(str(exc))
        return 1
    except ScenarioNotFoundError as exc:
        output_writer(str(exc))
        return 1

    if not results:
        output_writer(f"No scenarios found under {resolved_root}")
        return 1

    output_writer(f"VoicePilot Scenario Regression — {playbook_id}")
    output_writer("")
    for line in format_summary_table(results).splitlines():
        output_writer(line)
    output_writer("")
    output_writer(format_scenario_summary(results))

    if output_path is not None:
        discovery_plan_markdown: str | None = None
        investigation_quality_markdown: str | None = None
        change_package_markdown: str | None = None
        if (
            (include_discovery or include_quality or include_change_package)
            and scenario_id is not None
        ):
            scenario_dirs = resolve_scenario_dirs(
                playbook_id,
                scenario_id=scenario_id,
                scenarios_root=scenarios_root,
                repo_root=root,
            )
            if scenario_dirs:
                runtime, case_id = run_scenario_to_correlation(scenario_dirs[0])
                try:
                    if include_discovery:
                        plan = runtime.plan_discovery(case_id)
                        discovery_plan_markdown = format_discovery_plan_markdown(plan)
                    if include_quality:
                        quality_report = runtime.evaluate_investigation_quality(case_id)
                        investigation_quality_markdown = format_investigation_quality_markdown(
                            quality_report
                        )
                    if include_change_package:
                        runtime.generate_recommendation(case_id)
                        package = runtime.generate_change_package(case_id)
                        change_package_markdown = format_change_package_markdown(package)
                finally:
                    runtime.shutdown()

        markdown = format_scenario_markdown_report(
            playbook_id,
            results,
            scenarios_root=resolved_root,
            generated_at=generated_at,
            discovery_plan_markdown=discovery_plan_markdown,
            investigation_quality_markdown=investigation_quality_markdown,
            change_package_markdown=change_package_markdown,
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        output_writer("")
        output_writer(f"Scenario report saved: {output_path}")

    failures = [result for result in results if not result.passed]
    return 1 if failures else 0


def cmd_scenarios(args: argparse.Namespace) -> int:
    """Handle ``voicepilot scenarios <playbook_id>``."""
    output_path = Path(args.output) if args.output else None
    return run_scenario_assessment(
        args.playbook_id,
        print,
        scenario_id=args.scenario,
        output_path=output_path,
        include_discovery=args.include_discovery,
        include_quality=args.include_quality,
        include_change_package=args.include_change_package,
    )


def run_plan_scenario(
    playbook_id: str,
    output_writer: OutputWriter,
    *,
    scenario_id: str | None = None,
    repo_root: Path | None = None,
) -> int:
    """Run a scenario through correlation and print a discovery plan."""
    root = repo_root or REPO_ROOT
    try:
        scenario_dirs = resolve_scenario_dirs(
            playbook_id,
            scenario_id=scenario_id,
            repo_root=root,
        )
    except UnsupportedPlaybookScenarioError as exc:
        output_writer(str(exc))
        return 1
    except ScenarioNotFoundError as exc:
        output_writer(str(exc))
        return 1

    if not scenario_dirs:
        output_writer(
            f"No scenarios found under {default_scenarios_root(playbook_id, repo_root=root)}"
        )
        return 1
    if scenario_id is None and len(scenario_dirs) > 1:
        output_writer("Error: specify --scenario when multiple scenarios are available.")
        return 1

    scenario_dir = scenario_dirs[0]
    runtime, case_id = run_scenario_to_correlation(scenario_dir, playbook_id=playbook_id)
    service = VoicePilotService(runtime_engine=runtime)
    try:
        service.plan_discovery(case_id)
        plan = runtime.case_manager.load_case(case_id).discovery_plan
        if plan is None:
            output_writer("Error: Discovery plan not available.")
            return 1
        output_writer(format_discovery_plan_markdown(plan))
        return 0
    finally:
        runtime.shutdown()


def cmd_plan_scenario(args: argparse.Namespace) -> int:
    """Handle ``voicepilot plan-scenario <playbook_id>``."""
    return run_plan_scenario(args.playbook_id, print, scenario_id=args.scenario)


def run_plan_case(
    case_id: str,
    output_writer: OutputWriter,
    *,
    plugins_root: Path | None = None,
) -> int:
    """Generate and print a discovery plan for an in-memory case."""
    runtime = build_runtime_engine(plugins_root)
    runtime.start()
    service = VoicePilotService(runtime_engine=runtime)
    try:
        service.plan_discovery(case_id)
        plan = runtime.case_manager.load_case(case_id).discovery_plan
        if plan is None:
            output_writer(f"Error: Discovery plan not available for case: {case_id}")
            return 1
        output_writer(format_discovery_plan_markdown(plan))
        return 0
    except ServiceCaseNotFoundError:
        output_writer(f"Error: Case not found: {case_id}")
        return 1
    finally:
        runtime.shutdown()


def cmd_plan(args: argparse.Namespace) -> int:
    """Handle ``voicepilot plan <case_id>``."""
    plugins_root = Path(args.plugins_root) if args.plugins_root else None
    return run_plan_case(args.case_id, print, plugins_root=plugins_root)


def run_quality_scenario(
    playbook_id: str,
    output_writer: OutputWriter,
    *,
    scenario_id: str | None = None,
    repo_root: Path | None = None,
) -> int:
    """Run a scenario through correlation and print investigation quality."""
    root = repo_root or REPO_ROOT
    try:
        scenario_dirs = resolve_scenario_dirs(
            playbook_id,
            scenario_id=scenario_id,
            repo_root=root,
        )
    except UnsupportedPlaybookScenarioError as exc:
        output_writer(str(exc))
        return 1
    except ScenarioNotFoundError as exc:
        output_writer(str(exc))
        return 1

    if not scenario_dirs:
        output_writer(
            f"No scenarios found under {default_scenarios_root(playbook_id, repo_root=root)}"
        )
        return 1
    if scenario_id is None and len(scenario_dirs) > 1:
        output_writer("Error: specify --scenario when multiple scenarios are available.")
        return 1

    scenario_dir = scenario_dirs[0]
    runtime, case_id = run_scenario_to_correlation(scenario_dir, playbook_id=playbook_id)
    try:
        report = runtime.evaluate_investigation_quality(case_id)
        output_writer(format_investigation_quality_markdown(report))
        return 0
    finally:
        runtime.shutdown()


def cmd_quality_scenario(args: argparse.Namespace) -> int:
    """Handle ``voicepilot quality-scenario <playbook_id>``."""
    return run_quality_scenario(args.playbook_id, print, scenario_id=args.scenario)


def run_quality_case(
    case_id: str,
    output_writer: OutputWriter,
    *,
    plugins_root: Path | None = None,
) -> int:
    """Evaluate and print investigation quality for an in-memory case."""
    runtime = build_runtime_engine(plugins_root)
    runtime.start()
    try:
        report = runtime.evaluate_investigation_quality(case_id)
    except CaseNotFoundError:
        output_writer(f"Error: Case not found: {case_id}")
        return 1
    else:
        output_writer(format_investigation_quality_markdown(report))
        return 0
    finally:
        runtime.shutdown()


def cmd_quality(args: argparse.Namespace) -> int:
    """Handle ``voicepilot quality <case_id>``."""
    plugins_root = Path(args.plugins_root) if args.plugins_root else None
    return run_quality_case(args.case_id, print, plugins_root=plugins_root)


_HEALTH_SEVERITY_ORDER = {
    HealthSeverity.CRITICAL: 0,
    HealthSeverity.HIGH: 1,
    HealthSeverity.MEDIUM: 2,
    HealthSeverity.LOW: 3,
    HealthSeverity.INFO: 4,
}


def _top_health_findings(results: tuple[HealthResult, ...]) -> tuple[HealthResult, ...]:
    active = [
        result
        for result in results
        if result.status in {HealthStatus.WARN, HealthStatus.FAIL}
    ]
    return tuple(
        sorted(
            active,
            key=lambda result: (_HEALTH_SEVERITY_ORDER[result.severity], result.rule_id),
        )
    )


def _overall_health_status(fail_count: int, warn_count: int) -> str:
    if fail_count > 0:
        return "FAIL"
    if warn_count > 0:
        return "WARN"
    return "PASS"


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

    status = subparsers.add_parser(
        "status",
        help="Show the status of an investigation session",
    )
    status.add_argument(
        "session_id",
        help="Session ID (e.g. SES-abc123)",
    )
    status.add_argument(
        "--plugins-root",
        default=None,
        help="Override plugins directory (default: repo plugins/)",
    )
    status.set_defaults(func=cmd_status)

    continue_cmd = subparsers.add_parser(
        "continue",
        help="Continue an investigation session from the next input boundary",
    )
    continue_cmd.add_argument(
        "session_id",
        help="Session ID (e.g. SES-abc123)",
    )
    continue_cmd.add_argument(
        "--plugins-root",
        default=None,
        help="Override plugins directory (default: repo plugins/)",
    )
    continue_cmd.set_defaults(func=cmd_continue)

    decisions = subparsers.add_parser(
        "decisions",
        help="Print the decision log timeline for a case",
    )
    decisions.add_argument(
        "case_id",
        help="Case ID (e.g. CASE-abc123)",
    )
    decisions.add_argument(
        "--plugins-root",
        default=None,
        help="Override plugins directory (default: repo plugins/)",
    )
    decisions.set_defaults(func=cmd_decisions)

    health = subparsers.add_parser(
        "health",
        help="Assess health and knowledge matches from parser sample evidence",
    )
    health.add_argument(
        "--samples",
        default=None,
        help="Parser sample evidence directory "
        "(default: examples/sample_evidence/parser when present)",
    )
    health.add_argument(
        "--output",
        default=None,
        help="Write Markdown health report to the given file path",
    )
    health.set_defaults(func=cmd_health)

    scenarios = subparsers.add_parser(
        "scenarios",
        help="Run deterministic scenario regression tests for a playbook",
    )
    scenarios.add_argument(
        "playbook_id",
        help="Playbook with scenario pack (e.g. VP-CUBE-0001)",
    )
    scenarios.add_argument(
        "--scenario",
        default=None,
        help="Run only the named scenario folder (e.g. provider_503)",
    )
    scenarios.add_argument(
        "--output",
        default=None,
        help="Write Markdown scenario report to the given file path",
    )
    scenarios.add_argument(
        "--include-discovery",
        action="store_true",
        help="Include discovery plan in Markdown scenario output (requires --scenario)",
    )
    scenarios.add_argument(
        "--include-quality",
        action="store_true",
        help="Include investigation quality in Markdown scenario output (requires --scenario)",
    )
    scenarios.add_argument(
        "--include-change-package",
        action="store_true",
        help="Include engineering change package in Markdown scenario output (requires --scenario)",
    )
    scenarios.set_defaults(func=cmd_scenarios)

    change_package = subparsers.add_parser(
        "change-package",
        help="Generate a read-only engineering change package for a case",
    )
    change_package.add_argument(
        "case_id",
        help="Case ID (e.g. CASE-abc123)",
    )
    change_package.add_argument(
        "--output",
        default=None,
        help="Write Markdown change package to the given file path",
    )
    change_package.add_argument(
        "--plugins-root",
        default=None,
        help="Override plugins directory (default: repo plugins/)",
    )
    change_package.set_defaults(func=cmd_change_package)

    change_package_scenario = subparsers.add_parser(
        "change-package-scenario",
        help="Run a scenario and generate a read-only engineering change package",
    )
    change_package_scenario.add_argument(
        "playbook_id",
        help="Playbook with scenario pack (e.g. VP-CUBE-0001)",
    )
    change_package_scenario.add_argument(
        "--scenario",
        required=True,
        help="Scenario folder to run (e.g. sip_ua_disabled)",
    )
    change_package_scenario.add_argument(
        "--output",
        default=None,
        help="Write Markdown change package to the given file path",
    )
    change_package_scenario.set_defaults(func=cmd_change_package_scenario)

    report = subparsers.add_parser(
        "report",
        help="Generate an audience-specific enterprise report for a case",
    )
    report.add_argument(
        "case_id",
        help="Case ID (e.g. CASE-abc123)",
    )
    report.add_argument(
        "--type",
        type=_parse_report_type,
        default=ReportType.ENGINEERING,
        help="Report type: engineering, executive, customer, cab, operations",
    )
    report.add_argument(
        "--output",
        default=None,
        help="Write Markdown report to the given file path",
    )
    report.add_argument(
        "--plugins-root",
        default=None,
        help="Override plugins directory (default: repo plugins/)",
    )
    report.set_defaults(func=cmd_report)

    report_scenario = subparsers.add_parser(
        "report-scenario",
        help="Run a scenario and generate an audience-specific enterprise report",
    )
    report_scenario.add_argument(
        "playbook_id",
        help="Playbook with scenario pack (e.g. VP-CUBE-0001)",
    )
    report_scenario.add_argument(
        "--scenario",
        required=True,
        help="Scenario folder to run (e.g. sip_ua_disabled)",
    )
    report_scenario.add_argument(
        "--type",
        type=_parse_report_type,
        default=ReportType.ENGINEERING,
        help="Report type: engineering, executive, customer, cab, operations",
    )
    report_scenario.add_argument(
        "--output",
        default=None,
        help="Write Markdown report to the given file path",
    )
    report_scenario.set_defaults(func=cmd_report_scenario)

    compare = subparsers.add_parser(
        "compare",
        help="Compare two investigation cases and produce an improvement report",
    )
    compare.add_argument("before_case_id", help="Before case ID (e.g. CASE-abc123)")
    compare.add_argument("after_case_id", help="After case ID (e.g. CASE-def456)")
    compare.add_argument(
        "--output",
        default=None,
        help="Write Markdown comparison report to the given file path",
    )
    compare.add_argument(
        "--plugins-root",
        default=None,
        help="Override plugins directory (default: repo plugins/)",
    )
    compare.set_defaults(func=cmd_compare)

    compare_scenarios = subparsers.add_parser(
        "compare-scenarios",
        help="Compare before/after VP-CUBE-0001 scenarios",
    )
    compare_scenarios.add_argument(
        "playbook_id",
        help="Playbook with scenario pack (e.g. VP-CUBE-0001)",
    )
    compare_scenarios.add_argument(
        "before_scenario",
        help="Before scenario folder (e.g. sip_ua_disabled)",
    )
    compare_scenarios.add_argument(
        "after_scenario",
        nargs="?",
        default=None,
        help="After scenario folder (default: mapped fixed scenario)",
    )
    compare_scenarios.add_argument(
        "--output",
        default=None,
        help="Write Markdown comparison report to the given file path",
    )
    compare_scenarios.set_defaults(func=cmd_compare_scenarios)

    plan = subparsers.add_parser(
        "plan",
        help="Generate a discovery plan for an in-memory case",
    )
    plan.add_argument(
        "case_id",
        help="Case ID (e.g. CASE-abc123)",
    )
    plan.add_argument(
        "--plugins-root",
        default=None,
        help="Override plugins directory (default: repo plugins/)",
    )
    plan.set_defaults(func=cmd_plan)

    plan_scenario = subparsers.add_parser(
        "plan-scenario",
        help="Run a scenario through correlation and print a discovery plan",
    )
    plan_scenario.add_argument(
        "playbook_id",
        help="Playbook with scenario pack (e.g. VP-CUBE-0001)",
    )
    plan_scenario.add_argument(
        "--scenario",
        default=None,
        help="Scenario folder to run (e.g. provider_503)",
    )
    plan_scenario.set_defaults(func=cmd_plan_scenario)

    quality = subparsers.add_parser(
        "quality",
        help="Evaluate investigation quality for an in-memory case",
    )
    quality.add_argument(
        "case_id",
        help="Case ID (e.g. CASE-abc123)",
    )
    quality.add_argument(
        "--plugins-root",
        default=None,
        help="Override plugins directory (default: repo plugins/)",
    )
    quality.set_defaults(func=cmd_quality)

    quality_scenario = subparsers.add_parser(
        "quality-scenario",
        help="Run a scenario through correlation and print investigation quality",
    )
    quality_scenario.add_argument(
        "playbook_id",
        help="Playbook with scenario pack (e.g. VP-CUBE-0001)",
    )
    quality_scenario.add_argument(
        "--scenario",
        default=None,
        help="Scenario folder to run (e.g. provider_503)",
    )
    quality_scenario.set_defaults(func=cmd_quality_scenario)

    brain = subparsers.add_parser(
        "brain",
        help="VoicePilot Brain orchestration commands",
    )
    brain_sub = brain.add_subparsers(dest="brain_command", required=True)

    brain_start = brain_sub.add_parser(
        "start",
        help="Start a Brain orchestration session for a playbook",
    )
    brain_start.add_argument(
        "playbook_id",
        help="Cataloged playbook ID (e.g. VP-CUBE-0001)",
    )
    brain_start.add_argument(
        "--plugins-root",
        default=None,
        help="Override plugins directory (default: repo plugins/)",
    )
    brain_start.set_defaults(func=cmd_brain_start)

    brain_status = brain_sub.add_parser(
        "status",
        help="Show Brain session status",
    )
    brain_status.add_argument(
        "session_id",
        help="Brain session ID (e.g. BRN-abc123)",
    )
    brain_status.add_argument(
        "--plugins-root",
        default=None,
        help="Override plugins directory (default: repo plugins/)",
    )
    brain_status.set_defaults(func=cmd_brain_status)

    brain_replay = brain_sub.add_parser(
        "replay",
        help="Show Brain investigation replay",
    )
    brain_replay.add_argument(
        "session_id",
        help="Brain session ID (e.g. BRN-abc123)",
    )
    brain_replay.add_argument(
        "--plugins-root",
        default=None,
        help="Override plugins directory (default: repo plugins/)",
    )
    brain_replay.set_defaults(func=cmd_brain_replay)

    brain_list = brain_sub.add_parser(
        "list",
        help="List registered Brain sessions",
    )
    brain_list.add_argument(
        "--plugins-root",
        default=None,
        help="Override plugins directory (default: repo plugins/)",
    )
    brain_list.set_defaults(func=cmd_brain_list)

    brain_upload = brain_sub.add_parser(
        "upload",
        help="Upload CLI evidence for a Brain session",
    )
    brain_upload.add_argument(
        "session_id",
        help="Brain session ID (e.g. BRN-abc123)",
    )
    brain_upload.add_argument(
        "command",
        help='CLI command the evidence belongs to (e.g. "show sip-ua status")',
    )
    brain_upload.add_argument(
        "file",
        help="Path to a text file containing command output",
    )
    brain_upload.add_argument(
        "--plugins-root",
        default=None,
        help="Override plugins directory (default: repo plugins/)",
    )
    brain_upload.set_defaults(func=cmd_brain_upload)

    brain_next = brain_sub.add_parser(
        "next",
        help="Advance a Brain session through the orchestrated pipeline",
    )
    brain_next.add_argument(
        "session_id",
        help="Brain session ID (e.g. BRN-abc123)",
    )
    brain_next.add_argument(
        "--plugins-root",
        default=None,
        help="Override plugins directory (default: repo plugins/)",
    )
    brain_next.set_defaults(func=cmd_brain_next)

    assets = subparsers.add_parser(
        "assets",
        help="Search and inspect engineering knowledge assets",
    )
    assets_sub = assets.add_subparsers(dest="assets_command", required=True)

    assets_search = assets_sub.add_parser(
        "search",
        help="Search engineering knowledge assets",
    )
    assets_search.add_argument(
        "query",
        help='Search text (e.g. "sip-ua")',
    )
    assets_search.set_defaults(func=cmd_assets_search)

    assets_show = assets_sub.add_parser(
        "show",
        help="Show one engineering knowledge asset",
    )
    assets_show.add_argument(
        "asset_id",
        help="Asset ID (e.g. VP-CISCO-CUBE-000001)",
    )
    assets_show.set_defaults(func=cmd_assets_show)

    assets_stats = assets_sub.add_parser(
        "stats",
        help="Show engineering knowledge library statistics",
    )
    assets_stats.set_defaults(func=cmd_assets_stats)

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
