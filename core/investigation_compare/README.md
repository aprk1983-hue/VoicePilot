# Investigation Comparison Engine (ICE)

Deterministic before/after comparison of VoicePilot investigation outputs.

## Purpose

Compare two investigations or snapshots and produce improvement reports for operational validation and trend analysis.

## Read-Only by Design

ICE never diagnoses, recommends, or executes changes. It only compares outputs already produced by existing engines.

## Modules

| Module | Responsibility |
|--------|----------------|
| `compare_models.py` | Frozen dataclasses and `ComparisonStatus` |
| `compare_engine.py` | `InvestigationComparisonEngine` |
| `compare_report.py` | `format_comparison_markdown()` |

## Integration

- `RuntimeEngine.compare_cases(before_id, after_id)`
- `VoicePilotService.compare_cases(before_id, after_id)`
- CLI: `voicepilot compare`, `voicepilot compare-scenarios`

See `docs/sprint-10/investigation-comparison-engine-v1.md`.
