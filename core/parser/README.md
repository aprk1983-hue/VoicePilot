# VoicePilot Parser Framework

Vendor-neutral architecture for turning engineer-pasted CLI output into structured investigation artifacts.

## Design Principles

1. **Parsers never modify `Case`** — they only emit `ParserResult`.
2. **Runtime decides** — analysis, hypothesis, and evidence engines consume parser output.
3. **Vendor logic stays in plugins** — Cisco today; Microsoft Teams, Ribbon, and AudioCodes tomorrow.
4. **Wireshark mindset** — detect command fingerprints, dispatch to specialized parsers, emit structured findings.

## Package Layout

| Module | Responsibility |
|--------|----------------|
| `interfaces.py` | `CommandParser` ABC (`detect`, `parse`, `validate`, `extract_findings`, `extract_metadata`) |
| `command_detector.py` | Automatic CLI command detection from raw text |
| `parser_registry.py` | Register and resolve parsers by vendor + command |
| `parser_context.py` | Immutable parse-time context (vendor, device, case, timestamps) |
| `parser_result.py` | Structured parse output (findings, metadata, warnings, errors) |
| `parser_exceptions.py` | Framework-specific errors |
| `parser_engine.py` | Orchestrator: detect → lookup → parse |

## Plugin Layout

Vendor parsers live entirely inside plugin trees:

```
plugins/
  cisco/
    parser/          ← Cisco command parsers (future sprint)
  microsoft/
    parser/          ← Teams / SBC parsers (future)
  ribbon/
    parser/
  audiocodes/
    parser/
```

Core exposes contracts and orchestration only.

## Flow

```
Raw CLI text + ParserContext
        │
        ▼
CommandDetector.detect()
        │
        ▼
ParserRegistry.get_parser(vendor, command)
        │
        ▼
CommandParser.parse()
  ├─ validate()
  ├─ extract_metadata()
  └─ extract_findings()
        │
        ▼
ParserResult  →  Runtime / AnalysisEngine
```

## Status

Architecture sprint — skeleton interfaces and registry only. No Cisco parsing logic, regex, or production fingerprinting yet.

See [docs/parser-framework.md](../../docs/parser-framework.md) for the full design.
