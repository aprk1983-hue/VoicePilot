"""Deterministic interactive investigation session orchestration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import uuid4

from domain.enums import InvestigationState
from domain.models import InvestigationTurn
from discovery.planner_report import format_discovery_plan_markdown
from investigation.session_exceptions import InvalidSessionStateError
from investigation.session_models import (
    InvestigationSession,
    InvestigationSessionStatus,
    SessionActionType,
    SessionContinueResult,
    SessionJourneyEntry,
)
from investigation.session_registry import InvestigationSessionRegistry
from investigation.session_state_machine import InvestigationSessionStateMachine
from investigation_quality.quality_report import format_investigation_quality_markdown
from runtime.analysis_engine import format_analysis_summary
from runtime.correlation_engine import format_correlation_summary
from runtime.evidence_collection import (
    format_evidence_request,
    get_next_evidence_request,
    initialize_evidence_collection,
    submit_evidence,
)
from runtime.hypothesis_engine import format_hypothesis_summary
from runtime.intake_flow import build_investigation_turn, get_next_question_for_phase
from runtime.intake_summary import build_intake_summary, format_intake_summary
from runtime.learning_engine import format_learning_closure_summary
from runtime.recommendation_engine import format_recommendation_summary
from runtime.report_engine import format_incident_report
from runtime.verification_engine import (
    OUTCOME_COMPLETE,
    VerificationResultSubmission,
    format_verification_checklist,
    format_verification_summary,
)
from shared.constants import ID_PREFIX_SESSION

if TYPE_CHECKING:
    from runtime.runtime_engine import RuntimeEngine

InputProvider = Callable[[], str]
END_MARKER = "END"
_UNSET = object()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_session_id() -> str:
    return f"{ID_PREFIX_SESSION}{uuid4().hex[:12]}"


def _session_metadata(session: InvestigationSession) -> dict:
    return dict(session.metadata or {})


class InvestigationSessionEngine:
    """Orchestrate evidence collection using discovery planning and quality gates."""

    def __init__(
        self,
        runtime: RuntimeEngine,
        *,
        registry: InvestigationSessionRegistry | None = None,
        state_machine: InvestigationSessionStateMachine | None = None,
    ) -> None:
        self._runtime = runtime
        self._registry = registry or InvestigationSessionRegistry()
        self._state_machine = state_machine or InvestigationSessionStateMachine()

    @property
    def registry(self) -> InvestigationSessionRegistry:
        """Return the session registry."""
        return self._registry

    def start_session(self, playbook_id: str) -> InvestigationSession:
        """Start a new investigation session for a playbook."""
        turn = self._runtime.start_investigation(playbook_id)
        now = _utc_now()
        session = InvestigationSession(
            session_id=_new_session_id(),
            case_id=turn.case_id,
            playbook_id=playbook_id,
            status=InvestigationSessionStatus.ACTIVE,
            current_action=SessionActionType.INTAKE_QUESTION,
            case_state=turn.state,
            turn_number=1,
            journey=(
                SessionJourneyEntry(
                    sequence=1,
                    timestamp=now,
                    action=SessionActionType.INTAKE_QUESTION,
                    case_state=turn.state,
                    summary="Investigation session started",
                ),
            ),
            started_at=now,
            updated_at=now,
        )
        self._registry.save(session)
        self._sync_session_to_case(session)
        return session

    def get_session(self, session_id: str) -> InvestigationSession:
        """Return a registered session."""
        return self._registry.get(session_id)

    def continue_session(
        self,
        session_id: str,
        *,
        user_input: str | None = None,
        input_provider: InputProvider | None = None,
        end_marker: str = END_MARKER,
    ) -> SessionContinueResult:
        """Advance a session until the next input boundary or completion."""
        session = self.get_session(session_id)
        has_input = user_input is not None or input_provider is not None
        self._state_machine.validate_continue(
            session_id,
            session.status,
            has_input=has_input,
        )

        messages: list[str] = []
        if session.status == InvestigationSessionStatus.AWAITING_INPUT:
            messages.extend(
                self._process_input(
                    session,
                    user_input=user_input,
                    input_provider=input_provider,
                    end_marker=end_marker,
                )
            )
            session = self.get_session(session_id)

        while session.status == InvestigationSessionStatus.ACTIVE:
            messages.extend(self._advance_automatically(session))
            session = self.get_session(session_id)
            if session.status != InvestigationSessionStatus.ACTIVE:
                break

        prompt = session.pending_prompt if session.status == InvestigationSessionStatus.AWAITING_INPUT else None
        return SessionContinueResult(session=session, messages=tuple(messages), prompt=prompt)

    def format_session_status(self, session_id: str) -> str:
        """Format a read-only session status report."""
        session = self.get_session(session_id)
        case = self._runtime.case_manager.load_case(session.case_id)
        lines = [
            "Investigation Session Status",
            "",
            f"Session:  {session.session_id}",
            f"Case:     {session.case_id}",
            f"Playbook: {session.playbook_id}",
            f"Status:   {session.status.value}",
            f"State:    {session.case_state.value}",
            f"Action:   {session.current_action.value}",
            f"Turn:     {session.turn_number}",
            "",
            "Journey",
            "",
        ]
        if session.journey:
            for entry in session.journey:
                lines.append(
                    f"{entry.sequence}. [{entry.case_state.value}] "
                    f"{entry.action.value} — {entry.summary}"
                )
        else:
            lines.append("_No journey steps recorded._")

        if case.discovery_plan is not None and case.discovery_plan.next_best_command:
            lines.extend(
                [
                    "",
                    "Discovery",
                    "",
                    f"Next best command: `{case.discovery_plan.next_best_command}`",
                ]
            )

        if case.investigation_quality_report is not None:
            report = case.investigation_quality_report
            lines.extend(
                [
                    "",
                    "Quality",
                    "",
                    f"Overall score: {report.overall_score}/100 ({report.overall_status})",
                    f"Ready for recommendation: {'Yes' if report.ready_for_recommendation else 'No'}",
                ]
            )

        if session.pending_prompt:
            lines.extend(["", "Next", "", session.pending_prompt])

        return "\n".join(lines)

    def _process_input(
        self,
        session: InvestigationSession,
        *,
        user_input: str | None,
        input_provider: InputProvider | None,
        end_marker: str,
    ) -> list[str]:
        action = session.current_action
        if action == SessionActionType.INTAKE_QUESTION:
            return self._process_intake_answer(session, user_input, input_provider)
        if action == SessionActionType.COLLECT_EVIDENCE:
            return self._process_required_evidence(
                session,
                input_provider=input_provider,
                end_marker=end_marker,
            )
        if action == SessionActionType.COLLECT_DISCOVERY_EVIDENCE:
            return self._process_discovery_evidence(
                session,
                input_provider=input_provider,
                end_marker=end_marker,
            )
        if action == SessionActionType.RUN_VERIFICATION:
            return self._process_verification_input(session, user_input, input_provider)
        raise InvalidSessionStateError(
            session.session_id,
            f"no input handler for action {action.value}",
        )

    def _process_intake_answer(
        self,
        session: InvestigationSession,
        user_input: str | None,
        input_provider: InputProvider | None,
    ) -> list[str]:
        provider = input_provider or (lambda: user_input or "")
        answer = provider().strip()
        question_id = session.pending_question_id
        if not question_id:
            raise InvalidSessionStateError(session.session_id, "missing pending question")

        turn = self._runtime.submit_answer(session.case_id, question_id, answer)
        messages: list[str] = []
        metadata = _session_metadata(session)

        if turn.state == InvestigationState.DISCOVERY:
            messages.append("Intake complete. Next phase: DISCOVERY.")
            updated = self._record_step(
                session,
                action=SessionActionType.DISCOVERY_PLANNING,
                case_state=turn.state,
                summary="Intake completed",
                status=InvestigationSessionStatus.ACTIVE,
                turn_number=session.turn_number + 1,
                pending_question_id=None,
                pending_prompt=None,
                metadata=metadata,
            )
            self._registry.save(updated)
            self._sync_session_to_case(updated)
            return messages

        prompt = self._format_question(turn)
        updated = self._record_step(
            session,
            action=SessionActionType.INTAKE_QUESTION,
            case_state=turn.state,
            summary=f"Answered {question_id}",
            status=InvestigationSessionStatus.AWAITING_INPUT,
            turn_number=session.turn_number + 1,
            pending_question_id=turn.question_id,
            pending_prompt=prompt,
            metadata=metadata,
        )
        self._registry.save(updated)
        self._sync_session_to_case(updated)
        messages.append(prompt)
        return messages

    def _process_required_evidence(
        self,
        session: InvestigationSession,
        *,
        input_provider: InputProvider | None,
        end_marker: str,
    ) -> list[str]:
        if input_provider is None:
            raise InvalidSessionStateError(
                session.session_id,
                "evidence collection requires an input provider",
            )

        command = session.pending_evidence_command
        if not command:
            raise InvalidSessionStateError(session.session_id, "missing evidence command")

        raw_text = _read_multiline_paste(input_provider, end_marker=end_marker)
        case = self._runtime.case_manager.load_case(session.case_id)
        submit_evidence(
            case,
            self._runtime.case_manager,
            command,
            raw_text,
            decision_log=self._runtime.decision_log_engine,
        )

        case = self._runtime.case_manager.load_case(session.case_id)
        request = get_next_evidence_request(case)
        metadata = _session_metadata(session)
        messages: list[str] = []

        if request is None:
            messages.append("Evidence collection complete. Next phase: ANALYSIS.")
            updated = self._record_step(
                session,
                action=SessionActionType.RUN_ANALYSIS,
                case_state=case.status,
                summary=f"Collected evidence for `{command}`",
                status=InvestigationSessionStatus.ACTIVE,
                turn_number=session.turn_number + 1,
                pending_evidence_command=None,
                pending_prompt=None,
                metadata=metadata,
            )
        else:
            prompt = self._format_evidence_prompt(request)
            updated = self._record_step(
                session,
                action=SessionActionType.COLLECT_EVIDENCE,
                case_state=case.status,
                summary=f"Collected evidence for `{command}`",
                status=InvestigationSessionStatus.AWAITING_INPUT,
                turn_number=session.turn_number + 1,
                pending_evidence_command=request.command,
                pending_prompt=prompt,
                metadata=metadata,
            )
            messages.append(prompt)

        self._registry.save(updated)
        self._sync_session_to_case(updated)
        return messages

    def _process_discovery_evidence(
        self,
        session: InvestigationSession,
        *,
        input_provider: InputProvider | None,
        end_marker: str,
    ) -> list[str]:
        if input_provider is None:
            raise InvalidSessionStateError(
                session.session_id,
                "discovery evidence collection requires an input provider",
            )

        command = session.pending_evidence_command
        if not command:
            raise InvalidSessionStateError(session.session_id, "missing discovery command")

        raw_text = _read_multiline_paste(input_provider, end_marker=end_marker)
        case = self._runtime.case_manager.load_case(session.case_id)
        submit_evidence(
            case,
            self._runtime.case_manager,
            command,
            raw_text,
            decision_log=self._runtime.decision_log_engine,
        )
        case = self._runtime.case_manager.load_case(session.case_id)
        updated = self._record_step(
            session,
            action=SessionActionType.QUALITY_EVALUATION,
            case_state=case.status,
            summary=f"Collected discovery evidence for `{command}`",
            status=InvestigationSessionStatus.ACTIVE,
            turn_number=session.turn_number + 1,
            pending_evidence_command=None,
            pending_prompt=None,
            metadata=_session_metadata(session),
        )
        self._registry.save(updated)
        self._sync_session_to_case(updated)
        return [
            f"Discovery evidence collected for `{command}`. Re-evaluating investigation quality."
        ]

    def _process_verification_input(
        self,
        session: InvestigationSession,
        user_input: str | None,
        input_provider: InputProvider | None,
    ) -> list[str]:
        provider = input_provider or (lambda: user_input or "")
        metadata = _session_metadata(session)
        verification = dict(metadata.get("verification", {}))
        checklist = verification.get("checklist")
        if not checklist:
            raise InvalidSessionStateError(session.session_id, "verification checklist missing")

        item_index = int(verification.get("item_index", 0))
        input_phase = verification.get("input_phase", "status")
        submissions = list(verification.get("submissions", []))
        items = checklist["items"]
        messages: list[str] = []

        if item_index >= len(items):
            raise InvalidSessionStateError(session.session_id, "verification index out of range")

        current_item = items[item_index]
        if input_phase == "status":
            status = provider().strip()
            verification["pending_status"] = status
            verification["input_phase"] = "notes"
            prompt = f"Step {current_item['step_number']}: Notes (optional):"
            updated = self._record_step(
                session,
                action=SessionActionType.RUN_VERIFICATION,
                case_state=session.case_state,
                summary=f"Verification status recorded for step {current_item['step_number']}",
                status=InvestigationSessionStatus.AWAITING_INPUT,
                turn_number=session.turn_number + 1,
                pending_prompt=prompt,
                metadata={**metadata, "verification": verification},
            )
            self._registry.save(updated)
            self._sync_session_to_case(updated)
            messages.append(prompt)
            return messages

        notes = provider().strip()
        submissions.append(
            {
                "verification_id": current_item["verification_id"],
                "status": verification.pop("pending_status", "not_tested"),
                "notes": notes,
            }
        )
        verification["submissions"] = submissions
        verification["input_phase"] = "status"
        item_index += 1
        verification["item_index"] = item_index

        if item_index < len(items):
            next_item = items[item_index]
            prompt_status = (
                f"Step {next_item['step_number']}: {next_item['description']}\n"
                "Result (passed/failed/not_tested):"
            )
            updated = self._record_step(
                session,
                action=SessionActionType.RUN_VERIFICATION,
                case_state=session.case_state,
                summary=f"Verification notes recorded for step {current_item['step_number']}",
                status=InvestigationSessionStatus.AWAITING_INPUT,
                turn_number=session.turn_number + 1,
                pending_prompt=prompt_status,
                metadata={**metadata, "verification": verification},
            )
            self._registry.save(updated)
            self._sync_session_to_case(updated)
            messages.append(prompt_status)
            return messages

        submission_objects = tuple(
            VerificationResultSubmission(
                verification_id=item["verification_id"],
                status=item["status"],
                notes=item["notes"],
            )
            for item in submissions
        )
        summary = self._runtime.submit_verification(session.case_id, submission_objects)
        messages.append(format_verification_summary(summary))
        case = self._runtime.case_manager.load_case(session.case_id)

        if summary.outcome == OUTCOME_COMPLETE:
            updated = self._record_step(
                session,
                action=SessionActionType.RUN_CLOSURE,
                case_state=case.status,
                summary="Verification complete",
                status=InvestigationSessionStatus.ACTIVE,
                turn_number=session.turn_number + 1,
                pending_prompt=None,
                metadata=_session_metadata(session),
            )
        else:
            updated = self._record_step(
                session,
                action=SessionActionType.RUN_RECOMMENDATION,
                case_state=case.status,
                summary="Verification incomplete; returning to recommendation",
                status=InvestigationSessionStatus.COMPLETED,
                turn_number=session.turn_number + 1,
                pending_prompt=None,
                metadata=_session_metadata(session),
            )

        self._registry.save(updated)
        self._sync_session_to_case(updated)
        return messages

    def _advance_automatically(self, session: InvestigationSession) -> list[str]:
        action = session.current_action
        if action == SessionActionType.INTAKE_QUESTION:
            return self._present_intake_question(session)
        if action == SessionActionType.DISCOVERY_PLANNING:
            return self._run_discovery_planning(session)
        if action == SessionActionType.RUN_ANALYSIS:
            return self._run_analysis(session)
        if action == SessionActionType.RUN_HYPOTHESIS:
            return self._run_hypothesis(session)
        if action == SessionActionType.RUN_CORRELATION:
            return self._run_correlation(session)
        if action == SessionActionType.QUALITY_EVALUATION:
            return self._run_quality_evaluation(session)
        if action == SessionActionType.RUN_RECOMMENDATION:
            return self._run_recommendation(session)
        if action == SessionActionType.RUN_VERIFICATION:
            return self._begin_verification(session)
        if action == SessionActionType.RUN_CLOSURE:
            return self._run_closure(session)
        raise InvalidSessionStateError(
            session.session_id,
            f"cannot auto-advance action {action.value}",
        )

    def _present_intake_question(self, session: InvestigationSession) -> list[str]:
        case = self._runtime.case_manager.load_case(session.case_id)
        question = get_next_question_for_phase(case, InvestigationState.INTAKE)
        turn = build_investigation_turn(case, question)
        prompt = self._format_question(turn)
        updated = self._record_step(
            session,
            action=SessionActionType.INTAKE_QUESTION,
            case_state=turn.state,
            summary="Presented intake question",
            status=InvestigationSessionStatus.AWAITING_INPUT,
            pending_question_id=turn.question_id,
            pending_prompt=prompt,
            metadata=_session_metadata(session),
        )
        self._registry.save(updated)
        self._sync_session_to_case(updated)
        return [prompt]

    def _run_discovery_planning(self, session: InvestigationSession) -> list[str]:
        case = self._runtime.case_manager.load_case(session.case_id)
        playbook = self._runtime.playbook_catalog.get(session.playbook_id)
        plan = self._runtime.plan_discovery(session.case_id)
        summary = build_intake_summary(case, playbook)

        messages = [
            "Discovery plan generated.",
            format_discovery_plan_markdown(plan).rstrip(),
            format_intake_summary(summary).rstrip(),
        ]

        request = initialize_evidence_collection(
            case,
            self._runtime.case_manager,
            playbook,
        )
        case = self._runtime.case_manager.load_case(session.case_id)

        if request is None:
            updated = self._record_step(
                session,
                action=SessionActionType.RUN_ANALYSIS,
                case_state=case.status,
                summary="Discovery planning complete; no evidence required",
                status=InvestigationSessionStatus.ACTIVE,
                turn_number=session.turn_number + 1,
                metadata=_session_metadata(session),
            )
        else:
            prompt = self._format_evidence_prompt(request)
            messages.append(prompt)
            updated = self._record_step(
                session,
                action=SessionActionType.COLLECT_EVIDENCE,
                case_state=case.status,
                summary="Discovery planning complete; evidence collection started",
                status=InvestigationSessionStatus.AWAITING_INPUT,
                turn_number=session.turn_number + 1,
                pending_evidence_command=request.command,
                pending_prompt=prompt,
                metadata=_session_metadata(session),
            )

        self._registry.save(updated)
        self._sync_session_to_case(updated)
        return messages

    def _run_analysis(self, session: InvestigationSession) -> list[str]:
        summary = self._runtime.analyze_case(session.case_id)
        case = self._runtime.case_manager.load_case(session.case_id)
        messages = list(format_analysis_summary(summary).splitlines())
        updated = self._record_step(
            session,
            action=SessionActionType.RUN_HYPOTHESIS,
            case_state=case.status,
            summary="Analysis complete",
            status=InvestigationSessionStatus.ACTIVE,
            turn_number=session.turn_number + 1,
            metadata=_session_metadata(session),
        )
        self._registry.save(updated)
        self._sync_session_to_case(updated)
        return messages

    def _run_hypothesis(self, session: InvestigationSession) -> list[str]:
        summary = self._runtime.generate_hypotheses(session.case_id)
        case = self._runtime.case_manager.load_case(session.case_id)
        messages = list(format_hypothesis_summary(summary).splitlines())
        updated = self._record_step(
            session,
            action=SessionActionType.RUN_CORRELATION,
            case_state=case.status,
            summary="Hypothesis generation complete",
            status=InvestigationSessionStatus.ACTIVE,
            turn_number=session.turn_number + 1,
            metadata=_session_metadata(session),
        )
        self._registry.save(updated)
        self._sync_session_to_case(updated)
        return messages

    def _run_correlation(self, session: InvestigationSession) -> list[str]:
        summary = self._runtime.correlate_case(session.case_id)
        case = self._runtime.case_manager.load_case(session.case_id)
        messages = list(format_correlation_summary(summary).splitlines())
        updated = self._record_step(
            session,
            action=SessionActionType.QUALITY_EVALUATION,
            case_state=case.status,
            summary="Correlation complete",
            status=InvestigationSessionStatus.ACTIVE,
            turn_number=session.turn_number + 1,
            metadata=_session_metadata(session),
        )
        self._registry.save(updated)
        self._sync_session_to_case(updated)
        return messages

    def _run_quality_evaluation(self, session: InvestigationSession) -> list[str]:
        report = self._runtime.evaluate_investigation_quality(session.case_id)
        case = self._runtime.case_manager.load_case(session.case_id)
        messages = [
            "Investigation quality evaluated.",
            format_investigation_quality_markdown(report).rstrip(),
        ]

        if report.ready_for_recommendation:
            updated = self._record_step(
                session,
                action=SessionActionType.RUN_RECOMMENDATION,
                case_state=case.status,
                summary=f"Quality score {report.overall_score}/100 — ready for recommendation",
                status=InvestigationSessionStatus.ACTIVE,
                turn_number=session.turn_number + 1,
                metadata=_session_metadata(session),
            )
        elif case.discovery_plan and case.discovery_plan.next_best_command:
            command = case.discovery_plan.next_best_command
            prompt = "\n".join(
                [
                    "Investigation quality is below the recommendation threshold.",
                    "Please provide command output:",
                    command,
                    f"(paste output; type {END_MARKER} on its own line to finish)",
                ]
            )
            updated = self._record_step(
                session,
                action=SessionActionType.COLLECT_DISCOVERY_EVIDENCE,
                case_state=case.status,
                summary=f"Quality score {report.overall_score}/100 — collecting `{command}`",
                status=InvestigationSessionStatus.AWAITING_INPUT,
                turn_number=session.turn_number + 1,
                pending_evidence_command=command,
                pending_prompt=prompt,
                metadata=_session_metadata(session),
            )
            messages.append(prompt)
        else:
            updated = self._record_step(
                session,
                action=SessionActionType.RUN_RECOMMENDATION,
                case_state=case.status,
                summary=f"Quality score {report.overall_score}/100 — proceeding without additional evidence",
                status=InvestigationSessionStatus.ACTIVE,
                turn_number=session.turn_number + 1,
                metadata=_session_metadata(session),
            )

        self._registry.save(updated)
        self._sync_session_to_case(updated)
        return messages

    def _run_recommendation(self, session: InvestigationSession) -> list[str]:
        summary = self._runtime.generate_recommendation(session.case_id)
        case = self._runtime.case_manager.load_case(session.case_id)
        messages = list(format_recommendation_summary(summary).splitlines())

        if case.status == InvestigationState.RESOLUTION:
            updated = self._record_step(
                session,
                action=SessionActionType.RUN_VERIFICATION,
                case_state=case.status,
                summary="Recommendation generated; verification required",
                status=InvestigationSessionStatus.ACTIVE,
                turn_number=session.turn_number + 1,
                metadata=_session_metadata(session),
            )
        else:
            updated = self._record_step(
                session,
                action=SessionActionType.RUN_RECOMMENDATION,
                case_state=case.status,
                summary="Recommendation generated; awaiting engineer action",
                status=InvestigationSessionStatus.COMPLETED,
                turn_number=session.turn_number + 1,
                metadata=_session_metadata(session),
            )

        self._registry.save(updated)
        self._sync_session_to_case(updated)
        return messages

    def _begin_verification(self, session: InvestigationSession) -> list[str]:
        checklist = self._runtime.generate_verification_checklist(session.case_id)
        if checklist is None:
            updated = self._record_step(
                session,
                action=SessionActionType.RUN_CLOSURE,
                case_state=session.case_state,
                summary="No verification checklist required",
                status=InvestigationSessionStatus.ACTIVE,
                turn_number=session.turn_number + 1,
                metadata=_session_metadata(session),
            )
            self._registry.save(updated)
            self._sync_session_to_case(updated)
            return []

        metadata = _session_metadata(session)
        metadata["verification"] = {
            "checklist": {
                "items": [
                    {
                        "verification_id": item.verification_id,
                        "step_number": item.step_number,
                        "description": item.description,
                    }
                    for item in checklist.items
                ],
            },
            "item_index": 0,
            "input_phase": "status",
            "submissions": [],
        }
        first_item = checklist.items[0]
        prompt = (
            f"Step {first_item.step_number}: {first_item.description}\n"
            "Result (passed/failed/not_tested):"
        )
        messages = list(format_verification_checklist(checklist).splitlines())
        messages.append(prompt)
        updated = self._record_step(
            session,
            action=SessionActionType.RUN_VERIFICATION,
            case_state=InvestigationState.RESOLUTION,
            summary="Verification checklist generated",
            status=InvestigationSessionStatus.AWAITING_INPUT,
            turn_number=session.turn_number + 1,
            pending_prompt=prompt,
            metadata=metadata,
        )
        self._registry.save(updated)
        self._sync_session_to_case(updated)
        return messages

    def _run_closure(self, session: InvestigationSession) -> list[str]:
        closure = self._runtime.close_case_with_learning(session.case_id)
        report = self._runtime.generate_report(session.case_id)
        messages = list(format_learning_closure_summary(closure).splitlines())
        messages.extend(["", "=== Incident Report ==="])
        messages.extend(format_incident_report(report).splitlines())

        case = self._runtime.case_manager.load_case(session.case_id)
        updated = self._record_step(
            session,
            action=SessionActionType.RUN_CLOSURE,
            case_state=case.status,
            summary="Case closed with learning record",
            status=InvestigationSessionStatus.COMPLETED,
            turn_number=session.turn_number + 1,
            pending_prompt=None,
            metadata=_session_metadata(session),
        )
        self._registry.save(updated)
        self._sync_session_to_case(updated)
        return messages

    def _record_step(
        self,
        session: InvestigationSession,
        *,
        action: SessionActionType,
        case_state: InvestigationState,
        summary: str,
        status: InvestigationSessionStatus,
        turn_number: int | None = None,
        pending_question_id: str | None | object = _UNSET,
        pending_evidence_command: str | None | object = _UNSET,
        pending_prompt: str | None | object = _UNSET,
        metadata: dict | None = None,
    ) -> InvestigationSession:
        now = _utc_now()
        next_sequence = len(session.journey) + 1
        journey = session.journey + (
            SessionJourneyEntry(
                sequence=next_sequence,
                timestamp=now,
                action=action,
                case_state=case_state,
                summary=summary,
            ),
        )
        updates = {
            "current_action": action,
            "case_state": case_state,
            "status": status,
            "journey": journey,
            "updated_at": now,
        }
        if turn_number is not None:
            updates["turn_number"] = turn_number
        if pending_question_id is not _UNSET:
            updates["pending_question_id"] = pending_question_id
        if pending_evidence_command is not _UNSET:
            updates["pending_evidence_command"] = pending_evidence_command
        if pending_prompt is not _UNSET:
            updates["pending_prompt"] = pending_prompt
        if metadata is not None:
            updates["metadata"] = metadata
        return replace(session, **updates)

    def _sync_session_to_case(self, session: InvestigationSession) -> None:
        case = self._runtime.case_manager.load_case(session.case_id)
        case.metadata["investigation_session"] = {
            "session_id": session.session_id,
            "status": session.status.value,
            "current_action": session.current_action.value,
            "turn_number": session.turn_number,
            "journey": [
                {
                    "sequence": entry.sequence,
                    "timestamp": entry.timestamp.isoformat(),
                    "action": entry.action.value,
                    "case_state": entry.case_state.value,
                    "summary": entry.summary,
                }
                for entry in session.journey
            ],
        }
        self._runtime.case_manager.save_case(case)

    @staticmethod
    def _format_question(turn: InvestigationTurn) -> str:
        if not turn.question_id:
            return turn.prompt
        return f"[{turn.question_id}] {turn.prompt}"

    @staticmethod
    def _format_evidence_prompt(request) -> str:
        lines = list(format_evidence_request(request).splitlines())
        lines.append(f"(paste output; type {END_MARKER} on its own line to finish)")
        return "\n".join(lines)


def _read_multiline_paste(input_provider: InputProvider, *, end_marker: str) -> str:
    lines: list[str] = []
    while True:
        line = input_provider()
        if line.strip() == end_marker:
            break
        lines.append(line)
    return "\n".join(lines)
