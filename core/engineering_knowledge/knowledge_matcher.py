"""Deterministic engineering knowledge matcher."""

from __future__ import annotations

from domain.models import AnalysisFinding, Case
from engineering_assets.asset_models import EngineeringAsset
from engineering_assets.asset_registry import EngineeringAssetRegistry
from engineering_knowledge.knowledge_models import EngineeringKnowledge, KnowledgeMatch
from engineering_knowledge.knowledge_registry import EngineeringKnowledgeRegistry
from health.health_models import HealthResult
from health.health_report import HealthReport
from model.voice_graph import VoiceObject
from model.voice_topology import VoiceTopology


class EngineeringKnowledgeMatcher:
    """Match engineering knowledge to assets, objects, health, and findings."""

    def __init__(
        self,
        knowledge_registry: EngineeringKnowledgeRegistry,
        asset_registry: EngineeringAssetRegistry,
    ) -> None:
        self._knowledge_registry = knowledge_registry
        self._asset_registry = asset_registry

    def match_assets(self, assets: tuple[EngineeringAsset, ...]) -> tuple[KnowledgeMatch, ...]:
        """Match knowledge entries to engineering assets."""
        matches: list[KnowledgeMatch] = []
        for knowledge in self._knowledge_registry.list_knowledge():
            matched_asset_ids = tuple(
                asset.asset_id
                for asset in assets
                if asset.asset_id in knowledge.asset_ids
                or _tag_overlap(asset.tags, knowledge.tags)
            )
            if matched_asset_ids:
                matches.append(
                    _build_match(
                        knowledge,
                        matched_asset_ids=matched_asset_ids,
                        match_reason="Linked engineering asset or shared tag",
                        score=100.0 + knowledge.confidence * 10.0 + len(matched_asset_ids),
                        match_source="asset",
                    )
                )
        return _sort_matches(matches)

    def match_voice_objects(self, objects: tuple[VoiceObject, ...]) -> tuple[KnowledgeMatch, ...]:
        """Match knowledge entries to canonical voice objects."""
        matches: list[KnowledgeMatch] = []
        object_types = {obj.object_type for obj in objects}
        for knowledge in self._knowledge_registry.list_knowledge():
            if not knowledge.match_object_types:
                continue
            if not object_types.intersection(set(knowledge.match_object_types)):
                continue
            matched_asset_ids = knowledge.asset_ids
            matches.append(
                _build_match(
                    knowledge,
                    matched_asset_ids=matched_asset_ids,
                    match_reason="Matched canonical voice object type",
                    score=60.0 + knowledge.confidence * 10.0,
                    match_source="voice_object",
                )
            )
        return _sort_matches(matches)

    def match_health(self, health: HealthReport | tuple[HealthResult, ...]) -> tuple[KnowledgeMatch, ...]:
        """Match knowledge entries to health evaluation results."""
        results = health.results if isinstance(health, HealthReport) else health
        matches: list[KnowledgeMatch] = []
        rule_ids = {result.rule_id for result in results}
        for knowledge in self._knowledge_registry.list_knowledge():
            if not knowledge.match_health_rule_ids:
                continue
            if not rule_ids.intersection(set(knowledge.match_health_rule_ids)):
                continue
            matches.append(
                _build_match(
                    knowledge,
                    matched_asset_ids=knowledge.asset_ids,
                    match_reason="Matched health rule identifier",
                    score=50.0 + knowledge.confidence * 10.0,
                    match_source="health",
                )
            )
        return _sort_matches(matches)

    def match_findings(self, findings: tuple[AnalysisFinding, ...]) -> tuple[KnowledgeMatch, ...]:
        """Match knowledge entries to investigation findings."""
        matches: list[KnowledgeMatch] = []
        signals = {finding.signal for finding in findings}
        for knowledge in self._knowledge_registry.list_knowledge():
            if not knowledge.match_signals:
                continue
            overlap = signals.intersection(set(knowledge.match_signals))
            if not overlap:
                continue
            matches.append(
                _build_match(
                    knowledge,
                    matched_asset_ids=knowledge.asset_ids,
                    match_reason=f"Matched finding signals: {', '.join(sorted(overlap))}",
                    score=80.0 + len(overlap) * 5.0 + knowledge.confidence * 10.0,
                    match_source="finding",
                )
            )
        return _sort_matches(matches)

    def match_case(self, case: Case) -> tuple[KnowledgeMatch, ...]:
        """Match knowledge entries using case findings and voice objects."""
        finding_matches = self.match_findings(tuple(case.analysis_findings))
        object_matches = self.match_voice_objects(tuple(case.voice_objects))
        asset_matches = self._match_case_assets(case)
        return _merge_matches(finding_matches + object_matches + asset_matches)

    def match_topology(self, topology: VoiceTopology) -> tuple[KnowledgeMatch, ...]:
        """Match knowledge entries using all objects in a topology."""
        return self.match_voice_objects(topology.all_objects())

    def _match_case_assets(self, case: Case) -> tuple[KnowledgeMatch, ...]:
        asset_ids = case.metadata.get("engineering_asset_ids", [])
        if not asset_ids:
            return ()
        assets = tuple(
            self._asset_registry.get(asset_id)
            for asset_id in asset_ids
            if self._asset_registry.exists(asset_id)
        )
        return self.match_assets(assets)


def _build_match(
    knowledge: EngineeringKnowledge,
    *,
    matched_asset_ids: tuple[str, ...],
    match_reason: str,
    score: float,
    match_source: str,
) -> KnowledgeMatch:
    return KnowledgeMatch(
        knowledge_id=knowledge.knowledge_id,
        title=knowledge.title,
        summary=knowledge.summary,
        matched_asset_ids=matched_asset_ids,
        match_reason=match_reason,
        score=score,
        match_source=match_source,
    )


def _sort_matches(matches: list[KnowledgeMatch]) -> tuple[KnowledgeMatch, ...]:
    return tuple(sorted(matches, key=lambda item: (-item.score, item.knowledge_id)))


def _merge_matches(matches: tuple[KnowledgeMatch, ...]) -> tuple[KnowledgeMatch, ...]:
    merged: dict[str, KnowledgeMatch] = {}
    for match in matches:
        existing = merged.get(match.knowledge_id)
        if existing is None or match.score > existing.score:
            merged[match.knowledge_id] = match
    return tuple(sorted(merged.values(), key=lambda item: (-item.score, item.knowledge_id)))


def _tag_overlap(left: tuple[str, ...], right: tuple[str, ...]) -> bool:
    left_values = {tag.strip().lower() for tag in left}
    right_values = {tag.strip().lower() for tag in right}
    return bool(left_values.intersection(right_values))
