#!/usr/bin/env python3
"""One-time generator for AudioCodes SBC Professional Knowledge Pack v1."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "knowledge"
PRODUCT_DIR = "sbc"
VENDOR = "AudioCodes"
PRODUCT = "SBC"
CREATED = "2026-06-22T12:00:00+00:00"

CATEGORY_MAP = {
    "SIP OPTIONS": "SIP",
    "PROVIDER": "CALL_ROUTING",
    "TLS CERTIFICATE": "TLS",
    "TLS NEGOTIATION": "TLS",
    "SIP INTERFACE": "SIP",
    "PROXY SET": "SIP",
    "IP GROUP": "ROUTING",
    "ROUTING TABLE": "ROUTING",
    "MANIPULATION SET": "ROUTING",
    "MEDIA REALM": "MEDIA",
    "RTP": "MEDIA",
    "SRTP": "MEDIA",
    "LICENSING": "LICENSING",
    "HIGH AVAILABILITY": "MONITORING",
    "SECURITY": "SECURITY",
    "CODEC": "CODEC",
    "SIP RESPONSE": "SIP",
    "PERFORMANCE": "PERFORMANCE",
    "DNS": "NETWORK",
    "GATEWAY": "SIP",
    "REGISTRATION": "SIP",
}

INCIDENTS = (
    {
        "id": "000001",
        "slug": "sip_options_failure",
        "title": "SIP OPTIONS failure",
        "category": "SIP OPTIONS",
        "severity": "high",
        "finding": "sip_options_failure",
        "symptoms": [
            "SIP trunk marked unavailable in monitoring",
            "Periodic OPTIONS requests fail on AudioCodes SBC",
            "Intermittent call setup failures to provider",
        ],
        "causes": [
            "SBC not responding to SIP OPTIONS keepalive",
            "Firewall drops OPTIONS in one direction",
            "Proxy Set or IP Group misconfigured for OPTIONS",
        ],
        "resolution": [
            "Enable SIP OPTIONS response on affected SIP Interface",
            "Verify firewall permits OPTIONS bidirectionally",
            "Validate Proxy Set keepalive timer alignment with peer",
        ],
        "rollback": ["Restore previous SIP Interface and Proxy Set keepalive settings"],
        "health_rules": ["sip_options_failure", "sip_options_timeout"],
        "related": ["RB-001", "VG-001", "REF-002"],
    },
    {
        "id": "000002",
        "slug": "provider_503",
        "title": "Provider 503",
        "category": "PROVIDER",
        "severity": "high",
        "finding": "provider_503",
        "symptoms": [
            "Outbound calls receive SIP 503 Service Unavailable",
            "Provider trunk shows overload or maintenance state",
            "All destinations fail through same IP Group",
        ],
        "causes": [
            "ITSP trunk capacity exhausted",
            "Provider maintenance or route withdrawal",
            "Incorrect routing to unavailable provider gateway",
        ],
        "resolution": [
            "Verify provider trunk status with carrier NOC",
            "Fail over to alternate Proxy Set if configured",
            "Review IP Group routing to healthy provider endpoint",
        ],
        "rollback": ["Restore previous IP Group and routing table assignment"],
        "health_rules": ["provider_503", "provider_unavailable"],
        "related": ["RB-008", "VG-008", "REF-002"],
    },
    {
        "id": "000003",
        "slug": "tls_certificate_expired",
        "title": "TLS certificate expired",
        "category": "TLS CERTIFICATE",
        "severity": "critical",
        "finding": "tls_certificate_expired",
        "symptoms": [
            "TLS handshake failures on SIP Interface",
            "Certificate expiry alarm in SBC management",
            "Secure trunk registration lost",
        ],
        "causes": [
            "TLS certificate past notAfter date",
            "Incomplete certificate chain uploaded to SBC",
            "Automated renewal not applied to active interface",
        ],
        "resolution": [
            "Renew TLS certificate and upload full chain",
            "Apply certificate to affected SIP Interface",
            "Validate peer accepts renewed certificate",
        ],
        "rollback": ["Restore previous valid certificate if renewal fails"],
        "health_rules": ["tls_certificate_expired"],
        "related": ["RB-002", "VG-002", "REF-003"],
    },
    {
        "id": "000004",
        "slug": "tls_negotiation_failure",
        "title": "TLS negotiation failure",
        "category": "TLS NEGOTIATION",
        "severity": "critical",
        "finding": "tls_negotiation_failure",
        "symptoms": [
            "TLS handshake fails before SIP dialog",
            "Cipher suite mismatch in SBC logs",
            "Secure trunk never reaches REGISTER state",
        ],
        "causes": [
            "TLS version or cipher mismatch with peer",
            "Missing intermediate CA in trust store",
            "SIP Interface TLS settings incompatible with provider",
        ],
        "resolution": [
            "Align TLS version and cipher suites with provider requirements",
            "Import complete certificate chain and trusted CAs",
            "Test TLS handshake with openssl s_client from SBC network",
        ],
        "rollback": ["Restore previous TLS profile on SIP Interface"],
        "health_rules": ["tls_negotiation_failure", "tls_handshake_failed"],
        "related": ["RB-002", "VG-002", "REF-003"],
    },
    {
        "id": "000005",
        "slug": "sip_interface_down",
        "title": "SIP Interface down",
        "category": "SIP INTERFACE",
        "severity": "critical",
        "finding": "sip_interface_down",
        "symptoms": [
            "SIP Interface administrative or operational state down",
            "All calls on interface fail immediately",
            "Monitoring shows interface unavailable",
        ],
        "causes": [
            "SIP Interface administratively disabled",
            "Underlying network interface or VLAN failure",
            "License or resource constraint preventing interface start",
        ],
        "resolution": [
            "Verify SIP Interface enabled and bound to correct Media Realm",
            "Restore network connectivity to interface subnet",
            "Restart affected SIP Interface after configuration correction",
        ],
        "rollback": ["Restore previous SIP Interface configuration export"],
        "health_rules": ["sip_interface_down"],
        "related": ["RB-001", "VG-001", "REF-001"],
    },
    {
        "id": "000006",
        "slug": "proxy_set_unavailable",
        "title": "Proxy Set unavailable",
        "category": "PROXY SET",
        "severity": "high",
        "finding": "proxy_set_unavailable",
        "symptoms": [
            "Proxy Set health check fails",
            "Outbound routing through Proxy Set rejected",
            "Registration to upstream proxy fails",
        ],
        "causes": [
            "Proxy Set points to unreachable peer address",
            "Proxy Set disabled or misassigned to IP Group",
            "DNS name in Proxy Set does not resolve",
        ],
        "resolution": [
            "Validate Proxy Set host, port, and transport settings",
            "Confirm Proxy Set assignment in IP Group",
            "Test reachability with ping and SIP trace",
        ],
        "rollback": ["Restore previous Proxy Set configuration"],
        "health_rules": ["proxy_set_unavailable"],
        "related": ["RB-003", "VG-003", "REF-002"],
    },
    {
        "id": "000007",
        "slug": "ip_group_disabled",
        "title": "IP Group disabled",
        "category": "IP GROUP",
        "severity": "high",
        "finding": "ip_group_disabled",
        "symptoms": [
            "Calls matching IP Group pattern fail",
            "IP Group shows disabled in configuration",
            "Routing stops for affected number range",
        ],
        "causes": [
            "IP Group administratively disabled during change",
            "Change window left IP Group disabled",
            "Automated policy disabled IP Group after alarm",
        ],
        "resolution": [
            "Enable IP Group and verify Proxy Set linkage",
            "Validate routing table references enabled IP Group",
            "Place test call through affected route",
        ],
        "rollback": ["Restore previous IP Group enable state from export"],
        "health_rules": ["ip_group_disabled"],
        "related": ["RB-003", "VG-003", "REF-001"],
    },
    {
        "id": "000008",
        "slug": "ip_group_mismatch",
        "title": "IP Group mismatch",
        "category": "IP GROUP",
        "severity": "medium",
        "finding": "ip_group_mismatch",
        "symptoms": [
            "Calls route to wrong provider or fail with no match",
            "Source/destination IP Group classification incorrect",
            "Manipulation applied from wrong IP Group",
        ],
        "causes": [
            "IP Group classification rules do not match call source",
            "Overlapping IP Group definitions with wrong priority",
            "Recent network change altered source IP seen by SBC",
        ],
        "resolution": [
            "Review IP Group classification rules and priority order",
            "Align IP Group with actual signaling source addresses",
            "Validate with SIP ladder diagram and routing trace",
        ],
        "rollback": ["Restore previous IP Group classification rules"],
        "health_rules": ["ip_group_mismatch"],
        "related": ["RB-003", "VG-003", "REF-001"],
    },
    {
        "id": "000009",
        "slug": "routing_table_issue",
        "title": "Routing table issue",
        "category": "ROUTING TABLE",
        "severity": "high",
        "finding": "routing_table_issue",
        "symptoms": [
            "Calls fail with no route or wrong destination",
            "Routing Policy does not match expected prefix",
            "LCR selects incorrect trunk",
        ],
        "causes": [
            "Routing table entry missing for destination prefix",
            "Incorrect LCR priority or weight assignment",
            "Manipulation Set alters dialed number before route lookup",
        ],
        "resolution": [
            "Verify routing table entries for failing destination class",
            "Correct LCR policy priority and trunk selection",
            "Test route lookup with SBC routing trace tools",
        ],
        "rollback": ["Restore routing table export from last known good baseline"],
        "health_rules": ["routing_table_issue", "route_lookup_failed"],
        "related": ["RB-004", "VG-004", "REF-001"],
    },
    {
        "id": "000010",
        "slug": "manipulation_set_failure",
        "title": "Manipulation Set failure",
        "category": "MANIPULATION SET",
        "severity": "medium",
        "finding": "manipulation_set_failure",
        "symptoms": [
            "Dialed number transformed incorrectly",
            "Outbound URI or Request-URI malformed after manipulation",
            "Provider rejects call due to invalid number format",
        ],
        "causes": [
            "Manipulation rule regex incorrect or order wrong",
            "Manipulation Set not applied to expected IP Group",
            "Strip/add prefix rule removes required digits",
        ],
        "resolution": [
            "Review Manipulation Set rules and execution order",
            "Validate output against provider numbering requirements",
            "Test manipulation with SBC message trace",
        ],
        "rollback": ["Restore previous Manipulation Set configuration"],
        "health_rules": ["manipulation_set_failure"],
        "related": ["RB-004", "VG-004", "REF-001"],
    },
    {
        "id": "000011",
        "slug": "media_realm_failure",
        "title": "Media Realm failure",
        "category": "MEDIA REALM",
        "severity": "high",
        "finding": "media_realm_failure",
        "symptoms": [
            "Calls setup but no audio path established",
            "Media Realm unavailable or misconfigured",
            "RTP ports not allocated from expected range",
        ],
        "causes": [
            "Media Realm disabled or IP address unreachable",
            "RTP port range exhausted in Media Realm",
            "SIP Interface not associated with correct Media Realm",
        ],
        "resolution": [
            "Verify Media Realm enabled with valid IP and port range",
            "Expand RTP port pool if exhausted",
            "Associate SIP Interface with correct Media Realm",
        ],
        "rollback": ["Restore previous Media Realm configuration"],
        "health_rules": ["media_realm_failure"],
        "related": ["RB-005", "VG-005", "REF-004"],
    },
    {
        "id": "000012",
        "slug": "rtp_one_way_audio",
        "title": "RTP one-way audio",
        "category": "RTP",
        "severity": "high",
        "finding": "rtp_one_way_audio",
        "symptoms": [
            "Caller hears callee but not vice versa or opposite",
            "RTP stream present in one direction only",
            "Post-connect audio asymmetry on all calls",
        ],
        "causes": [
            "Asymmetric RTP routing or NAT pinhole failure",
            "Wrong Media Realm public IP advertised in SDP",
            "Firewall blocks RTP return path",
        ],
        "resolution": [
            "Verify symmetric RTP and correct public IP in Media Realm",
            "Open required RTP port range bidirectionally on firewall",
            "Enable RTCP and validate pinhole with packet capture",
        ],
        "rollback": ["Restore previous Media Realm NAT and public IP settings"],
        "health_rules": ["rtp_one_way_audio", "one_way_audio"],
        "related": ["RB-005", "VG-005", "REF-004"],
    },
    {
        "id": "000013",
        "slug": "srtp_mismatch",
        "title": "SRTP mismatch",
        "category": "SRTP",
        "severity": "high",
        "finding": "srtp_mismatch",
        "symptoms": [
            "Secure calls fail at media negotiation",
            "SDP crypto attribute rejected by peer",
            "Calls work when encryption disabled only",
        ],
        "causes": [
            "SRTP mandatory on one side and optional on other",
            "Mismatched crypto suite or key exchange method",
            "Media Security disabled on IP Group but required by peer",
        ],
        "resolution": [
            "Align SRTP policy on IP Group with peer requirements",
            "Match crypto suites supported by both endpoints",
            "Validate secure media with controlled test call",
        ],
        "rollback": ["Restore previous media security profile"],
        "health_rules": ["srtp_mismatch", "media_security_mismatch"],
        "related": ["RB-002", "VG-002", "REF-004"],
    },
    {
        "id": "000014",
        "slug": "session_license_exhausted",
        "title": "Session license exhausted",
        "category": "LICENSING",
        "severity": "critical",
        "finding": "session_license_exhausted",
        "symptoms": [
            "New calls rejected with license limit alarm",
            "SBC reports maximum session count reached",
            "Existing calls continue but new sessions fail",
        ],
        "causes": [
            "Session license capacity reached",
            "Zombie sessions not releasing licenses",
            "License file not updated after capacity upgrade order",
        ],
        "resolution": [
            "Verify active session count versus licensed capacity",
            "Clear stale sessions or restart affected service if safe",
            "Install updated license file from AudioCodes portal",
        ],
        "rollback": ["Restore previous license file if new license causes fault"],
        "health_rules": ["session_license_exhausted", "license_capacity_exceeded"],
        "related": ["RB-009", "VG-009", "REF-001"],
    },
    {
        "id": "000015",
        "slug": "ha_failover",
        "title": "HA failover",
        "category": "HIGH AVAILABILITY",
        "severity": "critical",
        "finding": "ha_failover",
        "symptoms": [
            "Active SBC node failed over to standby",
            "Brief call drop during HA switchover",
            "HA state shows active on secondary node",
        ],
        "causes": [
            "Primary node hardware or service failure",
            "Network partition triggered HA switch",
            "Manual failover during maintenance",
        ],
        "resolution": [
            "Verify HA pair health and synchronization state",
            "Investigate root cause on former active node",
            "Plan controlled failback after primary restored",
        ],
        "rollback": ["Fail back to preferred active node per HA runbook"],
        "health_rules": ["ha_failover", "ha_switchover"],
        "related": ["RB-006", "VG-006", "REF-005"],
    },
    {
        "id": "000016",
        "slug": "standby_synchronization_failure",
        "title": "Standby synchronization failure",
        "category": "HIGH AVAILABILITY",
        "severity": "critical",
        "finding": "standby_synchronization_failure",
        "symptoms": [
            "HA pair out of sync alarm",
            "Configuration drift between active and standby",
            "Failover readiness degraded",
        ],
        "causes": [
            "Sync link between HA nodes interrupted",
            "Configuration change not replicated to standby",
            "Standby node storage or service fault",
        ],
        "resolution": [
            "Restore HA synchronization link connectivity",
            "Force configuration sync from active to standby",
            "Verify standby node ready for failover",
        ],
        "rollback": ["Restore HA pair from last synchronized backup"],
        "health_rules": ["standby_synchronization_failure", "ha_sync_failed"],
        "related": ["RB-006", "VG-006", "REF-005"],
    },
    {
        "id": "000017",
        "slug": "sip_flood_protection",
        "title": "SIP flood protection",
        "category": "SECURITY",
        "severity": "high",
        "finding": "sip_flood_protection",
        "symptoms": [
            "Legitimate calls blocked after traffic spike",
            "SIP flood protection alarm active",
            "High rate of rejected INVITE or REGISTER",
        ],
        "causes": [
            "SIP flood threshold exceeded by attack or misbehaving endpoint",
            "Scan or registration storm from external source",
            "Protection profile too aggressive for normal peak load",
        ],
        "resolution": [
            "Identify source IP and block at firewall or SBC ACL",
            "Tune SIP flood protection thresholds if false positive",
            "Enable geo-blocking or rate limiting on untrusted interfaces",
        ],
        "rollback": ["Restore previous SIP flood protection profile"],
        "health_rules": ["sip_flood_protection", "sip_flood_detected"],
        "related": ["RB-007", "VG-007", "REF-001"],
    },
    {
        "id": "000018",
        "slug": "dos_protection",
        "title": "DoS protection",
        "category": "SECURITY",
        "severity": "high",
        "finding": "dos_protection",
        "symptoms": [
            "SBC enters DoS protection mode",
            "Call admission temporarily restricted",
            "Management reports denial-of-service event",
        ],
        "causes": [
            "Distributed SIP or network DoS attack",
            "Misconfigured endpoint sending excessive signaling",
            "Insufficient DoS profile tuning for deployment size",
        ],
        "resolution": [
            "Engage network team to filter attack traffic upstream",
            "Review DoS protection logs for attack pattern",
            "Adjust DoS thresholds after attack subsides",
        ],
        "rollback": ["Restore previous DoS protection configuration"],
        "health_rules": ["dos_protection", "dos_event_active"],
        "related": ["RB-007", "VG-007", "REF-001"],
    },
    {
        "id": "000019",
        "slug": "codec_mismatch_488",
        "title": "488 codec mismatch",
        "category": "CODEC",
        "severity": "medium",
        "finding": "codec_mismatch_488",
        "symptoms": [
            "Calls fail with SIP 488 Not Acceptable Here",
            "No common codec in SDP offer/answer",
            "Fax or modem calls fail on transcoding path",
        ],
        "causes": [
            "Codec restriction on IP Group excludes peer codecs",
            "Transcoding resource unavailable",
            "Priority codec list misaligned with provider",
        ],
        "resolution": [
            "Align allowed codec list with provider requirements",
            "Enable transcoding license and Media Profile if needed",
            "Test codec negotiation with SIP ladder diagram",
        ],
        "rollback": ["Restore previous codec restriction profile"],
        "health_rules": ["codec_mismatch_488", "sip_488_detected"],
        "related": ["RB-005", "VG-005", "REF-004"],
    },
    {
        "id": "000020",
        "slug": "forbidden_403",
        "title": "403 forbidden",
        "category": "SIP RESPONSE",
        "severity": "high",
        "finding": "forbidden_403",
        "symptoms": [
            "Outbound calls rejected with SIP 403 Forbidden",
            "Provider denies call based on identity or authorization",
            "Specific destination class consistently fails",
        ],
        "causes": [
            "Caller ID or From header not authorized by provider",
            "Digest authentication failure on outbound trunk",
            "Geo or class-of-service restriction on provider side",
        ],
        "resolution": [
            "Verify From/PAI headers match provider authorization policy",
            "Validate digest credentials on IP Group or Proxy Set",
            "Confirm destination permitted under trunk contract",
        ],
        "rollback": ["Restore previous manipulation and authentication settings"],
        "health_rules": ["forbidden_403", "sip_403_detected"],
        "related": ["RB-008", "VG-008", "REF-002"],
    },
    {
        "id": "000021",
        "slug": "timeout_408",
        "title": "408 timeout",
        "category": "SIP RESPONSE",
        "severity": "high",
        "finding": "timeout_408",
        "symptoms": [
            "Calls fail with SIP 408 Request Timeout",
            "No response from downstream gateway within timer",
            "Post-dial delay then timeout on all attempts",
        ],
        "causes": [
            "Downstream gateway unreachable or overloaded",
            "Timer T1/T2 misaligned causing premature timeout",
            "Network latency or packet loss on signaling path",
        ],
        "resolution": [
            "Verify downstream gateway reachability and load",
            "Review session timer and transaction timeout settings",
            "Capture signaling trace to identify silent hop",
        ],
        "rollback": ["Restore previous timer profile on SIP Interface"],
        "health_rules": ["timeout_408", "sip_408_detected"],
        "related": ["RB-001", "VG-001", "REF-002"],
    },
    {
        "id": "000022",
        "slug": "sbc_overload",
        "title": "SBC overload",
        "category": "PERFORMANCE",
        "severity": "critical",
        "finding": "sbc_overload",
        "symptoms": [
            "SBC CPU or session load at maximum",
            "New call attempts rejected under overload policy",
            "Management GUI sluggish or unresponsive",
        ],
        "causes": [
            "Call volume exceeds SBC rated capacity",
            "Resource leak or runaway signaling process",
            "Insufficient hardware sizing for peak traffic",
        ],
        "resolution": [
            "Reduce load via upstream throttling if possible",
            "Identify and clear abnormal session or process consumption",
            "Plan capacity upgrade or HA load distribution",
        ],
        "rollback": ["Restore overload thresholds after stabilization"],
        "health_rules": ["sbc_overload", "cpu_overload"],
        "related": ["RB-010", "VG-010", "REF-001"],
    },
    {
        "id": "000023",
        "slug": "dns_resolution_failure",
        "title": "DNS resolution failure",
        "category": "DNS",
        "severity": "high",
        "finding": "dns_resolution_failure",
        "symptoms": [
            "Proxy Set FQDN does not resolve",
            "Trunk registration fails after DNS change",
            "Intermittent failures when DNS server unreachable",
        ],
        "causes": [
            "DNS server unreachable from SBC management network",
            "Incorrect FQDN in Proxy Set or routing configuration",
            "DNS TTL expired during provider migration",
        ],
        "resolution": [
            "Verify DNS server settings on SBC",
            "Test resolution with nslookup from SBC shell",
            "Update FQDN or SRV records to current provider target",
        ],
        "rollback": ["Restore previous DNS and FQDN configuration"],
        "health_rules": ["dns_resolution_failure", "dns_lookup_failed"],
        "related": ["RB-010", "VG-010", "REF-002"],
    },
    {
        "id": "000024",
        "slug": "gateway_unreachable",
        "title": "Gateway unreachable",
        "category": "GATEWAY",
        "severity": "critical",
        "finding": "gateway_unreachable",
        "symptoms": [
            "All calls to provider gateway fail",
            "Ping or SIP OPTIONS to gateway fails",
            "Alarm for unreachable Proxy Set host",
        ],
        "causes": [
            "Network path to provider gateway blocked",
            "Provider gateway offline or maintenance",
            "Wrong IP address in Proxy Set after provider change",
        ],
        "resolution": [
            "Verify network routing and firewall to gateway IP",
            "Confirm provider gateway status with carrier",
            "Update Proxy Set with current gateway address",
        ],
        "rollback": ["Restore previous Proxy Set gateway assignment"],
        "health_rules": ["gateway_unreachable", "pstn_gateway_unreachable"],
        "related": ["RB-008", "VG-008", "REF-002"],
    },
    {
        "id": "000025",
        "slug": "registration_failure",
        "title": "Registration failure",
        "category": "REGISTRATION",
        "severity": "high",
        "finding": "registration_failure",
        "symptoms": [
            "SBC fails to register to upstream registrar",
            "401/407 authentication loop in SIP trace",
            "Trunk status shows unregistered",
        ],
        "causes": [
            "Incorrect registration credentials on IP Group",
            "Registrar rejects contact or expires binding",
            "Transport or port mismatch on registration request",
        ],
        "resolution": [
            "Verify registration username, password, and realm",
            "Align Contact header and transport with registrar policy",
            "Review SIP trace for final rejection reason",
        ],
        "rollback": ["Restore previous registration credentials from export"],
        "health_rules": ["registration_failure", "sip_registration_failed"],
        "related": ["RB-001", "VG-001", "REF-002"],
    },
)

RUNBOOKS = (
    ("RB-001", "validate_sip_trunk", "Validate SIP Trunk", "RB-AUDIOCODES-SIP-TRUNK"),
    ("RB-002", "validate_tls", "Validate TLS Configuration", "RB-AUDIOCODES-TLS"),
    ("RB-003", "validate_proxy_ip_group", "Validate Proxy Set and IP Group", "RB-AUDIOCODES-PROXY"),
    ("RB-004", "validate_routing", "Validate Routing and Manipulation", "RB-AUDIOCODES-ROUTING"),
    ("RB-005", "validate_media", "Validate Media and Codecs", "RB-AUDIOCODES-MEDIA"),
    ("RB-006", "validate_ha", "Validate HA Cluster", "RB-AUDIOCODES-HA"),
    ("RB-007", "validate_security", "Validate Security Policies", "RB-AUDIOCODES-SECURITY"),
    ("RB-008", "validate_provider", "Validate Provider Connectivity", "RB-AUDIOCODES-PROVIDER"),
    ("RB-009", "validate_licensing", "Validate Session Licensing", "RB-AUDIOCODES-LICENSE"),
    ("RB-010", "validate_dns_capacity", "Validate DNS and Capacity", "RB-AUDIOCODES-DNS"),
)

VERIFICATIONS = (
    ("VG-001", "verify_sip_trunk", "Verify SIP trunk health", "VG-AUDIOCODES-SIP-TRUNK"),
    ("VG-002", "verify_tls", "Verify TLS and SRTP", "VG-AUDIOCODES-TLS"),
    ("VG-003", "verify_proxy_ip_group", "Verify Proxy Set and IP Group", "VG-AUDIOCODES-PROXY"),
    ("VG-004", "verify_routing", "Verify routing table", "VG-AUDIOCODES-ROUTING"),
    ("VG-005", "verify_media", "Verify media path", "VG-AUDIOCODES-MEDIA"),
    ("VG-006", "verify_ha", "Verify HA synchronization", "VG-AUDIOCODES-HA"),
    ("VG-007", "verify_security", "Verify security policies", "VG-AUDIOCODES-SECURITY"),
    ("VG-008", "verify_provider", "Verify provider gateway", "VG-AUDIOCODES-PROVIDER"),
    ("VG-009", "verify_licensing", "Verify session licensing", "VG-AUDIOCODES-LICENSE"),
    ("VG-010", "verify_dns_capacity", "Verify DNS and capacity", "VG-AUDIOCODES-DNS"),
)

REFERENCES = (
    ("REF-001", "audiocodes_sbc_architecture", "AudioCodes SBC Architecture"),
    ("REF-002", "sip_trunk_configuration", "SIP Trunk Configuration Reference"),
    ("REF-003", "tls_certificate_management", "TLS Certificate Management"),
    ("REF-004", "media_realm_reference", "Media Realm Reference"),
    ("REF-005", "ha_cluster_reference", "HA Cluster Reference"),
)


def asset_id(suffix: str) -> str:
    return f"VP-AUDIOCODES-SBC-{suffix}"


def write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def incident_doc(item: dict) -> dict:
    related = [asset_id(related_id) for related_id in item["related"]]
    title = item["title"]
    if not title.lower().startswith("audiocodes"):
        title = f"AudioCodes SBC {title}"
    return {
        "asset_id": asset_id(item["id"]),
        "title": title,
        "asset_type": "INCIDENT",
        "vendor": VENDOR,
        "product": PRODUCT,
        "category": CATEGORY_MAP[item["category"]],
        "severity": item["severity"],
        "summary": f"{title} affecting AudioCodes SBC operations.",
        "description": f"{title} affecting AudioCodes SBC operations.",
        "symptoms": item["symptoms"],
        "required_evidence": [
            "AudioCodes SBC configuration export",
            "SIP message trace or Syslog snapshot",
            "Alarm and status screen capture",
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
            "audiocodes-sbc",
            "professional-pack",
            "audiocodes",
            item["category"].lower().replace(" ", "-"),
        ],
        "references": [
            "AudioCodes SBC Professional Pack v1",
            "AudioCodes Mediant SBC product documentation",
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
        "vendor": VENDOR,
        "product": PRODUCT,
        "category": "SIP",
        "severity": "high",
        "summary": f"{title} for AudioCodes SBC.",
        "description": f"{title} for AudioCodes SBC. Professional pack runbook {code}.",
        "symptoms": ["Service degradation requiring runbook remediation"],
        "expected_findings": ["runbook_remediation_required"],
        "expected_hypotheses": ["Known AudioCodes SBC failure pattern matched"],
        "known_causes": ["Configuration or connectivity fault on AudioCodes SBC"],
        "known_resolution": ["Execute runbook steps and validate with verification guide"],
        "recommended_actions": [
            f"Follow {code} remediation steps in order",
            "Document changes in change record",
            "Validate outcome with linked verification guide",
        ],
        "rollback_steps": [
            "Restore exported AudioCodes SBC configuration",
            "Revert policy assignment to previous baseline",
        ],
        "verification_steps": ["Execute linked verification guide after remediation"],
        "related_asset_ids": [asset_id(item) for item in vgs + incidents],
        "tags": ["audiocodes-sbc", "runbook", "professional-pack", "audiocodes"],
        "references": ["AudioCodes SBC Professional Pack v1", code],
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
        "vendor": VENDOR,
        "product": PRODUCT,
        "category": "SIP",
        "severity": "medium",
        "summary": f"{title} for AudioCodes SBC.",
        "description": f"{title} for AudioCodes SBC. Professional pack guide {code}.",
        "symptoms": ["Post-remediation validation required"],
        "expected_findings": ["verification_passed"],
        "expected_hypotheses": ["Service restored to operational baseline"],
        "known_causes": ["Remediation not yet validated"],
        "known_resolution": ["Complete verification steps and attach evidence"],
        "required_evidence": [
            "AudioCodes SBC status export after remediation",
            "Test call SIP ladder diagram",
            "Configuration snapshot after change",
        ],
        "verification_steps": [
            f"Execute {code} validation checklist",
            "Compare results against expected operational baseline",
            "Attach evidence to investigation record",
        ],
        "recommended_actions": ["Compare results against expected operational baseline"],
        "related_asset_ids": [asset_id(rb), *[asset_id(item) for item in incidents]],
        "tags": ["audiocodes-sbc", "verification", "professional-pack", "audiocodes"],
        "references": ["AudioCodes SBC Professional Pack v1", code],
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
        "vendor": VENDOR,
        "product": PRODUCT,
        "category": "SIP",
        "severity": "low",
        "summary": f"{title} reference for AudioCodes SBC engineering investigations.",
        "description": f"{title} for AudioCodes SBC deployments and troubleshooting.",
        "symptoms": ["Engineering reference consultation required"],
        "expected_findings": ["reference_applicable"],
        "expected_hypotheses": ["Authoritative AudioCodes guidance applies"],
        "known_causes": ["Misconfiguration relative to AudioCodes best practice"],
        "known_resolution": ["Align design and remediation with AudioCodes guidance"],
        "recommended_actions": ["Consult this reference during investigation and remediation"],
        "verification_steps": ["Confirm document version matches deployed SBC configuration"],
        "related_asset_ids": [asset_id(item) for item in incidents],
        "tags": ["audiocodes-sbc", "reference", "professional-pack", "audiocodes"],
        "references": [
            "https://www.audiocodes.com/solutions-products/sbc",
            "AudioCodes SBC Professional Pack v1",
        ],
        "confidence": 0.99,
        "status": "ACTIVE",
        "version": "1.0",
        "created_at": CREATED,
    }


def main() -> None:
    rb_incidents = {rb[0]: [] for rb in RUNBOOKS}
    vg_incidents = {vg[0]: [] for vg in VERIFICATIONS}

    for item in INCIDENTS:
        for related in item["related"]:
            if related.startswith("RB-"):
                rb_incidents[related].append(item["id"])
            elif related.startswith("VG-"):
                vg_incidents[related].append(item["id"])

        path = KNOWLEDGE / "incidents" / "audiocodes" / PRODUCT_DIR / f"{item['slug']}.yaml"
        write_yaml(path, incident_doc(item))

    rb_vg_map = {
        "RB-001": ["VG-001"],
        "RB-002": ["VG-002"],
        "RB-003": ["VG-003"],
        "RB-004": ["VG-004"],
        "RB-005": ["VG-005"],
        "RB-006": ["VG-006"],
        "RB-007": ["VG-007"],
        "RB-008": ["VG-008"],
        "RB-009": ["VG-009"],
        "RB-010": ["VG-010"],
    }

    for suffix, slug, title, code in RUNBOOKS:
        path = KNOWLEDGE / "runbooks" / "audiocodes" / PRODUCT_DIR / f"{slug}.yaml"
        write_yaml(
            path,
            runbook_doc(suffix, slug, title, code, rb_incidents[suffix][:3], rb_vg_map[suffix]),
        )

    vg_rb_map = {f"VG-{index:03d}": f"RB-{index:03d}" for index in range(1, 11)}

    for suffix, slug, title, code in VERIFICATIONS:
        path = KNOWLEDGE / "verification" / "audiocodes" / PRODUCT_DIR / f"{slug}.yaml"
        write_yaml(
            path,
            verification_doc(suffix, slug, title, code, vg_rb_map[suffix], vg_incidents[suffix][:3]),
        )

    ref_map = {
        "REF-001": ["000005", "000007", "000017", "000018", "000022"],
        "REF-002": ["000001", "000002", "000006", "000020", "000024", "000025"],
        "REF-003": ["000003", "000004", "000013"],
        "REF-004": ["000011", "000012", "000019"],
        "REF-005": ["000015", "000016"],
    }

    for suffix, slug, title in REFERENCES:
        path = KNOWLEDGE / "references" / "audiocodes" / PRODUCT_DIR / f"{slug}.yaml"
        write_yaml(path, reference_doc(suffix, slug, title, ref_map[suffix]))

    print(f"Generated {len(INCIDENTS)} incidents, {len(RUNBOOKS)} runbooks, "
          f"{len(VERIFICATIONS)} verification guides, {len(REFERENCES)} references")


if __name__ == "__main__":
    main()
