"""Deterministic intake question flow from DSL playbooks."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from domain.enums import InvestigationState, QuestionStatus, Severity
from domain.models import Case, InvestigationTurn, Playbook, Question, TimelineEvent
from domain.value_objects import AffectedScope, CaseIntake, PlatformRef, SymptomSummary
from shared.constants import ID_PREFIX_TIMELINE
from shared.types import JsonDict


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id(prefix: str) -> str:
    return f"{prefix}{uuid4().hex[:12]}"


def build_case_intake(playbook: Playbook, plugin_name: str) -> CaseIntake:
    """Build case intake values from playbook metadata."""
    document = playbook.raw_document.get("playbook", {})
    metadata = document.get("metadata", {})
    business_impact = document.get("business_impact", {})
    platforms = document.get("platforms", [])
    symptoms = document.get("symptoms", [])

    severity_raw = business_impact.get("default_severity", Severity.HIGH.value)
    severity = Severity(severity_raw)

    symptom_summary = metadata.get("title", playbook.title)
    if symptoms:
        first_symptom = symptoms[0].get("match", {})
        summary_parts = first_symptom.get("summary_contains", [])
        if summary_parts:
            symptom_summary = ", ".join(summary_parts)

    platform_vendor = "generic"
    platform_products: tuple[str, ...] = ()
    if platforms:
        platform_vendor = platforms[0].get("vendor", platform_vendor)
        platform_products = tuple(platforms[0].get("products", []))

    return CaseIntake(
        title=metadata.get("title", playbook.title),
        symptom=SymptomSummary(summary=symptom_summary),
        severity=severity,
        business_impact=business_impact.get("description", playbook.title),
        affected_scope=AffectedScope(),
        platform=PlatformRef(vendor=platform_vendor, products=platform_products),
        playbook_id=playbook.playbook_id,
        metadata={"plugin_name": plugin_name},
    )


def initialize_flow_state(playbook: Playbook, case_id: str) -> JsonDict:
    """Parse playbook questions and build per-phase flow state."""
    raw_questions = (
        playbook.raw_document.get("playbook", {}).get("intake", {}).get("questions", [])
    )
    phase_questions: dict[str, list[JsonDict]] = {}
    domain_questions: list[Question] = []

    for item in raw_questions:
        phase_name = str(item.get("phase", InvestigationState.INTAKE.value))
        phase_questions.setdefault(phase_name, []).append(item)

        target_field = item.get("target_field")
        target_fields = [target_field] if target_field else []
        domain_questions.append(
            Question(
                question_id=item["id"],
                case_id=case_id,
                text=item["text"],
                category=item.get("category", "intake"),
                phase=InvestigationState(phase_name),
                status=QuestionStatus.PENDING,
                source="playbook",
                target_fields=target_fields,
                information_gain_score=item.get("information_gain"),
                required=bool(item.get("required", True)),
            )
        )

    return {
        "phase_questions": {phase: [q["id"] for q in items] for phase, items in phase_questions.items()},
        "answered_question_ids": [],
        "questions": domain_questions,
        "playbook_version": playbook.version,
    }


def attach_flow_state(case: Case, flow_state: JsonDict) -> None:
    """Attach parsed questions and flow tracking to the case."""
    case.questions = list(flow_state["questions"])
    case.playbook_version = case.playbook_version or flow_state.get("playbook_version")
    case.metadata.setdefault("plugin_name", flow_state.get("plugin_name"))
    case.metadata["intake_flow"] = {
        "phase_questions": flow_state["phase_questions"],
        "answered_question_ids": flow_state["answered_question_ids"],
    }


def get_next_question_for_phase(case: Case, phase: InvestigationState) -> Question | None:
    """Return the next unanswered question for ``phase``."""
    flow = case.metadata.get("intake_flow", {})
    phase_questions: dict[str, list[str]] = flow.get("phase_questions", {})
    answered: set[str] = set(flow.get("answered_question_ids", []))
    question_ids = phase_questions.get(phase.value, [])

    questions_by_id = {question.question_id: question for question in case.questions}
    for question_id in question_ids:
        if question_id not in answered:
            return questions_by_id[question_id]
    return None


def mark_question_asked(question: Question) -> None:
    """Mark a question as presented to the engineer."""
    question.status = QuestionStatus.ASKED
    question.asked_at = _utc_now()


def record_answer(
    case: Case,
    question: Question,
    answer: Any,
    *,
    actor: str = "runtime-engine",
) -> TimelineEvent:
    """Store answer on the question, apply to case intake data, and add timeline event."""
    question.status = QuestionStatus.ANSWERED
    question.answered_at = _utc_now()
    question.answer_structured = {"value": answer}

    flow = case.metadata.setdefault("intake_flow", {})
    answered: list[str] = flow.setdefault("answered_question_ids", [])
    if question.question_id not in answered:
        answered.append(question.question_id)

    if question.target_fields:
        _apply_target_field(case, question.target_fields[0], answer)
    else:
        answers = case.metadata.setdefault("answers", {})
        answers[question.question_id] = answer

    event = TimelineEvent(
        event_id=_new_id(ID_PREFIX_TIMELINE),
        case_id=case.case_id,
        sequence=len(case.timeline_events) + 1,
        timestamp=_utc_now(),
        event_type="question_answered",
        source_engine=actor,
        summary=f"Answered question {question.question_id}",
        related_entity_ids={"question_id": question.question_id},
    )
    case.timeline_events.append(event)
    return event


def intake_phase_complete(case: Case) -> bool:
    """Return whether all INTAKE-phase questions are answered."""
    return get_next_question_for_phase(case, InvestigationState.INTAKE) is None


def build_investigation_turn(case: Case, question: Question | None) -> InvestigationTurn:
    """Build an investigation turn for the current or next question."""
    if question is None:
        return InvestigationTurn(
            case_id=case.case_id,
            state=case.status,
            prompt="Intake phase complete. Awaiting next investigation phase.",
            question_id=None,
            expected_response_type="none",
            available_options=[],
            required=False,
            context=_build_context(case),
            next_action_type="await_phase",
        )

    mark_question_asked(question)
    return InvestigationTurn(
        case_id=case.case_id,
        state=case.status,
        prompt=question.text,
        question_id=question.question_id,
        expected_response_type=_infer_response_type(question),
        available_options=[],
        required=_is_required(question),
        context=_build_context(case, question),
        next_action_type="ask_question",
    )


def find_question(case: Case, question_id: str) -> Question | None:
    """Find a question on the case by ID."""
    for question in case.questions:
        if question.question_id == question_id:
            return question
    return None


def _build_context(case: Case, question: Question | None = None) -> JsonDict:
    context: JsonDict = {
        "playbook_id": case.playbook_id,
        "playbook_version": case.playbook_version,
        "plugin_name": case.metadata.get("plugin_name"),
    }
    if question is not None:
        context["question_category"] = question.category
        context["target_fields"] = question.target_fields
    return context


def _infer_response_type(question: Question) -> str:
    field = question.target_fields[0] if question.target_fields else ""
    if field.endswith("_working") or field.endswith("_previously"):
        return "boolean"
    return "text"


def _is_required(question: Question) -> bool:
    return question.required


def _apply_target_field(case: Case, target_field: str, answer: Any) -> None:
    parts = target_field.split(".")
    cursor: JsonDict = case.metadata
    for part in parts[:-1]:
        nested = cursor.get(part)
        if not isinstance(nested, dict):
            nested = {}
            cursor[part] = nested
        cursor = nested
    cursor[parts[-1]] = answer
