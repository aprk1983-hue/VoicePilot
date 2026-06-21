"""Tests for the Engineering Knowledge Framework."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone

import pytest

from domain.models import AnalysisFinding
from engineering_assets import (
    EngineeringAsset,
    EngineeringAssetRegistry,
    EngineeringAssetStatus,
    EngineeringAssetType,
    EngineeringCategory,
    EngineeringRelationship,
    EngineeringRelationshipRegistry,
    EngineeringRelationshipType,
)
from engineering_knowledge import (
    DuplicateEngineeringKnowledgeError,
    DuplicateKnowledgeRelationshipError,
    EngineeringKnowledge,
    EngineeringKnowledgeEngine,
    EngineeringKnowledgeGraph,
    EngineeringKnowledgeMatcher,
    EngineeringKnowledgeRegistry,
    KnowledgeRelationship,
    KnowledgeRelationshipRegistry,
    KnowledgeRelationshipType,
    format_knowledge_report_markdown,
)
from health.health_models import HealthResult, HealthStatus
from health.health_report import HealthReport
from health.health_categories import HealthCategory
from health.health_severity import HealthSeverity
from model import SipUA
from model.voice_graph import OBJECT_TYPE_SIP_UA
from topology.topology_builder import TopologyBuilder


def _asset(
    asset_id: str,
    *,
    asset_type: EngineeringAssetType = EngineeringAssetType.RUNBOOK,
    tags: tuple[str, ...] = ("operations",),
) -> EngineeringAsset:
    now = datetime(2026, 6, 19, 12, 0, tzinfo=timezone.utc)
    return EngineeringAsset(
        asset_id=asset_id,
        title=f"Asset {asset_id}",
        asset_type=asset_type,
        category=EngineeringCategory.GENERAL,
        vendor="ExampleVendor",
        product="ExampleProduct",
        version="1.0",
        summary=f"Summary for {asset_id}",
        description="Generic asset description",
        tags=tags,
        references=(),
        related_asset_ids=(),
        metadata={},
        created_at=now,
        updated_at=now,
        status=EngineeringAssetStatus.ACTIVE,
        source="unit-test",
        confidence=0.9,
    )


def _knowledge(
    knowledge_id: str,
    *,
    asset_ids: tuple[str, ...] = (),
    match_signals: tuple[str, ...] = (),
    match_object_types: tuple[str, ...] = (),
    match_health_rule_ids: tuple[str, ...] = (),
) -> EngineeringKnowledge:
    return EngineeringKnowledge(
        knowledge_id=knowledge_id,
        title=f"Knowledge {knowledge_id}",
        summary=f"Summary for {knowledge_id}",
        asset_ids=asset_ids,
        tags=("operations",),
        match_signals=match_signals,
        match_object_types=match_object_types,
        match_health_rule_ids=match_health_rule_ids,
        confidence=0.8,
    )


def _sample_setup() -> tuple[EngineeringKnowledgeRegistry, EngineeringAssetRegistry, EngineeringKnowledgeEngine]:
    knowledge_registry = EngineeringKnowledgeRegistry()
    asset_registry = EngineeringAssetRegistry()
    asset_registry.register(_asset("EAF-RB-001", asset_type=EngineeringAssetType.RUNBOOK))
    asset_registry.register(
        _asset("EAF-VG-001", asset_type=EngineeringAssetType.VERIFICATION_GUIDE)
    )
    asset_registry.register(_asset("EAF-INC-001", asset_type=EngineeringAssetType.INCIDENT))
    knowledge_registry.register(
        _knowledge(
            "EKF-001",
            asset_ids=("EAF-RB-001", "EAF-VG-001"),
            match_signals=("service_unavailable",),
            match_object_types=(OBJECT_TYPE_SIP_UA,),
            match_health_rule_ids=("health-rule-001",),
        )
    )
    knowledge_registry.register(
        _knowledge("EKF-002", asset_ids=("EAF-INC-001",), match_signals=("link_down",))
    )
    engine = EngineeringKnowledgeEngine(
        knowledge_registry=knowledge_registry,
        asset_registry=asset_registry,
    )
    return knowledge_registry, asset_registry, engine


class TestKnowledgeModels:
    def test_models_are_immutable(self) -> None:
        knowledge = _knowledge("EKF-immutable")

        with pytest.raises(FrozenInstanceError):
            knowledge.title = "changed"  # type: ignore[misc]


class TestKnowledgeRegistry:
    def test_register_lookup_list_and_remove(self) -> None:
        registry = EngineeringKnowledgeRegistry()
        entry = _knowledge("EKF-001")
        registry.register(entry)

        assert registry.exists("EKF-001")
        assert registry.get("EKF-001") == entry
        assert [item.knowledge_id for item in registry.list_knowledge()] == ["EKF-001"]

        registry.remove("EKF-001")
        assert not registry.exists("EKF-001")

    def test_duplicate_prevention(self) -> None:
        registry = EngineeringKnowledgeRegistry()
        registry.register(_knowledge("EKF-dup"))

        with pytest.raises(DuplicateEngineeringKnowledgeError):
            registry.register(_knowledge("EKF-dup"))


class TestKnowledgeRelationships:
    def test_relationship_lookup(self) -> None:
        relationships = KnowledgeRelationshipRegistry()
        relationship = KnowledgeRelationship(
            source_knowledge_id="EKF-001",
            target_knowledge_id="EKF-002",
            relationship_type=KnowledgeRelationshipType.REFERENCES,
        )
        relationships.register(relationship)

        assert relationships.find_for_knowledge("EKF-001") == (relationship,)
        assert relationships.find_by_type(KnowledgeRelationshipType.REFERENCES) == (relationship,)

    def test_duplicate_relationship_prevention(self) -> None:
        relationships = KnowledgeRelationshipRegistry()
        relationship = KnowledgeRelationship(
            source_knowledge_id="EKF-001",
            target_knowledge_id="EKF-002",
            relationship_type=KnowledgeRelationshipType.RELATED,
        )
        relationships.register(relationship)

        with pytest.raises(DuplicateKnowledgeRelationshipError):
            relationships.register(relationship)


class TestKnowledgeGraph:
    def test_graph_views_and_traversal(self) -> None:
        knowledge_registry = EngineeringKnowledgeRegistry()
        asset_registry = EngineeringAssetRegistry()
        knowledge_relationships = KnowledgeRelationshipRegistry()
        asset_registry.register(_asset("EAF-A"))
        asset_registry.register(_asset("EAF-B"))
        knowledge_registry.register(_knowledge("EKF-A", asset_ids=("EAF-A",)))
        knowledge_registry.register(_knowledge("EKF-B", asset_ids=("EAF-B",)))
        knowledge_relationships.register(
            KnowledgeRelationship(
                source_knowledge_id="EKF-A",
                target_knowledge_id="EKF-B",
                relationship_type=KnowledgeRelationshipType.DEPENDS_ON,
            )
        )
        knowledge_relationships.register(
            KnowledgeRelationship(
                source_knowledge_id="EKF-A",
                target_knowledge_id="EKF-B",
                relationship_type=KnowledgeRelationshipType.RELATED,
            )
        )
        graph = EngineeringKnowledgeGraph(
            knowledge_registry,
            asset_registry,
            knowledge_relationships,
        )

        assert "EKF-B" in graph.dependencies("EKF-A")
        assert "EAF-A" in graph.references("EKF-A")
        assert "EKF-B" in graph.related("EKF-A")

        dfs = graph.traverse_depth_first("EKF-A")
        bfs = graph.traverse_breadth_first("EKF-A")

        assert dfs.start_node == "EKF-A"
        assert bfs.start_node == "EKF-A"
        assert "EKF-A" in dfs.visited_nodes

    def test_cycle_handling_does_not_revisit_nodes(self) -> None:
        knowledge_registry = EngineeringKnowledgeRegistry()
        asset_registry = EngineeringAssetRegistry()
        knowledge_relationships = KnowledgeRelationshipRegistry()
        knowledge_registry.register(_knowledge("EKF-A"))
        knowledge_registry.register(_knowledge("EKF-B"))
        knowledge_registry.register(_knowledge("EKF-C"))
        knowledge_relationships.register(
            KnowledgeRelationship("EKF-A", "EKF-B", KnowledgeRelationshipType.RELATED)
        )
        knowledge_relationships.register(
            KnowledgeRelationship("EKF-B", "EKF-C", KnowledgeRelationshipType.RELATED)
        )
        knowledge_relationships.register(
            KnowledgeRelationship("EKF-C", "EKF-A", KnowledgeRelationshipType.RELATED)
        )
        graph = EngineeringKnowledgeGraph(
            knowledge_registry,
            asset_registry,
            knowledge_relationships,
        )

        traversal = graph.traverse_depth_first("EKF-A", max_depth=10)

        assert len(traversal.visited_nodes) == len(set(traversal.visited_nodes))


class TestKnowledgeMatcher:
    def test_matcher_ranks_matches_deterministically(self) -> None:
        knowledge_registry, asset_registry, _engine = _sample_setup()
        matcher = EngineeringKnowledgeMatcher(knowledge_registry, asset_registry)

        asset_matches = matcher.match_assets((asset_registry.get("EAF-RB-001"),))
        finding = AnalysisFinding.create(
            "CASE-001",
            "EVD-001",
            "show status",
            "service_unavailable",
        )
        finding_matches = matcher.match_findings((finding,))
        sip_ua = SipUA.create(
            vendor="example",
            platform="ExampleProduct",
            hostname="edge-01",
            enabled=False,
            object_id="VOBJ-001",
            source_parser="example_parser",
            source_command="show status",
            source_evidence_id="EVD-001",
        )
        object_matches = matcher.match_voice_objects((sip_ua,))

        assert asset_matches[0].knowledge_id == "EKF-001"
        assert finding_matches[0].knowledge_id == "EKF-001"
        assert object_matches[0].knowledge_id == "EKF-001"
        assert asset_matches[0].score >= finding_matches[0].score

    def test_health_matching(self) -> None:
        _, asset_registry, engine = _sample_setup()
        health = HealthReport(
            overall_score=50,
            pass_count=0,
            warn_count=0,
            fail_count=1,
            category_counts=((HealthCategory.SIP, 1),),
            severity_counts=(("high", 1),),
            results=(
                HealthResult(
                    rule_id="health-rule-001",
                    title="Example health rule",
                    description="Generic health issue",
                    category=HealthCategory.SIP,
                    severity=HealthSeverity.HIGH,
                    status=HealthStatus.FAIL,
                    object_id="VOBJ-001",
                    object_type=OBJECT_TYPE_SIP_UA,
                    message="Example failure",
                ),
            ),
        )

        report = engine.evaluate_health(health)

        assert report.matches
        assert report.matches[0].knowledge_id == "EKF-001"


class TestKnowledgeEngine:
    def test_evaluate_findings_and_search_helpers(self) -> None:
        _, _, engine = _sample_setup()
        finding = AnalysisFinding.create(
            "CASE-001",
            "EVD-001",
            "show status",
            "service_unavailable",
        )

        report = engine.evaluate_findings((finding,))

        assert report.matches
        assert engine.find_runbooks()
        assert engine.find_verification_guides()
        assert engine.find_related_incidents()

    def test_evaluate_topology(self) -> None:
        _, _, engine = _sample_setup()
        sip_ua = SipUA.create(
            vendor="example",
            platform="ExampleProduct",
            hostname="edge-01",
            enabled=False,
            object_id="VOBJ-001",
            source_parser="example_parser",
            source_command="show status",
            source_evidence_id="EVD-001",
        )
        topology = TopologyBuilder().build([sip_ua])

        report = engine.evaluate_topology(topology)

        assert report.matches[0].match_source == "voice_object"

    def test_find_related_knowledge(self) -> None:
        knowledge_registry = EngineeringKnowledgeRegistry()
        asset_registry = EngineeringAssetRegistry()
        relationships = KnowledgeRelationshipRegistry()
        knowledge_registry.register(_knowledge("EKF-A"))
        knowledge_registry.register(_knowledge("EKF-B"))
        relationships.register(
            KnowledgeRelationship("EKF-A", "EKF-B", KnowledgeRelationshipType.RELATED)
        )
        engine = EngineeringKnowledgeEngine(
            knowledge_registry=knowledge_registry,
            asset_registry=asset_registry,
            knowledge_relationships=relationships,
        )

        related = engine.find_related_knowledge("EKF-A")

        assert len(related) == 1
        assert related[0].knowledge_id == "EKF-B"


class TestKnowledgeReport:
    def test_markdown_report_sections(self) -> None:
        _, _, engine = _sample_setup()
        finding = AnalysisFinding.create(
            "CASE-001",
            "EVD-001",
            "show status",
            "service_unavailable",
        )
        report = engine.evaluate_findings((finding,))
        markdown = format_knowledge_report_markdown(report)

        assert "# Engineering Knowledge Report" in markdown
        assert "## Matched Knowledge" in markdown
        assert "## Related Assets" in markdown
        assert "## Recommended Reading" in markdown
        assert "## Verification Guides" in markdown
        assert "## Runbooks" in markdown
        assert "## References" in markdown
        assert "EKF-001" in markdown
