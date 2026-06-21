# Engineering Change Package v1

## Purpose

Sprint 10.6 introduces the **Engineering Change Package (ECP)** — a read-only advisory document that converts existing VoicePilot investigation outputs into a structured change package for engineer and CAB review.

VoicePilot analyzes evidence and recommends changes. **Authorized engineers** review, approve, and implement configuration changes on production systems.

## Read-Only Design Principle

VoicePilot is **read-only by design**. ECP reinforces this at every layer:

| VoicePilot NEVER | VoicePilot MAY |
|------------------|----------------|
| Push configuration | Analyze evidence |
| Execute configuration commands | Explain root cause |
| Save configuration to devices | Recommend configuration changes |
| Reload devices | Generate configuration **examples** |
| Modify CUCM/Teams/AudioCodes/Genesys | Generate rollback **examples** |
| Perform auto-remediation | Generate verification steps |
| | Produce change packages for CAB review |

Every package includes:

> VoicePilot does not execute configuration changes. All changes must be reviewed, approved, and implemented by an authorized engineer.

Configuration and rollback blocks are prefixed with `! Example configuration for engineer review — not applied by VoicePilot`.

## Architecture

```text
Case (recommendations, hypotheses, findings, discovery plan, quality)
        │
        ▼
EngineeringChangePackageEngine.generate_for_case()
        │  (no independent diagnosis)
        ▼
EngineeringChangePackage (frozen dataclass)
        │
        ▼
format_change_package_markdown() → CLI / Service DTO
```

The engine **does not** generate new root-cause logic. It converts:

- Top `Recommendation` and `Hypothesis`
- `VP_CUBE_0001_ACTION_PLANS` (actions, verification, rollback guidance)
- `VP_CUBE_0001_CHANGE_TEMPLATES` (advisory config/rollback examples)
- Discovery plan gaps (when insufficient)
- EKF knowledge asset matches (when available)

## Model

| Type | Key fields |
|------|------------|
| `EngineeringChangePackage` | `package_id`, `case_id`, `executive_summary`, `recommended_changes`, `read_only_notice` |
| `RecommendedChange` | `config_example`, `rollback_example`, `risk_level`, `impacted_objects` |
| `VerificationStep` | `command`, `expected_result`, `purpose`, `required` |
| `ApprovalSection` | CAB placeholder sections |
| `ChangeRiskLevel` | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |

## Runtime Integration

```python
package = runtime.generate_change_package(case_id)
# Stored on case.change_package
```

If the case has hypotheses but no recommendation, the runtime generates a recommendation first (when state is `INVESTIGATION`).

## Service Integration

```python
from services import VoicePilotService

service = VoicePilotService()
result = service.generate_change_package(case_id)
# result.markdown, result.package_id, result.risk_level
```

## CLI Usage

```bash
# From a live in-memory case
voicepilot change-package CASE-abc123

# From VP-CUBE-0001 scenario
voicepilot change-package-scenario VP-CUBE-0001 --scenario sip_ua_disabled

# Write Markdown to file
voicepilot change-package-scenario VP-CUBE-0001 --scenario sip_ua_disabled --output change_package.md

# Include in scenario regression report
voicepilot scenarios VP-CUBE-0001 --scenario sip_ua_disabled --include-change-package --output report.md
```

## Example Package Sections

1. Read-Only Notice
2. Executive Summary
3. Root Cause / Confidence
4. Evidence Reviewed
5. Recommended Changes (with config and rollback examples)
6. Risk Assessment
7. Verification Steps
8. CAB Approval placeholders

## VP-CUBE-0001 Coverage

Advisory templates exist for:

- SIP-UA disabled (`HYP-SIP-UA-DISABLED`)
- Missing outbound dial peer (`HYP-404-MISSING`)
- Provider 503 (`HYP-503-PROVIDER`)
- Codec mismatch 488 (`HYP-488-CODEC`)
- Dial peer shutdown (`HYP-DIAL-PEER-DOWN`)

## Future Export

- PDF / DOCX rendering from Markdown
- ServiceNow change request field mapping
- Per-vendor change template libraries (CUCM, Teams, AudioCodes)

## Safety Limitations

- Examples may not match current device baseline — engineer validation required
- No connectivity to production systems
- No change execution audit trail beyond VoicePilot case artifacts
- Insufficient recommendation data produces an advisory "collect more evidence" package
