# VoicePilot Backend (Compatibility)

> **Deprecated entry point.** VoicePilot has evolved to a **Core + SDK + Plugins** platform layout.

## New Layout

| Path | Purpose |
|------|---------|
| [`core/`](../core/) | Platform kernel — runtime, domain, application, infrastructure |
| [`sdk/`](../sdk/) | Plugin SDK — manifests, interfaces, provider contracts |
| [`plugins/`](../plugins/) | Official and third-party plugins |
| [`tests/`](../tests/) | Platform test suite |
| [`cli/`](../cli/) | CLI (future) |
| [`api/`](../api/) | HTTP API (future) |

## Backward Compatibility

Importing `backend` adds `core/` and `sdk/` to `sys.path`:

```python
import backend  # noqa: F401 — enables legacy import paths
from domain.models import Case
from runtime.case_manager import CaseManager
```

## Running Tests

Use the **repository root** `pyproject.toml`:

```bash
cd ..   # repository root
pip install -e ".[dev]"
pytest
```

## Migration

| Old | New |
|-----|-----|
| `backend/runtime/` | `core/runtime/` |
| `backend/domain/` | `core/domain/` |
| `backend/tests/` | `tests/` |
| `playbooks/cube/*.vpb.yaml` | `plugins/cisco/playbooks/cube/*.vpb.yaml` |

This directory will be removed in a future major release after downstream consumers migrate.
