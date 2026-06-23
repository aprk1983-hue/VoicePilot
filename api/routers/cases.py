"""Investigation case endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.dependencies import get_voicepilot_service
from api.responses import success_response
from api.schemas.request_models import CreateCaseRequest
from api.schemas.response_models import CaseResponse, DeleteCaseResponse
from services import VoicePilotService

router = APIRouter(prefix="/cases", tags=["Cases"])


def _case_response(result) -> CaseResponse:
    return CaseResponse(
        case_id=result.case_id,
        playbook_id=result.playbook_id,
        state=result.state,
        finding_count=result.finding_count,
        hypothesis_count=result.hypothesis_count,
        recommendation_count=result.recommendation_count,
    )


@router.post("")
def create_case(
    request: Request,
    body: CreateCaseRequest,
    service: VoicePilotService = Depends(get_voicepilot_service),
):
    result = service.create_case(body.playbook_id)
    return success_response(request, _case_response(result))


@router.get("")
def list_cases(
    request: Request,
    service: VoicePilotService = Depends(get_voicepilot_service),
):
    results = service.list_cases()
    return success_response(request, [_case_response(item) for item in results])


@router.get("/{case_id}")
def get_case(
    case_id: str,
    request: Request,
    service: VoicePilotService = Depends(get_voicepilot_service),
):
    result = service.get_case(case_id)
    return success_response(request, _case_response(result))


@router.delete("/{case_id}")
def delete_case(
    case_id: str,
    request: Request,
    service: VoicePilotService = Depends(get_voicepilot_service),
):
    service.delete_case(case_id)
    return success_response(request, DeleteCaseResponse(case_id=case_id))
