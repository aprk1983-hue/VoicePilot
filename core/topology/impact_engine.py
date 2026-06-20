"""Deterministic operational impact analysis over voice topology graphs."""

from __future__ import annotations

from model.voice_graph import (
    OBJECT_TYPE_DIAL_PEER,
    OBJECT_TYPE_PROVIDER,
    OBJECT_TYPE_SIP_UA,
    OBJECT_TYPE_VOICE_SERVICE,
    VoiceObject,
)
from model.voice_topology import VoiceTopology
from topology.dependency_engine import DependencyEngine
from topology.impact_models import (
    ImpactDependencyPath,
    ImpactReport,
    ImpactSeverity,
)
from topology.topology_exceptions import TopologyObjectNotFoundError

_SCENARIO_FAILURE = "failure"
_SCENARIO_REMOVAL = "removal"
_SCENARIO_CONFIGURATION_CHANGE = "configuration_change"

_TYPE_RECOMMENDATIONS: dict[str, str] = {
    OBJECT_TYPE_SIP_UA: "Validate SIP registration after change.",
    OBJECT_TYPE_VOICE_SERVICE: "Verify all outbound dial peers.",
    OBJECT_TYPE_DIAL_PEER: "Perform outbound PSTN test.",
    OBJECT_TYPE_PROVIDER: "Verify all associated trunks.",
}


class ImpactEngine:
    """Predict graph-derived operational impact using dependency traversal."""

    def __init__(self, dependency_engine: DependencyEngine | None = None) -> None:
        self._dependency_engine = dependency_engine or DependencyEngine()

    def analyze_failure(self, topology: VoiceTopology, object_id: str) -> ImpactReport:
        """Assess impact if the object fails."""
        return self._analyze(topology, object_id, scenario=_SCENARIO_FAILURE)

    def analyze_removal(self, topology: VoiceTopology, object_id: str) -> ImpactReport:
        """Assess impact if the object is removed."""
        return self._analyze(topology, object_id, scenario=_SCENARIO_REMOVAL)

    def analyze_configuration_change(
        self,
        topology: VoiceTopology,
        object_id: str,
    ) -> ImpactReport:
        """Assess impact if the object configuration changes."""
        return self._analyze(topology, object_id, scenario=_SCENARIO_CONFIGURATION_CHANGE)

    def _analyze(
        self,
        topology: VoiceTopology,
        object_id: str,
        *,
        scenario: str,
    ) -> ImpactReport:
        object_index = {obj.id: obj for obj in topology.all_objects()}
        if object_id not in object_index:
            raise TopologyObjectNotFoundError(object_id)

        affected_object = object_index[object_id]
        dependent_ids = self._dependency_engine.get_transitive_dependents(topology, object_id)
        impacted_objects = tuple(object_index[dependent_id] for dependent_id in dependent_ids)
        dependency_paths = tuple(
            ImpactDependencyPath(
                impacted_object_id=impacted_object.id,
                relationships=self._dependency_engine.explain_dependency_path(
                    topology,
                    impacted_object.id,
                    object_id,
                ),
            )
            for impacted_object in impacted_objects
        )
        severity = _severity_for_dependent_count(len(impacted_objects))

        return ImpactReport(
            affected_object=affected_object,
            severity=severity,
            impacted_objects=impacted_objects,
            dependency_paths=dependency_paths,
            summary=_build_summary(
                affected_object=affected_object,
                impacted_count=len(impacted_objects),
                scenario=scenario,
            ),
            recommendations=_build_recommendations(affected_object),
        )


def _severity_for_dependent_count(count: int) -> ImpactSeverity:
    if count == 0:
        return ImpactSeverity.LOW
    if count <= 2:
        return ImpactSeverity.MEDIUM
    if count <= 5:
        return ImpactSeverity.HIGH
    return ImpactSeverity.CRITICAL


def _build_summary(
    *,
    affected_object: VoiceObject,
    impacted_count: int,
    scenario: str,
) -> str:
    label = f"{affected_object.name} ({affected_object.object_type})"
    if scenario == _SCENARIO_FAILURE:
        prefix = f"Failure of {label}"
    elif scenario == _SCENARIO_REMOVAL:
        prefix = f"Removal of {label}"
    else:
        prefix = f"Configuration change to {label}"

    if impacted_count == 0:
        return f"{prefix} has no graph-derived dependents."
    suffix = "object" if impacted_count == 1 else "objects"
    return f"{prefix} would impact {impacted_count} dependent {suffix}."


def _build_recommendations(affected_object: VoiceObject) -> tuple[str, ...]:
    recommendation = _TYPE_RECOMMENDATIONS.get(affected_object.object_type)
    if recommendation is None:
        return ()
    return (recommendation,)
