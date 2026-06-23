"""Evidence upload endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.dependencies import get_voicepilot_service
from api.responses import success_response
from api.schemas.request_models import UploadEvidenceRequest
from api.schemas.response_models import EvidenceResponse
from services import VoicePilotService

router = APIRouter(prefix="/cases", tags=["Evidence"])


@router.post("/{case_id}/evidence")
def upload_evidence(
    case_id: str,
    request: Request,
    body: UploadEvidenceRequest,
    service: VoicePilotService = Depends(get_voicepilot_service),
):
    result = service.upload_evidence(
        case_id,
        body.command,
        body.content,
        evidence_id=body.evidence_id,
    )
    return success_response(
        request,
        EvidenceResponse(
            case_id=result.case_id,
            evidence_id=result.evidence_id,
            command=result.command,
            accepted=result.accepted,
        ),
    )
