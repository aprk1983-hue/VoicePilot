# Scenario Expansion Pack v1 — VP-CUBE-0001

Deterministic Cisco CUBE outbound-call failure scenarios for regression testing VoicePilot beyond the original SIP-UA disabled demo.

## Scenario matrix

| Scenario ID | SIP code | Key evidence signals | Expected root cause | Min confidence |
|-------------|----------|----------------------|---------------------|----------------|
| `sip_ua_disabled` | 503 | `sip_ua_disabled`, `sip_ua_disabled_by_config` | CUBE SIP user agent disabled | 98% |
| `missing_outbound_dial_peer` | 404 | `dial_peer_summary_missing_or_empty`, `sip_404_detected` | Missing or unmatched outbound dial-peer | 85% |
| `provider_503` | 503 | `sip_ua_enabled`, `dial_peer_config_present`, `sip_503_detected` | Provider or SIP trunk service issue | 85% |
| `codec_mismatch_488` | 488 | `sip_488_detected`, healthy SIP-UA and dial-plan | Codec / SDP negotiation issue | 80% |
| `dial_peer_shutdown` | 404 | `dial_peer_down`, `dial_peer_out_of_service` | Outbound dial peer administratively down/out of service | 85% |

## Evidence required

Each scenario folder under `examples/sample_evidence/scenarios/vp_cube_0001/<scenario_id>/` contains:

| File | CLI command |
|------|-------------|
| `show_dial_peer_voice_summary.txt` | `show dial-peer voice summary` |
| `show_sip_ua_status.txt` | `show sip-ua status` |
| `show_run_voice_service_voip.txt` | `show run \| sec voice service voip` |
| `debug_ccsip_messages.txt` | `debug ccsip messages` |
| `expected_result.yaml` | Expected top hypothesis and confidence threshold |

## Expected findings

### sip_ua_disabled

- Parser: `sip_ua_disabled`, `sip_ua_disabled_by_config`
- Correlation: `sip_ua_disabled_confirmed` (+8 → 98%)
- Recommendation: enable SIP-UA under `voice service voip`

### missing_outbound_dial_peer

- Parser: `dial_peer_summary_missing_or_empty`, `sip_404_detected`
- Correlation: `routing_evidence_missing_dial_peer` (+10)
- Recommendation: review outbound dial-peer coverage

### provider_503

- Parser: healthy dial-peer summary, `sip_ua_enabled`, `sip_503_detected`, `sip_trace_present`
- Correlation: `provider_503_healthy_cube` (+12)
- Recommendation: verify provider/trunk health

### codec_mismatch_488

- Parser: `sip_488_detected` with healthy CUBE configuration
- Hypothesis: codec/SDP negotiation at 82% base confidence
- Recommendation: compare codec lists and SDP offer/answer

### dial_peer_shutdown

- Parser: `dial_peer_down`, `dial_peer_out_of_service`, `sip_404_detected`
- Correlation: `dial_peer_down_routing_failure` (+5)
- Recommendation: remove shutdown and verify peer state

## Running scenarios

```bash
python examples/run_vp_cube_0001_scenarios.py
pytest tests/test_vp_cube_0001_scenarios.py
```

The runner feeds scripted intake answers and scenario evidence through the same runtime pipeline used by the CLI (`analyze` → `hypotheses` → `correlate` → `recommendation`) and prints a pass/fail summary table. Exit code is non-zero when any scenario fails.

## Current limitations

- Scenarios use pasted CLI text only; no live device connectivity.
- Root-cause ranking is deterministic rule-based, not probabilistic inference.
- `provider_503` and `codec_mismatch_488` do not distinguish between multiple upstream carriers or codec policy variants without additional SDP evidence.
- `dial_peer_shutdown` does not differentiate administrative shutdown from hardware/OS failure without `show run | sec dial-peer`.
- Scenarios do not exercise verification or learning closure except in the dedicated report-generation test for `sip_ua_disabled`.
