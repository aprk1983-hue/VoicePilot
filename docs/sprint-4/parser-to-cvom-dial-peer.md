# Parser to CVOM: Cisco Dial-Peer Voice Summary

CVOM integration for `show dial-peer voice summary`.

## Flow

```
show dial-peer voice summary
        ↓
CiscoShowDialPeerVoiceSummaryParser.parse()
        ↓
ParserResult
  ├── findings[]          (summary signals)
  └── voice_objects[]     (DialPeer per parsed peer)
        ↓
AnalysisEngine.analyze()
        ↓
AnalysisFinding.metadata.related_voice_object_ids
```

## DialPeer mapping

| CVOM field | Parser source |
|------------|---------------|
| `tag` | dial-peer tag from summary line |
| `peer_type` | `voip`, `pots`, or `unknown` |
| `destination_pattern` | following `destination-pattern` line |
| `session_target` | following `session target` line |
| `status` | normalized peer status (`up`, `down`, `out_of_service`) |
| `shutdown` | `true` when status is `down` or `out_of_service` |
| `source_parser` | `cisco_show_dial_peer_voice_summary` |
| `source_command` | `show dial-peer voice summary` |
| `source_evidence_id` | `ParserContext.evidence_id` |
| `confidence` | parser result confidence |

## Structured data: `parsed_dial_peers`

Each parsed peer is a dict:

```json
{
  "tag": "1",
  "type": "voip",
  "destination_pattern": "9T",
  "session_target": "ipv4:192.0.2.10",
  "status": "up",
  "raw_line": "dial-peer 1 voip up"
}
```

## Samples

| Sample | DialPeer count | Notes |
|--------|----------------|-------|
| `show_dial_peer_voice_summary_normal.txt` | 2 | tags 1 & 2, patterns and session targets |
| `show_dial_peer_voice_summary_down.txt` | 2 | down / out_of_service status |
| `show_dial_peer_voice_summary_empty.txt` | 0 | missing/empty finding only |

## Next steps

- Register DialPeer objects on `ObjectRegistry` during analysis
- Topology engine links DialPeer → Provider via `session_target`
- Correlate SIP 404 with missing dial-peer coverage from CVOM objects
