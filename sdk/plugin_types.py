"""Plugin type enumerations for the VoicePilot SDK."""

from __future__ import annotations

from enum import Enum


class PluginType(str, Enum):
    """Classification of VoicePilot plugins."""

    VENDOR = "vendor"
    PARSER = "parser"
    KNOWLEDGE = "knowledge"
    AI = "ai"
    INTEGRATION = "integration"
    CUSTOM = "custom"


class PluginCapability(str, Enum):
    """Well-known capability tokens declared in plugin manifests."""

    CUBE_PLAYBOOKS = "cube_playbooks"
    CUCM_PLAYBOOKS = "cucm_playbooks_future"
    SIP_TROUBLESHOOTING = "sip_troubleshooting"
    PARSER_FINDINGS = "parser_findings"
    KNOWLEDGE_ITEMS = "knowledge_items"
    AI_REASONING = "ai_reasoning"
    ITSM_INTEGRATION = "itsm_integration"
