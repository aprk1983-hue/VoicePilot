# VoicePilot Service Layer

The `services` package exposes a stable public facade over the VoicePilot runtime kernel.

## Purpose

Future clients — CLI, REST API, Web UI, SDK, and automation — should depend on
`VoicePilotService` instead of wiring `RuntimeEngine` directly.

## Rules

The service layer:

- delegates to existing engines through `RuntimeEngine`
- returns frozen DTO models for stable public contracts
- does **not** parse evidence, diagnose faults, or embed vendor logic

## Usage

```python
from services import VoicePilotService

service = VoicePilotService()
case = service.create_case("VP-CUBE-0001")
```

See [Service Layer v1](../../docs/sprint-10/service-layer-v1.md) for the full API.
