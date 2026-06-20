"""Registry for deterministic health rules."""

from __future__ import annotations

from health.health_rule import HealthRule


class DuplicateHealthRuleError(Exception):
    """Raised when registering a rule with an existing identifier."""

    def __init__(self, rule_id: str) -> None:
        self.rule_id = rule_id
        super().__init__(f"Health rule already registered: {rule_id}")


class HealthRuleRegistry:
    """Register and lookup health rules by object type."""

    def __init__(self) -> None:
        self._rules: dict[str, HealthRule] = {}

    def register(self, rule: HealthRule) -> None:
        """Register a rule, preventing duplicate identifiers."""
        if rule.id in self._rules:
            raise DuplicateHealthRuleError(rule.id)
        self._rules[rule.id] = rule

    def get(self, rule_id: str) -> HealthRule | None:
        """Return a rule by identifier."""
        return self._rules.get(rule_id)

    def rules_for_object_type(self, object_type: str) -> tuple[HealthRule, ...]:
        """Return rules applicable to an object type in deterministic order."""
        return tuple(
            sorted(
                (
                    rule
                    for rule in self._rules.values()
                    if object_type in rule.supported_object_types
                ),
                key=lambda item: item.id,
            )
        )

    def all_rules(self) -> tuple[HealthRule, ...]:
        """Return all registered rules in deterministic order."""
        return tuple(sorted(self._rules.values(), key=lambda item: item.id))
