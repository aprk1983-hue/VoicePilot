"""Validation suite endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.dependencies import get_voicepilot_service
from api.responses import success_response
from api.schemas.request_models import ValidateRequest
from api.schemas.response_models import ValidationResponse
from services import VoicePilotService

router = APIRouter(prefix="/validate", tags=["Validation"])


@router.post("")
def validate_playbooks(
    request: Request,
    body: ValidateRequest,
    service: VoicePilotService = Depends(get_voicepilot_service),
):
    result = service.validate_playbook(body.playbook_id)
    return success_response(
        request,
        ValidationResponse(
            playbook_id=result.playbook_id,
            total_scenarios=result.total_scenarios,
            passed_count=result.passed_count,
            failed_count=result.failed_count,
            accuracy_percent=result.accuracy_percent,
            average_confidence=result.average_confidence,
        ),
    )
