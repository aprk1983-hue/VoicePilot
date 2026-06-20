# Part 2 — Architecture

Structural view of the VoicePilot platform: layers, runtime kernel, plugins, and events.

## Chapters

| Chapter | Status | Topic |
|---------|--------|-------|
| [01 — System Overview](01-system-overview.md) | Partial | High-level component map |
| [02 — Core Platform Layers](02-core-platform-layers.md) | Partial | Hexagonal layout: domain, application, infrastructure, runtime |
| [03 — Runtime Kernel](03-runtime-kernel.md) | Implemented | `RuntimeEngine`, case management, orchestration |
| [04 — Plugin Architecture](04-plugin-architecture.md) | Implemented | SDK, manifest, registry, catalog |
| [05 — State and Events](05-state-and-events.md) | Implemented | Investigation state machine and event bus |
| [06 — Brain Architecture](06-brain-architecture.md) | Planned | Documented brain engines vs implemented runtime |

## Related Documentation

- [`../../docs/architecture/system-overview.md`](../../docs/architecture/system-overview.md)
- [`../../docs/architecture/voicepilot-brain.md`](../../docs/architecture/voicepilot-brain.md)
- [`../../core/README.md`](../../core/README.md)
