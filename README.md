# VoicePilot

VoicePilot is an AI Voice Operations Engineer platform for structured voice incident investigation.

## Platform Layout

```
VoicePilot/
├── core/           # Platform kernel (runtime, domain, application, infrastructure)
├── sdk/            # Plugin SDK (manifests, interfaces, provider contracts)
├── plugins/        # Official and third-party plugins
├── tests/          # Platform test suite
├── cli/            # CLI (future)
├── api/            # FastAPI enterprise backend
├── web/            # React enterprise web UI
├── backend/        # Compatibility shim (deprecated)
├── brain/          # Architecture documentation
└── docs/           # Specifications (DSL, data model, playbooks)
```

## Quick Start (Tests)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Architecture

| Layer | Description |
|-------|-------------|
| **Core** | Vendor-neutral investigation runtime |
| **SDK** | Plugin contract for extending core |
| **Plugins** | Cisco and future vendor packs |
| **Brain** | Engine architecture (documentation) |

See [core/README.md](core/README.md), [sdk/README.md](sdk/README.md), and [plugins/README.md](plugins/README.md).
