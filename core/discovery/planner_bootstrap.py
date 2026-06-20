"""Bootstrap helpers for the discovery planner framework."""

from __future__ import annotations

from discovery.planner_registry import DiscoveryPlannerRegistry
from discovery.planner_rules import register_builtin_rules


def default_discovery_registry() -> DiscoveryPlannerRegistry:
    """Create a registry preloaded with built-in discovery rules."""
    registry = DiscoveryPlannerRegistry()
    register_builtin_rules(registry)
    return registry
