"""Tests for the VP-CUBE-0001 demo runner."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_ROOT = REPO_ROOT / "examples"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "core") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "core"))
if str(REPO_ROOT / "sdk") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "sdk"))

from domain.enums import InvestigationState
from examples.demo_vp_cube_0001 import build_demo_inputs, run_demo


class TestDemoRunner:
    def test_build_demo_inputs_includes_intake_evidence_and_verification(self) -> None:
        inputs = build_demo_inputs()

        assert "yes" in inputs
        assert "END" in inputs
        assert "passed" in inputs
        assert any("SIP-UA Status: disabled" in line for line in inputs)

    def test_demo_runs_to_closed_state(self) -> None:
        output: list[str] = []

        result = run_demo(output_writer=output.append)

        assert result.exit_code == 0
        assert result.case_id is not None
        assert result.final_state == InvestigationState.CLOSED.value
        assert result.learning_record_id is not None
        assert "Demo finished successfully: case CLOSED with learning record." in output
        assert "Likely Root Cause:" in "\n".join(output)
        assert "Case closed." in output
