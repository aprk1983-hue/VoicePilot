#!/usr/bin/env python3
"""Run VP-CUBE-0001 deterministic scenario expansion pack."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_ROOT = Path(__file__).resolve().parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "core") not in sys.path:
    sys.path[:0] = [str(REPO_ROOT / "core"), str(REPO_ROOT / "sdk")]

PLAYBOOK_ID = "VP-CUBE-0001"
SCENARIOS_ROOT = EXAMPLES_ROOT / "sample_evidence" / "scenarios" / "vp_cube_0001"
PLUGINS_ROOT = REPO_ROOT / "plugins"

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
    """Outcome of running one VP-CUBE-0001 scenario."""

    scenario_id: str
    expected_root_cause: str
    actual_top_hypothesis: str | None
    confidence: float
    passed: bool
    error: str | None = None


def build_runtime_engine():
    """Construct a fresh runtime engine for scenario execution."""
    from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
    from infrastructure.yaml_loader import YamlLoader
    from runtime.playbook_catalog import PlaybookCatalog
    from runtime.playbook_loader import PlaybookLoader
    from runtime.plugin_registry import PluginRegistry
    from runtime.runtime_engine import RuntimeEngine
    from shared.config import RuntimeConfig

    registry = PluginRegistry(plugins_root=PLUGINS_ROOT)
    loader = PlaybookLoader(repository=FilesystemPlaybookRepository(YamlLoader()))
    catalog = PlaybookCatalog(plugin_registry=registry, playbook_loader=loader)
    catalog.load_all()
    engine = RuntimeEngine(
        config=RuntimeConfig(playbooks_path=PLUGINS_ROOT),
        case_repository=InMemoryCaseRepository(),
        playbook_repository=FilesystemPlaybookRepository(YamlLoader()),
        plugin_registry=registry,
        playbook_catalog=catalog,
    )
    engine.start()
    return engine


def load_expected_result(scenario_dir: Path) -> dict:
    from infrastructure.yaml_loader import YamlLoader

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


def discover_scenario_dirs(root: Path = SCENARIOS_ROOT) -> list[Path]:
    """Return scenario directories containing expected_result.yaml."""
    if not root.is_dir():
        return []
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir() and (path / "expected_result.yaml").is_file()
    )


def run_scenario(scenario_dir: Path, *, runtime=None) -> ScenarioResult:
    """Execute one scenario through the runtime investigation pipeline."""
    from runtime.evidence_collection import initialize_evidence_collection, submit_evidence

    expected = load_expected_result(scenario_dir)
    scenario_id = str(expected.get("scenario_id", scenario_dir.name))
    min_confidence = float(expected.get("min_confidence", 0))
    expected_root = str(expected["expected_root_cause"])

    close_runtime = False
    if runtime is None:
        runtime = build_runtime_engine()
        close_runtime = True

    try:
        turn = runtime.start_investigation(PLAYBOOK_ID)
        for answer in INTAKE_ANSWERS:
            turn = runtime.submit_answer(turn.case_id, turn.question_id, answer)

        case = runtime.case_manager.load_case(turn.case_id)
        playbook = runtime.playbook_catalog.get(PLAYBOOK_ID)
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
                scenario_id=scenario_id,
                expected_root_cause=expected_root,
                actual_top_hypothesis=None,
                confidence=0.0,
                passed=False,
                error="No hypotheses generated",
            )

        top = min(case.hypotheses, key=lambda item: item.rank or 999)
        passed = root_cause_matches(top.title, expected) and top.confidence >= min_confidence
        return ScenarioResult(
            scenario_id=scenario_id,
            expected_root_cause=expected_root,
            actual_top_hypothesis=top.title,
            confidence=top.confidence,
            passed=passed,
        )
    except Exception as exc:
        return ScenarioResult(
            scenario_id=scenario_id,
            expected_root_cause=expected_root,
            actual_top_hypothesis=None,
            confidence=0.0,
            passed=False,
            error=str(exc),
        )
    finally:
        if close_runtime:
            runtime.shutdown()


def run_all_scenarios(*, scenarios_root: Path = SCENARIOS_ROOT) -> list[ScenarioResult]:
    """Run every scenario folder under the expansion pack root."""
    results: list[ScenarioResult] = []
    for scenario_dir in discover_scenario_dirs(scenarios_root):
        runtime = build_runtime_engine()
        try:
            results.append(run_scenario(scenario_dir, runtime=runtime))
        finally:
            runtime.shutdown()
    return results


def print_summary_table(results: list[ScenarioResult]) -> None:
    """Print a pass/fail summary table for scenario results."""
    headers = (
        "Scenario",
        "Expected Root Cause",
        "Actual Top Hypothesis",
        "Confidence",
        "Pass/Fail",
    )
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

    col_widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row):
            col_widths[index] = max(col_widths[index], len(cell))

    def format_row(cells: tuple[str, ...]) -> str:
        return " | ".join(cell.ljust(col_widths[index]) for index, cell in enumerate(cells))

    print(format_row(headers))
    print("-+-".join("-" * width for width in col_widths))
    for row in rows:
        print(format_row(row))


def main() -> int:
    """CLI entry point."""
    results = run_all_scenarios()
    if not results:
        print(f"No scenarios found under {SCENARIOS_ROOT}")
        return 1

    print("VP-CUBE-0001 Scenario Expansion Pack v1")
    print("")
    print_summary_table(results)

    failures = [result for result in results if not result.passed]
    print("")
    print(
        f"Scenarios: {len(results)} total, "
        f"{len(results) - len(failures)} passed, {len(failures)} failed"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
