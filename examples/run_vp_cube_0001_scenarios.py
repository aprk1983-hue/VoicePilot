#!/usr/bin/env python3
"""Run VP-CUBE-0001 deterministic scenario expansion pack."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "core") not in sys.path:
    sys.path[:0] = [str(REPO_ROOT / "core"), str(REPO_ROOT / "sdk")]

from runtime.scenario_runner import (  # noqa: E402
    VP_CUBE_0001_PLAYBOOK_ID,
    default_scenarios_root,
    format_scenario_summary,
    format_summary_table,
    run_playbook_scenarios,
)

PLAYBOOK_ID = VP_CUBE_0001_PLAYBOOK_ID
SCENARIOS_ROOT = default_scenarios_root(PLAYBOOK_ID, repo_root=REPO_ROOT)


def main() -> int:
    """CLI entry point."""
    results = run_playbook_scenarios(PLAYBOOK_ID, repo_root=REPO_ROOT)
    if not results:
        print(f"No scenarios found under {SCENARIOS_ROOT}")
        return 1

    print("VP-CUBE-0001 Scenario Expansion Pack v1")
    print("")
    print(format_summary_table(results))
    print("")
    print(format_scenario_summary(results))

    failures = [result for result in results if not result.passed]
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
