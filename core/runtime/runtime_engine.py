"""VoicePilot Runtime Engine — kernel orchestrator."""

from __future__ import annotations

from typing import Any

from domain.enums import InvestigationState
from domain.interfaces import CaseRepository, LoggerPort, PlaybookRepository
from domain.models import InvestigationTurn
from runtime.analysis_engine import (
    AnalysisEngine,
    AnalysisSummary,
    build_analysis_summary,
    format_analysis_summary,
)
from runtime.parser_bootstrap import build_default_parser_engine
from runtime.case_manager import CaseManager
from runtime.engine_registry import EngineRegistry
from runtime.event_bus import EventBus
from runtime.exceptions import CaseNotFoundError, InvalidInvestigationStateError, PlaybookIdNotFoundError, QuestionNotFoundError
from runtime.correlation_engine import (
    CorrelationEngine,
    CorrelationSummary,
    format_correlation_summary,
)
from runtime.hypothesis_engine import HypothesisEngine, HypothesisSummary, build_hypothesis_summary
from runtime.learning_engine import (
    LearningClosureSummary,
    LearningEngine,
    build_learning_closure_summary,
)
from runtime.recommendation_engine import RecommendationEngine, RecommendationSummary, build_recommendation_summary
from runtime.report_engine import IncidentReport, ReportEngine
from runtime.verification_engine import (
    OUTCOME_COMPLETE,
    OUTCOME_FAILED,
    VerificationChecklist,
    VerificationEngine,
    VerificationResultSubmission,
    VerificationSummary,
)
from runtime.intake_flow import (
    attach_flow_state,
    build_case_intake,
    build_investigation_turn,
    find_question,
    get_next_question_for_phase,
    initialize_flow_state,
    intake_phase_complete,
    record_answer,
)
from runtime.playbook_catalog import PlaybookCatalog
from runtime.playbook_loader import PlaybookLoader
from runtime.plugin_registry import PluginRegistry
from runtime.state_machine import InvestigationStateMachine
from shared.config import RuntimeConfig
from shared.constants import DEFAULT_CONFIDENCE_THRESHOLD
from parser.parser_engine import ParserEngine
from shared.types import CaseId


class RuntimeEngine:
    """Top-level runtime kernel orchestrator.

    v1 supports deterministic intake question flow from plugin playbooks.
    Reasoning, evidence evaluation, and confidence gates are future sprints.
    """

    def __init__(
        self,
        config: RuntimeConfig,
        case_repository: CaseRepository,
        playbook_repository: PlaybookRepository,
        plugin_registry: PluginRegistry | None = None,
        playbook_catalog: PlaybookCatalog | None = None,
        parser_engine: ParserEngine | None = None,
        logger: LoggerPort | None = None,
    ) -> None:
        self._config = config
        self._event_bus = EventBus(logger=logger)
        self._state_machine = InvestigationStateMachine()
        self._engine_registry = EngineRegistry(logger=logger)
        self._case_manager = CaseManager(
            repository=case_repository,
            state_machine=self._state_machine,
            event_bus=self._event_bus,
            logger=logger,
        )
        self._playbook_loader = PlaybookLoader(
            repository=playbook_repository,
            event_bus=self._event_bus,
            logger=logger,
        )
        self._plugin_registry = plugin_registry or PluginRegistry(
            plugins_root=config.playbooks_path,
            logger=logger,
        )
        self._playbook_catalog = playbook_catalog or PlaybookCatalog(
            plugin_registry=self._plugin_registry,
            playbook_loader=self._playbook_loader,
            logger=logger,
        )
        self._logger = logger
        self._parser_engine = parser_engine

        # TODO: Register real engine implementations and wire execution pipeline.
        self._engine_registry.register_defaults()

    @property
    def config(self) -> RuntimeConfig:
        """Runtime configuration."""
        return self._config

    @property
    def event_bus(self) -> EventBus:
        """Internal domain event bus."""
        return self._event_bus

    @property
    def case_manager(self) -> CaseManager:
        """Case aggregate manager."""
        return self._case_manager

    @property
    def playbook_loader(self) -> PlaybookLoader:
        """DSL playbook loader."""
        return self._playbook_loader

    @property
    def plugin_registry(self) -> PluginRegistry:
        """Plugin manifest registry."""
        return self._plugin_registry

    @property
    def playbook_catalog(self) -> PlaybookCatalog:
        """Plugin playbook catalog."""
        return self._playbook_catalog

    @property
    def state_machine(self) -> InvestigationStateMachine:
        """Investigation lifecycle state machine."""
        return self._state_machine

    @property
    def engine_registry(self) -> EngineRegistry:
        """Brain engine registry."""
        return self._engine_registry

    def start(self) -> None:
        """Initialize runtime kernel and warm playbook catalog."""
        self._ensure_playbook_catalog()

    def shutdown(self) -> None:
        """Gracefully shut down runtime kernel."""
        self._event_bus.clear()

    def start_investigation(self, playbook_id: str) -> InvestigationTurn:
        """Start a new investigation from a cataloged playbook ID.

        Loads the playbook, creates a case, transitions to ``INTAKE``, and
        returns the first intake question.
        """
        self._ensure_playbook_catalog()
        if not self._playbook_catalog.is_loaded(playbook_id):
            raise PlaybookIdNotFoundError(playbook_id)

        entry = self._playbook_catalog.get_entry(playbook_id)
        playbook = entry.playbook
        case = self._case_manager.create_case(
            build_case_intake(playbook, entry.plugin_name),
        )
        flow_state = initialize_flow_state(playbook, case.case_id)
        flow_state["plugin_name"] = entry.plugin_name
        attach_flow_state(case, flow_state)
        case.playbook_version = playbook.version

        self._case_manager.save_case(case)
        self._case_manager.transition_state(case.case_id, InvestigationState.INTAKE)

        case = self._case_manager.load_case(case.case_id)
        first_question = get_next_question_for_phase(case, InvestigationState.INTAKE)
        if first_question is None:
            raise PlaybookIdNotFoundError(playbook_id)

        turn = build_investigation_turn(case, first_question)
        self._case_manager.save_case(case)

        if self._logger:
            self._logger.info(
                "Investigation started",
                case_id=case.case_id,
                playbook_id=playbook_id,
            )
        return turn

    def submit_answer(
        self,
        case_id: CaseId,
        question_id: str,
        answer: Any,
    ) -> InvestigationTurn:
        """Record an answer and return the next investigation turn."""
        try:
            case = self._case_manager.load_case(case_id)
        except CaseNotFoundError:
            raise

        question = find_question(case, question_id)
        if question is None:
            raise QuestionNotFoundError(case_id, question_id)

        record_answer(case, question, answer)
        self._case_manager.save_case(case)

        if case.status == InvestigationState.INTAKE and intake_phase_complete(case):
            self._case_manager.transition_state(case_id, InvestigationState.DISCOVERY)
            case = self._case_manager.load_case(case_id)

        next_question = get_next_question_for_phase(case, case.status)
        if next_question is not None:
            turn = build_investigation_turn(case, next_question)
            self._case_manager.save_case(case)
            return turn

        return build_investigation_turn(case, None)

    def analyze_case(self, case_id: CaseId) -> AnalysisSummary:
        """Analyze collected evidence, attach findings, and move to HYPOTHESIS."""
        case = self._case_manager.load_case(case_id)
        engine = AnalysisEngine(parser_engine=self._get_parser_engine())
        findings = engine.analyze(case)
        case.analysis_findings = findings
        self._case_manager.save_case(case)

        if case.status == InvestigationState.ANALYSIS:
            self._case_manager.transition_state(case_id, InvestigationState.HYPOTHESIS)
            case = self._case_manager.load_case(case_id)

        if self._logger:
            self._logger.info(
                "Case analysis complete",
                case_id=case_id,
                findings=[finding.signal for finding in findings],
            )

        return build_analysis_summary(case, findings)

    def generate_hypotheses(self, case_id: CaseId) -> HypothesisSummary:
        """Generate ranked hypotheses and move the case to INVESTIGATION."""
        case = self._case_manager.load_case(case_id)
        if case.status != InvestigationState.HYPOTHESIS:
            raise InvalidInvestigationStateError(
                case_id,
                InvestigationState.HYPOTHESIS.value,
                case.status.value,
            )

        engine = HypothesisEngine()
        hypotheses = engine.generate(case)
        case.hypotheses = hypotheses
        self._case_manager.save_case(case)
        self._case_manager.transition_state(case_id, InvestigationState.INVESTIGATION)
        case = self._case_manager.load_case(case_id)

        if self._logger:
            self._logger.info(
                "Hypotheses generated",
                case_id=case_id,
                count=len(hypotheses),
                titles=[hypothesis.title for hypothesis in hypotheses],
            )

        return build_hypothesis_summary(case, hypotheses)

    def correlate_case(self, case_id: CaseId) -> CorrelationSummary:
        """Correlate findings, adjust hypothesis confidence, and store results."""
        case = self._case_manager.load_case(case_id)
        engine = CorrelationEngine()
        summary = engine.correlate(case)
        self._case_manager.save_case(case)

        if self._logger:
            self._logger.info(
                "Case correlation complete",
                case_id=case_id,
                correlation_count=summary.correlation_count,
                hypotheses_updated=summary.hypotheses_updated,
            )

        return summary

    def generate_recommendation(self, case_id: CaseId) -> RecommendationSummary:
        """Generate a recommendation from the top hypothesis."""
        case = self._case_manager.load_case(case_id)
        if case.status != InvestigationState.INVESTIGATION:
            raise InvalidInvestigationStateError(
                case_id,
                InvestigationState.INVESTIGATION.value,
                case.status.value,
            )

        engine = RecommendationEngine()
        recommendation = engine.generate(case)
        case.recommendations.append(recommendation)
        self._case_manager.save_case(case)

        confidence = recommendation.confidence or 0.0
        if confidence >= DEFAULT_CONFIDENCE_THRESHOLD:
            self._case_manager.transition_state(case_id, InvestigationState.RESOLUTION)
            case = self._case_manager.load_case(case_id)

        if self._logger:
            self._logger.info(
                "Recommendation generated",
                case_id=case_id,
                action_type=recommendation.action_type,
                confidence=confidence,
            )

        return build_recommendation_summary(case, recommendation)

    def generate_verification_checklist(self, case_id: CaseId) -> VerificationChecklist | None:
        """Build a verification checklist for a likely root cause recommendation."""
        case = self._case_manager.load_case(case_id)
        if case.status != InvestigationState.RESOLUTION:
            return None

        engine = VerificationEngine()
        checklist = engine.generate_checklist(case)
        if checklist is not None:
            self._case_manager.save_case(case)
        return checklist

    def submit_verification(
        self,
        case_id: CaseId,
        submissions: list[VerificationResultSubmission],
        *,
        actor: str = "engineer",
    ) -> VerificationSummary:
        """Record verification results and advance or regress investigation state."""
        case = self._case_manager.load_case(case_id)
        engine = VerificationEngine()

        if case.status == InvestigationState.RESOLUTION:
            engine.generate_checklist(case)
            self._case_manager.save_case(case)
            self._case_manager.transition_state(case_id, InvestigationState.VERIFICATION)
            case = self._case_manager.load_case(case_id)

        if case.status != InvestigationState.VERIFICATION:
            raise InvalidInvestigationStateError(
                case_id,
                InvestigationState.VERIFICATION.value,
                case.status.value,
            )

        summary = engine.apply_results(case, submissions, actor=actor)
        self._case_manager.save_case(case)

        if summary.outcome == OUTCOME_FAILED:
            self._case_manager.transition_state(case_id, InvestigationState.RESOLUTION)
            self._case_manager.transition_state(case_id, InvestigationState.INVESTIGATION)
            case = self._case_manager.load_case(case_id)
        elif summary.outcome == OUTCOME_COMPLETE:
            self._case_manager.transition_state(case_id, InvestigationState.LEARNING)
            case = self._case_manager.load_case(case_id)

        return VerificationSummary(
            case_id=case.case_id,
            state=case.status,
            outcome=summary.outcome,
            message=summary.message,
        )

    def close_case_with_learning(self, case_id: CaseId) -> LearningClosureSummary:
        """Create a learning record and close a verified case."""
        case = self._case_manager.load_case(case_id)
        if case.status != InvestigationState.LEARNING:
            raise InvalidInvestigationStateError(
                case_id,
                InvestigationState.LEARNING.value,
                case.status.value,
            )

        engine = LearningEngine()
        learning_record = engine.create_learning_record(case)
        case.learning_record = learning_record
        case.resolution_summary = learning_record.resolution_summary
        case.root_cause_id = learning_record.hypothesis_id
        case.closed_at = learning_record.created_at
        self._case_manager.save_case(case)
        self._case_manager.transition_state(case_id, InvestigationState.CLOSED)
        case = self._case_manager.load_case(case_id)

        if self._logger:
            self._logger.info(
                "Case closed with learning record",
                case_id=case_id,
                learning_record_id=learning_record.learning_record_id,
            )

        return build_learning_closure_summary(case, learning_record)

    def _get_parser_engine(self) -> ParserEngine | None:
        """Return configured parser engine or bootstrap Cisco parsers by default."""
        if self._parser_engine is not None:
            return self._parser_engine
        self._parser_engine = build_default_parser_engine()
        return self._parser_engine

    def generate_report(self, case_id: CaseId) -> IncidentReport:
        """Generate a readable incident report for a closed case."""
        case = self._case_manager.load_case(case_id)
        if case.status != InvestigationState.CLOSED:
            raise InvalidInvestigationStateError(
                case_id,
                InvestigationState.CLOSED.value,
                case.status.value,
            )

        engine = ReportEngine()
        report = engine.generate(case)

        if self._logger:
            self._logger.info(
                "Incident report generated",
                case_id=case_id,
                playbook_id=report.playbook_id,
            )

        return report

    def _ensure_playbook_catalog(self) -> None:
        """Load plugin playbooks if the catalog is empty."""
        if not self._playbook_catalog.list_all():
            self._playbook_catalog.load_all()
