"""Enterprise dashboard endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.dependencies import get_voicepilot_service
from api.responses import success_response
from api.schemas.response_models import DashboardSummaryResponse
from services import VoicePilotService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def get_dashboard_summary(
    request: Request,
    service: VoicePilotService = Depends(get_voicepilot_service),
):
    result = service.get_dashboard_summary()
    return success_response(
        request,
        DashboardSummaryResponse(
            api_status=result.api_status,
            platform_name=result.platform_name,
            platform_version=result.platform_version,
            api_version=result.api_version,
            total_cases=result.total_cases,
            cases_by_state=dict(result.cases_by_state),
            cases_by_playbook=dict(result.cases_by_playbook),
            total_findings=result.total_findings,
            total_hypotheses=result.total_hypotheses,
            total_recommendations=result.total_recommendations,
            knowledge_asset_count=result.knowledge_asset_count,
            supported_playbook_count=result.supported_playbook_count,
            supported_playbooks=list(result.supported_playbooks),
            read_only_notice=result.read_only_notice,
        ),
    )
