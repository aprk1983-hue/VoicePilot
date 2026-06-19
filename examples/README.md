# VoicePilot Examples

Runnable demonstrations of the VoicePilot investigation lifecycle.

## VP-CUBE-0001 Full Demo

Runs a complete deterministic investigation for **Outbound Calls Fail** without manual typing:

1. Intake questions
2. Intake summary
3. Evidence collection (3 CLI pastes)
4. Analysis findings
5. Hypothesis generation
6. Recommendation (likely root cause at >= 85% confidence)
7. Verification checklist (all steps passed)
8. Learning record creation and case closure
9. Incident report generation and Markdown export

### Run

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python examples/demo_vp_cube_0001.py
```

Or:

```bash
python examples/demo_vp_cube_0001.py
```

### Sample Evidence

Pre-baked CLI output lives in:

```
examples/sample_evidence/vp_cube_0001/
├── show_dial_peer_voice_summary.txt
├── show_sip_ua_status.txt
└── debug_ccsip_messages.txt
```

The SIP-UA sample triggers `sip_ua_disabled`, producing a high-confidence likely root cause recommendation (90%) so the demo reaches `RESOLUTION`, `VERIFICATION`, `LEARNING`, and `CLOSED`.

### Report Output

After closure, the demo writes a Markdown incident report to:

```
examples/output/vp_cube_0001_report.md
```

### Programmatic Use

```python
from examples.demo_vp_cube_0001 import run_demo

result = run_demo(output_writer=print)
print(result.final_state)  # CLOSED
```
