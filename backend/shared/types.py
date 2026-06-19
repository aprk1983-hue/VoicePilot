"""Shared type aliases for the VoicePilot Runtime Kernel."""

from __future__ import annotations

from typing import Any, TypeAlias

CaseId: TypeAlias = str
EvidenceId: TypeAlias = str
HypothesisId: TypeAlias = str
DecisionId: TypeAlias = str
QuestionId: TypeAlias = str
RecommendationId: TypeAlias = str
VerificationId: TypeAlias = str
TimelineEventId: TypeAlias = str
TopologyId: TypeAlias = str
DeviceId: TypeAlias = str
InvestigationStepId: TypeAlias = str
PlaybookId: TypeAlias = str
ConfidenceScoreId: TypeAlias = str
EngineName: TypeAlias = str
JsonDict: TypeAlias = dict[str, Any]
