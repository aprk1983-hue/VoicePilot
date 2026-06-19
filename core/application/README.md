# Application Layer

The application layer coordinates use cases by delegating to the runtime kernel. It expresses intent through commands and queries (CQRS-oriented skeleton).

## Contents

| Module | Responsibility |
|--------|----------------|
| `use_cases.py` | Application services — `CreateCaseUseCase`, `LoadPlaybookUseCase`, etc. |
| `commands.py` | Write-side intent objects |
| `queries.py` | Read-side intent objects |

## Pattern

```
Command/Query → UseCase → Runtime (CaseManager / PlaybookLoader / StateMachine)
```

## TODO

- Add use cases for playbook binding to case
- Add transaction boundaries when persistence is implemented
- Add authorization context for engineer actions
