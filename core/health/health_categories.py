"""Health categories for grouping rule findings."""

from __future__ import annotations

from enum import Enum


class HealthCategory(str, Enum):
    """Vendor-neutral health evaluation category."""

    CONFIGURATION = "configuration"
    SIP = "sip"
    ROUTING = "routing"
    SECURITY = "security"
    TLS = "tls"
    MEDIA = "media"
    PROVIDER = "provider"
    NETWORK = "network"
    DIAL_PLAN = "dial_plan"
    PERFORMANCE = "performance"
    HIGH_AVAILABILITY = "high_availability"
    GENERAL = "general"
