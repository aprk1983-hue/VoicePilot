"""VoicePilot Enterprise FastAPI application."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.middleware import RequestContextMiddleware
from api.responses import error_response
from api.routers import (
    brain,
    cases,
    change_package,
    dashboard,
    evidence,
    health,
    investigation,
    reports,
    validation,
)
from services.service_exceptions import (
    ServiceBrainSessionNotFoundError,
    ServiceCaseNotFoundError,
    ServicePlaybookNotFoundError,
    VoicePilotServiceError,
)

logging.basicConfig(level=logging.INFO)


def create_app() -> FastAPI:
    """Build and configure the VoicePilot REST API application."""
    app = FastAPI(
        title="VoicePilot Enterprise API",
        description=(
            "Read-only orchestration layer over VoicePilot investigation engines. "
            "All business logic is delegated to VoicePilotService."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(dashboard.router)
    app.include_router(cases.router)
    app.include_router(evidence.router)
    app.include_router(investigation.router)
    app.include_router(brain.router)
    app.include_router(reports.router)
    app.include_router(change_package.router)
    app.include_router(validation.router)

    @app.exception_handler(ServiceCaseNotFoundError)
    async def case_not_found_handler(request: Request, exc: ServiceCaseNotFoundError):
        payload = error_response(
            request,
            error="case_not_found",
            message=str(exc),
        )
        return JSONResponse(status_code=404, content=payload.model_dump(mode="json"))

    @app.exception_handler(ServiceBrainSessionNotFoundError)
    async def brain_not_found_handler(
        request: Request,
        exc: ServiceBrainSessionNotFoundError,
    ):
        payload = error_response(
            request,
            error="brain_session_not_found",
            message=str(exc),
        )
        return JSONResponse(status_code=404, content=payload.model_dump(mode="json"))

    @app.exception_handler(ServicePlaybookNotFoundError)
    async def playbook_not_found_handler(
        request: Request,
        exc: ServicePlaybookNotFoundError,
    ):
        payload = error_response(
            request,
            error="playbook_not_found",
            message=str(exc),
        )
        return JSONResponse(status_code=404, content=payload.model_dump(mode="json"))

    @app.exception_handler(VoicePilotServiceError)
    async def service_error_handler(request: Request, exc: VoicePilotServiceError):
        payload = error_response(
            request,
            error="service_error",
            message=str(exc),
        )
        return JSONResponse(status_code=400, content=payload.model_dump(mode="json"))

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        payload = error_response(
            request,
            error="validation_error",
            message="Request validation failed",
        )
        body = payload.model_dump(mode="json")
        body["details"] = exc.errors()
        return JSONResponse(status_code=422, content=body)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        payload = error_response(
            request,
            error="http_error",
            message=str(exc.detail),
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))

    return app


app = create_app()
