# Report Engine v1

Sprint 1 deliverable: deterministic incident report generation after case closure.

## Scope

When a case reaches `CLOSED`, VoicePilot can generate a readable Markdown incident report from the final `Case` aggregate. No AI, API, or React UI is involved.

**In v1:**

- Deterministic report from closed-case artifacts
- `RuntimeEngine.generate_report(case_id)`
- CLI and demo print the report after closure
- Demo writes `examples/output/vp_cube_0001_report.md`

**Not in v1:**

- PDF export
- HTML templates
- External ticketing integrations
- Report redaction / anonymization

## Report Sections

| Section | Source |
|---------|--------|
| Case overview | `case_id`, `playbook_id`, `status`, `closed_at` |
| Symptom | `case.symptom.summary` |
| Root cause assessment | Top hypothesis / learning record |
| Confidence | Learning record or recommendation |
| Evidence findings | `case.analysis_findings` |
| Recommendation | Likely root cause recommendation |
| Verification | `case.verifications` and pass/fail outcome |
| Learning record | `case.learning_record` |
| Timeline | `case.timeline_events` and intake onset metadata |

## Flow

```
Case closed (CLOSED)
        │
        ▼
generate_report(case_id)
        │
        ▼
ReportEngine.generate(case)
  → IncidentReport
        │
        ▼
format_incident_report(report)
        │
        ▼
CLI/demo print Markdown report
```

## API

```python
report = runtime.generate_report(case_id)
print(format_incident_report(report))
```

Requires case state `CLOSED`.

## CLI Output

After learning closure, the CLI prints:

```
=== Incident Report ===
# VoicePilot Incident Report
...
```

## Demo Output

The VP-CUBE-0001 demo saves the report to:

```
examples/output/vp_cube_0001_report.md
```

Run:

```bash
python examples/demo_vp_cube_0001.py
```

## Tests

- `tests/test_report_engine.py` — report content, state guard
- `tests/test_demo_runner.py` — demo writes report file

```bash
pytest tests/test_report_engine.py tests/test_demo_runner.py -v
```

## Next Steps

- Report templates per playbook
- Export to PDF / ticket systems
- Anonymized customer-facing report variants
