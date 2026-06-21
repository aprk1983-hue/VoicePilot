"""Enterprise Reporting Engine — audience-specific report generation."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from domain.models import Case
from reporting.report_exceptions import UnsupportedReportTypeError
from reporting.report_formatter import assemble_report_markdown
from reporting.report_models import (
    CABReport,
    CustomerReport,
    EngineeringReport,
    ExecutiveReport,
    OperationsReport,
    ReportType,
)
from reporting.report_templates import (
    CaseReportContext,
    build_cab_body,
    build_customer_body,
    build_engineering_body,
    build_executive_body,
    build_operations_body,
)
from runtime.recommendation_engine import ACTION_LIKELY_ROOT_CAUSE
from runtime.report_engine import build_incident_report, format_incident_report


class EnterpriseReportEngine:
    """Transform existing investigation outputs into audience-specific reports."""

    def generate(self, case: Case, report_type: ReportType):
        """Build an audience-specific report from case investigation artifacts."""
        context = _build_context(case)
        generated_at = datetime.now(timezone.utc)
        report_id = _new_report_id()

        if report_type == ReportType.ENGINEERING:
            title, summary, body = build_engineering_body(context)
            markdown = assemble_report_markdown(
                case_id=case.case_id,
                playbook_id=case.playbook_id,
                report_type=report_type,
                generated_at=generated_at,
                title=title,
                body=body,
            )
            return EngineeringReport(
                report_id=report_id,
                case_id=case.case_id,
                playbook_id=case.playbook_id,
                report_type=report_type,
                generated_at=generated_at,
                title=title,
                summary=summary,
                markdown=markdown,
                engineering_markdown=context.incident_markdown or body,
            )

        if report_type == ReportType.EXECUTIVE:
            title, summary, body = build_executive_body(context)
            markdown = assemble_report_markdown(
                case_id=case.case_id,
                playbook_id=case.playbook_id,
                report_type=report_type,
                generated_at=generated_at,
                title=title,
                body=body,
            )
            return ExecutiveReport(
                report_id=report_id,
                case_id=case.case_id,
                playbook_id=case.playbook_id,
                report_type=report_type,
                generated_at=generated_at,
                title=title,
                summary=summary,
                markdown=markdown,
                business_impact=context.business_impact,
                affected_services=context.affected_services,
                risk=context.change_risk or _executive_risk(context.confidence),
                resolution=context.resolution_summary
                or context.recommendation_summary
                or "Pending validation.",
                confidence=context.confidence,
                prevention=context.prevention,
                next_actions=context.next_actions,
            )

        if report_type == ReportType.CUSTOMER:
            title, summary, body = build_customer_body(context)
            markdown = assemble_report_markdown(
                case_id=case.case_id,
                playbook_id="Voice service investigation",
                report_type=report_type,
                generated_at=generated_at,
                title=title,
                body=body,
            )
            return CustomerReport(
                report_id=report_id,
                case_id=case.case_id,
                playbook_id=case.playbook_id,
                report_type=report_type,
                generated_at=generated_at,
                title=title,
                summary=summary,
                markdown=markdown,
                incident_summary=summary,
                business_language_impact=context.business_impact,
                resolution=context.resolution_summary
                or context.recommendation_summary
                or "In progress",
                verification="; ".join(context.verification_steps) or "Validation in progress",
                status=context.case_status,
            )

        if report_type == ReportType.CAB:
            title, summary, body = build_cab_body(context)
            markdown = assemble_report_markdown(
                case_id=case.case_id,
                playbook_id=case.playbook_id,
                report_type=report_type,
                generated_at=generated_at,
                title=title,
                body=body,
            )
            return CABReport(
                report_id=report_id,
                case_id=case.case_id,
                playbook_id=case.playbook_id,
                report_type=report_type,
                generated_at=generated_at,
                title=title,
                summary=summary,
                markdown=markdown,
                change_summary=context.change_summary or context.recommendation_summary or context.symptom,
                reason=context.root_cause or context.recommendation_summary or context.symptom,
                affected_components=context.affected_services,
                risk=context.change_risk or _executive_risk(context.confidence),
                rollback=context.change_rollback or context.rollback_steps,
                verification=context.change_verification or context.verification_steps,
                approvals=context.change_approvals
                or (
                    "Technical Reviewer",
                    "Change Manager",
                    "CAB Approval",
                    "Implementation Engineer",
                ),
                implementation_window="Approved maintenance window after CAB sign-off",
            )

        if report_type == ReportType.OPERATIONS:
            title, summary, body = build_operations_body(context)
            markdown = assemble_report_markdown(
                case_id=case.case_id,
                playbook_id=case.playbook_id,
                report_type=report_type,
                generated_at=generated_at,
                title=title,
                body=body,
            )
            return OperationsReport(
                report_id=report_id,
                case_id=case.case_id,
                playbook_id=case.playbook_id,
                report_type=report_type,
                generated_at=generated_at,
                title=title,
                summary=summary,
                markdown=markdown,
                health_score=context.health_score,
                investigation_quality_score=context.quality_score,
                knowledge_matches=context.knowledge_matches,
                open_findings=context.finding_signals,
                recommendations=context.recommendation_actions,
                future_monitoring=context.future_monitoring,
            )

        raise UnsupportedReportTypeError(report_type.value)


def _new_report_id() -> str:
    return f"RPT-{uuid4().hex[:12]}"


def _build_context(case: Case) -> CaseReportContext:
    incident = build_incident_report(case)
    incident_markdown = format_incident_report(incident)
    recommendation = _likely_root_cause_recommendation(case)
    change_package = case.change_package

    if change_package is None and case.recommendations:
        from change_package.change_engine import EngineeringChangePackageEngine

        change_package = EngineeringChangePackageEngine(knowledge_engine=None).generate_for_case(case)

    knowledge_matches = _engineering_knowledge_matches(case)
    quality = case.investigation_quality_report

    root_cause = (
        incident.top_hypothesis_title
        or (recommendation.likely_root_cause if recommendation else None)
    )
    next_actions = tuple(recommendation.recommended_actions) if recommendation else ()
    verification_steps = tuple(recommendation.verification_steps) if recommendation else ()
    rollback_steps = tuple(recommendation.rollback_steps) if recommendation else ()

    return CaseReportContext(
        case_id=case.case_id,
        playbook_id=case.playbook_id,
        case_status=case.status.value,
        symptom=case.symptom.summary,
        business_impact=case.business_impact,
        root_cause=root_cause,
        confidence=incident.confidence,
        resolution_summary=case.resolution_summary,
        recommendation_summary=incident.recommendation_summary,
        recommendation_actions=tuple(incident.recommendation_actions),
        verification_steps=verification_steps,
        rollback_steps=rollback_steps,
        finding_signals=tuple(finding.signal for finding in case.analysis_findings),
        affected_services=_affected_services(case, incident.playbook_id),
        incident_markdown=incident_markdown,
        health_score=incident.health_assessment.overall_score if incident.health_assessment.available else None,
        health_status=incident.health_assessment.overall_status if incident.health_assessment.available else None,
        health_recommendations=incident.health_assessment.recommendations,
        quality_score=quality.overall_score if quality else None,
        quality_status=quality.overall_status if quality else None,
        ready_for_recommendation=quality.ready_for_recommendation if quality else None,
        knowledge_matches=knowledge_matches,
        change_summary=change_package.executive_summary if change_package else None,
        change_risk=change_package.risk_level.value if change_package else None,
        change_rollback=change_package.rollback_examples if change_package else (),
        change_verification=tuple(step.expected_result for step in change_package.verification_steps)
        if change_package
        else (),
        change_approvals=tuple(section.name for section in change_package.approval_sections)
        if change_package
        else (),
        prevention=_prevention_text(root_cause),
        next_actions=next_actions or tuple(incident.recommendation_actions),
        future_monitoring=_future_monitoring(case, incident.health_assessment.recommendations),
    )


def _likely_root_cause_recommendation(case: Case):
    for recommendation in reversed(case.recommendations):
        if recommendation.action_type == ACTION_LIKELY_ROOT_CAUSE:
            return recommendation
    return case.recommendations[-1] if case.recommendations else None


def _affected_services(case: Case, playbook_id: str | None) -> tuple[str, ...]:
    services: list[str] = ["Outbound voice calling"]
    if case.affected_scope.call_direction:
        services.append(f"Call direction: {case.affected_scope.call_direction}")
    for site in case.affected_scope.sites:
        services.append(f"Site: {site}")
    if playbook_id:
        services.append(playbook_id)
    return tuple(dict.fromkeys(services))


def _engineering_knowledge_matches(case: Case) -> tuple[str, ...]:
    if not case.analysis_findings:
        return ()
    try:
        from engineering_knowledge import default_engineering_knowledge_engine

        report = default_engineering_knowledge_engine().evaluate_case(case)
        return tuple(match.knowledge_id for match in report.matches)
    except Exception:
        return ()


def _prevention_text(root_cause: str | None) -> str:
    if not root_cause:
        return "Complete evidence collection and validate configuration baseline before closure."
    return (
        f"Review change controls and monitoring for conditions related to: {root_cause}. "
        "Document baseline configuration after remediation."
    )


def _future_monitoring(case: Case, health_recommendations: tuple[str, ...]) -> tuple[str, ...]:
    items: list[str] = list(health_recommendations)
    if case.discovery_plan and case.discovery_plan.next_best_command:
        items.append(f"Monitor evidence gap: {case.discovery_plan.next_best_command}")
    items.append("Track call success rate and registration health post-remediation")
    items.append("Trend placeholder: attach observability metrics in future release")
    return tuple(dict.fromkeys(items))


def _executive_risk(confidence: float | None) -> str:
    if confidence is None or confidence < 50:
        return "Low — investigation incomplete"
    if confidence >= 85:
        return "Medium — validated root cause with recommended remediation"
    return "Low — additional validation recommended before change"
