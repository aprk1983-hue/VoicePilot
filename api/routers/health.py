"""Health and version endpoints."""

from __future__ import annotations

import importlib.metadata

from fastapi import APIRouter, Request

from api.responses import success_response
from api.schemas.response_models import HealthResponse, VersionResponse

router = APIRouter(tags=["Health"])


@router.get("/health")
def get_health(request: Request):
    return success_response(request, HealthResponse())


@router.get("/version")
def get_version(request: Request):
    try:
        version = importlib.metadata.version("voicepilot")
    except importlib.metadata.PackageNotFoundError:
        version = "0.1.0"
    return success_response(
        request,
        VersionResponse(name="voicepilot", version=version),
    )
