# Architecture Diagrams

Inventory of Mermaid diagrams for the VoicePilot Architecture Book. Diagrams marked **Existing** already appear in repository documentation. Diagrams marked **Required** are placeholders for future book chapters.

## Existing Diagrams (in `docs/`)

| Diagram | Location | Topic |
|---------|----------|-------|
| Parser pipeline | [`../docs/parser-framework.md`](../docs/parser-framework.md) | Raw CLI → ParserEngine → ParserResult |
| Analysis dual-path | [`../docs/sprint-2/parser-analysis-integration.md`](../docs/sprint-2/parser-analysis-integration.md) | Parser-first vs v1 pattern matcher |

## Required — Part 1 Foundation

| Diagram | Chapter | Description |
|---------|---------|-------------|
| Repository layout map | [01-project-overview](../part-1-foundation/01-project-overview.md) | Top-level directories |
| Implemented vs planned boundary | [01-project-overview](../part-1-foundation/01-project-overview.md) | `core/` vs `brain/` vs placeholders |
| Design constraint map | [02-design-principles](../part-1-foundation/02-design-principles.md) | Determinism, vendor neutrality |
| Case aggregate diagram | [03-investigation-domain-model](../part-1-foundation/03-investigation-domain-model.md) | `Case` entity graph |
| CVOM type hierarchy | [04-canonical-voice-object-model](../part-1-foundation/04-canonical-voice-object-model.md) | Voice object types |
| Investigation state machine | [05-investigation-lifecycle](../part-1-foundation/05-investigation-lifecycle.md) | `InvestigationState` transitions |
| Playbook discovery flow | [06-voicepilot-dsl](../part-1-foundation/06-voicepilot-dsl.md) | Manifest → catalog → loader |

## Required — Part 2 Architecture

| Diagram | Chapter | Description |
|---------|---------|-------------|
| System context | [01-system-overview](../part-2-architecture/01-system-overview.md) | CLI, runtime, plugins |
| Hexagonal layers | [02-core-platform-layers](../part-2-architecture/02-core-platform-layers.md) | Domain, application, infrastructure |
| RuntimeEngine sequence | [03-runtime-kernel](../part-2-architecture/03-runtime-kernel.md) | Orchestration calls |
| Plugin discovery flow | [04-plugin-architecture](../part-2-architecture/04-plugin-architecture.md) | Registry and catalog |
| Event bus flow | [05-state-and-events](../part-2-architecture/05-state-and-events.md) | Domain events |
| Brain vs core mapping | [06-brain-architecture](../part-2-architecture/06-brain-architecture.md) | Planned vs implemented |

## Required — Part 3 Engines

| Diagram | Chapter | Description |
|---------|---------|-------------|
| Investigation engine pipeline | [01-investigation-workflow-engines](../part-3-engines/01-investigation-workflow-engines.md) | Analysis through learning |
| Topology build pipeline | [03-topology-engines](../part-3-engines/03-topology-engines.md) | CVOM → VoiceTopology |
| Call path graph | [03-topology-engines](../part-3-engines/03-topology-engines.md) | Outbound path modeling |
| Health evaluation flow | [04-health-engine](../part-3-engines/04-health-engine.md) | Rules and scoring |
| VKF pipeline | [05-knowledge-framework](../part-3-engines/05-knowledge-framework.md) | Load, match, evaluate |
| Snapshot and drift pipeline | [06-configuration-engines](../part-3-engines/06-configuration-engines.md) | Snapshot → diff → drift |
| Report section assembly | [07-report-engine](../part-3-engines/07-report-engine.md) | Incident report sources |

## Required — Part 4 Platform

| Diagram | Chapter | Description |
|---------|---------|-------------|
| CLI command map | [01-cli](../part-4-platform/01-cli.md) | Subcommands |
| Health CLI pipeline | [01-cli](../part-4-platform/01-cli.md) | Sample → assessment → export |
| Demo lifecycle | [02-demo-and-examples](../part-4-platform/02-demo-and-examples.md) | VP-CUBE-0001 flow |
| Package discovery map | [03-packaging-and-distribution](../part-4-platform/03-packaging-and-distribution.md) | setuptools layout |

## Required — Part 5 Future

| Diagram | Chapter | Description |
|---------|---------|-------------|
| Future API layer | [01-http-api](../part-5-future/01-http-api.md) | Planned REST boundary |
| Brain maturity matrix | [05-brain-engine-roadmap](../part-5-future/05-brain-engine-roadmap.md) | Engine implementation status |

## Conventions

- Use Mermaid `flowchart TD` or `sequenceDiagram` consistently within a part
- Reference diagram source modules in chapter cross-links
- Do not add diagrams for unimplemented features without marking them **Planned**

## Cross References

- [Architecture Book README](../README.md)
- [ADR Index](../adr/README.md)
