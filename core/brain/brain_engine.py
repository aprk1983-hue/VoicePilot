"""VoicePilot Brain orchestration engine."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import uuid4

from domain.enums import DomainEventType, InvestigationState
from domain.events import DomainEvent
from brain.brain_context import BrainContext
from brain.brain_models import (
    BrainAdvanceResult,
    BrainJourneyEntry,
    BrainSession,
    BrainStage,
)
from brain.brain_registry import BrainRegistry
from health.health_engine import HealthEngine
from runtime.exceptions import InvalidInvestigationStateError, PlaybookIdNotFoundError
from runtime.knowledge_bootstrap import default_knowledge_engine
from runtime.verification_engine import VerificationResultSubmission
from shared.constants import ID_PREFIX_BRAIN

if TYPE_CHECKING:
    from runtime.runtime_engine import RuntimeEngine


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_brain_session_id() -> str:
    return f"{ID_PREFIX_BRAIN}{uuid4().hex[:12]}"


class BrainEngine:
    """Orchestrate VoicePilot engines without implementing troubleshooting logic."""

    def __init__(
        self,
        runtime: RuntimeEngine,
        *,
        registry: BrainRegistry | None = None,
    ) -> None:
        self._runtime = runtime
        self._registry = registry or BrainRegistry()

    @property
    def registry(self) -> BrainRegistry:
        """Return the Brain session registry."""
        return self._registry

    def start_session(self, playbook_id: str) -> BrainSession:
        """Create a case and Brain session, then wait for evidence."""
        try:
            turn = self._runtime.start_investigation(playbook_id)
        except PlaybookIdNotFoundError:
            raise

        now = _utc_now()
        session = BrainSession(
            session_id=_new_brain_session_id(),
            case_id=turn.case_id,
            playbook=playbook_id,
            current_stage=BrainStage.INITIALIZING,
            started_at=now,
            last_updated=now,
            current_confidence=None,
            current_quality_score=None,
            completed=False,
            failed=False,
            decision_log_ids=(),
            journey=(
                BrainJourneyEntry(
                    sequence=1,
                    timestamp=now,
                    stage=BrainStage.INITIALIZING,
                    summary="Brain session started",
                ),
            ),
        )
        self._registry.create_session(session)
        self._publish(
            DomainEventType.BRAIN_SESSION_STARTED,
            {
                "session_id": session.session_id,
                "case_id": session.case_id,
                "playbook_id": playbook_id,
            },
        )

        session = self._transition(
            session,
            BrainStage.WAITING_FOR_EVIDENCE,
            summary="Waiting for investigative evidence",
        )
        case = self._runtime.case_manager.load_case(session.case_id)
        entry = self._record_orchestration(
            case,
            title="Brain waiting for evidence",
            description="Brain session initialized and awaiting uploaded evidence.",
            brain_stage=BrainStage.WAITING_FOR_EVIDENCE.value,
        )
        session = self._append_decision_log_id(session, entry.entry_id)
        self._registry.save_session(session)
        self._sync_to_case(session)
        self._publish(
            DomainEventType.BRAIN_WAITING_FOR_EVIDENCE,
            {"session_id": session.session_id, "case_id": session.case_id},
        )
        return session

    def get_session(self, session_id: str) -> BrainSession:
        """Return a registered Brain session."""
        return self._registry.get_session(session_id)

    def list_sessions(self) -> tuple[BrainSession, ...]:
        """Return all registered Brain sessions."""
        return self._registry.list_sessions()

    def remove_session(self, session_id: str) -> None:
        """Remove a Brain session from the registry."""
        self._registry.remove_session(session_id)

    def build_context(self, session_id: str) -> BrainContext:
        """Assemble read-only orchestration context for a session."""
        session = self.get_session(session_id)
        case = self._runtime.case_manager.load_case(session.case_id)
        health_report = None
        knowledge_report = None
        if case.voice_objects:
            health_report = HealthEngine().evaluate_case(case)
            knowledge_report = default_knowledge_engine().evaluate_case(case)
        return BrainContext(
            case=case,
            discovery_plan=case.discovery_plan,
            investigation_quality_report=case.investigation_quality_report,
            health_report=health_report,
            knowledge_report=knowledge_report,
            topology=case.topology,
            decision_log=tuple(case.decision_log),
            hypotheses=tuple(case.hypotheses),
            recommendations=tuple(case.recommendations),
        )

    def advance_session(self, session_id: str) -> BrainAdvanceResult:
        """Advance the Brain pipeline through orchestrated runtime calls."""
        session = self.get_session(session_id)
        if session.completed or session.failed:
            return BrainAdvanceResult(session=session)

        if session.current_stage == BrainStage.WAITING_FOR_EVIDENCE:
            case = self._runtime.case_manager.load_case(session.case_id)
            if not case.evidence:
                return BrainAdvanceResult(
                    session=session,
                    messages=("Brain is waiting for evidence before continuing.",),
                )
            try:
                self._prepare_case_for_analysis(session.case_id)
            except InvalidInvestigationStateError as exc:
                session = self._mark_failed(session, str(exc))
                return BrainAdvanceResult(session=session, messages=(str(exc),))

        messages: list[str] = []
        try:
            session, stage_messages = self._run_pipeline(session)
            messages.extend(stage_messages)
        except Exception as exc:  # pragma: no cover - guardrail
            session = self._mark_failed(session, str(exc))
            messages.append(str(exc))

        return BrainAdvanceResult(session=session, messages=tuple(messages))

    def _run_pipeline(self, session: BrainSession) -> tuple[BrainSession, list[str]]:
        messages: list[str] = []
        case_id = session.case_id

        session = self._transition(session, BrainStage.PARSING, summary="Parsing evidence")
        messages.append("Invoking Parser Engine via RuntimeEngine.analyze_case().")

        self._runtime.analyze_case(case_id)
        session = self._transition(session, BrainStage.ANALYZING, summary="Analysis completed")
        self._publish(
            DomainEventType.BRAIN_ANALYSIS_COMPLETED,
            {"session_id": session.session_id, "case_id": case_id},
        )
        case = self._runtime.case_manager.load_case(case_id)
        entry = self._record_orchestration(
            case,
            title="Brain analysis completed",
            description="Parser and analysis engines completed via RuntimeEngine.",
            brain_stage=BrainStage.ANALYZING.value,
        )
        session = self._append_decision_log_id(session, entry.entry_id)
        session = self._update_metrics(session, case)

        self._runtime.generate_hypotheses(case_id)
        session = self._transition(session, BrainStage.CORRELATING, summary="Correlating findings")
        self._runtime.correlate_case(case_id)
        session = self._transition(session, BrainStage.CORRELATING, summary="Correlation completed")
        case = self._runtime.case_manager.load_case(case_id)
        session = self._update_metrics(session, case)

        session = self._transition(
            session,
            BrainStage.DISCOVERY_PLANNING,
            summary="Discovery plan generated",
        )
        self._runtime.plan_discovery(case_id)
        case = self._runtime.case_manager.load_case(case_id)
        entry = self._record_orchestration(
            case,
            title="Brain discovery planning completed",
            description="Discovery Planner invoked via RuntimeEngine.plan_discovery().",
            brain_stage=BrainStage.DISCOVERY_PLANNING.value,
        )
        session = self._append_decision_log_id(session, entry.entry_id)

        session = self._transition(
            session,
            BrainStage.QUALITY_EVALUATION,
            summary="Investigation quality updated",
        )
        quality_report = self._runtime.evaluate_investigation_quality(case_id)
        session = replace(session, current_quality_score=quality_report.overall_score)
        case = self._runtime.case_manager.load_case(case_id)
        entry = self._record_orchestration(
            case,
            title="Brain quality evaluation completed",
            description=f"Investigation quality score {quality_report.overall_score}/100.",
            brain_stage=BrainStage.QUALITY_EVALUATION.value,
            metadata={"overall_score": quality_report.overall_score},
        )
        session = self._append_decision_log_id(session, entry.entry_id)

        session = self._transition(
            session,
            BrainStage.RECOMMENDING,
            summary="Recommendation generated",
        )
        self._runtime.generate_recommendation(case_id)
        self._publish(
            DomainEventType.BRAIN_RECOMMENDATION_READY,
            {"session_id": session.session_id, "case_id": case_id},
        )
        case = self._runtime.case_manager.load_case(case_id)
        entry = self._record_orchestration(
            case,
            title="Brain recommendation ready",
            description="Recommendation Engine invoked via RuntimeEngine.",
            brain_stage=BrainStage.RECOMMENDING.value,
        )
        session = self._append_decision_log_id(session, entry.entry_id)
        session = self._update_metrics(session, case)

        if case.status == InvestigationState.RESOLUTION:
            session = self._transition(session, BrainStage.VERIFYING, summary="Verification started")
            checklist = self._runtime.generate_verification_checklist(case_id)
            if checklist is not None:
                submissions = [
                    VerificationResultSubmission(
                        verification_id=item.verification_id,
                        status="passed",
                        notes="Brain orchestration auto-verification",
                    )
                    for item in checklist.items
                ]
                self._runtime.submit_verification(case_id, submissions)
            session = self._transition(
                session,
                BrainStage.VERIFYING,
                summary="Verification complete",
            )

            session = self._transition(session, BrainStage.LEARNING, summary="Learning record created")
            self._runtime.close_case_with_learning(case_id)
            session = self._transition(session, BrainStage.COMPLETE, summary="Investigation closed")
            session = replace(session, completed=True, last_updated=_utc_now())
            self._publish(
                DomainEventType.BRAIN_COMPLETED,
                {"session_id": session.session_id, "case_id": case_id},
            )
            case = self._runtime.case_manager.load_case(case_id)
            entry = self._record_orchestration(
                case,
                title="Brain investigation complete",
                description="Verification and Learning engines completed; case closed.",
                brain_stage=BrainStage.COMPLETE.value,
            )
            session = self._append_decision_log_id(session, entry.entry_id)
        else:
            session = replace(session, completed=True, last_updated=_utc_now())
            self._publish(
                DomainEventType.BRAIN_COMPLETED,
                {"session_id": session.session_id, "case_id": case_id},
            )

        self._registry.save_session(session)
        self._sync_to_case(session)
        return session, messages

    def _prepare_case_for_analysis(self, case_id: str) -> None:
        case = self._runtime.case_manager.load_case(case_id)
        if case.status == InvestigationState.ANALYSIS:
            return
        if case.status == InvestigationState.INTAKE:
            self._runtime.case_manager.transition_state(case_id, InvestigationState.DISCOVERY)
        case = self._runtime.case_manager.load_case(case_id)
        if case.status == InvestigationState.DISCOVERY:
            self._runtime.case_manager.transition_state(case_id, InvestigationState.COLLECTION)
        case = self._runtime.case_manager.load_case(case_id)
        if case.status == InvestigationState.COLLECTION:
            self._runtime.case_manager.transition_state(case_id, InvestigationState.ANALYSIS)

    def _transition(
        self,
        session: BrainSession,
        stage: BrainStage,
        *,
        summary: str,
    ) -> BrainSession:
        if session.current_stage == stage and session.journey and session.journey[-1].summary == summary:
            return session

        now = _utc_now()
        journey = session.journey + (
            BrainJourneyEntry(
                sequence=len(session.journey) + 1,
                timestamp=now,
                stage=stage,
                summary=summary,
            ),
        )
        updated = replace(
            session,
            current_stage=stage,
            journey=journey,
            last_updated=now,
        )
        self._registry.save_session(updated)
        self._sync_to_case(updated)
        self._publish(
            DomainEventType.BRAIN_STAGE_CHANGED,
            {
                "session_id": updated.session_id,
                "case_id": updated.case_id,
                "from_stage": session.current_stage.value,
                "to_stage": stage.value,
            },
        )
        return updated

    def _update_metrics(self, session: BrainSession, case) -> BrainSession:
        context = BrainContext(
            case=case,
            discovery_plan=case.discovery_plan,
            investigation_quality_report=case.investigation_quality_report,
            health_report=None,
            knowledge_report=None,
            topology=case.topology,
            decision_log=tuple(case.decision_log),
            hypotheses=tuple(case.hypotheses),
            recommendations=tuple(case.recommendations),
        )
        updated = replace(
            session,
            current_confidence=context.top_confidence,
            current_quality_score=(
                case.investigation_quality_report.overall_score
                if case.investigation_quality_report is not None
                else session.current_quality_score
            ),
            last_updated=_utc_now(),
        )
        self._registry.save_session(updated)
        self._sync_to_case(updated)
        return updated

    def _record_orchestration(
        self,
        case,
        *,
        title: str,
        description: str,
        brain_stage: str,
        metadata: dict | None = None,
    ):
        entry = self._runtime.decision_log_engine.append_brain_orchestration(
            case,
            title=title,
            description=description,
            brain_stage=brain_stage,
            metadata=metadata,
        )
        self._runtime.case_manager.save_case(case)
        return entry

    def _append_decision_log_id(self, session: BrainSession, entry_id: str) -> BrainSession:
        updated = replace(
            session,
            decision_log_ids=session.decision_log_ids + (entry_id,),
            last_updated=_utc_now(),
        )
        self._registry.save_session(updated)
        return updated

    def _mark_failed(self, session: BrainSession, reason: str) -> BrainSession:
        updated = self._transition(session, BrainStage.FAILED, summary=reason)
        updated = replace(updated, failed=True, last_updated=_utc_now())
        self._registry.save_session(updated)
        self._sync_to_case(updated)
        return updated

    def _publish(self, event_type: DomainEventType, payload: dict) -> None:
        self._runtime.event_bus.publish(DomainEvent.create(event_type, payload))

    def _sync_to_case(self, session: BrainSession) -> None:
        case = self._runtime.case_manager.load_case(session.case_id)
        case.metadata["brain_session"] = {
            "session_id": session.session_id,
            "playbook": session.playbook,
            "current_stage": session.current_stage.value,
            "current_confidence": session.current_confidence,
            "current_quality_score": session.current_quality_score,
            "completed": session.completed,
            "failed": session.failed,
            "decision_log_ids": list(session.decision_log_ids),
            "journey": [
                {
                    "sequence": entry.sequence,
                    "timestamp": entry.timestamp.isoformat(),
                    "stage": entry.stage.value,
                    "summary": entry.summary,
                    "decision_log_id": entry.decision_log_id,
                }
                for entry in session.journey
            ],
        }
        self._runtime.case_manager.save_case(case)
