"""Enterprise reporting endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from api.dependencies import get_voicepilot_service
from api.responses import success_response
from api.schemas.response_models import MarkdownReportResponse, ReportResponse
from reporting import ReportType
from services import VoicePilotService

router = APIRouter(prefix="/cases", tags=["Reports"])


def _report(result, report_type: str) -> ReportResponse:
    return ReportResponse(
        case_id=result.case_id,
        report_id=result.report_id,
        report_type=report_type,
        markdown=result.markdown,
    )


@router.get("/{case_id}/report")
def get_legacy_report(
    case_id: str,
    request: Request,
    service: VoicePilotService = Depends(get_voicepilot_service),
):
    result = service.generate_legacy_report(case_id)
    return success_response(
        request,
        MarkdownReportResponse(
            case_id=result.case_id,
            report_type="LEGACY",
            markdown=result.markdown,
        ),
    )


@router.get("/{case_id}/executive")
def get_executive_report(
    case_id: str,
    request: Request,
    service: VoicePilotService = Depends(get_voicepilot_service),
):
    result = service.generate_report(case_id, ReportType.EXECUTIVE)
    return success_response(request, _report(result, ReportType.EXECUTIVE.value))


@router.get("/{case_id}/engineering")
def get_engineering_report(
    case_id: str,
    request: Request,
    service: VoicePilotService = Depends(get_voicepilot_service),
):
    result = service.generate_report(case_id, ReportType.ENGINEERING)
    return success_response(request, _report(result, ReportType.ENGINEERING.value))


@router.get("/{case_id}/cab")
def get_cab_report(
    case_id: str,
    request: Request,
    service: VoicePilotService = Depends(get_voicepilot_service),
):
    result = service.generate_report(case_id, ReportType.CAB)
    return success_response(request, _report(result, ReportType.CAB.value))
