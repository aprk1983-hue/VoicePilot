# Cisco Parser: debug ccsip messages

Lightweight deterministic parser for Cisco `debug ccsip messages` SIP trace output.

## Implementation

| Item | Value |
|------|-------|
| Class | `CiscoDebugCcsipMessagesParser` |
| Location | `plugins/cisco/parser/debug_ccsip_messages.py` |
| Vendor | `cisco` |
| Command | `debug ccsip messages` |
| Version | `1.0.0` |

This is **not** a full SIP stack parser. It extracts high-value investigation signals from pasted CUBE CCSIP debug traces using pattern matching only.

## Registration

Registered automatically via `register_cisco_parsers()` alongside other Cisco parsers.

## Structured Data

| Field | Type | Description |
|-------|------|-------------|
| `sip_trace_present` | `bool` | SIP trace headers or CCSIP display markers detected |
| `response_codes` | `list[int]` | SIP response codes (e.g. 404, 503) |
| `response_phrases` | `list[str]` | Phrases paired with response codes |
| `call_ids` | `list[str]` | Extracted `Call-ID` header values |
| `from_headers` | `list[str]` | Extracted `From` header values |
| `to_headers` | `list[str]` | Extracted `To` header values |
| `cseq_methods` | `list[str]` | SIP methods from `CSeq` headers |
| `has_invite` | `bool` | INVITE method detected |
| `has_bye` | `bool` | BYE method detected |
| `has_cancel` | `bool` | CANCEL method detected |
| `has_ack` | `bool` | ACK method detected |

## Findings

| Signal | When emitted |
|--------|----------------|
| `sip_trace_present` | Full or partial SIP trace detected |
| `sip_404_detected` | SIP 404 response found |
| `sip_403_detected` | SIP 403 response found |
| `sip_408_detected` | SIP 408 response found |
| `sip_488_detected` | SIP 488 response found |
| `sip_503_detected` | SIP 503 response found |
| `sip_call_id_present` | `Call-ID` header extracted |
| `sip_invite_present` | INVITE method detected |
| `sip_bye_present` | BYE method detected |
| `sip_cancel_present` | CANCEL method detected |

## Sample Evidence

```
examples/sample_evidence/parser/
├── debug_ccsip_503.txt
├── debug_ccsip_404.txt
└── debug_ccsip_488.txt
```

## Analysis Integration

When `AnalysisEngine` is configured with the default `ParserEngine`, `debug ccsip messages` evidence is parsed by this module instead of the v1 `analyze_ccsip_debug()` pattern matcher.

Findings are stored on `AnalysisFinding.metadata.structured_data` with `source: parser`.

## Tests

```bash
pytest tests/test_cisco_debug_ccsip_messages_parser.py -v
```

## Related

- [Parser framework](../parser-framework.md)
- [Parser analysis integration](../sprint-2/parser-analysis-integration.md)
- [Cisco show sip-ua status parser](cisco-show-sip-ua-status.md)
