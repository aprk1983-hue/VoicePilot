"""Engineering Knowledge evaluation engine."""

from __future__ import annotations

from domain.models import AnalysisFinding, Case
from engineering_assets.asset_registry import EngineeringAssetRegistry
from engineering_assets.asset_relationships import EngineeringRelationshipRegistry
from engineering_assets.asset_types import EngineeringAssetType
from engineering_knowledge.knowledge_graph import EngineeringKnowledgeGraph
from engineering_knowledge.knowledge_matcher import EngineeringKnowledgeMatcher
from engineering_knowledge.knowledge_models import EngineeringKnowledge, KnowledgeReport
from engineering_knowledge.knowledge_registry import EngineeringKnowledgeRegistry
from engineering_knowledge.knowledge_relationships import KnowledgeRelationshipRegistry
from engineering_knowledge.knowledge_report import (
    build_knowledge_report,
    build_recommendations_from_assets,
    format_knowledge_report_markdown,
)
from health.health_report import HealthReport
from model.voice_topology import VoiceTopology
from topology.topology_builder import TopologyBuilder


class EngineeringKnowledgeEngine:
    """Evaluate engineering knowledge against cases, topology, health, and findings."""

    def __init__(
        self,
        knowledge_registry: EngineeringKnowledgeRegistry | None = None,
        asset_registry: EngineeringAssetRegistry | None = None,
        knowledge_relationships: KnowledgeRelationshipRegistry | None = None,
        asset_relationships: EngineeringRelationshipRegistry | None = None,
    ) -> None:
        self._knowledge_registry = knowledge_registry or EngineeringKnowledgeRegistry()
        self._asset_registry = asset_registry or EngineeringAssetRegistry()
        self._knowledge_relationships = knowledge_relationships or KnowledgeRelationshipRegistry()
        self._asset_relationships = asset_relationships or EngineeringRelationshipRegistry()
        self._matcher = EngineeringKnowledgeMatcher(self._knowledge_registry, self._asset_registry)
        self._graph = EngineeringKnowledgeGraph(
            self._knowledge_registry,
            self._asset_registry,
            self._knowledge_relationships,
            self._asset_relationships,
        )

    @property
    def registry(self) -> EngineeringKnowledgeRegistry:
        """Return the knowledge registry."""
        return self._knowledge_registry

    @property
    def asset_registry(self) -> EngineeringAssetRegistry:
        """Return the asset registry."""
        return self._asset_registry

    @property
    def graph(self) -> EngineeringKnowledgeGraph:
        """Return the knowledge graph."""
        return self._graph

    def evaluate_case(self, case: Case) -> KnowledgeReport:
        """Evaluate engineering knowledge for a case."""
        matches = self._matcher.match_case(case)
        return self._build_report(matches)

    def evaluate_topology(self, topology: VoiceTopology) -> KnowledgeReport:
        """Evaluate engineering knowledge for a topology."""
        matches = self._matcher.match_topology(topology)
        return self._build_report(matches)

    def evaluate_health(self, health: HealthReport) -> KnowledgeReport:
        """Evaluate engineering knowledge for health results."""
        matches = self._matcher.match_health(health)
        return self._build_report(matches)

    def evaluate_findings(self, findings: tuple[AnalysisFinding, ...]) -> KnowledgeReport:
        """Evaluate engineering knowledge for investigation findings."""
        matches = self._matcher.match_findings(findings)
        return self._build_report(matches)

    def find_related_knowledge(self, knowledge_id: str) -> tuple[EngineeringKnowledge, ...]:
        """Return knowledge entries related to a knowledge ID."""
        related_ids = set(self._graph.related(knowledge_id))
        related_ids.update(self._graph.dependencies(knowledge_id))
        related_ids.update(self._graph.references(knowledge_id))
        return tuple(
            self._knowledge_registry.get(related_id)
            for related_id in sorted(related_ids)
            if self._knowledge_registry.exists(related_id)
        )

    def find_verification_guides(self) -> tuple[EngineeringKnowledge, ...]:
        """Return knowledge entries linked to verification guide assets."""
        return self._find_by_asset_type(EngineeringAssetType.VERIFICATION_GUIDE)

    def find_runbooks(self) -> tuple[EngineeringKnowledge, ...]:
        """Return knowledge entries linked to runbook assets."""
        return self._find_by_asset_type(EngineeringAssetType.RUNBOOK)

    def find_references(self, knowledge_id: str) -> tuple[EngineeringKnowledge, ...]:
        """Return knowledge entries referenced by a knowledge ID."""
        reference_ids = set(self._graph.references(knowledge_id))
        return tuple(
            self._knowledge_registry.get(item_id)
            for item_id in sorted(reference_ids)
            if self._knowledge_registry.exists(item_id)
        )

    def find_related_incidents(self) -> tuple[EngineeringKnowledge, ...]:
        """Return knowledge entries linked to incident assets."""
        return self._find_by_asset_type(EngineeringAssetType.INCIDENT)

    def format_report(self, report: KnowledgeReport) -> str:
        """Return markdown for a knowledge report."""
        return format_knowledge_report_markdown(report)

    def _find_by_asset_type(self, asset_type: EngineeringAssetType) -> tuple[EngineeringKnowledge, ...]:
        asset_ids = {
            asset.asset_id
            for asset in self._asset_registry.list_assets()
            if asset.asset_type == asset_type
        }
        return tuple(
            knowledge
            for knowledge in self._knowledge_registry.list_knowledge()
            if asset_ids.intersection(set(knowledge.asset_ids))
        )

    def _build_report(self, matches: tuple) -> KnowledgeReport:
        related_assets = self._related_assets_for_matches(matches)
        recommendations = build_recommendations_from_assets(matches, related_assets)
        return build_knowledge_report(
            matches,
            related_assets=related_assets,
            recommendations=recommendations,
        )

    def _related_assets_for_matches(self, matches: tuple) -> tuple:
        asset_ids: set[str] = set()
        for match in matches:
            asset_ids.update(match.matched_asset_ids)
            if self._knowledge_registry.exists(match.knowledge_id):
                asset_ids.update(self._knowledge_registry.get(match.knowledge_id).asset_ids)
        assets = tuple(
            self._asset_registry.get(asset_id)
            for asset_id in sorted(asset_ids)
            if self._asset_registry.exists(asset_id)
        )
        return assets


def evaluate_case_with_topology(case: Case, engine: EngineeringKnowledgeEngine | None = None) -> KnowledgeReport:
    """Evaluate a case, falling back to topology when no direct matches exist."""
    evaluator = engine or EngineeringKnowledgeEngine()
    report = evaluator.evaluate_case(case)
    if report.matches:
        return report
    topology = TopologyBuilder().build(case.voice_objects)
    return evaluator.evaluate_topology(topology)
