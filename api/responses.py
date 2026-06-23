"""Shared API response helpers."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import Request
from pydantic import BaseModel

from api.schemas.response_models import ApiEnvelope, ErrorResponse


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def success_response(request: Request, data: BaseModel | dict | list | str | None) -> ApiEnvelope:
    payload = data.model_dump() if isinstance(data, BaseModel) else data
    return ApiEnvelope(
        success=True,
        request_id=request_id(request),
        timestamp=utc_now(),
        data=payload,
    )


def error_response(
    request: Request,
    *,
    error: str,
    message: str,
) -> ErrorResponse:
    return ErrorResponse(
        success=False,
        error=error,
        message=message,
        request_id=request_id(request),
        timestamp=utc_now(),
    )
