# Infrastructure Layer

Infrastructure provides adapters for external concerns: filesystem, YAML parsing, and logging.

## Contents

| Module | Responsibility |
|--------|----------------|
| `yaml_loader.py` | Parse YAML files via PyYAML |
| `filesystem.py` | `InMemoryCaseRepository`, `FilesystemPlaybookRepository`, `FilesystemCaseRepository` (skeleton) |
| `logger.py` | `StructuredLogger` implementing `LoggerPort` |

## Hexagonal Adapters

Infrastructure implements domain ports:

- `CaseRepository` ← `InMemoryCaseRepository`, `FilesystemCaseRepository`
- `PlaybookRepository` ← `FilesystemPlaybookRepository`
- `LoggerPort` ← `StructuredLogger`

## TODO

- Full `Case` JSON serialization/deserialization
- Playbook index cache under `playbooks_path`
- Structured JSON logging for production
