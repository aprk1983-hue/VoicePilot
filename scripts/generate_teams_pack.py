#!/usr/bin/env python3
"""One-time generator for Microsoft Teams Professional Knowledge Pack v1."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "knowledge"
CREATED = "2026-06-19T12:00:00+00:00"

CATEGORY_MAP = {
    "LICENSING": "LICENSING",
    "OPERATOR CONNECT": "CALL_ROUTING",
    "DIRECT ROUTING": "SIP",
    "CALLING PLANS": "LICENSING",
    "VOICE ROUTING POLICY": "CALL_ROUTING",
    "DIAL PLAN": "ROUTING",
    "NORMALIZATION RULES": "ROUTING",
    "EMERGENCY CALLING": "VOICE",
    "RESOURCE ACCOUNTS": "COLLABORATION",
    "AUTO ATTENDANTS": "COLLABORATION",
    "CALL QUEUES": "COLLABORATION",
    "TEAMS ROOMS": "COLLABORATION",
    "MEDIA BYPASS": "MEDIA",
    "TLS CERTIFICATE": "TLS",
    "SBC CONNECTIVITY": "SIP",
    "SIP OPTIONS": "SIP",
    "NUMBER ASSIGNMENT": "VOICE",
    "CALLER ID": "VOICE",
    "LOCATION POLICY": "ROUTING",
    "VOICE ROUTING FAILURE": "CALL_ROUTING",
}

INCIDENTS = (
    {
        "id": "000001",
        "slug": "teams_phone_license_missing",
        "title": "Teams Phone license missing",
        "category": "LICENSING",
        "severity": "high",
        "finding": "teams_phone_license_missing",
        "symptoms": [
            "User cannot make or receive PSTN calls in Teams",
            "Teams client shows calling unavailable",
            "Admin center shows no Teams Phone license assigned",
        ],
        "causes": [
            "Teams Phone license not assigned to user",
            "License SKU removed during subscription change",
        ],
        "resolution": [
            "Assign Teams Phone or appropriate calling license in Microsoft 365 admin center",
            "Allow license propagation and sign user out of Teams",
        ],
        "rollback": ["Remove license assignment if incorrectly applied to wrong user"],
        "health_rules": ["teams_phone_license_missing"],
        "related": ["RB-006", "VG-001", "REF-004"],
    },
    {
        "id": "000002",
        "slug": "enterprise_voice_disabled",
        "title": "Enterprise Voice disabled",
        "category": "LICENSING",
        "severity": "high",
        "finding": "enterprise_voice_disabled",
        "symptoms": [
            "User has license but no dial pad in Teams",
            "PowerShell shows EnterpriseVoiceEnabled is False",
        ],
        "causes": [
            "Enterprise Voice not enabled on CsOnlineUser",
            "Phone number not assigned after license assignment",
        ],
        "resolution": [
            "Enable Enterprise Voice and assign telephone number",
            "Verify voice routing policy assignment",
        ],
        "rollback": ["Revert CsOnlineUser voice settings to previous export"],
        "health_rules": ["enterprise_voice_disabled"],
        "related": ["RB-001", "VG-001", "REF-004"],
    },
    {
        "id": "000003",
        "slug": "voice_routing_policy_missing",
        "title": "Voice Routing Policy missing",
        "category": "VOICE ROUTING POLICY",
        "severity": "high",
        "finding": "voice_routing_policy_missing",
        "symptoms": [
            "Outbound PSTN calls fail for affected users",
            "No voice routing policy assigned in Teams admin",
        ],
        "causes": [
            "User not assigned a Teams voice routing policy",
            "Policy deleted or renamed without reassignment",
        ],
        "resolution": [
            "Assign correct voice routing policy to user or group",
            "Validate policy contains reachable PSTN route",
        ],
        "rollback": ["Restore previous voice routing policy assignment"],
        "health_rules": ["voice_routing_policy_missing"],
        "related": ["RB-002", "VG-002", "REF-001"],
    },
    {
        "id": "000004",
        "slug": "dial_plan_mismatch",
        "title": "Dial Plan mismatch",
        "category": "DIAL PLAN",
        "severity": "high",
        "finding": "dial_plan_mismatch",
        "symptoms": [
            "Users cannot dial expected external numbers",
            "Normalization produces unexpected dial strings",
        ],
        "causes": [
            "Tenant dial plan does not match user location",
            "Incorrect normalization rules applied",
        ],
        "resolution": [
            "Assign correct tenant or user dial plan",
            "Validate normalization rules for target numbering plan",
        ],
        "rollback": ["Restore previous dial plan assignment"],
        "health_rules": ["dial_plan_mismatch"],
        "related": ["RB-008", "VG-008", "REF-001"],
    },
    {
        "id": "000005",
        "slug": "normalization_rule_failure",
        "title": "Normalization Rule failure",
        "category": "NORMALIZATION RULES",
        "severity": "medium",
        "finding": "normalization_rule_failure",
        "symptoms": [
            "External calls fail with invalid number format",
            "Teams sends malformed E.164 dial strings",
        ],
        "causes": [
            "Normalization rule missing or incorrect regex",
            "Dial plan rule order causes wrong match",
        ],
        "resolution": [
            "Correct normalization rule pattern and priority",
            "Test dial strings against expected E.164 output",
        ],
        "rollback": ["Restore exported dial plan configuration"],
        "health_rules": ["normalization_rule_failure"],
        "related": ["RB-008", "VG-008", "REF-001"],
    },
    {
        "id": "000006",
        "slug": "operator_connect_provisioning_incomplete",
        "title": "Operator Connect provisioning incomplete",
        "category": "OPERATOR CONNECT",
        "severity": "high",
        "finding": "operator_connect_provisioning_incomplete",
        "symptoms": [
            "Operator Connect numbers show provisioning failed",
            "Carrier assignment incomplete in Teams admin",
        ],
        "causes": [
            "Carrier onboarding not completed",
            "Number order pending carrier acceptance",
        ],
        "resolution": [
            "Complete Operator Connect carrier onboarding steps",
            "Reconcile number order with carrier portal",
        ],
        "rollback": ["Release pending number assignment if incorrect order"],
        "health_rules": ["operator_connect_provisioning_incomplete"],
        "related": ["RB-004", "VG-007", "REF-003"],
    },
    {
        "id": "000007",
        "slug": "direct_routing_sbc_unreachable",
        "title": "Direct Routing SBC unreachable",
        "category": "DIRECT ROUTING",
        "severity": "critical",
        "finding": "direct_routing_sbc_unreachable",
        "symptoms": [
            "All Direct Routing calls fail",
            "SBC health shows offline in Teams admin",
            "SIP trunk status down on session border controller",
        ],
        "causes": [
            "Network path to SBC blocked",
            "SBC service stopped or certificate failure",
        ],
        "resolution": [
            "Restore network connectivity to certified SBC",
            "Validate SBC trunk registration to Teams",
        ],
        "rollback": ["Fail over to secondary SBC if configured"],
        "health_rules": ["direct_routing_sbc_unreachable", "sbc_unreachable"],
        "related": ["RB-003", "VG-006", "REF-002"],
    },
    {
        "id": "000008",
        "slug": "tls_certificate_expired",
        "title": "TLS certificate expired",
        "category": "TLS CERTIFICATE",
        "severity": "critical",
        "finding": "tls_certificate_expired",
        "symptoms": [
            "Direct Routing TLS handshake failures",
            "SBC logs show certificate validation errors",
        ],
        "causes": [
            "SBC or reverse proxy certificate expired",
            "Incomplete certificate chain presented to Teams",
        ],
        "resolution": [
            "Renew TLS certificate on SBC or proxy",
            "Validate full certificate chain and SAN entries",
        ],
        "rollback": ["Restore previous valid certificate if renewal fails"],
        "health_rules": ["tls_certificate_expired"],
        "related": ["RB-005", "VG-004", "REF-002"],
    },
    {
        "id": "000009",
        "slug": "sip_options_failure",
        "title": "SIP OPTIONS failure",
        "category": "SIP OPTIONS",
        "severity": "high",
        "finding": "sip_options_failure",
        "symptoms": [
            "Teams marks SBC as unavailable",
            "Periodic OPTIONS requests fail on SBC",
        ],
        "causes": [
            "SBC not responding to SIP OPTIONS",
            "Firewall drops OPTIONS or asymmetric routing",
        ],
        "resolution": [
            "Enable SIP OPTIONS response on SBC",
            "Verify firewall permits OPTIONS in both directions",
        ],
        "rollback": ["Restore previous SBC SIP profile settings"],
        "health_rules": ["sip_options_failure"],
        "related": ["RB-005", "VG-003", "REF-002"],
    },
    {
        "id": "000010",
        "slug": "media_bypass_disabled",
        "title": "Media bypass disabled",
        "category": "MEDIA BYPASS",
        "severity": "medium",
        "finding": "media_bypass_disabled",
        "symptoms": [
            "Increased media latency on Direct Routing calls",
            "Media path hairpins through Teams cloud unexpectedly",
        ],
        "causes": [
            "Media bypass disabled on SBC trunk",
            "Client subnet not configured for bypass",
        ],
        "resolution": [
            "Enable media bypass where supported by SBC and client location",
            "Configure trusted IP subnets for bypass",
        ],
        "rollback": ["Disable media bypass if call quality degrades"],
        "health_rules": ["media_bypass_disabled"],
        "related": ["RB-005", "VG-003", "REF-002"],
    },
    {
        "id": "000011",
        "slug": "auto_attendant_transfer_failure",
        "title": "Auto Attendant transfer failure",
        "category": "AUTO ATTENDANTS",
        "severity": "medium",
        "finding": "auto_attendant_transfer_failure",
        "symptoms": [
            "Auto attendant cannot transfer to operator or queue",
            "Caller hears transfer failed message",
        ],
        "causes": [
            "Target resource account or queue misconfigured",
            "Operator license or routing policy missing on target",
        ],
        "resolution": [
            "Validate auto attendant call flow targets",
            "Confirm resource account licensing and routing",
        ],
        "rollback": ["Restore previous auto attendant call flow export"],
        "health_rules": ["auto_attendant_transfer_failure"],
        "related": ["RB-010", "VG-010", "REF-001"],
    },
    {
        "id": "000012",
        "slug": "call_queue_timeout",
        "title": "Call Queue timeout",
        "category": "CALL QUEUES",
        "severity": "medium",
        "finding": "call_queue_timeout",
        "symptoms": [
            "Callers wait until queue timeout without agent answer",
            "Overflow action not triggered as expected",
        ],
        "causes": [
            "No agents signed in to call queue",
            "Overflow or timeout settings misconfigured",
        ],
        "resolution": [
            "Verify agents opted in and licensed for queue",
            "Adjust timeout and overflow configuration",
        ],
        "rollback": ["Restore previous call queue configuration"],
        "health_rules": ["call_queue_timeout"],
        "related": ["RB-010", "VG-010", "REF-001"],
    },
    {
        "id": "000013",
        "slug": "resource_account_missing_license",
        "title": "Resource Account missing license",
        "category": "RESOURCE ACCOUNTS",
        "severity": "high",
        "finding": "resource_account_missing_license",
        "symptoms": [
            "Auto attendant or call queue cannot receive calls",
            "Resource account shows no phone system license",
        ],
        "causes": [
            "Phone System license not assigned to resource account",
            "Resource account not associated with application",
        ],
        "resolution": [
            "Assign Phone System or appropriate resource license",
            "Associate resource account with auto attendant or queue",
        ],
        "rollback": ["Remove license if assigned to wrong resource account"],
        "health_rules": ["resource_account_missing_license"],
        "related": ["RB-009", "VG-009", "REF-001"],
    },
    {
        "id": "000014",
        "slug": "emergency_calling_policy_missing",
        "title": "Emergency Calling policy missing",
        "category": "EMERGENCY CALLING",
        "severity": "critical",
        "finding": "emergency_calling_policy_missing",
        "symptoms": [
            "Emergency calls fail or route incorrectly",
            "Users not assigned emergency calling policy",
        ],
        "causes": [
            "Emergency calling policy not assigned",
            "Emergency location not configured for site",
        ],
        "resolution": [
            "Assign emergency calling and location policies",
            "Validate emergency address and routing configuration",
        ],
        "rollback": ["Restore previous emergency policy assignment"],
        "health_rules": ["emergency_calling_policy_missing"],
        "related": ["RB-007", "VG-005", "REF-005"],
    },
    {
        "id": "000015",
        "slug": "phone_number_assignment_failed",
        "title": "Phone number assignment failed",
        "category": "NUMBER ASSIGNMENT",
        "severity": "high",
        "finding": "phone_number_assignment_failed",
        "symptoms": [
            "Telephone number assignment fails in Teams admin",
            "User shows no assigned number after provisioning",
        ],
        "causes": [
            "Number not available in tenant inventory",
            "Conflicting assignment on another user or resource",
        ],
        "resolution": [
            "Verify number inventory and release conflicting assignment",
            "Reassign number through Teams admin or PowerShell export workflow",
        ],
        "rollback": ["Unassign number and restore previous assignment record"],
        "health_rules": ["phone_number_assignment_failed"],
        "related": ["RB-006", "VG-001", "REF-004"],
    },
    {
        "id": "000016",
        "slug": "calling_plans_license_mismatch",
        "title": "Calling Plans license mismatch",
        "category": "CALLING PLANS",
        "severity": "high",
        "finding": "calling_plans_license_mismatch",
        "symptoms": [
            "Calling Plans user cannot dial out",
            "License SKU does not include domestic calling plan",
        ],
        "causes": [
            "Wrong Calling Plans SKU assigned",
            "Domestic or international plan not provisioned",
        ],
        "resolution": [
            "Assign correct Microsoft Calling Plans license",
            "Validate calling plan coverage for user country",
        ],
        "rollback": ["Restore previous Calling Plans license assignment"],
        "health_rules": ["calling_plans_license_mismatch"],
        "related": ["RB-006", "VG-001", "REF-004"],
    },
    {
        "id": "000017",
        "slug": "teams_rooms_device_offline",
        "title": "Teams Rooms device offline",
        "category": "TEAMS ROOMS",
        "severity": "medium",
        "finding": "teams_rooms_device_offline",
        "symptoms": [
            "Teams Rooms console shows offline in admin center",
            "Room cannot join scheduled meetings",
        ],
        "causes": [
            "Network connectivity loss on room device",
            "Teams Rooms app or device firmware issue",
        ],
        "resolution": [
            "Restore network connectivity and restart Teams Rooms app",
            "Verify device health in Teams admin center",
        ],
        "rollback": ["Restore previous device configuration backup"],
        "health_rules": ["teams_rooms_device_offline"],
        "related": ["RB-001", "VG-010", "REF-001"],
    },
    {
        "id": "000018",
        "slug": "sbc_connectivity_lost",
        "title": "SBC connectivity lost",
        "category": "SBC CONNECTIVITY",
        "severity": "critical",
        "finding": "sbc_connectivity_lost",
        "symptoms": [
            "Direct Routing gateway shows disconnected",
            "No active SIP sessions through SBC",
        ],
        "causes": [
            "SBC to Teams signaling path failure",
            "Certificate or FQDN mismatch on SBC trunk",
        ],
        "resolution": [
            "Restore SBC signaling path and trunk configuration",
            "Validate SBC FQDN matches Teams Direct Routing settings",
        ],
        "rollback": ["Fail over to alternate SBC pair if available"],
        "health_rules": ["sbc_connectivity_lost", "sbc_unreachable"],
        "related": ["RB-005", "VG-003", "REF-002"],
    },
    {
        "id": "000019",
        "slug": "caller_id_policy_misconfigured",
        "title": "Caller ID policy misconfigured",
        "category": "CALLER ID",
        "severity": "medium",
        "finding": "caller_id_policy_misconfigured",
        "symptoms": [
            "Outbound calls show incorrect caller ID",
            "Called party sees blocked or wrong number",
        ],
        "causes": [
            "Calling policy or caller ID policy misassigned",
            "Resource or user override conflicts with tenant policy",
        ],
        "resolution": [
            "Assign correct caller ID policy to user or resource",
            "Validate displayed number is authorized for tenant",
        ],
        "rollback": ["Restore previous caller ID policy assignment"],
        "health_rules": ["caller_id_policy_misconfigured"],
        "related": ["RB-002", "VG-009", "REF-001"],
    },
    {
        "id": "000020",
        "slug": "location_based_routing_blocked",
        "title": "Location Based Routing blocked",
        "category": "LOCATION POLICY",
        "severity": "high",
        "finding": "location_based_routing_blocked",
        "symptoms": [
            "PSTN calls blocked for users at specific sites",
            "Location policy shows routing restricted",
        ],
        "causes": [
            "Location Based Routing policy blocks PSTN at site",
            "Network site not associated with correct policy",
        ],
        "resolution": [
            "Validate network site and LBR policy assignment",
            "Confirm user network site detection is correct",
        ],
        "rollback": ["Restore previous location policy configuration"],
        "health_rules": ["location_based_routing_blocked"],
        "related": ["RB-002", "VG-002", "REF-001"],
    },
    {
        "id": "000021",
        "slug": "voice_routing_failure_pstn",
        "title": "Voice routing failure to PSTN",
        "category": "VOICE ROUTING FAILURE",
        "severity": "critical",
        "finding": "voice_routing_failure_pstn",
        "symptoms": [
            "All outbound PSTN calls fail for tenant segment",
            "Voice route selection returns no available path",
        ],
        "causes": [
            "PSTN usage or voice route misconfigured",
            "All SBC gateways in route marked unavailable",
        ],
        "resolution": [
            "Validate voice routes, PSTN usages, and SBC availability",
            "Restore at least one healthy PSTN path",
        ],
        "rollback": ["Restore exported voice routing configuration"],
        "health_rules": ["voice_routing_failure_pstn"],
        "related": ["RB-002", "VG-002", "REF-001"],
    },
    {
        "id": "000022",
        "slug": "direct_routing_trunk_not_registered",
        "title": "Direct Routing trunk not registered",
        "category": "DIRECT ROUTING",
        "severity": "high",
        "finding": "direct_routing_trunk_not_registered",
        "symptoms": [
            "SBC trunk shows not registered in Teams admin",
            "Direct Routing calls fail with gateway unavailable",
        ],
        "causes": [
            "SBC trunk credentials or FQDN incorrect",
            "TLS or SIP port blocked between SBC and Teams",
        ],
        "resolution": [
            "Correct SBC trunk parameters for Teams Direct Routing",
            "Validate TLS handshake and SIP registration",
        ],
        "rollback": ["Restore previous SBC trunk configuration"],
        "health_rules": ["direct_routing_trunk_not_registered"],
        "related": ["RB-003", "VG-006", "REF-002"],
    },
    {
        "id": "000023",
        "slug": "operator_connect_routing_failure",
        "title": "Operator Connect carrier routing failure",
        "category": "OPERATOR CONNECT",
        "severity": "high",
        "finding": "operator_connect_routing_failure",
        "symptoms": [
            "Operator Connect outbound calls fail",
            "Carrier route shows error in Teams admin",
        ],
        "causes": [
            "Carrier trunk or route unavailable",
            "Operator Connect number not linked to carrier route",
        ],
        "resolution": [
            "Validate Operator Connect carrier route health",
            "Engage carrier to restore trunk availability",
        ],
        "rollback": ["Route traffic through alternate carrier if configured"],
        "health_rules": ["operator_connect_routing_failure"],
        "related": ["RB-004", "VG-007", "REF-003"],
    },
    {
        "id": "000024",
        "slug": "calling_plans_outbound_blocked",
        "title": "Calling Plans outbound blocked",
        "category": "CALLING PLANS",
        "severity": "high",
        "finding": "calling_plans_outbound_blocked",
        "symptoms": [
            "Calling Plans users cannot dial specific destinations",
            "Outbound call rejected immediately",
        ],
        "causes": [
            "Calling plan restrictions or spend cap applied",
            "User not enabled for international calling",
        ],
        "resolution": [
            "Review Calling Plans restrictions and user enablement",
            "Adjust policy to allow required destination class",
        ],
        "rollback": ["Restore previous calling policy restrictions"],
        "health_rules": ["calling_plans_outbound_blocked"],
        "related": ["RB-006", "VG-001", "REF-004"],
    },
    {
        "id": "000025",
        "slug": "sip_options_keepalive_failure",
        "title": "SIP OPTIONS keepalive failure",
        "category": "SIP OPTIONS",
        "severity": "high",
        "finding": "sip_options_keepalive_failure",
        "symptoms": [
            "Intermittent Direct Routing failures",
            "SBC marked unhealthy during OPTIONS timeout",
        ],
        "causes": [
            "SBC OPTIONS timer misaligned with Teams expectations",
            "Network latency causes OPTIONS timeout",
        ],
        "resolution": [
            "Tune SBC OPTIONS response and timer settings",
            "Verify network latency within supported bounds",
        ],
        "rollback": ["Restore previous SBC keepalive configuration"],
        "health_rules": ["sip_options_keepalive_failure", "sip_options_failure"],
        "related": ["RB-005", "VG-003", "REF-002"],
    },
)

RUNBOOKS = (
    ("RB-001", "validate_enterprise_voice", "Validate Enterprise Voice", "RB-TEAMS-ENTERPRISE-VOICE"),
    ("RB-002", "validate_voice_routing", "Validate Voice Routing", "RB-TEAMS-VOICE-ROUTING"),
    ("RB-003", "validate_direct_routing", "Validate Direct Routing", "RB-TEAMS-DIRECT-ROUTING"),
    ("RB-004", "validate_operator_connect", "Validate Operator Connect", "RB-TEAMS-OPERATOR-CONNECT"),
    ("RB-005", "validate_sbc_connectivity", "Validate SBC Connectivity", "RB-TEAMS-SBC"),
    ("RB-006", "validate_licensing", "Validate Licensing", "RB-TEAMS-LICENSING"),
    ("RB-007", "validate_emergency_calling", "Validate Emergency Calling", "RB-TEAMS-EMERGENCY"),
    ("RB-008", "validate_dial_plan", "Validate Dial Plan", "RB-TEAMS-DIAL-PLAN"),
    ("RB-009", "validate_resource_accounts", "Validate Resource Accounts", "RB-TEAMS-RESOURCE-ACCOUNTS"),
    ("RB-010", "validate_auto_attendants", "Validate Auto Attendants", "RB-TEAMS-AUTO-ATTENDANTS"),
)

VERIFICATIONS = (
    ("VG-001", "verify_license", "Verify Teams Phone license", "VG-TEAMS-LICENSE"),
    ("VG-002", "verify_voice_routing", "Verify voice routing", "VG-TEAMS-VOICE-ROUTING"),
    ("VG-003", "verify_sbc", "Verify SBC connectivity", "VG-TEAMS-SBC"),
    ("VG-004", "verify_tls", "Verify TLS certificate", "VG-TEAMS-TLS"),
    ("VG-005", "verify_emergency_calling", "Verify emergency calling", "VG-TEAMS-EMERGENCY"),
    ("VG-006", "verify_direct_routing", "Verify Direct Routing", "VG-TEAMS-DIRECT-ROUTING"),
    ("VG-007", "verify_operator_connect", "Verify Operator Connect", "VG-TEAMS-OPERATOR-CONNECT"),
    ("VG-008", "verify_normalization", "Verify normalization rules", "VG-TEAMS-NORMALIZATION"),
    ("VG-009", "verify_caller_id", "Verify caller ID", "VG-TEAMS-CALLER-ID"),
    ("VG-010", "verify_teams_client", "Verify Teams client", "VG-TEAMS-CLIENT"),
)

REFERENCES = (
    ("REF-001", "teams_voice_architecture", "Microsoft Teams Voice Architecture"),
    ("REF-002", "direct_routing_reference", "Direct Routing Reference"),
    ("REF-003", "operator_connect_guide", "Operator Connect Guide"),
    ("REF-004", "teams_phone_licensing", "Teams Phone Licensing"),
    ("REF-005", "emergency_calling_reference", "Emergency Calling Reference"),
)


def asset_id(suffix: str) -> str:
    return f"VP-MS-TEAMS-{suffix}"


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def incident_doc(item: dict) -> dict:
    incident_id = asset_id(item["id"])
    related = [asset_id(related_id) for related_id in item["related"]]
    prefix = "Teams Phone "
    raw_title = item["title"]
    title = raw_title if raw_title.startswith(prefix) else f"{prefix}{raw_title}"
    return {
        "asset_id": incident_id,
        "title": title,
        "asset_type": "INCIDENT",
        "vendor": "Microsoft",
        "product": "Teams Phone",
        "category": CATEGORY_MAP[item["category"]],
        "severity": item["severity"],
        "summary": f"{title} affecting Microsoft Teams Phone operations.",
        "description": f"{title} affecting Microsoft Teams Phone operations.",
        "symptoms": item["symptoms"],
        "required_evidence": [
            "Teams admin center export",
            "Tenant voice configuration snapshot",
            "Affected user or resource account details",
        ],
        "expected_findings": [item["finding"], f"{item['slug']}_detected"],
        "expected_hypotheses": item["causes"],
        "known_causes": item["causes"],
        "known_resolution": item["resolution"],
        "recommended_actions": item["resolution"],
        "rollback_steps": item["rollback"],
        "verification_steps": [
            "Confirm expected findings in collected evidence",
            "Execute linked verification guide after remediation",
        ],
        "related_health_rules": item["health_rules"],
        "related_asset_ids": related,
        "tags": [
            "teams-phone",
            "professional-pack",
            "microsoft",
            item["category"].lower().replace(" ", "-"),
        ],
        "references": [
            "Microsoft Teams Professional Pack v1",
            "Microsoft Teams Phone product documentation",
        ],
        "confidence": 0.95,
        "status": "ACTIVE",
        "version": "1.0",
        "created_at": CREATED,
    }


def runbook_doc(suffix: str, slug: str, title: str, code: str, incidents: list[str], vgs: list[str]) -> dict:
    return {
        "asset_id": asset_id(suffix),
        "title": title,
        "asset_type": "RUNBOOK",
        "vendor": "Microsoft",
        "product": "Teams Phone",
        "category": "COLLABORATION",
        "severity": "high",
        "summary": f"{title} for Microsoft Teams Phone.",
        "description": f"{title} for Microsoft Teams Phone. Professional pack runbook {code}.",
        "symptoms": ["Service degradation requiring runbook remediation"],
        "expected_findings": ["runbook_remediation_required"],
        "expected_hypotheses": ["Known Teams Phone failure pattern matched"],
        "known_causes": ["Configuration or routing fault in Teams Phone tenant"],
        "known_resolution": ["Execute runbook steps and validate with verification guide"],
        "recommended_actions": [
            f"Follow {code} remediation steps in order",
            "Document changes in change record",
            "Validate outcome with linked verification guide",
        ],
        "rollback_steps": [
            "Restore exported Teams voice configuration",
            "Revert policy assignment to previous baseline",
        ],
        "verification_steps": ["Execute linked verification guide after remediation"],
        "related_asset_ids": [asset_id(item) for item in vgs + incidents],
        "tags": ["teams-phone", "runbook", "professional-pack", "microsoft"],
        "references": ["Microsoft Teams Professional Pack v1", code],
        "confidence": 0.93,
        "status": "ACTIVE",
        "version": "1.0",
        "created_at": CREATED,
    }


def verification_doc(suffix: str, slug: str, title: str, code: str, rb: str, incidents: list[str]) -> dict:
    return {
        "asset_id": asset_id(suffix),
        "title": title,
        "asset_type": "VERIFICATION_GUIDE",
        "vendor": "Microsoft",
        "product": "Teams Phone",
        "category": "COLLABORATION",
        "severity": "medium",
        "summary": f"{title} for Microsoft Teams Phone.",
        "description": f"{title} for Microsoft Teams Phone. Professional pack guide {code}.",
        "symptoms": ["Post-remediation validation required"],
        "expected_findings": ["verification_passed"],
        "expected_hypotheses": ["Service restored to operational baseline"],
        "known_causes": ["Remediation not yet validated"],
        "known_resolution": ["Complete verification steps and attach evidence"],
        "required_evidence": [
            "Teams admin center validation export",
            "Test call results",
            "Configuration snapshot after remediation",
        ],
        "verification_steps": [
            f"Execute {code} validation checklist",
            "Compare results against expected operational baseline",
            "Attach evidence to investigation record",
        ],
        "recommended_actions": ["Compare results against expected operational baseline"],
        "related_asset_ids": [asset_id(rb), *[asset_id(item) for item in incidents]],
        "tags": ["teams-phone", "verification", "professional-pack", "microsoft"],
        "references": ["Microsoft Teams Professional Pack v1", code],
        "confidence": 0.92,
        "status": "ACTIVE",
        "version": "1.0",
        "created_at": CREATED,
    }


def reference_doc(suffix: str, slug: str, title: str, incidents: list[str]) -> dict:
    return {
        "asset_id": asset_id(suffix),
        "title": title,
        "asset_type": "REFERENCE",
        "vendor": "Microsoft",
        "product": "Teams Phone",
        "category": "COLLABORATION",
        "severity": "low",
        "summary": f"{title} reference for Microsoft Teams Phone engineering investigations.",
        "description": f"{title} for Microsoft Teams Phone deployments and troubleshooting.",
        "symptoms": ["Engineering reference consultation required"],
        "expected_findings": ["reference_applicable"],
        "expected_hypotheses": ["Authoritative Microsoft guidance applies"],
        "known_causes": ["Misconfiguration relative to Microsoft Teams best practice"],
        "known_resolution": ["Align design and remediation with Microsoft Teams guidance"],
        "recommended_actions": ["Consult this reference during investigation and remediation"],
        "verification_steps": ["Confirm document version matches deployed Teams Phone configuration"],
        "related_asset_ids": [asset_id(item) for item in incidents],
        "tags": ["teams-phone", "reference", "professional-pack", "microsoft"],
        "references": [
            "https://learn.microsoft.com/microsoftteams/cloud-voice-cloud-voice-overview",
            "Microsoft Teams Professional Pack v1",
        ],
        "confidence": 0.99,
        "status": "ACTIVE",
        "version": "1.0",
        "created_at": CREATED,
    }


def main() -> None:
    rb_incidents = {rb[0]: [] for rb in RUNBOOKS}
    vg_incidents = {vg[0]: [] for vg in VERIFICATIONS}
    ref_incidents = {ref[0]: [] for ref in REFERENCES}

    for item in INCIDENTS:
        for related in item["related"]:
            if related.startswith("RB-"):
                rb_incidents[related].append(item["id"])
            elif related.startswith("VG-"):
                vg_incidents[related].append(item["id"])
            elif related.startswith("REF-"):
                ref_incidents[related].append(item["id"])

        path = KNOWLEDGE / "incidents" / "microsoft" / "teams-phone" / f"{item['slug']}.yaml"
        write_yaml(path, incident_doc(item))

    rb_vg_map = {
        "RB-001": ["VG-001"],
        "RB-002": ["VG-002"],
        "RB-003": ["VG-006"],
        "RB-004": ["VG-007"],
        "RB-005": ["VG-003", "VG-004"],
        "RB-006": ["VG-001"],
        "RB-007": ["VG-005"],
        "RB-008": ["VG-008"],
        "RB-009": ["VG-009"],
        "RB-010": ["VG-010"],
    }

    for suffix, slug, title, code in RUNBOOKS:
        path = KNOWLEDGE / "runbooks" / "microsoft" / "teams-phone" / f"{slug}.yaml"
        write_yaml(
            path,
            runbook_doc(suffix, slug, title, code, rb_incidents[suffix][:3], rb_vg_map[suffix]),
        )

    vg_rb_map = {
        "VG-001": "RB-006",
        "VG-002": "RB-002",
        "VG-003": "RB-005",
        "VG-004": "RB-005",
        "VG-005": "RB-007",
        "VG-006": "RB-003",
        "VG-007": "RB-004",
        "VG-008": "RB-008",
        "VG-009": "RB-009",
        "VG-010": "RB-010",
    }

    for suffix, slug, title, code in VERIFICATIONS:
        path = KNOWLEDGE / "verification" / "microsoft" / "teams-phone" / f"{slug}.yaml"
        write_yaml(
            path,
            verification_doc(suffix, slug, title, code, vg_rb_map[suffix], vg_incidents[suffix][:3]),
        )

    ref_map = {
        "REF-001": ["000001", "000003", "000004", "000011", "000021"],
        "REF-002": ["000007", "000008", "000009", "000018", "000022"],
        "REF-003": ["000006", "000023"],
        "REF-004": ["000001", "000002", "000015", "000016"],
        "REF-005": ["000014"],
    }

    for suffix, slug, title in REFERENCES:
        path = KNOWLEDGE / "references" / "microsoft" / "teams-phone" / f"{slug}.yaml"
        write_yaml(path, reference_doc(suffix, slug, title, ref_map[suffix]))


if __name__ == "__main__":
    main()
