"""Knowledge evaluation engine."""

from __future__ import annotations

from domain.models import Case
from knowledge.knowledge_matcher import KnowledgeMatcher, _build_match, _match_sort_key
from knowledge.knowledge_models import KnowledgeMatch
from knowledge.knowledge_registry import KnowledgeRegistry
from knowledge.knowledge_report import KnowledgeReport
from model.voice_graph import VoiceObject
from model.voice_topology import VoiceTopology
from topology.topology_builder import TopologyBuilder


class KnowledgeEngine:
    """Evaluate canonical voice objects against registered knowledge packs."""

    def __init__(self, registry: KnowledgeRegistry | None = None) -> None:
        self._registry = registry or KnowledgeRegistry()
        self._matcher = KnowledgeMatcher(self._registry)

    @property
    def registry(self) -> KnowledgeRegistry:
        """Return the engine registry."""
        return self._registry

    def evaluate_object(self, obj: VoiceObject) -> tuple[KnowledgeMatch, ...]:
        """Return knowledge matches for one object."""
        matches = [_build_match(pack, obj) for pack in self._matcher.match_object(obj)]
        return tuple(sorted(matches, key=_match_sort_key))

    def evaluate_topology(self, topology: VoiceTopology) -> KnowledgeReport:
        """Evaluate all objects in a topology."""
        matches = self._matcher.match_topology(topology)
        return _build_knowledge_report(matches)

    def evaluate_case(self, case: Case) -> KnowledgeReport:
        """Evaluate all voice objects attached to a case."""
        topology = TopologyBuilder().build(case.voice_objects)
        return self.evaluate_topology(topology)


def _build_knowledge_report(matches: tuple[KnowledgeMatch, ...]) -> KnowledgeReport:
    recommendations: list[str] = []
    references: list[str] = []
    seen_recommendations: set[str] = set()
    seen_references: set[str] = set()

    for match in matches:
        for recommendation in match.recommendations:
            if recommendation in seen_recommendations:
                continue
            seen_recommendations.add(recommendation)
            recommendations.append(recommendation)
        for reference in match.references:
            if reference in seen_references:
                continue
            seen_references.add(reference)
            references.append(reference)

    summary = _build_summary(len(matches))
    return KnowledgeReport(
        matched_packs=matches,
        recommendations=tuple(recommendations),
        references=tuple(references),
        summary=summary,
    )


def _build_summary(match_count: int) -> str:
    if match_count == 0:
        return "No knowledge packs matched."
    suffix = "pack" if match_count == 1 else "packs"
    return f"Matched {match_count} knowledge {suffix}."
