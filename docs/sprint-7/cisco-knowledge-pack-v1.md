# Cisco Knowledge Pack v1

Sprint 7.2 ships the first bundled Cisco knowledge packs and integrates matched knowledge into incident reports.

## Goals

- Load structured Cisco best-practice packs from YAML
- Match packs against Canonical Voice Objects during report generation
- Surface actionable guidance in the **Matched Knowledge** report section
- No AI, API, React, or persistence changes

## Pack location

```
knowledge/packs/cisco/best-practices/
├── sip-ua-enabled.yaml
├── voice-service-allow-connections.yaml
└── dial-peer-destination-pattern.yaml
```

## Bootstrap

`core/runtime/knowledge_bootstrap.py` loads all YAML files under `knowledge/packs/` into a shared registry:

```python
from runtime.knowledge_bootstrap import default_knowledge_engine

report = default_knowledge_engine().evaluate_case(case)
```

## Bundled packs

| ID | Object | Condition | Severity | Category |
|----|--------|-----------|----------|----------|
| `CISCO-BP-SIP-UA-ENABLED` | `sip_ua` | `enabled == false` | CRITICAL | BEST_PRACTICE |
| `CISCO-BP-VOICE-SERVICE-ALLOW-CONNECTIONS` | `voice_service` | `allow_connections` missing or false | MEDIUM | BEST_PRACTICE |
| `CISCO-BP-DIAL-PEER-DESTINATION-PATTERN` | `dial_peer` | `destination_pattern` missing | HIGH | BEST_PRACTICE |

## Condition semantics

The matcher supports:

- Exact field equality (`enabled: false`)
- Missing sentinel (`destination_pattern: missing`) for `None` or empty strings
- OR lists (`allow_connections: [false, missing]`)

## Report integration

When a closed case includes voice objects, `ReportEngine` evaluates bundled packs and renders:

```markdown
## Matched Knowledge

### CISCO-BP-SIP-UA-ENABLED
- **Knowledge ID:** CISCO-BP-SIP-UA-ENABLED
- **Title:** ...
- **Severity:** CRITICAL
- **Category:** BEST_PRACTICE
- **Matched object:** SipUA
- **Recommendation:** ...
- **References:** ...
```

If no packs match:

```markdown
_No knowledge packs matched current case._
```

## VP-CUBE-0001 demo

The VP-CUBE-0001 scenario attaches:

- Disabled `SipUA` → matches `CISCO-BP-SIP-UA-ENABLED`
- `VoiceService` without allow-connections → matches `CISCO-BP-VOICE-SERVICE-ALLOW-CONNECTIONS`
- Dial peer with destination `9T` → does not match destination-pattern pack

Run:

```bash
python examples/demo_vp_cube_0001.py
pytest tests/test_knowledge_pack_integration.py tests/test_report_engine.py tests/test_demo_runner.py
```

## Future vendor packs

Additional vendors can ship packs under:

```
knowledge/packs/microsoft/
knowledge/packs/avaya/
plugins/cisco/knowledge/
```

The bootstrap loader recursively loads all `*.yaml` files under `knowledge/packs/` without core code changes.

## Related

- [Knowledge framework v1](./knowledge-framework-v1.md)
- [VKF package README](../../core/knowledge/README.md)
- [Report engine v1](../sprint-1/report-engine-v1.md)
