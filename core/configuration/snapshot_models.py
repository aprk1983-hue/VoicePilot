"""Configuration snapshot data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from health.health_report import HealthReport
from knowledge.knowledge_report import KnowledgeReport
from model.voice_graph import VoiceObject, VoiceRelationship
from shared.types import JsonDict


@dataclass(frozen=True)
class ConfigurationSnapshot:
    """Immutable point-in-time capture of canonical voice configuration."""

    snapshot_id: str
    timestamp: datetime
    hostname: str
    vendor: str
    platform: str
    software_version: str
    voice_objects: tuple[VoiceObject, ...]
    relationships: tuple[VoiceRelationship, ...]
    health_report: HealthReport
    knowledge_report: KnowledgeReport
    metadata: JsonDict = field(default_factory=dict)
    snapshot_hash: str = ""
