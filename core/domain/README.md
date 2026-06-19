# Domain Layer

The domain layer contains the core business model for VoicePilot investigations. It has no dependencies on infrastructure or runtime frameworks.

## Contents

| Module | Responsibility |
|--------|----------------|
| `models.py` | Entity dataclasses — `Case`, `Evidence`, `Hypothesis`, etc. |
| `value_objects.py` | Immutable value objects — `SymptomSummary`, `CaseIntake`, etc. |
| `enums.py` | Domain enumerations — `InvestigationState`, `Severity`, etc. |
| `events.py` | Domain events for the internal event bus |
| `interfaces.py` | Ports — `CaseRepository`, `EventBusPort`, `StateMachinePort`, etc. |

## Aggregate Root

`Case` is the root aggregate. All child entities reference `case_id`.

## Alignment

Models align with the [Canonical Data Model](../../docs/data-model/canonical-data-model.md).

## TODO

- Add `InvestigationGraph` and `LearningRecord` entities
- Add domain validation methods on aggregates
- Add factory methods for child entities from playbook templates
