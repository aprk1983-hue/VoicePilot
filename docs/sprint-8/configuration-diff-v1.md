# Configuration Diff v1

Sprint 8.2 introduces deterministic object-level diffing between two `ConfigurationSnapshot` captures.

## Goals

- Compare before/after snapshots at the CVOM object level
- Ignore provenance-only fields during comparison
- Assign vendor-neutral risk levels to changes
- Produce human-readable Markdown diff reports
- No AI, API, React, or database changes

## Architecture

```
ConfigurationSnapshot (before)
ConfigurationSnapshot (after)
      ↓
DiffEngine.compare()
      ↓
SnapshotDiff
      ↓
format_diff_report_markdown()
```

## Change types

| Type | Meaning |
|------|---------|
| `ADDED` | Object present only in after snapshot |
| `REMOVED` | Object present only in before snapshot |
| `MODIFIED` | Same object ID with comparable field changes |
| `UNCHANGED` | Same comparable content |

## Ignored provenance fields

These fields do not affect diff classification:

- `source_parser`
- `source_command`
- `source_evidence_id`
- `metadata`
- `confidence`

## Risk rules v1

| Change | Risk |
|--------|------|
| SipUA `enabled` true → false | CRITICAL |
| VoiceService `allow_connections` true → false/missing | HIGH |
| DialPeer `shutdown` false → true | HIGH |
| DialPeer `destination_pattern` changed | MEDIUM |
| Provider removed | HIGH |
| DialPeer removed | MEDIUM |
| Object added | LOW |

Snapshot diff risk level is the highest severity across all added, removed, and modified objects.

## API

```python
from configuration.diff_engine import DiffEngine
from configuration.diff_report import format_diff_report_markdown

engine = DiffEngine()
diff = engine.compare(before_snapshot, after_snapshot)
summary = engine.summarize(diff)
markdown = format_diff_report_markdown(diff)
```

## Example report

```markdown
## Configuration Diff

Before: SNAP-001
After: SNAP-002

Critical:
- SipUA changed from enabled to disabled

High:
- DialPeer dial-peer 100 changed to shutdown
```

## Future work

- Relationship-level diffing
- Baseline comparison workflows
- Drift detection schedules
- Snapshot diff integration in incident reports and CLI

## Tests

```bash
pytest tests/test_configuration_diff_engine.py -v
```

## Related

- [Configuration snapshot v1](./configuration-snapshot-v1.md)
- [Configuration package README](../../core/configuration/README.md)
