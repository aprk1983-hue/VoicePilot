"""Investigation pipeline endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.dependencies import get_voicepilot_service
from api.responses import success_response
from api.schemas.response_models import (
    AnalysisResponse,
    ChangePackageResponse,
    DiscoveryResponse,
    InvestigationResponse,
    InvestigationStatusResponse,
    QualityResponse,
    RecommendationResponse,
)
from services import VoicePilotService

router = APIRouter(prefix="/cases", tags=["Investigation"])


def _analysis(result) -> AnalysisResponse:
    return AnalysisResponse(
        case_id=result.case_id,
        finding_count=result.finding_count,
        top_hypothesis=result.top_hypothesis,
        confidence=result.confidence,
    )


def _discovery(result) -> DiscoveryResponse:
    return DiscoveryResponse(
        case_id=result.case_id,
        current_confidence=result.current_confidence,
        estimated_final_confidence=result.estimated_final_confidence,
        next_best_command=result.next_best_command,
        request_count=result.request_count,
    )


def _quality(result) -> QualityResponse:
    return QualityResponse(
        case_id=result.case_id,
        overall_score=result.overall_score,
        overall_status=result.overall_status,
        ready_for_recommendation=result.ready_for_recommendation,
        ready_for_case_closure=result.ready_for_case_closure,
    )


def _recommendation(result) -> RecommendationResponse:
    return RecommendationResponse(
        case_id=result.case_id,
        recommendation_count=result.recommendation_count,
        top_recommendation=result.top_recommendation,
    )


def _change_package(result) -> ChangePackageResponse:
    return ChangePackageResponse(
        case_id=result.case_id,
        package_id=result.package_id,
        risk_level=result.risk_level,
        title=result.title,
        markdown=result.markdown,
    )


@router.post("/{case_id}/investigate")
def investigate_case(
    case_id: str,
    request: Request,
    service: VoicePilotService = Depends(get_voicepilot_service),
):
    result = service.investigate_case(case_id)
    return success_response(
        request,
        InvestigationResponse(
            case_id=result.case_id,
            analysis=_analysis(result.analysis),
            discovery=_discovery(result.discovery),
            quality=_quality(result.quality),
            recommendation=_recommendation(result.recommendation),
            change_package=_change_package(result.change_package),
        ),
    )


@router.get("/{case_id}/status")
def get_investigation_status(
    case_id: str,
    request: Request,
    service: VoicePilotService = Depends(get_voicepilot_service),
):
    result = service.get_investigation_status(case_id)
    return success_response(
        request,
        InvestigationStatusResponse(
            case_id=result.case_id,
            playbook_id=result.playbook_id,
            state=result.state,
            finding_count=result.finding_count,
            hypothesis_count=result.hypothesis_count,
            recommendation_count=result.recommendation_count,
            top_hypothesis=result.top_hypothesis,
            confidence=result.confidence,
        ),
    )
