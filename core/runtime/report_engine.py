"""Deterministic incident report generation from closed cases."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from domain.enums import InvestigationState
from domain.models import Case, CorrelationResult, DecisionLogEntry, Hypothesis, Recommendation
from model.dial_peer import DialPeer
from model.provider import Provider
from model.sip_ua import SipUA
from model.voice_graph import (
    OBJECT_TYPE_DIAL_PEER,
    OBJECT_TYPE_PROVIDER,
    OBJECT_TYPE_SIP_UA,
    OBJECT_TYPE_VOICE_SERVICE,
    VoiceObject,
)
from health.health_engine import HealthEngine
from health.health_models import HealthResult, HealthStatus
from health.health_severity import HealthSeverity
from runtime.knowledge_bootstrap import default_knowledge_engine
from topology.call_path_engine import CallPathEngine
from topology.topology_builder import TopologyBuilder
from runtime.decision_log_engine import _finding_labels, _timeline_category
from runtime.analysis_engine import (
    format_finding_source_label,
    summarize_structured_data,
)
from runtime.recommendation_engine import ACTION_LIKELY_ROOT_CAUSE
from runtime.verification_engine import RESULT_PASSED

VERIFICATION_OUTCOME_PASSED = "all_steps_passed"
VERIFICATION_OUTCOME_PARTIAL = "partial"
VERIFICATION_OUTCOME_NONE = "not_recorded"


_DISABLED_SIP_UA_NOTE = (
    "SIP-UA is disabled and may affect all SIP call processing, "
    "even if not directly present in the current path graph."
)


@dataclass(frozen=True)
class ReportKnowledgeMatch:
    """Knowledge pack match included in an incident report."""

    pack_id: str
    title: str
    severity: str
    category: str
    matched_object: str
    recommendation: str
    references: tuple[str, ...]


@dataclass(frozen=True)
class ReportKnowledgeAssessment:
    """Knowledge evaluation summary for an incident report."""

    available: bool
    matches: tuple[ReportKnowledgeMatch, ...] = ()
    summary: str | None = None


@dataclass(frozen=True)
class ReportHealthFinding:
    """Top health finding included in an incident report."""

    severity: str
    status: str
    message: str
    recommendation: str | None = None


@dataclass(frozen=True)
class ReportHealthAssessment:
    """Health evaluation summary for an incident report."""

    available: bool
    overall_score: int | None = None
    overall_status: str | None = None
    pass_count: int = 0
    warn_count: int = 0
    fail_count: int = 0
    unknown_count: int = 0
    severity_counts: tuple[tuple[str, int], ...] = ()
    category_counts: tuple[tuple[str, int], ...] = ()
    top_findings: tuple[ReportHealthFinding, ...] = ()
    recommendations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReportCallPathBreakpoint:
    """Breakpoint candidate on a modeled call path."""

    label: str
    health_status: str


@dataclass(frozen=True)
class ReportCallPath:
    """Call path included in an incident report."""

    direction: str
    source_label: str
    destination_label: str
    hops: tuple[str, ...]
    warnings: tuple[str, ...]
    breakpoints: tuple[ReportCallPathBreakpoint, ...]


@dataclass(frozen=True)
class ReportCallPathAnalysis:
    """Call path analysis derived from case voice objects."""

    paths: tuple[ReportCallPath, ...]
    disabled_sip_ua_note: str | None = None


@dataclass(frozen=True)
class ReportVoiceObject:
    """Canonical voice object included in an incident report."""

    label: str
    detail: str
    source_parser: str
    source_command: str
    confidence: float


@dataclass(frozen=True)
class ReportFinding:
    """Evidence finding included in an incident report."""

    signal: str
    command: str
    detail: str | None
    source: str | None = None
    structured_summary: str | None = None


@dataclass(frozen=True)
class ReportCorrelation:
    """Correlation result included in an incident report."""

    rule_id: str
    correlation_type: str
    confidence_delta: float
    explanation: str
    evidence_names: tuple[str, ...]


@dataclass(frozen=True)
class ReportDecision:
    """Decision log entry included in an incident report."""

    timestamp: str
    category: str
    title: str
    description: str
    confidence_before: float | None
    confidence_after: float | None
    evidence_names: tuple[str, ...]
    rejected_hypotheses: tuple[str, ...]


@dataclass(frozen=True)
class ReportVerification:
    """Verification step included in an incident report."""

    step_name: str
    description: str
    result_status: str | None
    notes: str | None


@dataclass(frozen=True)
class ReportDiscoveryRequest:
    """Recommended evidence item included in an incident report."""

    command: str
    priority: str
    reason: str
    estimated_confidence_gain: float
    estimated_minutes: int
    optional: bool


@dataclass(frozen=True)
class ReportDiscoveryPlan:
    """Discovery planning summary for an incident report."""

    available: bool
    current_confidence: float | None = None
    estimated_final_confidence: float | None = None
    remaining_uncertainty: float | None = None
    next_best_command: str | None = None
    requests: tuple[ReportDiscoveryRequest, ...] = ()


@dataclass(frozen=True)
class ReportInvestigationQualityMetric:
    """Investigation quality metric included in an incident report."""

    metric_name: str
    score: int
    max_score: int
    status: str
    summary: str
    recommendations: tuple[str, ...]


@dataclass(frozen=True)
class ReportInvestigationQuality:
    """Investigation quality summary for an incident report."""

    available: bool
    overall_score: int | None = None
    overall_status: str | None = None
    ready_for_recommendation: bool | None = None
    ready_for_case_closure: bool | None = None
    metrics: tuple[ReportInvestigationQualityMetric, ...] = ()


@dataclass(frozen=True)
class ReportTimelineEntry:
    """Chronological event included in an incident report."""

    sequence: int
    timestamp: str
    event_type: str
    summary: str


@dataclass(frozen=True)
class IncidentReport:
    """Structured incident report for a closed investigation."""

    case_id: str
    playbook_id: str | None
    final_state: InvestigationState
    symptom: str
    top_hypothesis_title: str | None
    top_hypothesis_id: str | None
    confidence: float | None
    findings: tuple[ReportFinding, ...]
    voice_objects: tuple[ReportVoiceObject, ...]
    call_path_analysis: ReportCallPathAnalysis
    health_assessment: ReportHealthAssessment
    knowledge_assessment: ReportKnowledgeAssessment
    correlations: tuple[ReportCorrelation, ...]
    decisions: tuple[ReportDecision, ...]
    recommendation_summary: str | None
    recommendation_actions: tuple[str, ...]
    verification_outcome: str | None
    verifications: tuple[ReportVerification, ...]
    learning_record_id: str | None
    learning_root_cause: str | None
    learning_reusable_pattern: str | None
    learning_lessons: str | None
    discovery_plan: ReportDiscoveryPlan
    investigation_quality: ReportInvestigationQuality
    timeline: tuple[ReportTimelineEntry, ...]
    closed_at: str | None


class ReportEngine:
    """v1 deterministic incident report generator."""

    def generate(self, case: Case) -> IncidentReport:
        """Build an incident report from a closed case."""
        return build_incident_report(case)


def build_incident_report(case: Case) -> IncidentReport:
    """Build a structured incident report from a closed case."""
    top_hypothesis = _top_hypothesis(case)
    recommendation = _likely_root_cause_recommendation(case)
    learning = case.learning_record

    confidence = _resolve_confidence(top_hypothesis, recommendation, learning)
    top_title = (
        learning.root_cause
        if learning
        else (
            recommendation.likely_root_cause
            if recommendation and recommendation.likely_root_cause
            else top_hypothesis.title if top_hypothesis else None
        )
    )
    top_id = (
        learning.hypothesis_id
        if learning and learning.hypothesis_id
        else top_hypothesis.hypothesis_id if top_hypothesis else None
    )

    return IncidentReport(
        case_id=case.case_id,
        playbook_id=case.playbook_id,
        final_state=case.status,
        symptom=case.symptom.summary,
        top_hypothesis_title=top_title,
        top_hypothesis_id=top_id,
        confidence=confidence,
        findings=tuple(
            ReportFinding(
                signal=finding.signal,
                command=finding.command,
                detail=finding.detail,
                source=format_finding_source_label(finding.metadata),
                structured_summary=summarize_structured_data(finding.metadata),
            )
            for finding in case.analysis_findings
        ),
        voice_objects=tuple(_build_report_voice_objects(case.voice_objects)),
        call_path_analysis=_build_call_path_analysis(case.voice_objects),
        health_assessment=_build_health_assessment(case),
        knowledge_assessment=_build_knowledge_assessment(case),
        correlations=tuple(_build_report_correlations(case.correlation_results)),
        decisions=tuple(_build_report_decisions(case.decision_log)),
        recommendation_summary=_format_recommendation_summary(recommendation),
        recommendation_actions=tuple(recommendation.recommended_actions) if recommendation else (),
        verification_outcome=_verification_outcome(case),
        verifications=tuple(
            ReportVerification(
                step_name=step.step_name,
                description=step.description,
                result_status=step.result_status,
                notes=step.notes,
            )
            for step in case.verifications
        ),
        learning_record_id=learning.learning_record_id if learning else None,
        learning_root_cause=learning.root_cause if learning else None,
        learning_reusable_pattern=learning.reusable_pattern if learning else None,
        learning_lessons=learning.lessons_learned if learning else None,
        discovery_plan=_build_discovery_plan(case),
        investigation_quality=_build_investigation_quality(case),
        timeline=_build_timeline(case),
        closed_at=_format_timestamp(case.closed_at),
    )


def format_incident_report(report: IncidentReport) -> str:
    """Format an incident report as readable Markdown."""
    lines = [
        "# VoicePilot Incident Report",
        "",
        "## Case Overview",
        "",
        f"- **Case ID:** {report.case_id}",
        f"- **Playbook ID:** {report.playbook_id or 'unknown'}",
        f"- **Final State:** {report.final_state.value}",
        f"- **Closed At:** {report.closed_at or 'not recorded'}",
        "",
        "## Symptom",
        "",
        report.symptom,
        "",
        "## Root Cause Assessment",
        "",
    ]

    if report.top_hypothesis_title:
        lines.append(f"- **Top Hypothesis:** {report.top_hypothesis_title}")
    if report.top_hypothesis_id:
        lines.append(f"- **Hypothesis ID:** {report.top_hypothesis_id}")
    if report.confidence is not None:
        lines.append(f"- **Confidence:** {int(report.confidence)}%")

    lines.extend(["", "## Evidence Findings", ""])
    if report.findings:
        for finding in report.findings:
            detail = f" — {finding.detail}" if finding.detail else ""
            source = f" ({finding.source})" if finding.source else ""
            structured = (
                f" — structured: {finding.structured_summary}"
                if finding.structured_summary
                else ""
            )
            lines.append(
                f"- `{finding.command}`: **{finding.signal}**{source}{detail}{structured}"
            )
    else:
        lines.append("_No analysis findings recorded._")

    lines.extend(["", "## Canonical Voice Objects", ""])
    if report.voice_objects:
        for voice_object in report.voice_objects:
            confidence = int(voice_object.confidence)
            lines.append(
                f"- {voice_object.label} — {voice_object.detail} — "
                f"{voice_object.source_parser} — {voice_object.source_command} — {confidence}%"
            )
    else:
        lines.append("_No canonical voice objects recorded._")

    lines.extend(_format_call_path_analysis_section(report.call_path_analysis))
    lines.extend(_format_health_assessment_section(report.health_assessment))
    lines.extend(_format_knowledge_assessment_section(report.knowledge_assessment))

    lines.extend(["", "## Correlation Reasoning", ""])
    if report.correlations:
        for correlation in report.correlations:
            impact = _format_confidence_impact(correlation.confidence_delta)
            lines.append(
                f"- **{correlation.rule_id}** — {correlation.correlation_type}{impact}"
            )
            lines.append(f"  {correlation.explanation}")
            if correlation.evidence_names:
                evidence = ", ".join(correlation.evidence_names)
                lines.append(f"  Evidence: {evidence}")
    else:
        lines.append("_No correlation results recorded._")

    lines.extend(["", "## Decision Timeline", ""])
    if report.decisions:
        for index, decision in enumerate(report.decisions):
            if index > 0:
                lines.append("")
                lines.append("↓")
                lines.append("")
            lines.append(decision.timestamp)
            lines.append(decision.category)
            lines.append(decision.title)
            if decision.description and decision.description != decision.title:
                lines.append(decision.description)
            if decision.confidence_before is not None and decision.confidence_after is not None:
                lines.append(
                    "Confidence: "
                    f"{int(decision.confidence_before)} → {int(decision.confidence_after)}"
                )
            if decision.evidence_names:
                lines.append(f"Evidence: {', '.join(decision.evidence_names)}")
            if decision.rejected_hypotheses:
                lines.append(f"Rejected: {', '.join(decision.rejected_hypotheses)}")
    else:
        lines.append("_No decision log entries recorded._")

    lines.extend(["", "## Recommendation", ""])
    if report.recommendation_summary:
        lines.append(report.recommendation_summary)
    else:
        lines.append("_No recommendation recorded._")

    if report.recommendation_actions:
        lines.append("")
        lines.append("**Recommended Actions:**")
        for action in report.recommendation_actions:
            lines.append(f"- {action}")

    lines.extend(_format_discovery_plan_section(report.discovery_plan))
    lines.extend(_format_investigation_quality_section(report.investigation_quality))

    lines.extend(["", "## Verification", ""])
    if report.verification_outcome:
        lines.append(f"- **Outcome:** {report.verification_outcome.replace('_', ' ')}")
    if report.verifications:
        for step in report.verifications:
            status = step.result_status or "pending"
            note = f" ({step.notes})" if step.notes else ""
            lines.append(f"- {step.step_name}: {step.description} — **{status}**{note}")
    else:
        lines.append("_No verification steps recorded._")

    lines.extend(["", "## Learning Record", ""])
    if report.learning_record_id:
        lines.append(f"- **Learning Record ID:** {report.learning_record_id}")
        if report.learning_root_cause:
            lines.append(f"- **Root Cause:** {report.learning_root_cause}")
        if report.learning_reusable_pattern:
            lines.append(f"- **Reusable Pattern:** {report.learning_reusable_pattern}")
        if report.learning_lessons:
            lines.append(f"- **Lessons Learned:** {report.learning_lessons}")
    else:
        lines.append("_No learning record attached._")

    lines.extend(["", "## Timeline", ""])
    if report.timeline:
        for entry in report.timeline:
            lines.append(
                f"{entry.sequence}. [{entry.timestamp}] {entry.event_type}: {entry.summary}"
            )
    else:
        lines.append("_No timeline events recorded._")

    return "\n".join(lines)


def _build_health_assessment(case: Case) -> ReportHealthAssessment:
    if not case.voice_objects:
        return ReportHealthAssessment(available=False)

    health_report = HealthEngine().evaluate_case(case)
    unknown_count = sum(
        1 for result in health_report.results if result.status == HealthStatus.UNKNOWN
    )
    top_findings = tuple(
        ReportHealthFinding(
            severity=result.severity.value.upper(),
            status=result.status.value.upper(),
            message=result.message,
            recommendation=result.recommendation,
        )
        for result in _top_health_findings(health_report.results)
    )
    category_counts = tuple(
        (category.value, count) for category, count in health_report.category_counts
    )

    return ReportHealthAssessment(
        available=True,
        overall_score=health_report.overall_score,
        overall_status=_overall_health_status(health_report.fail_count, health_report.warn_count),
        pass_count=health_report.pass_count,
        warn_count=health_report.warn_count,
        fail_count=health_report.fail_count,
        unknown_count=unknown_count,
        severity_counts=health_report.severity_counts,
        category_counts=category_counts,
        top_findings=top_findings,
        recommendations=health_report.recommendations,
    )


def _format_health_assessment_section(assessment: ReportHealthAssessment) -> list[str]:
    lines = ["", "## Health Assessment", ""]
    if not assessment.available:
        lines.append("_No canonical voice objects available for health evaluation._")
        return lines

    lines.append(f"- **Overall Score:** {assessment.overall_score}/100")
    lines.append(f"- **Status:** {assessment.overall_status}")
    lines.append(
        "- **Counts:** "
        f"PASS {assessment.pass_count} | "
        f"WARN {assessment.warn_count} | "
        f"FAIL {assessment.fail_count} | "
        f"UNKNOWN {assessment.unknown_count}"
    )

    if assessment.severity_counts:
        severity_text = ", ".join(f"{name} {count}" for name, count in assessment.severity_counts)
        lines.append(f"- **Severity Counts:** {severity_text}")

    if assessment.category_counts:
        category_text = ", ".join(f"{name} {count}" for name, count in assessment.category_counts)
        lines.append(f"- **Category Counts:** {category_text}")

    lines.extend(["", "**Findings:**"])
    if assessment.top_findings:
        for finding in assessment.top_findings:
            lines.append(f"- {finding.severity} {finding.status} — {finding.message}")
            if finding.recommendation:
                lines.append(f"  Recommendation: {finding.recommendation}")
    else:
        lines.append("_No health findings recorded._")

    lines.extend(["", "**Recommendations:**"])
    if assessment.recommendations:
        for recommendation in assessment.recommendations:
            lines.append(f"- {recommendation}")
    else:
        lines.append("_None_")

    return lines


def _build_knowledge_assessment(case: Case) -> ReportKnowledgeAssessment:
    if not case.voice_objects:
        return ReportKnowledgeAssessment(available=False)

    knowledge_report = default_knowledge_engine().evaluate_case(case)
    object_index = {obj.id: obj for obj in case.voice_objects}
    matches = tuple(
        ReportKnowledgeMatch(
            pack_id=match.pack_id,
            title=match.title,
            severity=match.severity.value.upper(),
            category=match.category.value.upper(),
            matched_object=_matched_object_label(object_index.get(match.object_id), match),
            recommendation=match.recommendations[0] if match.recommendations else "",
            references=match.references,
        )
        for match in knowledge_report.matched_packs
    )
    return ReportKnowledgeAssessment(
        available=True,
        matches=matches,
        summary=knowledge_report.summary,
    )


def _matched_object_label(obj: VoiceObject | None, match) -> str:
    if obj is not None:
        return _voice_object_label(obj)
    return match.object_type


def _format_knowledge_assessment_section(assessment: ReportKnowledgeAssessment) -> list[str]:
    lines = ["", "## Matched Knowledge", ""]
    if not assessment.available or not assessment.matches:
        lines.append("_No knowledge packs matched current case._")
        return lines

    for index, match in enumerate(assessment.matches):
        if index > 0:
            lines.append("")
        lines.append(f"### {match.pack_id}")
        lines.append(f"- **Knowledge ID:** {match.pack_id}")
        lines.append(f"- **Title:** {match.title}")
        lines.append(f"- **Severity:** {match.severity}")
        lines.append(f"- **Category:** {match.category}")
        lines.append(f"- **Matched object:** {match.matched_object}")
        lines.append(f"- **Recommendation:** {match.recommendation}")
        if match.references:
            reference_text = "; ".join(match.references)
            lines.append(f"- **References:** {reference_text}")
        else:
            lines.append("- **References:** _None_")

    return lines


_SEVERITY_ORDER = {
    HealthSeverity.CRITICAL: 0,
    HealthSeverity.HIGH: 1,
    HealthSeverity.MEDIUM: 2,
    HealthSeverity.LOW: 3,
    HealthSeverity.INFO: 4,
}


def _top_health_findings(results: tuple[HealthResult, ...]) -> tuple[HealthResult, ...]:
    active = [
        result
        for result in results
        if result.status in {HealthStatus.WARN, HealthStatus.FAIL}
    ]
    return tuple(
        sorted(
            active,
            key=lambda result: (_SEVERITY_ORDER[result.severity], result.rule_id),
        )
    )


def _overall_health_status(fail_count: int, warn_count: int) -> str:
    if fail_count > 0:
        return "FAIL"
    if warn_count > 0:
        return "WARN"
    return "PASS"


def _build_call_path_analysis(voice_objects: list[VoiceObject]) -> ReportCallPathAnalysis:
    if not voice_objects:
        return ReportCallPathAnalysis(paths=())

    topology = TopologyBuilder().build(_supplement_call_path_objects(voice_objects))
    call_path_engine = CallPathEngine()
    outbound_paths = call_path_engine.build_outbound_paths(topology)
    object_index = {obj.id: obj for obj in topology.all_objects()}

    report_paths: list[ReportCallPath] = []
    path_hop_ids: set[str] = set()
    for call_path in outbound_paths:
        path_hop_ids.update(hop.object_id for hop in call_path.hops)
        source_object = object_index.get(call_path.source_object_id)
        destination_object = object_index.get(call_path.destination_object_id)
        breakpoints = call_path_engine.find_breakpoints(call_path)
        report_paths.append(
            ReportCallPath(
                direction=call_path.direction.value,
                source_label=_call_path_endpoint_label(source_object) if source_object else call_path.source_object_id,
                destination_label=(
                    _call_path_endpoint_label(destination_object)
                    if destination_object
                    else call_path.destination_object_id
                ),
                hops=tuple(_call_path_hop_label(hop, object_index) for hop in call_path.hops),
                warnings=call_path.warnings,
                breakpoints=tuple(
                    ReportCallPathBreakpoint(
                        label=_call_path_hop_label(breakpoint, object_index),
                        health_status=breakpoint.health_status,
                    )
                    for breakpoint in breakpoints
                ),
            )
        )

    disabled_sip_ua_note = _disabled_sip_ua_note(voice_objects, path_hop_ids)
    return ReportCallPathAnalysis(
        paths=tuple(report_paths),
        disabled_sip_ua_note=disabled_sip_ua_note,
    )


def _supplement_call_path_objects(voice_objects: list[VoiceObject]) -> list[VoiceObject]:
    """Add provider placeholders from dial-peer session targets for report-time path modeling."""
    if any(obj.object_type == OBJECT_TYPE_PROVIDER for obj in voice_objects):
        return list(voice_objects)

    dial_peers = [obj for obj in voice_objects if isinstance(obj, DialPeer)]
    if not dial_peers:
        return list(voice_objects)

    supplemented = list(voice_objects)
    seen_targets: set[str] = set()
    provider_index = 0
    for dial_peer in sorted(dial_peers, key=lambda item: item.id):
        session_target = (dial_peer.session_target or "").strip()
        if not session_target or session_target in seen_targets:
            continue
        seen_targets.add(session_target)
        provider_index += 1
        provider_suffix = session_target.split(":")[-1] if ":" in session_target else session_target
        supplemented.append(
            Provider.create(
                vendor=dial_peer.vendor,
                platform=dial_peer.platform,
                hostname=dial_peer.hostname,
                name=f"Provider-{provider_suffix}",
                source_parser=dial_peer.source_parser,
                source_command=dial_peer.source_command,
                source_evidence_id=dial_peer.source_evidence_id,
                addresses=(session_target,),
                object_id=f"VOBJ-report-provider-{provider_index:03d}",
            )
        )
    return supplemented


def _disabled_sip_ua_note(voice_objects: list[VoiceObject], path_hop_ids: set[str]) -> str | None:
    for obj in voice_objects:
        if isinstance(obj, SipUA) and obj.enabled is False and obj.id not in path_hop_ids:
            return _DISABLED_SIP_UA_NOTE
    return None


def _format_call_path_analysis_section(analysis: ReportCallPathAnalysis) -> list[str]:
    lines = ["", "## Call Path Analysis", ""]
    if not analysis.paths:
        lines.append("_No call paths derived from current evidence._")
    else:
        for index, call_path in enumerate(analysis.paths):
            if index > 0:
                lines.append("")
            lines.append(f"### {call_path.source_label} → {call_path.destination_label}")
            lines.append(f"- **Direction:** {call_path.direction}")
            lines.append(f"- **Source:** {call_path.source_label}")
            lines.append(f"- **Destination:** {call_path.destination_label}")
            lines.append("")
            lines.append("**Hops:**")
            if call_path.hops:
                for hop_index, hop_label in enumerate(call_path.hops, start=1):
                    lines.append(f"{hop_index}. {hop_label}")
            else:
                lines.append("_No hops recorded._")
            lines.append("")
            lines.append("**Warnings:**")
            if call_path.warnings:
                for warning in call_path.warnings:
                    lines.append(f"- {warning}")
            else:
                lines.append("_None_")
            lines.append("")
            lines.append("**Breakpoints:**")
            if call_path.breakpoints:
                for breakpoint in call_path.breakpoints:
                    lines.append(f"- {breakpoint.label} — {breakpoint.health_status}")
            else:
                lines.append("_None on path._")

    if analysis.disabled_sip_ua_note:
        lines.append("")
        lines.append(f"**Note:** {analysis.disabled_sip_ua_note}")

    return lines


def _call_path_endpoint_label(obj: VoiceObject) -> str:
    if obj.object_type == OBJECT_TYPE_DIAL_PEER:
        return _voice_object_label(obj)
    if obj.object_type == OBJECT_TYPE_PROVIDER:
        return obj.name
    return _voice_object_label(obj)


def _call_path_hop_label(hop, object_index: dict[str, VoiceObject]) -> str:
    obj = object_index.get(hop.object_id)
    if obj is not None:
        return _call_path_endpoint_label(obj)
    return hop.label


def _build_report_voice_objects(objects: list[VoiceObject]) -> list[ReportVoiceObject]:
    return [
        ReportVoiceObject(
            label=_voice_object_label(obj),
            detail=_voice_object_detail(obj),
            source_parser=obj.source_parser,
            source_command=obj.source_command,
            confidence=obj.confidence,
        )
        for obj in objects
    ]


def _voice_object_label(obj: VoiceObject) -> str:
    if obj.object_type == OBJECT_TYPE_DIAL_PEER:
        name = obj.name
        if name.lower().startswith("dial-peer "):
            return f"DialPeer {name.split(' ', 1)[1]}"
        return name
    labels = {
        OBJECT_TYPE_SIP_UA: "SipUA",
        OBJECT_TYPE_VOICE_SERVICE: "VoiceService",
    }
    return labels.get(obj.object_type, obj.object_type)


def _voice_object_detail(obj: VoiceObject) -> str:
    if obj.object_type == OBJECT_TYPE_DIAL_PEER and isinstance(obj, DialPeer):
        if obj.destination_pattern:
            return f"destination {obj.destination_pattern}"
    if obj.object_type == OBJECT_TYPE_SIP_UA:
        return "SIP-UA"
    if obj.object_type == OBJECT_TYPE_VOICE_SERVICE:
        return "voice service voip"
    return obj.name


def _build_report_decisions(entries: list[DecisionLogEntry]) -> list[ReportDecision]:
    ordered = sorted(entries, key=lambda item: item.timestamp)
    report_decisions: list[ReportDecision] = []
    for entry in ordered:
        evidence_names = tuple(_finding_labels(entry))
        if not evidence_names and entry.supporting_findings:
            evidence_names = tuple(entry.supporting_findings)
        report_decisions.append(
            ReportDecision(
                timestamp=entry.timestamp.strftime("%H:%M:%S"),
                category=_timeline_category(entry),
                title=entry.title,
                description=entry.description,
                confidence_before=entry.confidence_before,
                confidence_after=entry.confidence_after,
                evidence_names=evidence_names,
                rejected_hypotheses=entry.rejected_hypotheses,
            )
        )
    return report_decisions


def _build_report_correlations(
    correlations: list[CorrelationResult],
) -> list[ReportCorrelation]:
    return [
        ReportCorrelation(
            rule_id=correlation.rule_id,
            correlation_type=correlation.correlation_type,
            confidence_delta=correlation.confidence_delta,
            explanation=correlation.explanation,
            evidence_names=tuple(correlation.finding_codes),
        )
        for correlation in correlations
    ]


def _format_confidence_impact(delta: float) -> str:
    if delta == 0.0:
        return ""
    value = int(delta)
    sign = "+" if value > 0 else ""
    return f", {sign}{value} confidence"


def _top_hypothesis(case: Case) -> Hypothesis | None:
    if not case.hypotheses:
        return None
    return min(case.hypotheses, key=lambda hypothesis: hypothesis.rank or 999)


def _likely_root_cause_recommendation(case: Case) -> Recommendation | None:
    for recommendation in reversed(case.recommendations):
        if recommendation.action_type == ACTION_LIKELY_ROOT_CAUSE:
            return recommendation
    return None


def _resolve_confidence(
    hypothesis: Hypothesis | None,
    recommendation: Recommendation | None,
    learning,
) -> float | None:
    if learning is not None:
        return learning.confidence
    if recommendation and recommendation.confidence is not None:
        return recommendation.confidence
    if hypothesis is not None:
        return hypothesis.confidence
    return None


def _format_recommendation_summary(recommendation: Recommendation | None) -> str | None:
    if recommendation is None:
        return None
    parts = [recommendation.description]
    if recommendation.likely_root_cause:
        parts.append(f"Likely root cause: {recommendation.likely_root_cause}")
    if recommendation.rationale:
        parts.append(recommendation.rationale)
    return " ".join(part for part in parts if part)


def _verification_outcome(case: Case) -> str | None:
    if not case.verifications:
        return None
    statuses = [step.result_status for step in case.verifications if step.result_status]
    if not statuses:
        return VERIFICATION_OUTCOME_NONE
    if all(status == RESULT_PASSED for status in statuses):
        return VERIFICATION_OUTCOME_PASSED
    return VERIFICATION_OUTCOME_PARTIAL


def _build_timeline(case: Case) -> tuple[ReportTimelineEntry, ...]:
    entries: list[ReportTimelineEntry] = []
    metadata_timeline = case.metadata.get("timeline", {})
    if isinstance(metadata_timeline, dict):
        onset = metadata_timeline.get("onset")
        if onset:
            entries.append(
                ReportTimelineEntry(
                    sequence=0,
                    timestamp="intake",
                    event_type="symptom_onset",
                    summary=f"Symptom onset recorded: {onset}",
                )
            )

    for event in sorted(case.timeline_events, key=lambda item: item.sequence):
        entries.append(
            ReportTimelineEntry(
                sequence=event.sequence,
                timestamp=_format_timestamp(event.timestamp) or "unknown",
                event_type=event.event_type,
                summary=event.summary,
            )
        )
    return tuple(entries)


def _build_discovery_plan(case: Case) -> ReportDiscoveryPlan:
    plan = case.discovery_plan
    if plan is None:
        return ReportDiscoveryPlan(available=False)

    return ReportDiscoveryPlan(
        available=True,
        current_confidence=plan.current_confidence,
        estimated_final_confidence=plan.estimated_final_confidence,
        remaining_uncertainty=plan.remaining_uncertainty,
        next_best_command=plan.next_best_command,
        requests=tuple(
            ReportDiscoveryRequest(
                command=request.command,
                priority=request.priority.value,
                reason=request.reason,
                estimated_confidence_gain=request.estimated_confidence_gain,
                estimated_minutes=request.estimated_minutes,
                optional=request.optional,
            )
            for request in plan.requests
        ),
    )


def _format_discovery_plan_section(plan: ReportDiscoveryPlan) -> list[str]:
    lines = ["", "## Discovery Plan", ""]
    if not plan.available:
        lines.append("_No discovery plan recorded._")
        return lines

    if plan.current_confidence is not None:
        lines.append(f"- **Current Confidence:** {int(plan.current_confidence)}%")
    if plan.estimated_final_confidence is not None:
        lines.append(
            f"- **Estimated Final Confidence:** {int(plan.estimated_final_confidence)}%"
        )
    if plan.remaining_uncertainty is not None:
        lines.append(f"- **Remaining Uncertainty:** {int(plan.remaining_uncertainty)}%")
    if plan.next_best_command:
        lines.append(f"- **Next Best Command:** `{plan.next_best_command}`")

    lines.append("")
    lines.append("**Recommended Evidence:**")
    if plan.requests:
        for index, request in enumerate(plan.requests, start=1):
            optional = " (optional)" if request.optional else ""
            lines.append(
                f"{index}. `{request.command}` — **{request.priority}** — "
                f"{request.reason} (+{int(request.estimated_confidence_gain)}%, "
                f"{request.estimated_minutes} min){optional}"
            )
    else:
        lines.append("_No additional evidence recommended._")

    return lines


def _build_investigation_quality(case: Case) -> ReportInvestigationQuality:
    report = case.investigation_quality_report
    if report is None:
        return ReportInvestigationQuality(available=False)

    return ReportInvestigationQuality(
        available=True,
        overall_score=report.overall_score,
        overall_status=report.overall_status,
        ready_for_recommendation=report.ready_for_recommendation,
        ready_for_case_closure=report.ready_for_case_closure,
        metrics=tuple(
            ReportInvestigationQualityMetric(
                metric_name=metric.metric_name,
                score=metric.score,
                max_score=metric.max_score,
                status=metric.status,
                summary=metric.summary,
                recommendations=metric.recommendations,
            )
            for metric in report.metric_results
        ),
    )


def _format_investigation_quality_section(
    quality: ReportInvestigationQuality,
) -> list[str]:
    from datetime import datetime, timezone

    from investigation_quality.quality_models import InvestigationQualityReport, QualityMetricResult
    from investigation_quality.quality_report import format_investigation_quality_report_section

    if not quality.available:
        return ["", "## Investigation Quality", "", "_No investigation quality report recorded._"]

    report = InvestigationQualityReport(
        overall_score=quality.overall_score or 0,
        overall_status=quality.overall_status or "UNKNOWN",
        metric_results=tuple(
            QualityMetricResult(
                metric_name=metric.metric_name,
                score=metric.score,
                max_score=metric.max_score,
                status=metric.status,
                summary=metric.summary,
                recommendations=metric.recommendations,
            )
            for metric in quality.metrics
        ),
        ready_for_recommendation=bool(quality.ready_for_recommendation),
        ready_for_case_closure=bool(quality.ready_for_case_closure),
        generated_at=datetime.now(timezone.utc),
    )
    return format_investigation_quality_report_section(report)


def _format_timestamp(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()
