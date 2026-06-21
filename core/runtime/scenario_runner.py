"""Deterministic playbook scenario regression runner."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from domain.enums import InvestigationState
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.evidence_collection import initialize_evidence_collection, submit_evidence
from runtime.exceptions import ScenarioNotFoundError, UnsupportedPlaybookScenarioError
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry
from runtime.runtime_engine import RuntimeEngine
from shared.config import RuntimeConfig

VP_CUBE_0001_PLAYBOOK_ID = "VP-CUBE-0001"

SCENARIO_COMPARISON_PAIRS: dict[str, str] = {
    "sip_ua_disabled": "sip_ua_fixed",
    "provider_503": "provider_restored",
    "dial_peer_shutdown": "dial_peer_enabled",
    "codec_mismatch_488": "codec_fixed",
    "missing_outbound_dial_peer": "dial_peer_added",
}

SCENARIO_COMPARISON_AFTER = frozenset(SCENARIO_COMPARISON_PAIRS.values())

INTAKE_ANSWERS = [
    "yes",
    "2026-06-10",
    "outbound call failure during troubleshooting",
    "all destinations",
    "yes",
]

EVIDENCE_FILES: tuple[tuple[str, str], ...] = (
    ("show dial-peer voice summary", "show_dial_peer_voice_summary.txt"),
    ("show sip-ua status", "show_sip_ua_status.txt"),
    ("show run | sec voice service voip", "show_run_voice_service_voip.txt"),
    ("debug ccsip messages", "debug_ccsip_messages.txt"),
)


@dataclass(frozen=True)
class ScenarioResult:
    """Outcome of running one playbook scenario."""

    scenario_id: str
    expected_root_cause: str
    actual_top_hypothesis: str | None
    confidence: float
    passed: bool
    error: str | None = None


def default_repo_root() -> Path:
    """Return the VoicePilot repository root."""
    return Path(__file__).resolve().parents[2]


def default_plugins_root(repo_root: Path | None = None) -> Path:
    """Return the default plugins directory."""
    return (repo_root or default_repo_root()) / "plugins"


def default_scenarios_root(playbook_id: str, repo_root: Path | None = None) -> Path:
    """Return the default scenario evidence root for a supported playbook."""
    root = repo_root or default_repo_root()
    if playbook_id == VP_CUBE_0001_PLAYBOOK_ID:
        return root / "examples" / "sample_evidence" / "scenarios" / "vp_cube_0001"
    raise UnsupportedPlaybookScenarioError(playbook_id)


def resolve_scenarios_root(
    playbook_id: str,
    scenarios_root: Path | None = None,
    *,
    repo_root: Path | None = None,
) -> Path:
    """Resolve the scenario evidence directory for a playbook."""
    if scenarios_root is not None:
        return scenarios_root
    return default_scenarios_root(playbook_id, repo_root=repo_root)


def build_scenario_runtime_engine(plugins_root: Path | None = None) -> RuntimeEngine:
    """Construct a fresh runtime engine for scenario execution."""
    root = plugins_root or default_plugins_root()
    registry = PluginRegistry(plugins_root=root)
    loader = PlaybookLoader(repository=FilesystemPlaybookRepository(YamlLoader()))
    catalog = PlaybookCatalog(plugin_registry=registry, playbook_loader=loader)
    catalog.load_all()
    engine = RuntimeEngine(
        config=RuntimeConfig(playbooks_path=root),
        case_repository=InMemoryCaseRepository(),
        playbook_repository=FilesystemPlaybookRepository(YamlLoader()),
        plugin_registry=registry,
        playbook_catalog=catalog,
    )
    engine.start()
    return engine


def load_expected_result(scenario_dir: Path) -> dict:
    return YamlLoader().load_file(scenario_dir / "expected_result.yaml")


def root_cause_matches(actual: str, expected: dict) -> bool:
    """Return whether the top hypothesis title matches expected root cause."""
    candidates = [expected["expected_root_cause"]]
    candidates.extend(expected.get("expected_root_cause_aliases", []))
    actual_lower = actual.lower()
    for candidate in candidates:
        candidate_lower = candidate.lower()
        if candidate_lower in actual_lower or actual_lower in candidate_lower:
            return True
    return False


def _all_scenario_dirs(scenarios_root: Path) -> list[Path]:
    """Return all scenario directories containing expected_result.yaml."""
    if not scenarios_root.is_dir():
        return []
    return sorted(
        path
        for path in scenarios_root.iterdir()
        if path.is_dir() and (path / "expected_result.yaml").is_file()
    )


def discover_scenario_dirs(scenarios_root: Path) -> list[Path]:
    """Return scenario directories for standalone playbook validation."""
    return [
        path
        for path in _all_scenario_dirs(scenarios_root)
        if path.name not in SCENARIO_COMPARISON_AFTER
    ]


def list_scenario_ids(scenarios_root: Path) -> tuple[str, ...]:
    """Return scenario IDs available under a scenario root."""
    return tuple(path.name for path in discover_scenario_dirs(scenarios_root))


def resolve_scenario_dirs(
    playbook_id: str,
    *,
    scenario_id: str | None = None,
    scenarios_root: Path | None = None,
    repo_root: Path | None = None,
) -> list[Path]:
    """Resolve scenario directories to execute for a playbook."""
    if playbook_id != VP_CUBE_0001_PLAYBOOK_ID:
        raise UnsupportedPlaybookScenarioError(playbook_id)

    root = resolve_scenarios_root(playbook_id, scenarios_root, repo_root=repo_root)
    scenario_dirs = _all_scenario_dirs(root)
    if scenario_id is None:
        return discover_scenario_dirs(root)

    for scenario_dir in scenario_dirs:
        if scenario_dir.name == scenario_id:
            return [scenario_dir]

    raise ScenarioNotFoundError(playbook_id, scenario_id, list_scenario_ids(root))


def run_scenario(
    scenario_dir: Path,
    *,
    playbook_id: str = VP_CUBE_0001_PLAYBOOK_ID,
    runtime: RuntimeEngine | None = None,
) -> ScenarioResult:
    """Execute one scenario through the runtime investigation pipeline."""
    expected = load_expected_result(scenario_dir)
    scenario_name = str(expected.get("scenario_id", scenario_dir.name))
    min_confidence = float(expected.get("min_confidence", 0))
    expected_root = str(expected["expected_root_cause"])

    close_runtime = False
    if runtime is None:
        runtime = build_scenario_runtime_engine()
        close_runtime = True

    try:
        turn = runtime.start_investigation(playbook_id)
        for answer in INTAKE_ANSWERS:
            turn = runtime.submit_answer(turn.case_id, turn.question_id, answer)

        case = runtime.case_manager.load_case(turn.case_id)
        playbook = runtime.playbook_catalog.get(playbook_id)
        initialize_evidence_collection(case, runtime.case_manager, playbook)
        case = runtime.case_manager.load_case(case.case_id)

        for command, filename in EVIDENCE_FILES:
            raw_text = (scenario_dir / filename).read_text(encoding="utf-8")
            submit_evidence(
                case,
                runtime.case_manager,
                command,
                raw_text,
                decision_log=runtime.decision_log_engine,
            )
            case = runtime.case_manager.load_case(case.case_id)

        runtime.analyze_case(case.case_id)
        runtime.generate_hypotheses(case.case_id)
        runtime.correlate_case(case.case_id)
        runtime.generate_recommendation(case.case_id)

        case = runtime.case_manager.load_case(case.case_id)
        if not case.hypotheses:
            return ScenarioResult(
                scenario_id=scenario_name,
                expected_root_cause=expected_root,
                actual_top_hypothesis=None,
                confidence=0.0,
                passed=False,
                error="No hypotheses generated",
            )

        top = min(case.hypotheses, key=lambda item: item.rank or 999)
        passed = root_cause_matches(top.title, expected) and top.confidence >= min_confidence
        return ScenarioResult(
            scenario_id=scenario_name,
            expected_root_cause=expected_root,
            actual_top_hypothesis=top.title,
            confidence=top.confidence,
            passed=passed,
        )
    except Exception as exc:
        return ScenarioResult(
            scenario_id=scenario_name,
            expected_root_cause=expected_root,
            actual_top_hypothesis=None,
            confidence=0.0,
            passed=False,
            error=str(exc),
        )
    finally:
        if close_runtime:
            runtime.shutdown()


def run_playbook_scenarios(
    playbook_id: str,
    *,
    scenario_id: str | None = None,
    scenarios_root: Path | None = None,
    plugins_root: Path | None = None,
    repo_root: Path | None = None,
) -> list[ScenarioResult]:
    """Run one or all scenarios for a supported playbook."""
    scenario_dirs = resolve_scenario_dirs(
        playbook_id,
        scenario_id=scenario_id,
        scenarios_root=scenarios_root,
        repo_root=repo_root,
    )
    results: list[ScenarioResult] = []
    for scenario_dir in scenario_dirs:
        runtime = build_scenario_runtime_engine(plugins_root)
        try:
            results.append(run_scenario(scenario_dir, playbook_id=playbook_id, runtime=runtime))
        finally:
            runtime.shutdown()
    return results


def run_scenario_to_correlation(
    scenario_dir: Path,
    *,
    playbook_id: str = VP_CUBE_0001_PLAYBOOK_ID,
    plugins_root: Path | None = None,
    evidence_files: tuple[tuple[str, str], ...] | None = None,
    runtime: RuntimeEngine | None = None,
) -> tuple[RuntimeEngine, str]:
    """Run a scenario through correlation and return the runtime and case ID."""
    active_runtime = runtime or build_scenario_runtime_engine(plugins_root)
    files = evidence_files or EVIDENCE_FILES

    turn = active_runtime.start_investigation(playbook_id)
    for answer in INTAKE_ANSWERS:
        turn = active_runtime.submit_answer(turn.case_id, turn.question_id, answer)

    case = active_runtime.case_manager.load_case(turn.case_id)
    playbook = active_runtime.playbook_catalog.get(playbook_id)
    initialize_evidence_collection(case, active_runtime.case_manager, playbook)
    case = active_runtime.case_manager.load_case(case.case_id)

    for command, filename in files:
        raw_text = (scenario_dir / filename).read_text(encoding="utf-8")
        submit_evidence(
            case,
            active_runtime.case_manager,
            command,
            raw_text,
            decision_log=active_runtime.decision_log_engine,
        )
        case = active_runtime.case_manager.load_case(case.case_id)

    if len(files) < len(EVIDENCE_FILES) and case.status == InvestigationState.COLLECTION:
        active_runtime.case_manager.transition_state(case.case_id, InvestigationState.ANALYSIS)
        case = active_runtime.case_manager.load_case(case.case_id)

    active_runtime.analyze_case(case.case_id)
    active_runtime.generate_hypotheses(case.case_id)
    active_runtime.correlate_case(case.case_id)
    return active_runtime, turn.case_id


def run_scenario_for_comparison(
    scenario_dir: Path,
    *,
    playbook_id: str = VP_CUBE_0001_PLAYBOOK_ID,
    runtime: RuntimeEngine | None = None,
) -> tuple[RuntimeEngine, str]:
    """Run a scenario through correlation and quality evaluation for comparison."""
    close_runtime = False
    if runtime is None:
        runtime = build_scenario_runtime_engine()
        close_runtime = True

    try:
        _, case_id = run_scenario_to_correlation(scenario_dir, playbook_id=playbook_id, runtime=runtime)
        runtime.evaluate_investigation_quality(case_id)
        return runtime, case_id
    finally:
        if close_runtime:
            runtime.shutdown()


def resolve_comparison_after_scenario(before_scenario: str, after_scenario: str | None) -> str:
    """Resolve the after scenario from explicit input or known comparison pairs."""
    if after_scenario is not None:
        return after_scenario
    if before_scenario in SCENARIO_COMPARISON_PAIRS:
        return SCENARIO_COMPARISON_PAIRS[before_scenario]
    raise ValueError(
        f"No default after-scenario mapping for {before_scenario!r}; provide after scenario explicitly."
    )


def _result_rows(results: list[ScenarioResult]) -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        if result.error:
            status = f"FAIL ({result.error})"
        rows.append(
            (
                result.scenario_id,
                result.expected_root_cause,
                result.actual_top_hypothesis or "(none)",
                f"{int(result.confidence)}%",
                status,
            )
        )
    return rows


def format_summary_table(results: list[ScenarioResult]) -> str:
    """Format scenario results as a fixed-width text table."""
    headers = (
        "Scenario",
        "Expected Root Cause",
        "Actual Top Hypothesis",
        "Confidence",
        "Pass/Fail",
    )
    rows = _result_rows(results)
    col_widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            col_widths[index] = max(col_widths[index], len(cell))

    def format_row(cells: tuple[str, ...]) -> str:
        return " | ".join(cell.ljust(col_widths[index]) for index, cell in enumerate(cells))

    lines = [
        format_row(headers),
        "-+-".join("-" * width for width in col_widths),
    ]
    lines.extend(format_row(row) for row in rows)
    return "\n".join(lines)


def format_scenario_summary(results: list[ScenarioResult]) -> str:
    """Format pass/fail counts for scenario results."""
    failures = [result for result in results if not result.passed]
    return (
        f"Scenarios: {len(results)} total, "
        f"{len(results) - len(failures)} passed, {len(failures)} failed"
    )


def format_scenario_markdown_report(
    playbook_id: str,
    results: list[ScenarioResult],
    *,
    scenarios_root: Path,
    generated_at: datetime | None = None,
    discovery_plan_markdown: str | None = None,
    investigation_quality_markdown: str | None = None,
    change_package_markdown: str | None = None,
) -> str:
    """Format scenario results as a Markdown report."""
    timestamp = generated_at or datetime.now(timezone.utc)
    failures = [result for result in results if not result.passed]
    lines = [
        "# VoicePilot Scenario Results",
        "",
        f"**Playbook:** {playbook_id}",
        f"**Generated:** {timestamp.isoformat()}",
        f"**Scenarios root:** {scenarios_root}",
        "",
        "## Summary",
        "",
        f"- **Total:** {len(results)}",
        f"- **Passed:** {len(results) - len(failures)}",
        f"- **Failed:** {len(failures)}",
        "",
        "## Results",
        "",
        "| Scenario | Expected Root Cause | Actual Top Hypothesis | Confidence | Pass/Fail |",
        "| --- | --- | --- | --- | --- |",
    ]
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        if result.error:
            status = f"FAIL ({result.error})"
        lines.append(
            "| "
            + " | ".join(
                (
                    result.scenario_id,
                    result.expected_root_cause,
                    result.actual_top_hypothesis or "(none)",
                    f"{int(result.confidence)}%",
                    status,
                )
            )
            + " |"
        )
    if discovery_plan_markdown:
        lines.extend(["", "## Discovery Plan", "", discovery_plan_markdown.strip(), ""])
    if investigation_quality_markdown:
        lines.extend(
            ["", "## Investigation Quality", "", investigation_quality_markdown.strip(), ""]
        )
    if change_package_markdown:
        lines.extend(["", "## Engineering Change Package", "", change_package_markdown.strip(), ""])
    return "\n".join(lines) + "\n"
