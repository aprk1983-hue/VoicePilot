# 15 — AudioCodes SBC Investigation Engine

> **Status:** Implemented

## Purpose

Document the AudioCodes SBC Investigation Engine: deterministic end-to-end investigation using uploaded CLI evidence and AVOM objects.

## Repository Modules Involved

- [`../../plugins/audiocodes/playbooks/sbc/`](../../plugins/audiocodes/playbooks/sbc/) — VP-AUDIOCODES-0001 playbook
- [`../../core/runtime/audiocodes_investigation.py`](../../core/runtime/audiocodes_investigation.py) — hypotheses, correlation, action plans
- [`../../core/runtime/intake_summary.py`](../../core/runtime/intake_summary.py) — intake handoff
- [`../../core/discovery/audiocodes_planner_rules.py`](../../core/discovery/audiocodes_planner_rules.py) — discovery planner rules
- [`../../core/health/audiocodes_rules.py`](../../core/health/audiocodes_rules.py) — health evaluation
- [`../../plugins/audiocodes/parser/sbc/`](../../plugins/audiocodes/parser/sbc/) — evidence parsers
- [`../../core/runtime/scenario_runner.py`](../../core/runtime/scenario_runner.py) — scenario regression

## Pipeline Diagram

```text
VP-AUDIOCODES-0001 Playbook → Intake → Evidence → Parsers → AVOM
  → HypothesisEngine → CorrelationEngine → DiscoveryPlanner
  → InvestigationQuality → RecommendationEngine → ChangePackage → ReportEngine
```

## Object Flow

```text
CLI Evidence → ParserEngine → AVOM (SBCDevice, ProxySet, IPGroup, RoutingRule, MediaRealm, ...)
  → TopologyBuilder → HealthEngine → AnalysisFindings
```

## Evidence Flow

```text
show voip status / sip-options / proxy-set / ip-group / routing-table
  / media-realm / tls-context / certificates / ha-status / licenses
  → Parser signals → Hypothesis rules → Correlation boosts → Recommendations
```

## Decision Flow

```text
Parser signals → HypothesisRule match → Ranked hypotheses
  → CorrelationRule reinforcement → Top hypothesis
  → Action plan (VP-AUDIOCODES-SBC-RB-*) → ECP advisory package
```

## Knowledge Flow

```text
Hypothesis signals → EKF asset matching → VP-AUDIOCODES-SBC-000001..000025
  → VP-AUDIOCODES-SBC-RB-* runbooks → VP-AUDIOCODES-SBC-VG-* verification
  → VP-AUDIOCODES-SBC-REF-* references → Report / Change Package
```

## Hypotheses

15 deterministic hypotheses covering SIP trunk health, routing, TLS, media, licensing, HA, and provider connectivity.

## Scenario Pack

`examples/sample_evidence/scenarios/vp_audiocodes_0001/` — 10 regression scenarios with `expected_result.yaml` and `golden_report.md`.

## Constraints

- Read-only investigation
- Advisory recommendations and change packages only
- No SSH, REST, SNMP, or live AudioCodes connectivity
- Vendor-specific logic in AudioCodes modules only

## Related Tests

- [`../../tests/test_audiocodes_investigation_engine.py`](../../tests/test_audiocodes_investigation_engine.py)
- [`../../tests/test_vp_audiocodes_0001_scenarios.py`](../../tests/test_vp_audiocodes_0001_scenarios.py)

## Related Documentation

- [`../../docs/sprint-13/audiocodes-investigation-engine-v1.md`](../../docs/sprint-13/audiocodes-investigation-engine-v1.md)
- [13 — AudioCodes SBC Object Model](13-audiocodes-object-model.md)
- [14 — AudioCodes SBC Health Engine](14-audiocodes-health-engine.md)

## Cross References

- [02 — Parser Engine](../part-3-engines/02-parser-engine.md)
- [03 — Topology Engines](../part-3-engines/03-topology-engines.md)
