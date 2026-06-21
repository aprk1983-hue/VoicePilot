"""Public VoicePilot service facade over existing runtime engines."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from brain.brain_models import BrainSession
from brain.brain_report import format_brain_replay
from domain.enums import InvestigationState
from domain.models import Case, Hypothesis
from infrastructure.filesystem import FilesystemPlaybookRepository, InMemoryCaseRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.analysis_engine import build_analysis_summary
from runtime.evidence_collection import submit_evidence
from runtime.exceptions import CaseNotFoundError, PlaybookIdNotFoundError
from brain.brain_exceptions import BrainSessionNotFoundError
from change_package.change_report import format_change_package_markdown
from investigation_compare.compare_models import InvestigationSnapshot
from investigation_compare.compare_report import format_comparison_markdown
from reporting.report_models import ReportType
from runtime.runtime_engine import RuntimeEngine
from services.service_exceptions import (
    ServiceBrainSessionNotFoundError,
    ServiceCaseNotFoundError,
    ServicePlaybookNotFoundError,
)
from services.service_models import (
    ServiceAnalysisResult,
    ServiceBrainSessionResult,
    ServiceCaseResult,
    ServiceChangePackageResult,
    ServiceDiscoveryResult,
    ServiceEvidenceResult,
    ServiceQualityResult,
    ServiceRecommendationResult,
    ServiceReportResult,
    ReportResult,
    ComparisonResult,
    AssetValidationResult,
    AssetStatisticsResult,
)
from shared.config import RuntimeConfig
from shared.types import CaseId

if TYPE_CHECKING:
    from brain.brain_engine import BrainEngine


def default_plugins_root() -> Path:
    """Return the default plugins directory for VoicePilot."""
    return Path(__file__).resolve().parents[2] / "plugins"


def build_default_runtime_engine(plugins_root: Path | None = None) -> RuntimeEngine:
    """Construct a runtime engine wired to plugin playbooks."""
    root = plugins_root or default_plugins_root()
    return RuntimeEngine(
        config=RuntimeConfig(playbooks_path=root),
        case_repository=InMemoryCaseRepository(),
        playbook_repository=FilesystemPlaybookRepository(YamlLoader()),
    )


class VoicePilotService:
    """Stable public facade for VoicePilot investigation workflows.

    Delegates all behavior to ``RuntimeEngine`` and Brain orchestration without
    implementing troubleshooting logic directly.
    """

    def __init__(
        self,
        runtime_engine: RuntimeEngine | None = None,
        brain_engine: BrainEngine | None = None,
        *,
        plugins_root: Path | None = None,
    ) -> None:
        self._runtime = runtime_engine
        self._brain_engine = brain_engine
        self._plugins_root = plugins_root
        self._started = False

    @property
    def runtime(self) -> RuntimeEngine:
        """Return the underlying runtime engine, starting it if needed."""
        return self._ensure_runtime()

    def create_case(self, playbook_id: str) -> ServiceCaseResult:
        """Create a new investigation case from a cataloged playbook."""
        runtime = self._ensure_runtime()
        try:
            turn = runtime.start_investigation(playbook_id)
        except PlaybookIdNotFoundError as exc:
            raise ServicePlaybookNotFoundError(playbook_id) from exc

        case = runtime.case_manager.load_case(turn.case_id)
        return _map_case_result(case)

    def upload_evidence(
        self,
        case_id: str,
        command: str,
        content: str,
        evidence_id: str | None = None,
    ) -> ServiceEvidenceResult:
        """Upload CLI evidence output to a case."""
        runtime = self._ensure_runtime()
        case = self._load_case(case_id)
        submission = submit_evidence(
            case,
            runtime.case_manager,
            command,
            content,
            decision_log=runtime.decision_log_engine,
        )
        return ServiceEvidenceResult(
            case_id=case_id,
            evidence_id=evidence_id or submission.evidence_id,
            command=command,
            accepted=True,
        )

    def analyze_case(self, case_id: str) -> ServiceAnalysisResult:
        """Analyze evidence and produce ranked hypotheses for a case."""
        runtime = self._ensure_runtime()
        case = self._load_case(case_id)

        if case.status in {
            InvestigationState.INTAKE,
            InvestigationState.DISCOVERY,
            InvestigationState.COLLECTION,
        }:
            self._prepare_case_for_analysis(case_id)
            case = runtime.case_manager.load_case(case_id)

        if case.status == InvestigationState.ANALYSIS:
            summary = runtime.analyze_case(case_id)
            case = runtime.case_manager.load_case(case_id)
        else:
            summary = build_analysis_summary(case, case.analysis_findings)

        if case.status == InvestigationState.HYPOTHESIS:
            runtime.generate_hypotheses(case_id)
            case = runtime.case_manager.load_case(case_id)

        if case.status == InvestigationState.INVESTIGATION and case.hypotheses:
            if not case.correlation_results:
                runtime.correlate_case(case_id)
                case = runtime.case_manager.load_case(case_id)

        top_hypothesis = _top_hypothesis(case)
        return ServiceAnalysisResult(
            case_id=case_id,
            finding_count=len(summary.findings),
            top_hypothesis=top_hypothesis.title if top_hypothesis else None,
            confidence=top_hypothesis.confidence if top_hypothesis else None,
        )

    def plan_discovery(self, case_id: str) -> ServiceDiscoveryResult:
        """Generate and store a discovery plan for a case."""
        runtime = self._ensure_runtime()
        plan = runtime.plan_discovery(case_id)
        return ServiceDiscoveryResult(
            case_id=case_id,
            current_confidence=plan.current_confidence,
            estimated_final_confidence=plan.estimated_final_confidence,
            next_best_command=plan.next_best_command,
            request_count=len(plan.requests),
        )

    def evaluate_quality(self, case_id: str) -> ServiceQualityResult:
        """Evaluate investigation quality for a case."""
        runtime = self._ensure_runtime()
        report = runtime.evaluate_investigation_quality(case_id)
        return ServiceQualityResult(
            case_id=case_id,
            overall_score=report.overall_score,
            overall_status=report.overall_status,
            ready_for_recommendation=report.ready_for_recommendation,
            ready_for_case_closure=report.ready_for_case_closure,
        )

    def generate_recommendation(self, case_id: str) -> ServiceRecommendationResult:
        """Generate a recommendation for a case."""
        runtime = self._ensure_runtime()
        summary = runtime.generate_recommendation(case_id)
        case = runtime.case_manager.load_case(case_id)
        top_recommendation = summary.likely_root_cause
        if top_recommendation is None and case.recommendations:
            top_recommendation = case.recommendations[-1].description
        return ServiceRecommendationResult(
            case_id=case_id,
            recommendation_count=len(case.recommendations),
            top_recommendation=top_recommendation,
        )

    def generate_report(
        self,
        case_id: str,
        report_type: ReportType = ReportType.ENGINEERING,
    ) -> ReportResult:
        """Generate an audience-specific enterprise report for a case."""
        runtime = self._ensure_runtime()
        report = runtime.generate_report(case_id, report_type)
        return ReportResult(
            case_id=case_id,
            report_id=report.report_id,
            report_type=report.report_type.value,
            markdown=report.markdown,
        )

    def generate_legacy_report(self, case_id: str) -> ServiceReportResult:
        """Generate a legacy closed-case incident report."""
        runtime = self._ensure_runtime()
        incident = runtime.generate_report(case_id)
        from runtime.report_engine import format_incident_report

        return ServiceReportResult(
            case_id=case_id,
            markdown=format_incident_report(incident),
        )

    def generate_change_package(self, case_id: str) -> ServiceChangePackageResult:
        """Generate a read-only engineering change package for a case."""
        runtime = self._ensure_runtime()
        package = runtime.generate_change_package(case_id)
        return ServiceChangePackageResult(
            case_id=case_id,
            package_id=package.package_id,
            risk_level=package.risk_level.value,
            title=package.title,
            markdown=format_change_package_markdown(package),
        )

    def compare_cases(self, before_case_id: str, after_case_id: str) -> ComparisonResult:
        """Compare two investigation cases and return a comparison report."""
        runtime = self._ensure_runtime()
        comparison = runtime.compare_cases(before_case_id, after_case_id)
        return ComparisonResult(
            comparison_id=comparison.comparison_id,
            status=comparison.status.value,
            summary=comparison.summary,
            markdown=format_comparison_markdown(comparison),
            before_case_id=before_case_id,
            after_case_id=after_case_id,
        )

    def compare_snapshots(
        self,
        before_snapshot: InvestigationSnapshot,
        after_snapshot: InvestigationSnapshot,
    ) -> ComparisonResult:
        """Compare two investigation snapshots and return a comparison report."""
        runtime = self._ensure_runtime()
        comparison = runtime.compare_snapshots(before_snapshot, after_snapshot)
        return ComparisonResult(
            comparison_id=comparison.comparison_id,
            status=comparison.status.value,
            summary=comparison.summary,
            markdown=format_comparison_markdown(comparison),
            before_case_id=comparison.before_case_id,
            after_case_id=comparison.after_case_id,
        )

    def validate_assets(self) -> AssetValidationResult:
        """Validate bundled engineering knowledge assets."""
        runtime = self._ensure_runtime()
        report = runtime.validate_assets()
        invalid_count = sum(1 for item in report.asset_reports if not item.valid)
        return AssetValidationResult(
            valid=report.valid,
            total_assets=len(report.asset_reports),
            invalid_count=invalid_count,
            duplicate_ids=report.duplicate_ids,
            duplicate_titles=report.duplicate_titles,
        )

    def asset_statistics(self) -> AssetStatisticsResult:
        """Return statistics for bundled engineering knowledge assets."""
        runtime = self._ensure_runtime()
        stats = runtime.asset_statistics()
        return AssetStatisticsResult(
            total_assets=stats.total_assets,
            average_quality=stats.average_quality,
            missing_references=stats.missing_references,
            relationship_count=stats.relationship_count,
            duplicate_ids=stats.duplicate_ids,
            vendor_counts=stats.vendor_counts,
            product_counts=stats.product_counts,
            category_counts=stats.category_counts,
        )

    def get_case(self, case_id: str) -> ServiceCaseResult:
        """Return a summary view of a case."""
        case = self._load_case(case_id)
        return _map_case_result(case)

    def list_cases(self) -> list[ServiceCaseResult]:
        """Return summary views for all in-memory cases."""
        runtime = self._ensure_runtime()
        return [
            _map_case_result(runtime.case_manager.load_case(case_id))
            for case_id in runtime.case_manager.list_cases()
        ]

    def start_brain_session(self, playbook_id: str) -> ServiceBrainSessionResult:
        """Start a Brain orchestration session for a playbook."""
        runtime = self._ensure_runtime()
        try:
            session = runtime.start_brain_session(playbook_id)
        except PlaybookIdNotFoundError as exc:
            raise ServicePlaybookNotFoundError(playbook_id) from exc
        return _map_brain_session(session)

    def get_brain_status(self, session_id: str) -> ServiceBrainSessionResult:
        """Return Brain session status."""
        session = self._load_brain_session(session_id)
        return _map_brain_session(session)

    def replay_brain_session(self, session_id: str) -> str:
        """Return a formatted Brain investigation replay timeline."""
        runtime = self._ensure_runtime()
        session = self._load_brain_session(session_id)
        context = self._brain(runtime).build_context(session_id)
        return format_brain_replay(session, context)

    def _ensure_runtime(self) -> RuntimeEngine:
        if self._runtime is None:
            self._runtime = build_default_runtime_engine(self._plugins_root)
        if not self._started:
            self._runtime.start()
            self._started = True
        return self._runtime

    def _brain(self, runtime: RuntimeEngine) -> BrainEngine:
        if self._brain_engine is not None:
            return self._brain_engine
        return runtime.brain_engine

    def _load_case(self, case_id: CaseId) -> Case:
        runtime = self._ensure_runtime()
        try:
            return runtime.case_manager.load_case(case_id)
        except CaseNotFoundError as exc:
            raise ServiceCaseNotFoundError(case_id) from exc

    def _load_brain_session(self, session_id: str) -> BrainSession:
        runtime = self._ensure_runtime()
        try:
            return self._brain(runtime).get_session(session_id)
        except BrainSessionNotFoundError as exc:
            raise ServiceBrainSessionNotFoundError(session_id) from exc

    def _prepare_case_for_analysis(self, case_id: str) -> None:
        runtime = self._ensure_runtime()
        case = runtime.case_manager.load_case(case_id)
        if case.status == InvestigationState.ANALYSIS:
            return
        if case.status == InvestigationState.INTAKE:
            runtime.case_manager.transition_state(case_id, InvestigationState.DISCOVERY)
        case = runtime.case_manager.load_case(case_id)
        if case.status == InvestigationState.DISCOVERY:
            runtime.case_manager.transition_state(case_id, InvestigationState.COLLECTION)
        case = runtime.case_manager.load_case(case_id)
        if case.status == InvestigationState.COLLECTION:
            runtime.case_manager.transition_state(case_id, InvestigationState.ANALYSIS)


def _map_case_result(case: Case) -> ServiceCaseResult:
    return ServiceCaseResult(
        case_id=case.case_id,
        playbook_id=case.playbook_id or "",
        state=case.status.value,
        finding_count=len(case.analysis_findings),
        hypothesis_count=len(case.hypotheses),
        recommendation_count=len(case.recommendations),
    )


def _map_brain_session(session: BrainSession) -> ServiceBrainSessionResult:
    return ServiceBrainSessionResult(
        session_id=session.session_id,
        case_id=session.case_id,
        playbook_id=session.playbook,
        current_stage=session.current_stage.value,
        current_confidence=session.current_confidence,
        current_quality_score=session.current_quality_score,
        completed=session.completed,
        failed=session.failed,
    )


def _top_hypothesis(case: Case) -> Hypothesis | None:
    active = [
        hypothesis
        for hypothesis in case.hypotheses
        if hypothesis.confidence is not None
    ]
    if not active:
        return None
    return max(active, key=lambda item: (item.confidence or 0.0, -item.rank))
