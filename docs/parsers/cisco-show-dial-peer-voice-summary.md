# Cisco Parser: show dial-peer voice summary

Deterministic parser for Cisco IOS / IOS-XE / CUBE `show dial-peer voice summary` output.

## Implementation

| Item | Value |
|------|-------|
| Class | `CiscoShowDialPeerVoiceSummaryParser` |
| Location | `plugins/cisco/parser/show_dial_peer_voice_summary.py` |
| Vendor | `cisco` |
| Command | `show dial-peer voice summary` |
| Version | `1.0.0` |

## Registration

Registered automatically via `register_cisco_parsers()`.

## Structured Data

| Field | Type | Description |
|-------|------|-------------|
| `dial_peer_summary_present` | `bool` | Non-empty dial-peer summary detected |
| `dial_peer_summary_missing_or_empty` | `bool` | Output missing or effectively empty |
| `dial_peer_config_present` | `bool` | Dial-peer configuration markers found |
| `dial_peer_count` | `int` | Number of parsed dial-peer entries |
| `voip_dial_peer_count` | `int` | VoIP dial-peer entries |
| `pots_dial_peer_count` | `int` | POTS dial-peer entries |
| `down_dial_peer_count` | `int` | Dial-peers in `down` state |
| `out_of_service_count` | `int` | Dial-peers marked out of service |
| `destination_patterns` | `list[str]` | Parsed `destination-pattern` values |
| `session_targets` | `list[str]` | Parsed `session target` values |
| `raw_dial_peer_lines` | `list[str]` | Non-empty summary lines (prompt stripped) |
| `outbound_dial_peer_candidates_present` | `bool` | VoIP peers with destination patterns |

## Findings

| Signal | When emitted |
|--------|----------------|
| `dial_peer_summary_present` | Valid dial-peer summary content |
| `dial_peer_config_present` | Dial-peer configuration detected |
| `dial_peer_summary_missing_or_empty` | Missing or empty summary |
| `dial_peer_down` | One or more dial-peers in down state |
| `dial_peer_out_of_service` | One or more dial-peers out of service |
| `outbound_dial_peer_candidates_present` | VoIP peers with destination patterns |
| `session_target_present` | Session targets extracted |

## Sample Evidence

```
examples/sample_evidence/parser/
├── show_dial_peer_voice_summary_normal.txt
├── show_dial_peer_voice_summary_empty.txt
└── show_dial_peer_voice_summary_down.txt
```

## Analysis Integration

When `AnalysisEngine` is configured with the default `ParserEngine`, `show dial-peer voice summary` evidence is parsed by this module instead of the v1 `analyze_dial_peer_summary()` pattern matcher.

## Tests

```bash
pytest tests/test_cisco_show_dial_peer_voice_summary_parser.py -v
```

## Related

- [Parser framework](../parser-framework.md)
- [Parser analysis integration](../sprint-2/parser-analysis-integration.md)
