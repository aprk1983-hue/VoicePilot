# Parser-Backed Demo

Sprint 2 deliverable: VP-CUBE-0001 demo and reports clearly distinguish parser-backed findings from v1 pattern matching.

## Demo Evidence

The demo now uses parser sample outputs:

```
examples/sample_evidence/parser/
├── show_dial_peer_voice_summary_normal.txt
├── show_sip_ua_status_disabled.txt
└── debug_ccsip_503.txt
```

These samples exercise all three Cisco parsers registered in `register_cisco_parsers()`:

| Command | Parser ID |
|---------|-----------|
| `show dial-peer voice summary` | `cisco_show_dial_peer_voice_summary` |
| `show sip-ua status` | `cisco_show_sip_ua_status` |
| `debug ccsip messages` | `cisco_debug_ccsip_messages` |

The disabled SIP-UA sample still drives the likely root cause path (`sip_ua_disabled` at 90% confidence) through closure.

## Finding Source Labels

`AnalysisFinding.metadata` stores parser provenance:

| Source label | Meaning |
|--------------|---------|
| `parser:cisco_show_sip_ua_status` | Finding from Cisco SIP-UA parser |
| `parser:cisco_debug_ccsip_messages` | Finding from Cisco CCSIP debug parser |
| `parser:cisco_show_dial_peer_voice_summary` | Finding from Cisco dial-peer parser |
| `v1_pattern_match` | Legacy deterministic pattern matcher fallback |

## CLI Output

Analysis findings now print source labels:

```
Analysis complete. Next phase: HYPOTHESIS.
Findings:
- sip_ua_disabled (parser:cisco_show_sip_ua_status)
- sip_503_detected (parser:cisco_debug_ccsip_messages)
```

## Incident Report

Evidence findings in the Markdown report include source and a short structured summary when available:

```markdown
- `show sip-ua status`: **sip_ua_disabled** (parser:cisco_show_sip_ua_status) — SIP user agent is disabled — structured: sip_ua_enabled=False
```

## Run

```bash
python examples/demo_vp_cube_0001.py
```

Report written to `examples/output/vp_cube_0001_report.md`.

## Tests

```bash
pytest tests/test_demo_runner.py tests/test_report_engine.py tests/test_cli.py -v
```

## Related

- [Parser analysis integration](parser-analysis-integration.md)
- [Parser framework](../parser-framework.md)
