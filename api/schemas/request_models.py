"""Pydantic request models for the VoicePilot REST API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateCaseRequest(BaseModel):
    """Request body for creating a new investigation case."""

    playbook_id: str = Field(..., min_length=1, description="Catalog playbook identifier")


class UploadEvidenceRequest(BaseModel):
    """Request body for uploading evidence to a case."""

    command: str = Field(..., min_length=1, description="Evidence collection command")
    content: str = Field(..., min_length=1, description="Raw evidence output")
    evidence_id: str | None = Field(default=None, description="Optional client evidence identifier")


class StartBrainRequest(BaseModel):
    """Request body for starting a Brain orchestration session."""

    playbook_id: str = Field(..., min_length=1, description="Catalog playbook identifier")


class ValidateRequest(BaseModel):
    """Request body for running the validation suite."""

    playbook_id: str | None = Field(
        default=None,
        description="Playbook to validate; omit to validate all supported playbooks",
    )
