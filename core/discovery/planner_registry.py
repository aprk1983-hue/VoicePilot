"""Registry for deterministic discovery planner rules."""

from __future__ import annotations

from domain.models import Case
from discovery.planner_models import DiscoveryRequest
from discovery.planner_rule import DiscoveryPlannerRule


class DuplicateDiscoveryRuleError(Exception):
    """Raised when registering a rule with an existing identifier."""

    def __init__(self, rule_id: str) -> None:
        self.rule_id = rule_id
        super().__init__(f"Discovery rule already registered: {rule_id}")


class DiscoveryPlannerRegistry:
    """Register and evaluate discovery planner rules."""

    def __init__(self) -> None:
        self._rules: dict[str, DiscoveryPlannerRule] = {}

    def register_rule(self, rule: DiscoveryPlannerRule) -> None:
        """Register a rule, preventing duplicate identifiers."""
        if rule.id in self._rules:
            raise DuplicateDiscoveryRuleError(rule.id)
        self._rules[rule.id] = rule

    def get(self, rule_id: str) -> DiscoveryPlannerRule | None:
        """Return a rule by identifier."""
        return self._rules.get(rule_id)

    def all_rules(self) -> tuple[DiscoveryPlannerRule, ...]:
        """Return all registered rules in deterministic order."""
        return tuple(sorted(self._rules.values(), key=lambda item: item.id))

    def evaluate(self, case: Case) -> tuple[DiscoveryRequest, ...]:
        """Evaluate all rules and return non-null discovery requests."""
        requests: list[DiscoveryRequest] = []
        for rule in self.all_rules():
            result = rule.evaluate(case)
            if result is not None:
                requests.append(result)
        return tuple(requests)
