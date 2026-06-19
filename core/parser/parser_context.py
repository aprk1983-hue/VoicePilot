"""Execution context passed into every parser invocation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from shared.types import CaseId, DeviceId, JsonDict


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class ParserContext:
    """Immutable context for a single parse operation.

    Supplied by the runtime or evidence collection layer. Parsers use this
    for provenance, timezone normalization, and vendor/platform disambiguation.
    """

    vendor: str
    case_id: CaseId
    device_id: DeviceId | None = None
    platform: str | None = None
    ios_version: str | None = None
    hostname: str | None = None
    timezone: str = "UTC"
    collection_timestamp: datetime = field(default_factory=_utc_now)
    metadata: JsonDict = field(default_factory=dict)
