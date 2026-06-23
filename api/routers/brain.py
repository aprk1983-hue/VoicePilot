"""Brain orchestration endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.dependencies import get_voicepilot_service
from api.responses import success_response
from api.schemas.request_models import StartBrainRequest
from api.schemas.response_models import BrainSessionResponse, BrainTimelineResponse
from services import VoicePilotService

router = APIRouter(prefix="/brain", tags=["Brain"])


def _brain_session(result) -> BrainSessionResponse:
    return BrainSessionResponse(
        session_id=result.session_id,
        case_id=result.case_id,
        playbook_id=result.playbook_id,
        current_stage=result.current_stage,
        current_confidence=result.current_confidence,
        current_quality_score=result.current_quality_score,
        completed=result.completed,
        failed=result.failed,
    )


@router.post("/start")
def start_brain_session(
    request: Request,
    body: StartBrainRequest,
    service: VoicePilotService = Depends(get_voicepilot_service),
):
    result = service.start_brain_session(body.playbook_id)
    return success_response(request, _brain_session(result))


@router.get("/{session_id}")
def get_brain_session(
    session_id: str,
    request: Request,
    service: VoicePilotService = Depends(get_voicepilot_service),
):
    result = service.get_brain_status(session_id)
    return success_response(request, _brain_session(result))


@router.get("/{session_id}/timeline")
def get_brain_timeline(
    session_id: str,
    request: Request,
    service: VoicePilotService = Depends(get_voicepilot_service),
):
    markdown = service.replay_brain_session(session_id)
    return success_response(
        request,
        BrainTimelineResponse(session_id=session_id, markdown=markdown),
    )
