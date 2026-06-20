# Discovery Runtime Integration v1

Sprint 9.2 integrates the discovery planner with `RuntimeEngine`, incident reports, and the VoicePilot CLI.

## Runtime integration

```python
plan = runtime.plan_discovery(case_id)
case.discovery_plan  # stored on the case aggregate
```

Behavior:

- Loads the case from the in-memory repository
- Runs `PlannerEngine.evaluate_case(case)`
- Stores the resulting `DiscoveryPlan` on `Case.discovery_plan`
- Appends a `discovery_planned` decision log entry
- Returns the immutable plan

## Incident report section

Closed-case reports now include:

```markdown
## Discovery Plan
```

When a plan exists, the report lists current confidence, estimated final confidence, remaining uncertainty, next best command, and recommended evidence.

When no plan was generated:

```markdown
_No discovery plan recorded._
```

## CLI commands

Generate a plan for an in-memory case:

```bash
voicepilot plan CASE-ID
```

Run a scenario through correlation and print a discovery plan:

```bash
voicepilot plan-scenario VP-CUBE-0001 --scenario provider_503
```

Optional discovery plan section in scenario Markdown output:

```bash
voicepilot scenarios VP-CUBE-0001 --scenario provider_503 --output results.md --include-discovery
```

## Limitations

- Cases remain in-memory only; `voicepilot plan CASE-ID` requires a case created in the same process unless persistence is added later
- Built-in planner rules target Cisco CUBE outbound-failure evidence gaps
- Scenario packs with all evidence collected may produce an empty recommendation list

## Tests

```bash
pytest tests/test_discovery_runtime_integration.py
pytest tests/test_cli_scenarios.py
pytest tests/test_report_engine.py
```
