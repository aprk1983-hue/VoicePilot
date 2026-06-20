# Call Path Reporting v1

Sprint 5.4 integrates the Call Path Engine into closed-case incident reports and the VP-CUBE-0001 demo output.

## Goals

- Show outbound call paths derived from case voice objects
- Surface breakpoint candidates and disabled SIP-UA operational notes
- Remain deterministic with no AI, API, React, or persistence changes

## Report flow

During `build_incident_report()`:

1. Supplement case voice objects with report-time provider placeholders when dial peers expose `session_target` values but no `Provider` objects exist yet
2. Build `VoiceTopology` via `TopologyBuilder`
3. Build outbound paths via `CallPathEngine.build_outbound_paths()`
4. Attach a structured `ReportCallPathAnalysis` section to `IncidentReport`

## Markdown section

Reports include:

```markdown
## Call Path Analysis

### DialPeer 1 → Provider-192.0.2.10
- **Direction:** outbound
- **Source:** DialPeer 1
- **Destination:** Provider-192.0.2.10

**Hops:**
1. DialPeer 1
2. Provider-192.0.2.10

**Warnings:**
_None_

**Breakpoints:**
_None on path._

**Note:** SIP-UA is disabled and may affect all SIP call processing, even if not directly present in the current path graph.
```

When no paths can be derived:

```markdown
_No call paths derived from current evidence._
```

## Disabled SIP-UA note

If a case contains a `SipUA` object with `enabled=False` and that SIP-UA is not present on the current outbound path hop chain, the report adds a safe operational note. This covers VP-CUBE-0001 scenarios where the direct DialPeer → Provider path does not traverse the SIP-UA hop even though SIP-UA state affects all call processing.

## Provider supplementation

v1 report generation may add deterministic in-memory `Provider` objects from parsed dial-peer `session_target` values solely for call path modeling. These objects:

- Are not persisted separately
- Use dial-peer provenance fields
- Are deduplicated by session target
- Are skipped when real provider objects already exist on the case

## Demo integration

`examples/demo_vp_cube_0001.py` uses `format_incident_report()`, so the demo Markdown output automatically includes **Call Path Analysis** after case closure.

## Testing

```bash
pytest tests/test_report_engine.py tests/test_demo_runner.py
```

## Related

- [Call path engine v1](./call-path-engine-v1.md)
- [Impact analysis v1](./impact-analysis-v1.md)
