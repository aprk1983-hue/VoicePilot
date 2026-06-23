#!/usr/bin/env python3
"""Generate VP-GENESYS-0001 scenario evidence packs."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HEALTHY = REPO / "examples" / "sample_evidence" / "genesys" / "healthy"
FAILURE = REPO / "examples" / "sample_evidence" / "genesys" / "failure"
SCENARIOS = REPO / "examples" / "sample_evidence" / "scenarios" / "vp_genesys_0001"

BASELINE = {
    "organization_export.csv": HEALTHY / "organization_export.csv",
    "users_export.json": HEALTHY / "users_export.json",
    "queues_export.csv": HEALTHY / "queues_export.csv",
    "queue_members_export.csv": HEALTHY / "queue_members_export.csv",
    "agents_export.txt": HEALTHY / "agents_export.txt",
    "presence_export.yaml": HEALTHY / "presence_export.yaml",
    "flows_export.csv": HEALTHY / "flows_export.csv",
    "architect_export.json": HEALTHY / "architect_export.json",
    "data_actions_export.csv": HEALTHY / "data_actions_export.csv",
    "byoc_cloud_trunks_export.txt": HEALTHY / "byoc_cloud_trunks_export.txt",
    "byoc_premises_trunks_export.csv": HEALTHY / "byoc_premises_trunks_export.csv",
    "edge_devices_export.json": HEALTHY / "edge_devices_export.json",
    "recording_policies_export.yaml": HEALTHY / "recording_policies_export.yaml",
    "campaigns_export.csv": HEALTHY / "campaigns_export.csv",
    "skills_export.json": HEALTHY / "skills_export.json",
}

OVERRIDES: dict[str, dict[str, str | Path]] = {
    "oauth_failure": {
        "organization_export.csv": (
            "Organization ID,Organization Name,State,OAuth Status,Token Status\n"
            "org-100,Acme CC,Active,failed,expired\n"
        ),
    },
    "edge_offline": {
        "edge_devices_export.json": (
            '[{"edge_id": "edge-901", "edge_name": "Edge-East-01", '
            '"state": "Offline", "organization_id": "org-100"}]'
        ),
    },
    "byoc_cloud_trunk_unavailable": {
        "byoc_cloud_trunks_export.txt": FAILURE / "byoc_cloud_trunk_failure.txt",
    },
    "byoc_premises_edge_unavailable": {
        "byoc_premises_trunks_export.csv": (
            "Trunk ID,Trunk Name,State,Edge ID\n"
            "trunk-prem-02,BYOC Premises Backup,Unavailable,edge-901\n"
        ),
        "edge_devices_export.json": (
            '[{"edge_id": "edge-901", "edge_name": "Edge-East-01", '
            '"state": "Offline", "organization_id": "org-100"}]'
        ),
    },
    "sip_options_failure": {
        "byoc_cloud_trunks_export.txt": (
            "Trunk ID: trunk-cloud-02\n"
            "Trunk Name: BYOC Cloud Backup\n"
            "State: Active\n"
            "SIP Options Status: Failed\n"
        ),
    },
    "tls_certificate_expired": {
        "byoc_cloud_trunks_export.txt": (
            "Trunk ID: trunk-cloud-03\n"
            "Trunk Name: BYOC Cloud TLS\n"
            "State: Active\n"
            "Certificate Status: expired\n"
            "TLS Status: failed\n"
        ),
    },
    "queue_unavailable": {
        "queues_export.csv": FAILURE / "queues_unavailable.csv",
    },
    "agent_not_logged_in": {
        "agents_export.txt": FAILURE / "agents_offline.txt",
    },
    "architect_flow_failure": {
        "flows_export.csv": (
            "Flow ID,Flow Name,State,Target Queue\n"
            "flow-500,Broken IVR,failed,queue-100\n"
        ),
        "architect_export.json": (
            '[{"flow_id": "arch-500", "flow_name": "Broken IVR", "publish_state": "Failed"}]'
        ),
    },
    "data_action_failure": {
        "data_actions_export.csv": (
            "Action ID,Action Name,State,Endpoint URL\n"
            "da-900,CRM Lookup,Failed,\n"
        ),
        "flows_export.csv": (
            "Flow ID,Flow Name,State,Target Queue\n"
            "flow-600,CRM Flow,failed,queue-100\n"
        ),
    },
    "webrtc_media_failure": {
        "organization_export.csv": (
            "Organization ID,Organization Name,State,Media Service Status,WebRTC Status\n"
            "org-100,Acme CC,Active,down,failed\n"
        ),
    },
    "outbound_campaign_failure": {
        "campaigns_export.csv": (
            "Campaign ID,Campaign Name,State,Queue ID\n"
            "camp-800,Outbound Sales,Failed,queue-100\n"
        ),
    },
}

EXPECTED = {
    "oauth_failure": ("OAuth failure", 94),
    "edge_offline": ("Edge offline", 93),
    "byoc_cloud_trunk_unavailable": ("BYOC Cloud trunk unavailable", 93),
    "byoc_premises_edge_unavailable": ("BYOC Premises Edge unavailable", 92),
    "sip_options_failure": ("SIP OPTIONS failure", 89),
    "tls_certificate_expired": ("TLS certificate expired", 95),
    "queue_unavailable": ("Queue unavailable", 92),
    "agent_not_logged_in": ("Agent not logged in", 90),
    "architect_flow_failure": ("Architect flow failure", 91),
    "data_action_failure": ("Data Action failure", 91),
    "webrtc_media_failure": ("Media service unavailable", 91),
    "outbound_campaign_failure": ("Outbound campaign failure", 91),
}


def _content(value: str | Path) -> str:
    if isinstance(value, Path):
        if value.suffix == ".txt" and "edge" in value.name:
            return value.read_text(encoding="utf-8")
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
            f"**Playbook:** VP-GENESYS-0001\n\n"
            f"**Scenario:** {scenario_id}\n\n"
            f"**Expected Root Cause:** {root_cause}\n\n"
            "VoicePilot advisory investigation — read-only, no configuration changes.\n"
        )
        (scenario_dir / "golden_report.md").write_text(golden, encoding="utf-8")


if __name__ == "__main__":
    main()
