"""Engineering Change Package generator — converts investigation output to advisory packages."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from change_package.change_models import (
    ApprovalSection,
    EngineeringChangePackage,
    READ_ONLY_NOTICE,
    RecommendedChange,
    VerificationStep,
)
from change_package.change_risk import ChangeRiskLevel, assess_change_risk, format_risk_summary
from domain.models import Case, Hypothesis, Recommendation
from runtime.recommendation_engine import ACTION_LIKELY_ROOT_CAUSE, VP_CUBE_0001_ACTION_PLANS
from runtime.cucm_investigation import VP_CUCM_0001_ACTION_PLANS, VP_CUCM_0001_PLAYBOOK_ID
from shared.constants import DEFAULT_CONFIDENCE_THRESHOLD

_EXAMPLE_PREFIX = "! Example configuration for engineer review — not applied by VoicePilot"


@dataclass(frozen=True)
class _ChangeTemplate:
    """Advisory configuration template keyed to hypothesis category."""

    current_state: str
    recommended_state: str
    config_example: str
    rollback_example: str
    impacted_objects: tuple[str, ...]
    risk_level: ChangeRiskLevel
    affected_components: tuple[str, ...] = ()
    vendor_references: tuple[str, ...] = ()


VP_CUBE_0001_CHANGE_TEMPLATES: dict[str, _ChangeTemplate] = {
    "HYP-SIP-UA-DISABLED": _ChangeTemplate(
        current_state="CUBE SIP user agent is administratively disabled.",
        recommended_state="SIP-UA enabled for outbound SIP processing.",
        config_example=(
            f"{_EXAMPLE_PREFIX}\n"
            "voice service voip\n"
            " allow-connections sip\n"
            " sip\n"
            "  bind control source-interface <interface>\n"
            " ! Confirm SIP-UA is not disabled\n"
        ),
        rollback_example=(
            f"{_EXAMPLE_PREFIX}\n"
            "! Restore previous voice service voip configuration from change record\n"
            "voice service voip\n"
            " ! prior baseline lines\n"
        ),
        impacted_objects=("CUBE voice service voip", "SIP-UA"),
        risk_level=ChangeRiskLevel.HIGH,
        affected_components=("Cisco CUBE", "SIP-UA", "Provider SIP trunk"),
        vendor_references=("Cisco CUBE SIP configuration guide",),
    ),
    "HYP-404-MISSING": _ChangeTemplate(
        current_state="No matching outbound dial-peer for failing destination class.",
        recommended_state="Outbound dial-peer covers required destination pattern.",
        config_example=(
            f"{_EXAMPLE_PREFIX}\n"
            "dial-peer voice 9100 voip\n"
            " description Outbound PSTN via provider\n"
            " destination-pattern 9T\n"
            " session target sip:provider.example.com\n"
            " voice-class codec 1\n"
        ),
        rollback_example=(
            f"{_EXAMPLE_PREFIX}\n"
            "! Remove or restore prior dial-peer configuration from change record\n"
        ),
        impacted_objects=("Outbound dial-peer", "Destination pattern"),
        risk_level=ChangeRiskLevel.HIGH,
        affected_components=("Cisco CUBE", "Outbound dial-peer", "PSTN routing"),
        vendor_references=("Cisco CUBE dial-peer configuration guide",),
    ),
    "HYP-503-PROVIDER": _ChangeTemplate(
        current_state="Provider or SIP trunk returning 503 Service Unavailable.",
        recommended_state="Provider trunk healthy; coordinate with ITSP if provider-side issue.",
        config_example=(
            f"{_EXAMPLE_PREFIX}\n"
            "! No local configuration change if provider-side outage.\n"
            "! If trunk policy limits are misconfigured, review:\n"
            "voice service voip\n"
            " sip\n"
            "  registrar dns:provider.example.com expires 3600\n"
        ),
        rollback_example=(
            f"{_EXAMPLE_PREFIX}\n"
            "! Revert any trunk parameter changes to pre-change baseline\n"
        ),
        impacted_objects=("SIP trunk", "Provider session target"),
        risk_level=ChangeRiskLevel.MEDIUM,
        affected_components=("Cisco CUBE", "ITSP SIP trunk"),
        vendor_references=("ITSP incident coordination", "Cisco CUBE SIP trunk guide"),
    ),
    "HYP-488-CODEC": _ChangeTemplate(
        current_state="Codec or SDP negotiation failure (SIP 488).",
        recommended_state="Overlapping codec set between CUBE and provider.",
        config_example=(
            f"{_EXAMPLE_PREFIX}\n"
            "voice class codec 1\n"
            " codec preference g711ulaw\n"
            " codec preference g729r8\n"
        ),
        rollback_example=(
            f"{_EXAMPLE_PREFIX}\n"
            "! Restore prior voice class codec configuration\n"
        ),
        impacted_objects=("Voice class codec", "Dial-peer codec assignment"),
        risk_level=ChangeRiskLevel.MEDIUM,
        affected_components=("Cisco CUBE", "Media negotiation", "Provider codec policy"),
        vendor_references=("Cisco CUBE codec configuration guide",),
    ),
    "HYP-DIAL-PEER-DOWN": _ChangeTemplate(
        current_state="Outbound dial-peer administratively shutdown or out of service.",
        recommended_state="Dial-peer operational and session target reachable.",
        config_example=(
            f"{_EXAMPLE_PREFIX}\n"
            "interface Dial-peer 9100\n"
            " no shutdown\n"
            "! Or within dial-peer configuration:\n"
            "dial-peer voice 9100 voip\n"
            " no shutdown\n"
        ),
        rollback_example=(
            f"{_EXAMPLE_PREFIX}\n"
            "dial-peer voice 9100 voip\n"
            " shutdown\n"
        ),
        impacted_objects=("Outbound dial-peer",),
        risk_level=ChangeRiskLevel.HIGH,
        affected_components=("Cisco CUBE", "Outbound dial-peer"),
        vendor_references=("Cisco CUBE dial-peer operations guide",),
    ),
}

VP_CUCM_0001_CHANGE_TEMPLATES: dict[str, _ChangeTemplate] = {
    "HYP-CUCM-PHONE-REG": _ChangeTemplate(
        current_state="One or more phones are not registered to CUCM.",
        recommended_state="Phones registered to correct CM group and device pool.",
        config_example=(
            f"{_EXAMPLE_PREFIX}\n"
            "! Review device pool, CM group, and network reachability per runbook VP-CISCO-CUCM-RB-001\n"
            "! Example: verify phone can reach TFTP and CallManager on required ports\n"
        ),
        rollback_example=(
            f"{_EXAMPLE_PREFIX}\n"
            "! Restore prior device pool and CM group assignment from change record\n"
        ),
        impacted_objects=("Phone", "Device pool", "CM group"),
        risk_level=ChangeRiskLevel.MEDIUM,
        affected_components=("Cisco CUCM", "IP phones"),
        vendor_references=("VP-CISCO-CUCM-RB-001", "VP-CISCO-CUCM-VG-001"),
    ),
    "HYP-CUCM-DB-REP": _ChangeTemplate(
        current_state="CUCM database replication is unhealthy between cluster nodes.",
        recommended_state="All cluster nodes report replication state 2 (Connected).",
        config_example=(
            f"{_EXAMPLE_PREFIX}\n"
            "! Follow VP-CISCO-CUCM-RB-005 cluster replication runbook\n"
            "! Verify NTP, network connectivity, and utils dbreplication status output\n"
        ),
        rollback_example=(
            f"{_EXAMPLE_PREFIX}\n"
            "! No configuration rollback — resolve replication per Cisco cluster recovery guide\n"
        ),
        impacted_objects=("CUCM cluster", "Database replication"),
        risk_level=ChangeRiskLevel.CRITICAL,
        affected_components=("Cisco CUCM publisher", "CUCM subscribers"),
        vendor_references=("VP-CISCO-CUCM-RB-005", "VP-CISCO-CUCM-VG-004"),
    ),
    "HYP-CUCM-CM-SVC": _ChangeTemplate(
        current_state="Cisco CallManager service is stopped on a cluster node.",
        recommended_state="Cisco CallManager service running on all cluster nodes.",
        config_example=(
            f"{_EXAMPLE_PREFIX}\n"
            "! Follow VP-CISCO-CUCM-RB-005 service recovery runbook\n"
            "! utils service list should show Cisco CallManager Started\n"
        ),
        rollback_example=(
            f"{_EXAMPLE_PREFIX}\n"
            "! Document service restart window; no config rollback typically required\n"
        ),
        impacted_objects=("Cisco CallManager service",),
        risk_level=ChangeRiskLevel.CRITICAL,
        affected_components=("Cisco CUCM", "Phone registration"),
        vendor_references=("VP-CISCO-CUCM-RB-005", "VP-CISCO-CUCM-VG-010"),
    ),
    "HYP-CUCM-CERT": _ChangeTemplate(
        current_state="Tomcat or phone trust certificate is expired.",
        recommended_state="Valid certificates installed; CTL/ITL updated on phones.",
        config_example=(
            f"{_EXAMPLE_PREFIX}\n"
            "! Follow VP-CISCO-CUCM-RB-009 certificate runbook\n"
            "! Renew Tomcat certificates and update phone trust list\n"
        ),
        rollback_example=(
            f"{_EXAMPLE_PREFIX}\n"
            "! Restore prior certificate and trust list from backup if renewal fails\n"
        ),
        impacted_objects=("Tomcat certificate", "CTL/ITL"),
        risk_level=ChangeRiskLevel.HIGH,
        affected_components=("Cisco CUCM", "Secure SIP/TLS endpoints"),
        vendor_references=("VP-CISCO-CUCM-RB-009", "VP-CISCO-CUCM-VG-005"),
    ),
    "HYP-CUCM-SIP-TRUNK": _ChangeTemplate(
        current_state="CUCM SIP trunk is down or unreachable.",
        recommended_state="SIP trunk registered and OPTIONS healthy.",
        config_example=(
            f"{_EXAMPLE_PREFIX}\n"
            "! Follow VP-CISCO-CUCM-RB-002 SIP trunk runbook\n"
            "! Verify trunk destination, security profile, and provider status\n"
        ),
        rollback_example=(
            f"{_EXAMPLE_PREFIX}\n"
            "! Restore prior SIP trunk configuration from change record\n"
        ),
        impacted_objects=("SIP trunk", "SIP trunk security profile"),
        risk_level=ChangeRiskLevel.HIGH,
        affected_components=("Cisco CUCM", "ITSP SIP trunk"),
        vendor_references=("VP-CISCO-CUCM-RB-002", "VP-CISCO-CUCM-VG-002"),
    ),
}

_DEFAULT_APPROVAL_SECTIONS: tuple[ApprovalSection, ...] = (
    ApprovalSection(
        name="Technical Reviewer",
        required=True,
        placeholder="Name / signature / date",
    ),
    ApprovalSection(
        name="Change Manager",
        required=True,
        placeholder="Change record ID / approval date",
    ),
    ApprovalSection(
        name="CAB Approval",
        required=True,
        placeholder="CAB decision / scheduled window",
    ),
    ApprovalSection(
        name="Implementation Engineer",
        required=True,
        placeholder="Implementer acknowledges read-only VoicePilot advisory",
    ),
)

_DEFAULT_PREREQUISITES: tuple[str, ...] = (
    "Authorized change window scheduled",
    "Current configuration backup captured by engineer",
    "Rollback plan reviewed and understood",
    "Test call plan defined for post-change validation",
)

_DEFAULT_ASSUMPTIONS: tuple[str, ...] = (
    "Investigation evidence accurately reflects production state at collection time",
    "Engineer will validate configuration examples against current baseline",
    "VoicePilot output is advisory only and does not modify devices",
)


class EngineeringChangePackageEngine:
    """Convert existing investigation outputs into read-only change advisory packages."""

    def __init__(self, knowledge_engine=None) -> None:
        self._knowledge_engine = knowledge_engine

    def _knowledge_engine_or_default(self):
        if self._knowledge_engine is not None:
            return self._knowledge_engine
        from engineering_knowledge import default_engineering_knowledge_engine

        return default_engineering_knowledge_engine()

    def generate_for_case(self, case: Case) -> EngineeringChangePackage:
        """Build a change package from stored case investigation artifacts."""
        recommendation = _latest_recommendation(case)
        top_hypothesis = _top_hypothesis(case)
        knowledge_assets = _related_knowledge_assets(case, self._knowledge_engine_or_default())

        if recommendation is None and top_hypothesis is None:
            return _insufficient_package(case, knowledge_assets=knowledge_assets)

        has_likely_root_cause = (
            recommendation is not None
            and recommendation.action_type == ACTION_LIKELY_ROOT_CAUSE
            and recommendation.likely_root_cause is not None
        )
        confidence = _package_confidence(recommendation, top_hypothesis)
        root_cause = _root_cause_text(recommendation, top_hypothesis)

        if not has_likely_root_cause and confidence < DEFAULT_CONFIDENCE_THRESHOLD:
            return _insufficient_package(
                case,
                recommendation=recommendation,
                top_hypothesis=top_hypothesis,
                knowledge_assets=knowledge_assets,
            )

        category = _hypothesis_category(top_hypothesis, recommendation)
        plans = _action_plans_for_playbook(case.playbook_id)
        templates = _change_templates_for_playbook(case.playbook_id)
        plan = plans.get(category)
        template = templates.get(category)

        recommended_changes = _build_recommended_changes(
            recommendation,
            top_hypothesis,
            plan,
            template,
            has_likely_root_cause=has_likely_root_cause,
            confidence=confidence,
        )
        verification_steps = _build_verification_steps(recommendation, plan)
        risk_level = _package_risk_level(recommended_changes, recommendation, confidence, has_likely_root_cause)

        config_examples = tuple(change.config_example for change in recommended_changes if change.config_example)
        rollback_examples = tuple(change.rollback_example for change in recommended_changes if change.rollback_example)
        post_change_validation = tuple(step.expected_result for step in verification_steps)

        title = f"Engineering Change Package — {root_cause or case.title}"
        executive_summary = _executive_summary(case, root_cause, confidence, has_likely_root_cause)

        return EngineeringChangePackage(
            package_id=_new_package_id(),
            case_id=case.case_id,
            playbook_id=case.playbook_id,
            generated_at=datetime.now(timezone.utc),
            title=title,
            executive_summary=executive_summary,
            root_cause=root_cause,
            confidence=confidence,
            evidence_reviewed=_evidence_reviewed(case),
            affected_components=_affected_components(case, template),
            recommended_changes=recommended_changes,
            configuration_examples=config_examples,
            rollback_examples=rollback_examples,
            verification_steps=verification_steps,
            post_change_validation=post_change_validation,
            risk_level=risk_level,
            risk_summary=format_risk_summary(risk_level, has_likely_root_cause=has_likely_root_cause),
            prerequisites=_DEFAULT_PREREQUISITES,
            assumptions=_DEFAULT_ASSUMPTIONS,
            related_knowledge_assets=knowledge_assets,
            vendor_references=_vendor_references(template),
            approval_sections=_DEFAULT_APPROVAL_SECTIONS,
            engineer_notes=_engineer_notes(case, recommendation),
            read_only_notice=READ_ONLY_NOTICE,
        )


def _new_package_id() -> str:
    return f"ECP-{uuid4().hex[:12]}"


def _latest_recommendation(case: Case) -> Recommendation | None:
    if not case.recommendations:
        return None
    return case.recommendations[-1]


def _top_hypothesis(case: Case) -> Hypothesis | None:
    if not case.hypotheses:
        return None
    return min(case.hypotheses, key=lambda hypothesis: hypothesis.rank or 999)


def _hypothesis_category(
    hypothesis: Hypothesis | None,
    recommendation: Recommendation | None,
) -> str:
    if hypothesis is not None and hypothesis.category:
        return hypothesis.category
    return "insufficient-evidence"


def _action_plans_for_playbook(playbook_id: str | None) -> dict:
    if playbook_id == VP_CUCM_0001_PLAYBOOK_ID:
        return VP_CUCM_0001_ACTION_PLANS
    return VP_CUBE_0001_ACTION_PLANS


def _change_templates_for_playbook(playbook_id: str | None) -> dict[str, _ChangeTemplate]:
    if playbook_id == VP_CUCM_0001_PLAYBOOK_ID:
        return VP_CUCM_0001_CHANGE_TEMPLATES
    return VP_CUBE_0001_CHANGE_TEMPLATES


def _package_confidence(
    recommendation: Recommendation | None,
    hypothesis: Hypothesis | None,
) -> float:
    if recommendation is not None and recommendation.confidence is not None:
        return float(recommendation.confidence)
    if hypothesis is not None:
        return float(hypothesis.confidence)
    return 0.0


def _root_cause_text(
    recommendation: Recommendation | None,
    hypothesis: Hypothesis | None,
) -> str | None:
    if recommendation is not None and recommendation.likely_root_cause:
        return recommendation.likely_root_cause
    if hypothesis is not None:
        return hypothesis.title
    return None


def _evidence_reviewed(case: Case) -> tuple[str, ...]:
    reviewed: list[str] = []
    for evidence in case.evidence:
        command = evidence.source.command if evidence.source else None
        label = command or evidence.title
        reviewed.append(label)
    for finding in case.analysis_findings:
        reviewed.append(f"{finding.signal} ({finding.command})")
    return tuple(dict.fromkeys(reviewed))


def _affected_components(case: Case, template: _ChangeTemplate | None) -> tuple[str, ...]:
    components: list[str] = []
    if template is not None and template.affected_components:
        components.extend(template.affected_components)
    if case.platform:
        if case.platform.vendor:
            components.append(case.platform.vendor)
        components.extend(case.platform.products)
    if case.playbook_id:
        components.append(case.playbook_id)
    return tuple(dict.fromkeys(components))


def _vendor_references(template: _ChangeTemplate | None) -> tuple[str, ...]:
    if template is None:
        return ("Vendor documentation to be confirmed by engineer",)
    return template.vendor_references


def _executive_summary(
    case: Case,
    root_cause: str | None,
    confidence: float,
    has_likely_root_cause: bool,
) -> str:
    if not has_likely_root_cause:
        return (
            f"VoicePilot analyzed case {case.case_id} but does not have sufficient "
            "recommendation confidence to propose configuration changes. "
            "Review missing evidence and discovery plan before CAB submission."
        )
    return (
        f"VoicePilot recommends CAB review for case {case.case_id}. "
        f"Likely root cause: {root_cause} ({int(confidence)}% confidence). "
        "Configuration examples below are advisory and require engineer validation."
    )


def _build_recommended_changes(
    recommendation: Recommendation | None,
    hypothesis: Hypothesis | None,
    plan,
    template: _ChangeTemplate | None,
    *,
    has_likely_root_cause: bool,
    confidence: float,
) -> tuple[RecommendedChange, ...]:
    if recommendation is None and hypothesis is None:
        return ()

    title = _root_cause_text(recommendation, hypothesis) or "Investigation recommendation"
    reason = ""
    if recommendation is not None:
        reason = recommendation.rationale or recommendation.description
    elif hypothesis is not None:
        reason = hypothesis.explanation or hypothesis.title

    actions = tuple(recommendation.recommended_actions) if recommendation else ()
    if not actions and plan is not None:
        actions = plan.recommended_actions
    if not actions and hypothesis is not None and hypothesis.next_best_action:
        actions = (hypothesis.next_best_action,)

    verification = tuple(recommendation.verification_steps) if recommendation else ()
    if not verification and plan is not None:
        verification = plan.verification_steps

    requires_approval = bool(recommendation and recommendation.requires_engineer_approval)
    risk_level = assess_change_risk(
        confidence,
        has_likely_root_cause=has_likely_root_cause,
        requires_engineer_approval=requires_approval,
        template_risk=template.risk_level if template else None,
    )

    if template is not None:
        return (
            RecommendedChange(
                title=title,
                reason=reason,
                current_state=template.current_state,
                recommended_state=template.recommended_state,
                config_example=template.config_example,
                rollback_example=template.rollback_example,
                verification=verification,
                risk_level=risk_level,
                impacted_objects=template.impacted_objects,
            ),
        )

    config_example = "\n".join(f"! Advisory action: {action}" for action in actions) if actions else ""
    rollback_example = ""
    if recommendation and recommendation.rollback_steps:
        rollback_example = "\n".join(
            f"! Rollback guidance: {step}" for step in recommendation.rollback_steps
        )

    return (
        RecommendedChange(
            title=title,
            reason=reason,
            current_state="See investigation evidence and hypothesis.",
            recommended_state="; ".join(actions) if actions else "Collect additional evidence.",
            config_example=config_example,
            rollback_example=rollback_example,
            verification=verification,
            risk_level=risk_level,
            impacted_objects=(case_component for case_component in ("Investigation target",)),
        ),
    )


def _build_verification_steps(recommendation: Recommendation | None, plan) -> tuple[VerificationStep, ...]:
    steps: list[VerificationStep] = []
    command = None
    if recommendation is not None:
        command = recommendation.command
    if command is None and plan is not None:
        command = plan.command

    verification_lines: list[str] = []
    if recommendation is not None:
        verification_lines.extend(recommendation.verification_steps)
    elif plan is not None:
        verification_lines.extend(plan.verification_steps)

    for index, expected in enumerate(verification_lines, start=1):
        steps.append(
            VerificationStep(
                command=command or f"verification-step-{index}",
                expected_result=expected,
                purpose="Confirm remediation outcome after engineer-implemented change",
                required=True,
            )
        )

    return tuple(steps)


def _package_risk_level(
    changes: tuple[RecommendedChange, ...],
    recommendation: Recommendation | None,
    confidence: float,
    has_likely_root_cause: bool,
) -> ChangeRiskLevel:
    if changes:
        return max(changes, key=lambda item: _risk_rank(item.risk_level)).risk_level
    return assess_change_risk(
        confidence,
        has_likely_root_cause=has_likely_root_cause,
        requires_engineer_approval=bool(recommendation and recommendation.requires_engineer_approval),
    )


def _risk_rank(level: ChangeRiskLevel) -> int:
    order = {
        ChangeRiskLevel.LOW: 0,
        ChangeRiskLevel.MEDIUM: 1,
        ChangeRiskLevel.HIGH: 2,
        ChangeRiskLevel.CRITICAL: 3,
    }
    return order[level]


def _engineer_notes(case: Case, recommendation: Recommendation | None) -> tuple[str, ...]:
    notes: list[str] = [
        "This package is generated from VoicePilot investigation artifacts only.",
        "Validate all configuration examples against the current device baseline.",
    ]
    if recommendation is not None and recommendation.requires_engineer_approval:
        notes.append("Recommendation flagged for engineer approval before implementation.")
    if case.discovery_plan is not None and case.discovery_plan.next_best_command:
        notes.append(
            f"Discovery plan next command: {case.discovery_plan.next_best_command}"
        )
    if case.investigation_quality_report is not None:
        report = case.investigation_quality_report
        notes.append(
            f"Investigation quality score: {report.overall_score} ({report.overall_status})"
        )
    return tuple(notes)


def _related_knowledge_assets(case: Case, knowledge_engine) -> tuple[str, ...]:
    if knowledge_engine is None or not case.analysis_findings:
        return ()
    report = knowledge_engine.evaluate_case(case)
    return tuple(match.knowledge_id for match in report.matches)


def _insufficient_package(
    case: Case,
    *,
    recommendation: Recommendation | None = None,
    top_hypothesis: Hypothesis | None = None,
    knowledge_assets: tuple[str, ...] = (),
) -> EngineeringChangePackage:
    missing_notes: list[str] = []
    if case.discovery_plan is not None:
        for request in case.discovery_plan.requests:
            if not request.already_collected:
                missing_notes.append(f"Collect: {request.command} — {request.reason}")
        if case.discovery_plan.next_best_command:
            missing_notes.append(f"Next best command: {case.discovery_plan.next_best_command}")

    executive_summary = (
        "Insufficient recommendation data to produce a configuration change advisory. "
        "VoicePilot did not identify a likely root cause with adequate confidence."
    )
    if top_hypothesis is not None:
        executive_summary += f" Top hypothesis: {top_hypothesis.title} ({int(top_hypothesis.confidence)}%)."

    engineer_notes = (
        "Collect additional evidence before submitting a change package to CAB.",
        *missing_notes,
    )

    return EngineeringChangePackage(
        package_id=_new_package_id(),
        case_id=case.case_id,
        playbook_id=case.playbook_id,
        generated_at=datetime.now(timezone.utc),
        title=f"Engineering Change Package — Insufficient Data ({case.case_id})",
        executive_summary=executive_summary,
        root_cause=top_hypothesis.title if top_hypothesis else None,
        confidence=_package_confidence(recommendation, top_hypothesis),
        evidence_reviewed=_evidence_reviewed(case),
        affected_components=(case.playbook_id,) if case.playbook_id else (),
        recommended_changes=(),
        configuration_examples=(),
        rollback_examples=(),
        verification_steps=(),
        post_change_validation=(),
        risk_level=ChangeRiskLevel.LOW,
        risk_summary=format_risk_summary(ChangeRiskLevel.LOW, has_likely_root_cause=False),
        prerequisites=_DEFAULT_PREREQUISITES,
        assumptions=_DEFAULT_ASSUMPTIONS,
        related_knowledge_assets=knowledge_assets,
        vendor_references=(),
        approval_sections=_DEFAULT_APPROVAL_SECTIONS,
        engineer_notes=tuple(engineer_notes),
        read_only_notice=READ_ONLY_NOTICE,
    )
