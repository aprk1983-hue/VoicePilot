"""Immutable Brain context passed between orchestration stages."""

from __future__ import annotations

from dataclasses import dataclass

from discovery.planner_models import DiscoveryPlan
from domain.models import Case, DecisionLogEntry, Hypothesis, Recommendation
from health.health_report import HealthReport
from investigation_quality.quality_models import InvestigationQualityReport
from knowledge.knowledge_report import KnowledgeReport
from model.voice_topology import VoiceTopology


@dataclass(frozen=True)
class BrainContext:
    """Read-only orchestration context assembled from case state."""

    case: Case
    discovery_plan: DiscoveryPlan | None
    investigation_quality_report: InvestigationQualityReport | None
    health_report: HealthReport | None
    knowledge_report: KnowledgeReport | None
    topology: VoiceTopology | None
    decision_log: tuple[DecisionLogEntry, ...]
    hypotheses: tuple[Hypothesis, ...]
    recommendations: tuple[Recommendation, ...]

    @property
    def top_hypothesis(self) -> Hypothesis | None:
        """Return the highest-ranked active hypothesis."""
        active = [
            hypothesis
            for hypothesis in self.hypotheses
            if hypothesis.confidence is not None
        ]
        if not active:
            return None
        return max(active, key=lambda item: (item.confidence or 0.0, -item.rank))

    @property
    def top_confidence(self) -> float | None:
        hypothesis = self.top_hypothesis
        return hypothesis.confidence if hypothesis else None
