"""Tests for the discovery planner framework."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass

import pytest

from domain.enums import HypothesisStatus, InvestigationState, Severity
from domain.models import Case, Evidence, Hypothesis
from domain.value_objects import AffectedScope, PlatformRef, SymptomSummary
from discovery import (
    DiscoveryPlan,
    DiscoveryPlannerRegistry,
    DiscoveryPlannerRule,
    DiscoveryPriority,
    DiscoveryRequest,
    DuplicateDiscoveryRuleError,
    PlannerEngine,
    default_discovery_registry,
    format_discovery_plan_markdown,
)
from discovery.planner_models import PRIORITY_WEIGHTS, compute_discovery_score
from discovery.planner_rules import (
    BUILTIN_DISCOVERY_RULES,
    DialPeerSummaryMissingRule,
    register_builtin_rules,
)


def _case(**kwargs) -> Case:
    status = kwargs.pop("status", InvestigationState.INVESTIGATION)
    case = Case.create(
        title="Outbound calls fail",
        symptom=SymptomSummary(summary="PSTN outbound failure"),
        severity=Severity.HIGH,
        business_impact="Users cannot place outbound calls",
        affected_scope=AffectedScope(),
        platform=PlatformRef(vendor="cisco", products=("CUBE",)),
        **kwargs,
    )
    case.status = status
    return case


def _hypothesis(
    case_id: str,
    title: str,
    *,
    confidence: float,
    rank: int,
) -> Hypothesis:
    return Hypothesis.create(
        case_id,
        title,
        confidence,
        supporting_finding_ids=[],
        rank=rank,
    )


def _evidence(case_id: str, command: str) -> Evidence:
    return Evidence.create_cli_paste(case_id, command, "sample output")


class TestDiscoveryModels:
    def test_discovery_request_is_immutable(self) -> None:
        request = DiscoveryRequest(
            request_id="DISC-test",
            command="show sip-ua status",
            vendor="cisco",
            priority=DiscoveryPriority.HIGH,
            reason="Need SIP-UA state",
            estimated_confidence_gain=10.0,
            estimated_minutes=1,
            related_hypotheses=("Provider issue",),
            already_collected=False,
            optional=False,
        )

        with pytest.raises(FrozenInstanceError):
            request.reason = "changed"  # type: ignore[misc]

    def test_discovery_plan_is_immutable(self) -> None:
        plan = DiscoveryPlan(
            requests=(),
            current_confidence=0.0,
            estimated_final_confidence=0.0,
            remaining_uncertainty=100.0,
            next_best_command=None,
            total_estimated_minutes=0,
        )

        with pytest.raises(FrozenInstanceError):
            plan.current_confidence = 50.0  # type: ignore[misc]

    def test_compute_discovery_score_uses_priority_gain_and_hypotheses(self) -> None:
        request = DiscoveryRequest(
            request_id="DISC-score",
            command="debug ccsip messages",
            vendor="cisco",
            priority=DiscoveryPriority.CRITICAL,
            reason="Need SIP trace",
            estimated_confidence_gain=18.0,
            estimated_minutes=3,
            related_hypotheses=("Codec issue", "Provider issue"),
            already_collected=False,
            optional=False,
        )

        assert compute_discovery_score(request) == PRIORITY_WEIGHTS[DiscoveryPriority.CRITICAL] + 18.0 + 2

    def test_with_score_returns_new_request_with_score(self) -> None:
        request = DiscoveryRequest(
            request_id="DISC-score",
            command="show sip-ua status",
            vendor="cisco",
            priority=DiscoveryPriority.LOW,
            reason="Need SIP-UA state",
            estimated_confidence_gain=5.0,
            estimated_minutes=1,
            related_hypotheses=(),
            already_collected=False,
            optional=False,
        )

        scored = request.with_score()
        assert scored.score == 30.0
        assert request.score == 0.0


class TestDiscoveryRegistry:
    def test_duplicate_rule_rejection(self) -> None:
        registry = DiscoveryPlannerRegistry()

        @dataclass(frozen=True)
        class SampleRule(DiscoveryPlannerRule):
            id: str = "sample_rule"
            title: str = "Sample"

            def evaluate(self, case: Case) -> DiscoveryRequest | None:
                return None

        registry.register_rule(SampleRule())
        with pytest.raises(DuplicateDiscoveryRuleError):
            registry.register_rule(SampleRule())

    def test_evaluate_returns_requests_in_rule_id_order(self) -> None:
        registry = DiscoveryPlannerRegistry()
        register_builtin_rules(registry)
        case = _case()

        requests = registry.evaluate(case)
        assert len(requests) == 4
        assert requests[0].request_id == "DISC-ccsip_debug_missing"
        assert requests[1].request_id == "DISC-dial_peer_summary_missing"
        assert requests[2].request_id == "DISC-sip_ua_status_missing"
        assert requests[3].request_id == "DISC-voice_service_voip_missing"

    def test_evaluate_skips_rules_that_return_none(self) -> None:
        registry = DiscoveryPlannerRegistry()
        registry.register_rule(DialPeerSummaryMissingRule())
        case = _case(evidence=[_evidence("CASE-test", "show dial-peer voice summary")])

        assert registry.evaluate(case) == ()


class TestPlannerEngine:
    def test_empty_plan_when_all_evidence_collected(self) -> None:
        case = _case(
            evidence=[
                _evidence("CASE-1", "show dial-peer voice summary"),
                _evidence("CASE-1", "show sip-ua status"),
                _evidence("CASE-1", "show run | sec voice service voip"),
                _evidence("CASE-1", "debug ccsip messages"),
            ],
            hypotheses=[
                _hypothesis("CASE-1", "Provider issue", confidence=61.0, rank=1),
            ],
        )

        plan = PlannerEngine().evaluate_case(case)

        assert plan.requests == ()
        assert plan.current_confidence == 61.0
        assert plan.estimated_final_confidence == 61.0
        assert plan.remaining_uncertainty == 39.0
        assert plan.next_best_command is None
        assert plan.total_estimated_minutes == 0

    def test_planner_sorts_by_score_descending(self) -> None:
        case = _case(
            hypotheses=[
                _hypothesis(
                    "CASE-2",
                    "Missing or unmatched outbound dial-peer",
                    confidence=40.0,
                    rank=1,
                ),
            ],
        )

        plan = PlannerEngine().evaluate_case(case)
        scores = [request.score for request in plan.requests]
        assert scores == sorted(scores, reverse=True)
        assert plan.requests[0].command == "show dial-peer voice summary"
        assert plan.next_best_command == plan.requests[0].command

    def test_score_ordering_breaks_ties_by_command(self) -> None:
        registry = DiscoveryPlannerRegistry()

        @dataclass(frozen=True)
        class AlphaRule(DiscoveryPlannerRule):
            id: str = "alpha_rule"
            title: str = "Alpha"

            def evaluate(self, case: Case) -> DiscoveryRequest | None:
                return DiscoveryRequest(
                    request_id="DISC-alpha",
                    command="show alpha",
                    vendor="cisco",
                    priority=DiscoveryPriority.MEDIUM,
                    reason="Alpha",
                    estimated_confidence_gain=10.0,
                    estimated_minutes=1,
                    related_hypotheses=(),
                    already_collected=False,
                    optional=False,
                )

        @dataclass(frozen=True)
        class BetaRule(DiscoveryPlannerRule):
            id: str = "beta_rule"
            title: str = "Beta"

            def evaluate(self, case: Case) -> DiscoveryRequest | None:
                return DiscoveryRequest(
                    request_id="DISC-beta",
                    command="show beta",
                    vendor="cisco",
                    priority=DiscoveryPriority.MEDIUM,
                    reason="Beta",
                    estimated_confidence_gain=10.0,
                    estimated_minutes=1,
                    related_hypotheses=(),
                    already_collected=False,
                    optional=False,
                )

        registry.register_rule(BetaRule())
        registry.register_rule(AlphaRule())
        plan = PlannerEngine(registry).evaluate_case(_case())

        assert [request.command for request in plan.requests] == ["show alpha", "show beta"]

    def test_duplicate_commands_keep_highest_score(self) -> None:
        registry = DiscoveryPlannerRegistry()

        @dataclass(frozen=True)
        class LowPriorityRule(DiscoveryPlannerRule):
            id: str = "low_rule"
            title: str = "Low"

            def evaluate(self, case: Case) -> DiscoveryRequest | None:
                return DiscoveryRequest(
                    request_id="DISC-low",
                    command="show dial-peer voice summary",
                    vendor="cisco",
                    priority=DiscoveryPriority.LOW,
                    reason="Low priority",
                    estimated_confidence_gain=1.0,
                    estimated_minutes=1,
                    related_hypotheses=(),
                    already_collected=False,
                    optional=False,
                )

        @dataclass(frozen=True)
        class HighPriorityRule(DiscoveryPlannerRule):
            id: str = "high_rule"
            title: str = "High"

            def evaluate(self, case: Case) -> DiscoveryRequest | None:
                return DiscoveryRequest(
                    request_id="DISC-high",
                    command="show dial-peer voice summary",
                    vendor="cisco",
                    priority=DiscoveryPriority.CRITICAL,
                    reason="High priority",
                    estimated_confidence_gain=18.0,
                    estimated_minutes=1,
                    related_hypotheses=("Routing issue",),
                    already_collected=False,
                    optional=False,
                )

        registry.register_rule(LowPriorityRule())
        registry.register_rule(HighPriorityRule())
        plan = PlannerEngine(registry).evaluate_case(_case())

        assert len(plan.requests) == 1
        assert plan.requests[0].request_id == "DISC-high"
        assert plan.requests[0].score > 100.0

    def test_estimated_final_confidence_caps_at_100(self) -> None:
        case = _case(
            hypotheses=[_hypothesis("CASE-3", "Provider issue", confidence=90.0, rank=1)],
        )
        plan = PlannerEngine().evaluate_case(case)

        assert plan.current_confidence == 90.0
        assert plan.estimated_final_confidence == 100.0
        assert plan.total_estimated_minutes == sum(
            request.estimated_minutes for request in plan.requests
        )

    def test_default_registry_is_preloaded(self) -> None:
        from discovery.teams_planner_rules import TEAMS_DISCOVERY_RULES

        registry = default_discovery_registry()
        assert len(registry.all_rules()) == len(BUILTIN_DISCOVERY_RULES) + len(TEAMS_DISCOVERY_RULES)


class TestDiscoveryReport:
    def test_planner_report_matches_expected_sections(self) -> None:
        request = DiscoveryRequest(
            request_id="DISC-dial_peer_summary_missing",
            command="show dial-peer voice summary",
            vendor="cisco",
            priority=DiscoveryPriority.CRITICAL,
            reason="Outbound routing has not yet been verified.",
            estimated_confidence_gain=18.0,
            estimated_minutes=1,
            related_hypotheses=("Missing or unmatched outbound dial-peer",),
            already_collected=False,
            optional=False,
            score=119.0,
        )
        plan = DiscoveryPlan(
            requests=(request,),
            current_confidence=61.0,
            estimated_final_confidence=79.0,
            remaining_uncertainty=39.0,
            next_best_command=request.command,
            total_estimated_minutes=1,
        )

        markdown = format_discovery_plan_markdown(plan)

        assert markdown.startswith("# Discovery Plan\n")
        assert "Current Confidence\n\n61%" in markdown
        assert "Estimated Final Confidence\n\n79%" in markdown
        assert "Remaining Uncertainty\n\n39%" in markdown
        assert "## Recommended Evidence" in markdown
        assert "show dial-peer voice summary" in markdown
        assert "Priority\n\nCRITICAL" in markdown
        assert "Estimated Gain\n\n18%" in markdown
        assert "Outbound routing has not yet been verified." in markdown
        assert "Estimated Time\n\n1 minute" in markdown

    def test_empty_plan_report(self) -> None:
        plan = DiscoveryPlan(
            requests=(),
            current_confidence=0.0,
            estimated_final_confidence=0.0,
            remaining_uncertainty=100.0,
            next_best_command=None,
            total_estimated_minutes=0,
        )

        markdown = format_discovery_plan_markdown(plan)

        assert "_No additional evidence recommended._" in markdown
        assert "Remaining Uncertainty\n\n100%" in markdown

    def test_eliminated_hypotheses_are_ignored_for_confidence(self) -> None:
        case = _case(
            hypotheses=[
                Hypothesis.create(
                    "CASE-4",
                    "Eliminated",
                    95.0,
                    supporting_finding_ids=[],
                    rank=1,
                    status=HypothesisStatus.ELIMINATED,
                ),
                _hypothesis("CASE-4", "Active root cause", confidence=55.0, rank=2),
            ],
        )

        plan = PlannerEngine().evaluate_case(case)
        assert plan.current_confidence == 55.0
