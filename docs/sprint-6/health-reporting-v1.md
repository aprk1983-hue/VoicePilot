# Health Reporting v1

Sprint 6.2 integrates the Health Rule Framework into closed-case incident reports and the VP-CUBE-0001 demo output.

## Goals

- Surface deterministic health evaluation in incident reports
- Reuse `HealthEngine.evaluate_case()` against case voice objects and topology
- No AI, API, React, or persistence changes

## Report flow

During `build_incident_report()`:

1. Check whether `case.voice_objects` is populated
2. Call `HealthEngine().evaluate_case(case)`
3. Attach structured `ReportHealthAssessment` to `IncidentReport`
4. Render **Health Assessment** in Markdown after **Call Path Analysis**

## Markdown section

```markdown
## Health Assessment

- **Overall Score:** 60/100
- **Status:** FAIL
- **Counts:** PASS 4 | WARN 1 | FAIL 1 | UNKNOWN 0
- **Severity Counts:** critical 1, medium 1
- **Category Counts:** sip 1, configuration 1

**Findings:**
- CRITICAL FAIL — SIP-UA is disabled.
  Recommendation: Enable SIP-UA and validate registration.
- MEDIUM WARN — allow-connections policy is missing from voice service configuration.
  Recommendation: Review voice service voip allow-connections settings.

**Recommendations:**
- Enable SIP-UA and validate registration.
- Review voice service voip allow-connections settings.
```

When no voice objects exist:

```markdown
_No canonical voice objects available for health evaluation._
```

## VP-CUBE-0001 behavior

Closed VP-CUBE-0001 cases with parser-attached voice objects typically show:

- **CRITICAL FAIL** for disabled SIP-UA
- **MEDIUM WARN** when voice service `allow-connections` is absent
- Overall status **FAIL** when any FAIL findings exist

## Demo integration

`examples/demo_vp_cube_0001.py` writes reports through `format_incident_report()`, so the demo Markdown output includes **Health Assessment** automatically after case closure.

## Testing

```bash
pytest tests/test_report_engine.py tests/test_demo_runner.py
```

## Related

- [Health framework v1](./health-framework-v1.md)
- [Call path reporting v1](./call-path-reporting-v1.md)
- [Report engine v1](../sprint-1/report-engine-v1.md)
