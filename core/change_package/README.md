# Engineering Change Package (ECP)

Read-only change advisory engine for VoicePilot investigations.

## Purpose

Convert existing investigation outputs — recommendations, hypotheses, findings, discovery plans, and engineering knowledge matches — into a structured **Engineering Change Package** for engineer and CAB review.

## Read-Only by Design

VoicePilot **never** executes, pushes, saves, or reloads configuration. ECP output is advisory only:

- Configuration examples are illustrations for human review
- Rollback examples are planning aids
- Verification steps are checklists for engineers after manual implementation

## Modules

| Module | Responsibility |
|--------|----------------|
| `change_models.py` | Frozen dataclasses (`EngineeringChangePackage`, etc.) |
| `change_engine.py` | `EngineeringChangePackageEngine.generate_for_case()` |
| `change_report.py` | `format_change_package_markdown()` |
| `change_risk.py` | `ChangeRiskLevel` and advisory risk assessment |

## Integration

- `RuntimeEngine.generate_change_package(case_id)`
- `VoicePilotService.generate_change_package(case_id)`
- CLI: `voicepilot change-package`, `voicepilot change-package-scenario`

See `docs/sprint-10/engineering-change-package-v1.md`.
