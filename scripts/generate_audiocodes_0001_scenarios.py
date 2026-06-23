#!/usr/bin/env python3
"""Generate VP-AUDIOCODES-0001 scenario evidence packs."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SAMPLE = REPO / "examples" / "sample_evidence" / "audiocodes"
SCENARIOS = REPO / "examples" / "sample_evidence" / "scenarios" / "vp_audiocodes_0001"

BASELINE = {
    "show_voip_status.txt": SAMPLE / "show_voip_status.txt",
    "show_sip_options.txt": SAMPLE / "show_sip_options.txt",
    "show_proxy_set.txt": SAMPLE / "show_proxy_set.txt",
    "show_ip_group.txt": SAMPLE / "show_ip_group.txt",
    "show_routing_table.txt": SAMPLE / "show_routing_table.txt",
    "show_media_realm.txt": SAMPLE / "show_media_realm.txt",
    "show_tls_context.txt": SAMPLE / "show_tls_context.txt",
    "show_certificates.txt": SAMPLE / "show_certificates.txt",
    "show_ha_status.txt": SAMPLE / "show_ha_status.txt",
    "show_licenses.txt": SAMPLE / "show_licenses.txt",
}

OVERRIDES: dict[str, dict[str, str]] = {
    "sip_options_failed": {
        "show_sip_options.txt": (
            "show sip-options\n"
            "Policy Name: OPTIONS_KEEPALIVE\n"
            "Options Enabled: True\n"
            "Options Status: Failed\n"
        ),
    },
    "provider_503": {
        "show_sip_options.txt": (
            "show sip-options\n"
            "Policy Name: OPTIONS_KEEPALIVE\n"
            "Options Enabled: True\n"
            "Options Status: 503\n"
        ),
    },
    "proxy_set_unavailable": {
        "show_proxy_set.txt": (
            "show proxy-set\n"
            "Proxy Set Name: PROVIDER_PS\n"
            "State: Unavailable\n"
            "Enable Heartbeat: Enabled\n"
            "Address: 203.0.113.10\n"
            "Transport: UDP\n"
            "Port: 5060\n"
        ),
    },
    "ip_group_disabled": {
        "show_ip_group.txt": (
            "show ip-group\n"
            "IP Group Name: TO_PROVIDER\n"
            "State: Disabled\n"
            "Proxy Set: PROVIDER_PS\n"
            "Media Realm: MR_INTERNAL\n"
            "IP Profile: DEFAULT_PROFILE\n"
            "Enable SRTP: True\n"
        ),
    },
    "routing_rule_missing": {
        "show_routing_table.txt": (
            "show routing-table\n"
            "Rule Name: PSTN_OUT\n"
            "Priority: 1\n"
        ),
    },
    "tls_certificate_expired": {
        "show_certificates.txt": SAMPLE / "show_certificates_expired.txt",
    },
    "media_realm_down": {
        "show_media_realm.txt": (
            "show media-realm\n"
            "Realm Name: MR_INTERNAL\n"
            "State: Failed\n"
            "IP Address: 10.10.2.10\n"
            "Port Range: 6000-6499\n"
        ),
    },
    "rtp_one_way_audio": {
        "show_media_realm.txt": (
            "show media-realm\n"
            "Realm Name: MR_INTERNAL\n"
            "State: Active\n"
            "Port Range: 6000-6499\n"
        ),
    },
    "session_license_exhausted": {
        "show_licenses.txt": SAMPLE / "show_licenses_exhausted.txt",
        "show_voip_status.txt": (
            "show voip status\n"
            "Device Name: SBC-LAB-01\n"
            "Device Status: Active\n"
            "Active Sessions: 100\n"
            "Call Failures: Elevated\n"
        ),
    },
    "ha_sync_failure": {
        "show_ha_status.txt": (
            "show ha-status\n"
            "Active Node: SBC-LAB-02\n"
            "Standby Node: SBC-LAB-01\n"
            "Cluster State: Failover\n"
            "Sync State: Out_of_sync\n"
        ),
    },
}

EXPECTED = {
    "sip_options_failed": ("SIP OPTIONS failure", 89),
    "provider_503": ("Provider SIP service unavailable", 90),
    "proxy_set_unavailable": ("Proxy Set unavailable", 92),
    "ip_group_disabled": ("IP Group disabled", 93),
    "routing_rule_missing": ("Routing configuration issue", 91),
    "tls_certificate_expired": ("TLS certificate expired", 95),
    "media_realm_down": ("Media Realm failure", 92),
    "rtp_one_way_audio": ("One-way audio", 88),
    "session_license_exhausted": ("License exhaustion", 94),
    "ha_sync_failure": ("HA synchronization issue", 91),
}


def _content(value: str | Path) -> str:
    if isinstance(value, Path):
        return value.read_text(encoding="utf-8")
    return value


def main() -> None:
    SCENARIOS.mkdir(parents=True, exist_ok=True)
    for scenario_id, overrides in OVERRIDES.items():
        scenario_dir = SCENARIOS / scenario_id
        scenario_dir.mkdir(parents=True, exist_ok=True)
        for filename, source in BASELINE.items():
            content = overrides.get(filename, source)
            (scenario_dir / filename).write_text(_content(content), encoding="utf-8")
        root_cause, min_confidence = EXPECTED[scenario_id]
        (scenario_dir / "expected_result.yaml").write_text(
            (
                f"scenario_id: {scenario_id}\n"
                f"expected_root_cause: {root_cause}\n"
                f"min_confidence: {min_confidence}\n"
            ),
            encoding="utf-8",
        )
        golden = (
            "# VoicePilot Incident Report (Golden)\n\n"
            f"## Scenario: {scenario_id}\n\n"
            f"**Expected Root Cause:** {root_cause}\n\n"
            f"**Minimum Confidence:** {min_confidence}%\n\n"
            "This golden report documents the deterministic investigation outcome "
            "for regression validation. VoicePilot is read-only and advisory only.\n"
        )
        (scenario_dir / "golden_report.md").write_text(golden, encoding="utf-8")
    print(f"Generated {len(OVERRIDES)} scenarios under {SCENARIOS}")


if __name__ == "__main__":
    main()
