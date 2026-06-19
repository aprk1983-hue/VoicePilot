#!/usr/bin/env python3
"""Repeatable full-lifecycle demo for VP-CUBE-0001."""

from __future__ import annotations

import sys
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_ROOT = Path(__file__).resolve().parent
SAMPLE_EVIDENCE_DIR = EXAMPLES_ROOT / "sample_evidence" / "vp_cube_0001"
REPORT_PATH = EXAMPLES_ROOT / "output" / "vp_cube_0001_report.md"

PLAYBOOK_ID = "VP-CUBE-0001"

INTAKE_ANSWERS = [
    "yes",
    "2026-06-10",
    "voice service voip sip disabled during maintenance",
    "all destinations",
    "yes",
]

EVIDENCE_FILES = (
    "show_dial_peer_voice_summary.txt",
    "show_sip_ua_status.txt",
    "debug_ccsip_messages.txt",
)

VERIFICATION_RESULTS = [
    ("passed", "SIP-UA enabled after change"),
    ("passed", "Provider trunk registered"),
    ("passed", "Outbound test call successful"),
]


@dataclass(frozen=True)
class DemoResult:
    """Outcome of running the VP-CUBE-0001 demo."""

    exit_code: int
    case_id: str | None
    final_state: str | None
    learning_record_id: str | None
    report_path: Path | None = None


def build_demo_inputs(
    *,
    sample_evidence_dir: Path = SAMPLE_EVIDENCE_DIR,
) -> list[str]:
    """Build scripted CLI inputs for the full investigation lifecycle."""
    inputs = list(INTAKE_ANSWERS)

    for filename in EVIDENCE_FILES:
        evidence_path = sample_evidence_dir / filename
        content = evidence_path.read_text(encoding="utf-8").strip()
        if content:
            inputs.extend(content.splitlines())
        inputs.append("END")

    for status, notes in VERIFICATION_RESULTS:
        inputs.append(status)
        inputs.append(notes)

    return inputs


def iter_demo_inputs(
    *,
    sample_evidence_dir: Path = SAMPLE_EVIDENCE_DIR,
) -> Iterator[str]:
    """Iterate scripted demo inputs."""
    return iter(build_demo_inputs(sample_evidence_dir=sample_evidence_dir))


def run_demo(
    *,
    output_writer: Callable[[str], None] | None = None,
    plugins_root: Path | None = None,
    sample_evidence_dir: Path = SAMPLE_EVIDENCE_DIR,
) -> DemoResult:
    """Run the full VP-CUBE-0001 investigation demo without manual typing."""
    if str(REPO_ROOT / "core") not in sys.path:
        sys.path[:0] = [str(REPO_ROOT / "core"), str(REPO_ROOT / "sdk")]

    from domain.enums import InvestigationState
    from cli.voicepilot_cli import build_runtime_engine, run_investigation

    writer = output_writer or print
    runtime = build_runtime_engine(plugins_root or REPO_ROOT / "plugins")
    inputs = iter_demo_inputs(sample_evidence_dir=sample_evidence_dir)

    writer("VoicePilot Demo: VP-CUBE-0001 Outbound Calls Fail")
    writer("")

    exit_code = run_investigation(
        PLAYBOOK_ID,
        input_provider=lambda: next(inputs),
        output_writer=writer,
        plugins_root=plugins_root or REPO_ROOT / "plugins",
        engine=runtime,
    )

    case_id: str | None = None
    final_state: str | None = None
    learning_record_id: str | None = None
    report_path: Path | None = None

    if runtime.case_manager.list_cases():
        case_id = runtime.case_manager.list_cases()[-1]
        case = runtime.case_manager.load_case(case_id)
        final_state = case.status.value
        if case.learning_record is not None:
            learning_record_id = case.learning_record.learning_record_id

        _print_final_lifecycle(case, writer)
        report_path = _write_incident_report(runtime, case_id, writer)

    return DemoResult(
        exit_code=exit_code,
        case_id=case_id,
        final_state=final_state,
        learning_record_id=learning_record_id,
        report_path=report_path,
    )


def _print_final_lifecycle(case, output_writer: Callable[[str], None]) -> None:
    from domain.enums import InvestigationState

    output_writer("")
    output_writer("=== Demo Lifecycle Summary ===")
    output_writer(f"Case ID:          {case.case_id}")
    output_writer(f"Playbook:         {case.playbook_id}")
    output_writer(f"Final state:      {case.status.value}")
    output_writer(f"Evidence items:   {len(case.evidence)}")
    output_writer(f"Findings:         {len(case.analysis_findings)}")
    output_writer(f"Hypotheses:       {len(case.hypotheses)}")
    output_writer(f"Recommendations:  {len(case.recommendations)}")
    output_writer(f"Verifications:    {len(case.verifications)}")

    if case.hypotheses:
        top = min(case.hypotheses, key=lambda item: item.rank or 999)
        output_writer(f"Top hypothesis:   {top.title} ({int(top.confidence)}%)")

    if case.learning_record is not None:
        record = case.learning_record
        output_writer(f"Learning record:  {record.learning_record_id}")
        output_writer(f"Root cause:       {record.root_cause}")
        output_writer(f"Reusable pattern: {record.reusable_pattern}")

    if case.status == InvestigationState.CLOSED:
        output_writer("")
        output_writer("Demo finished successfully: case CLOSED with learning record.")


def _write_incident_report(runtime, case_id: str, output_writer: Callable[[str], None]) -> Path:
    from runtime.report_engine import format_incident_report

    report = runtime.generate_report(case_id)
    markdown = format_incident_report(report)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(markdown + "\n", encoding="utf-8")

    output_writer("")
    output_writer(f"Incident report saved: {REPORT_PATH}")
    return REPORT_PATH


def main() -> int:
    """CLI entry point."""
    result = run_demo()
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
