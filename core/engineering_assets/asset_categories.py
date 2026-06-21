"""Engineering Asset Framework — vendor-neutral category definitions."""

from __future__ import annotations

from enum import Enum


class EngineeringCategory(str, Enum):
    """High-level engineering knowledge categories."""

    NETWORK = "NETWORK"
    VOICE = "VOICE"
    SECURITY = "SECURITY"
    COLLABORATION = "COLLABORATION"
    ROUTING = "ROUTING"
    MEDIA = "MEDIA"
    SIP = "SIP"
    TLS = "TLS"
    CERTIFICATES = "CERTIFICATES"
    LICENSING = "LICENSING"
    PERFORMANCE = "PERFORMANCE"
    MONITORING = "MONITORING"
    CALL_ROUTING = "CALL_ROUTING"
    CODEC = "CODEC"
    GENERAL = "GENERAL"
