"""Engineering change package endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.dependencies import get_voicepilot_service
from api.responses import success_response
from api.schemas.response_models import ChangePackageResponse
from services import VoicePilotService

router = APIRouter(prefix="/cases", tags=["Change Package"])


@router.get("/{case_id}/change-package")
def get_change_package(
    case_id: str,
    request: Request,
    service: VoicePilotService = Depends(get_voicepilot_service),
):
    result = service.generate_change_package(case_id)
    return success_response(
        request,
        ChangePackageResponse(
            case_id=result.case_id,
            package_id=result.package_id,
            risk_level=result.risk_level,
            title=result.title,
            markdown=result.markdown,
        ),
    )
