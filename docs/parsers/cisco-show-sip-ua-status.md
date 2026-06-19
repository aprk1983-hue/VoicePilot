# Cisco Parser: show sip-ua status

Deterministic parser for Cisco IOS / IOS-XE / CUBE `show sip-ua status` output.

## Implementation

| Item | Value |
|------|-------|
| Class | `CiscoShowSipUaStatusParser` |
| Location | `plugins/cisco/parser/show_sip_ua_status.py` |
| Vendor | `cisco` |
| Command | `show sip-ua status` |
| Version | `1.0.0` |

## Registration

```python
from parser.parser_registry import ParserRegistry
from plugins.cisco.parser import register_cisco_parsers

registry = ParserRegistry()
register_cisco_parsers(registry)
```

## Structured Data

| Field | Type | Description |
|-------|------|-------------|
| `sip_ua_enabled` | `bool \| None` | Whether SIP-UA is administratively enabled |
| `registration_state` | `registered` / `unregistered` / `failed` / `unknown` | Trunk/registrar registration state |
| `registrar_present` | `bool` | Whether registrar configuration appears in output |
| `registrar_host` | `str \| None` | Parsed registrar host / URI |
| `transport` | `udp` / `tcp` / `tls` / `unknown` | Detected SIP transport |
| `raw_status_lines` | `list[str]` | Non-empty status lines (prompt stripped) |

## Findings

| Signal | When emitted |
|--------|----------------|
| `sip_ua_enabled` | SIP-UA is enabled |
| `sip_ua_disabled` | SIP-UA is disabled or administratively down |
| `sip_registration_present` | Registration state is `registered` |
| `sip_registration_issue` | Registration state is `unregistered` or `failed` |
| `sip_registrar_present` | Registrar configuration detected |
| `sip_transport_tls_detected` | Transport is TLS |

## Sample Evidence

```
examples/sample_evidence/parser/
├── show_sip_ua_status_enabled.txt
├── show_sip_ua_status_disabled.txt
└── show_sip_ua_status_registered_tls.txt
```

## Usage

```python
from parser.parser_context import ParserContext
from parser.parser_engine import ParserEngine
from parser.parser_registry import ParserRegistry
from plugins.cisco.parser import register_cisco_parsers

registry = ParserRegistry()
register_cisco_parsers(registry)
engine = ParserEngine(registry=registry)

context = ParserContext(vendor="cisco", case_id="CASE-001", platform="CUBE")
result = engine.parse(raw_text, context, command="show sip-ua status")

print(result.structured_data)
print([finding.signal for finding in result.findings])
```

## Design Notes

- Parser returns `ParserResult` only — it never reads or mutates `Case`.
- Runtime / analysis engines decide how `ParserFinding` maps to case artifacts.
- Sprint 1 `AnalysisEngine` pattern matching remains in place; this parser is the first vendor pack implementation on the new framework.

## Tests

```bash
pytest tests/test_cisco_show_sip_ua_status_parser.py -v
```

## Related

- [Parser framework](../parser-framework.md)
- [Cisco parser pack README](../../plugins/cisco/parser/README.md)
