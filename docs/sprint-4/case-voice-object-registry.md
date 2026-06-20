# Case Voice Object Registry

VoicePilot parsers emit canonical voice objects (CVOM) alongside analysis findings. The runtime attaches those objects to the investigation case so downstream engines and reports can reference a single registry of parsed network state.

## Case field

Each `Case` carries:

```python
voice_objects: list[VoiceObject]
```

Objects are appended during analysis when a parser returns `ParserResult.voice_objects`. The list is deduplicated by object ID; re-analysis of the same evidence does not create duplicates.

## Attachment flow

1. Evidence is collected and stored on the case.
2. `AnalysisEngine.analyze()` runs parser-backed analysis per evidence item.
3. On a valid parser result, `attach_voice_objects_to_case()` merges new objects into `case.voice_objects`.
4. `RuntimeEngine.analyze_case()` persists findings and voice objects together.

Parsers never mutate the case directly. Attachment is owned by the analysis/runtime layer.

## Provenance

Each `VoiceObject` records:

- `source_parser` — parser identifier (e.g. `cisco_show_sip_ua_status`)
- `source_command` — CLI command that produced the object
- `source_evidence_id` — evidence item the parser ran against
- `confidence` — parser confidence for that extraction

Analysis findings may reference related object IDs via finding metadata (`related_voice_object_ids`).

## Incident reports

Closed-case reports include a **Canonical Voice Objects** section after evidence findings:

```markdown
## Canonical Voice Objects

- SipUA — SIP-UA — cisco_show_sip_ua_status — show sip-ua status — 95%
- VoiceService — voice service voip — cisco_show_run_voice_service_voip — show run | sec voice service voip — 95%
- DialPeer 1 — destination 9T — cisco_show_dial_peer_voice_summary — show dial-peer voice summary — 90%
```

The CLI demo and `format_incident_report()` pick up this section automatically from `case.voice_objects`.

## VP-CUBE-0001 demo coverage

After analyzing all four parser evidence samples, a case typically contains:

| Object type   | Count | Source parser                          |
|---------------|-------|----------------------------------------|
| DialPeer      | 2     | `cisco_show_dial_peer_voice_summary`   |
| SipUA         | 1     | `cisco_show_sip_ua_status`             |
| VoiceService  | 1     | `cisco_show_run_voice_service_voip`    |

Debug CCSIP output contributes findings but does not emit CVOM objects in v1.
