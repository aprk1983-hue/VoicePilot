# 11 — Microsoft Teams Investigation Engine

> **Status:** Implemented

## Purpose

Document the Microsoft Teams Investigation Engine: deterministic end-to-end investigation using exported PowerShell evidence and CVOM objects.

## Repository Modules Involved

- [`../../plugins/microsoft/playbooks/teams/`](../../plugins/microsoft/playbooks/teams/) — VP-TEAMS-0001 playbook
- [`../../core/runtime/teams_investigation.py`](../../core/runtime/teams_investigation.py) — hypotheses, correlation, action plans
- [`../../core/runtime/intake_summary.py`](../../core/runtime/intake_summary.py) — intake handoff
- [`../../core/discovery/teams_planner_rules.py`](../../core/discovery/teams_planner_rules.py) — discovery planner rules
- [`../../core/health/teams_rules.py`](../../core/health/teams_rules.py) — health evaluation
- [`../../plugins/microsoft/parser/teams/`](../../plugins/microsoft/parser/teams/) — evidence parsers
- [`../../core/runtime/scenario_runner.py`](../../core/runtime/scenario_runner.py) — scenario regression

## Pipeline

```text
VP-TEAMS-0001 Playbook → Intake → Evidence → Parsers → CVOM
  → HypothesisEngine → CorrelationEngine → DiscoveryPlanner
  → InvestigationQuality → RecommendationEngine → ChangePackage → ReportEngine
```

## Hypotheses

11 deterministic hypotheses covering licensing, routing, Direct Routing, emergency calling, and resource accounts.

## Scenario Pack

`examples/sample_evidence/scenarios/vp_teams_0001/` — 11 regression scenarios with `expected_result.yaml`.

## Constraints

- Read-only investigation
- Advisory recommendations and change packages only
- No Graph API, PowerShell execution, or Microsoft authentication
- Vendor-specific logic in Teams modules only

## Related Tests

- [`../../tests/test_teams_investigation_engine.py`](../../tests/test_teams_investigation_engine.py)
- [`../../tests/test_vp_teams_0001_scenarios.py`](../../tests/test_vp_teams_0001_scenarios.py)

## Related Documentation

- [`../../docs/sprint-12/teams-investigation-engine-v1.md`](../../docs/sprint-12/teams-investigation-engine-v1.md)
- [09 — Microsoft Teams Parser Pipeline](09-microsoft-teams-parser-pipeline.md)
- [10 — Microsoft Teams Health Engine](10-microsoft-teams-health-engine.md)

## Cross References

- [02 — Parser Engine](../part-3-engines/02-parser-engine.md)
- [03 — Topology Engines](../part-3-engines/03-topology-engines.md)
