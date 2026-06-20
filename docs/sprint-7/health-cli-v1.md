# Health CLI v1

Sprint 7.7 adds a standalone `voicepilot health` command for assessing parser sample evidence without running a full investigation.

## Problem

When VoicePilot is launched from the installed console entry point (`voicepilot`), Python does not automatically include `core/`, `sdk/`, or `plugins/` on `sys.path`. That caused imports such as `model` and `health` to fail.

## Bootstrap fix

`cli/voicepilot_cli.py` now calls `bootstrap_import_paths()` before importing domain/runtime packages. It safely prepends:

- repository root
- `core/`
- `sdk/`
- `plugins/`

This works for editable installs and direct module execution.

## Command

```bash
voicepilot health
voicepilot health --samples examples/sample_evidence/parser
```

### Default samples

When `--samples` is omitted, the CLI uses `examples/sample_evidence/parser` if that directory exists.

### Pipeline

```
Parser sample files (*.txt)
      ↓
ParserEngine (Cisco parsers)
      ↓
CVOM voice_objects
      ↓
TopologyBuilder
      ↓
HealthEngine.evaluate_topology()
KnowledgeEngine.evaluate_topology()
      ↓
Terminal summary
```

## Output

```
VoicePilot Health Assessment

Score: 45/100
Status: FAIL
Counts: PASS 8 | WARN 2 | FAIL 3

Top Findings:
- CRITICAL FAIL — SIP-UA is disabled.
  Recommendation: Enable SIP-UA and validate registration.

Matched Knowledge:
- CISCO-BP-SIP-UA-ENABLED — SIP-UA must be enabled for CUBE SIP processing
  Recommendation: Enable SIP-UA and verify SIP registration before closing the incident.
```

## Tests

```bash
pytest tests/test_cli_health.py -v
```

Coverage includes:

- CLI bootstrap path setup
- Entry-point style import without `PYTHONPATH`
- Health command execution
- Score/status output
- SIP-UA disabled finding from disabled sample
- Matched Cisco knowledge packs

## Related

- [Health framework v1](../sprint-6/health-framework-v1.md)
- [Cisco knowledge pack v1](./cisco-knowledge-pack-v1.md)
- [Parser framework](../parser-framework.md)
