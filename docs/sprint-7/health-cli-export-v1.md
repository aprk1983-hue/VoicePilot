# Health CLI Export v1

Sprint 8 extension adds Markdown report export to the `voicepilot health` command.

## Command

```bash
voicepilot health --samples examples/sample_evidence/parser --output health_report.md
```

When `--output` is provided:

1. The normal health summary is still printed to the terminal.
2. A Markdown report is written to the given path.
3. Parent directories are created automatically when needed.

## Markdown sections

```markdown
# VoicePilot Health Assessment

- **Score:** 30/100
- **Status:** FAIL
- **Counts:** PASS 10 | WARN 1 | FAIL 3

## Top Findings

- CRITICAL FAIL — SIP-UA is disabled.
  - Recommendation: Enable SIP-UA and validate registration.

## Matched Knowledge

- **CISCO-BP-SIP-UA-ENABLED** — SIP-UA must be enabled for CUBE SIP processing
  - Recommendation: Enable SIP-UA and verify SIP registration before closing the incident.

## Report Metadata

- **Generated:** 2026-06-20T12:00:00+00:00
- **Samples:** examples/sample_evidence/parser
```

## Tests

```bash
pytest tests/test_cli_health.py -v
```

Coverage includes:

- `--output` writes the report file
- Report contains score, SIP-UA disabled finding, and matched knowledge
- Parent directory creation for nested output paths

## Related

- [Health CLI v1](./health-cli-v1.md)
- [Health framework v1](../sprint-6/health-framework-v1.md)
