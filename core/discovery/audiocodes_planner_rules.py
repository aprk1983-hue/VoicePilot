"""AudioCodes SBC discovery planner rules."""

from __future__ import annotations

from dataclasses import dataclass

from discovery.planner_models import DiscoveryPriority, DiscoveryRequest
from discovery.planner_rule import DiscoveryPlannerRule
from discovery.planner_rules import collected_commands, related_hypothesis_titles, _request_id
from domain.models import Case
from runtime.audiocodes_investigation import VP_AUDIOCODES_0001_PLAYBOOK_ID

VOIP_STATUS_COMMAND = "show voip status"
SIP_OPTIONS_COMMAND = "show sip-options"
PROXY_SET_COMMAND = "show proxy-set"
IP_GROUP_COMMAND = "show ip-group"
ROUTING_TABLE_COMMAND = "show routing-table"
MEDIA_REALM_COMMAND = "show media-realm"
TLS_CONTEXT_COMMAND = "show tls-context"
CERTIFICATES_COMMAND = "show certificates"
HA_STATUS_COMMAND = "show ha-status"
LICENSES_COMMAND = "show licenses"


def _audiocodes_case(case: Case) -> bool:
    return case.playbook_id == VP_AUDIOCODES_0001_PLAYBOOK_ID


@dataclass(frozen=True)
class AudioCodesVoipStatusMissingRule(DiscoveryPlannerRule):
    id: str = "audiocodes_voip_status_missing"
    title: str = "VoIP status evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _audiocodes_case(case) or VOIP_STATUS_COMMAND in collected_commands(case):
            return None
        return DiscoveryRequest(
            request_id=_request_id(self.id),
            command=VOIP_STATUS_COMMAND,
            vendor="audiocodes",
            priority=DiscoveryPriority.CRITICAL,
            reason="SBC device status and session utilization are not confirmed.",
            estimated_confidence_gain=18.0,
            estimated_minutes=2,
            related_hypotheses=related_hypothesis_titles(
                case,
                keywords=("license", "dns", "capacity"),
            ),
            already_collected=False,
            optional=False,
        )


@dataclass(frozen=True)
class AudioCodesSipOptionsMissingRule(DiscoveryPlannerRule):
    id: str = "audiocodes_sip_options_missing"
    title: str = "SIP OPTIONS evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _audiocodes_case(case) or SIP_OPTIONS_COMMAND in collected_commands(case):
            return None
        return DiscoveryRequest(
            request_id=_request_id(self.id),
            command=SIP_OPTIONS_COMMAND,
            vendor="audiocodes",
            priority=DiscoveryPriority.CRITICAL,
            reason="SIP OPTIONS keepalive and provider response are not available.",
            estimated_confidence_gain=20.0,
            estimated_minutes=2,
            related_hypotheses=related_hypothesis_titles(
                case,
                keywords=("sip options", "provider", "503"),
            ),
            already_collected=False,
            optional=False,
        )


@dataclass(frozen=True)
class AudioCodesProxySetMissingRule(DiscoveryPlannerRule):
    id: str = "audiocodes_proxy_set_missing"
    title: str = "Proxy Set evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _audiocodes_case(case) or PROXY_SET_COMMAND in collected_commands(case):
            return None
        return DiscoveryRequest(
            request_id=_request_id(self.id),
            command=PROXY_SET_COMMAND,
            vendor="audiocodes",
            priority=DiscoveryPriority.HIGH,
            reason="Proxy Set availability and gateway address are not confirmed.",
            estimated_confidence_gain=16.0,
            estimated_minutes=2,
            related_hypotheses=related_hypothesis_titles(
                case,
                keywords=("proxy", "gateway"),
            ),
            already_collected=False,
            optional=False,
        )


@dataclass(frozen=True)
class AudioCodesIpGroupMissingRule(DiscoveryPlannerRule):
    id: str = "audiocodes_ip_group_missing"
    title: str = "IP Group evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _audiocodes_case(case) or IP_GROUP_COMMAND in collected_commands(case):
            return None
        return DiscoveryRequest(
            request_id=_request_id(self.id),
            command=IP_GROUP_COMMAND,
            vendor="audiocodes",
            priority=DiscoveryPriority.HIGH,
            reason="IP Group state and associations are not available.",
            estimated_confidence_gain=15.0,
            estimated_minutes=2,
            related_hypotheses=related_hypothesis_titles(
                case,
                keywords=("ip group", "routing"),
            ),
            already_collected=False,
            optional=False,
        )


@dataclass(frozen=True)
class AudioCodesRoutingTableMissingRule(DiscoveryPlannerRule):
    id: str = "audiocodes_routing_table_missing"
    title: str = "Routing table evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _audiocodes_case(case) or ROUTING_TABLE_COMMAND in collected_commands(case):
            return None
        return DiscoveryRequest(
            request_id=_request_id(self.id),
            command=ROUTING_TABLE_COMMAND,
            vendor="audiocodes",
            priority=DiscoveryPriority.HIGH,
            reason="Routing table destination and IP Group mapping are not confirmed.",
            estimated_confidence_gain=14.0,
            estimated_minutes=2,
            related_hypotheses=related_hypothesis_titles(
                case,
                keywords=("routing", "destination"),
            ),
            already_collected=False,
            optional=False,
        )


@dataclass(frozen=True)
class AudioCodesMediaRealmMissingRule(DiscoveryPlannerRule):
    id: str = "audiocodes_media_realm_missing"
    title: str = "Media Realm evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _audiocodes_case(case) or MEDIA_REALM_COMMAND in collected_commands(case):
            return None
        return DiscoveryRequest(
            request_id=_request_id(self.id),
            command=MEDIA_REALM_COMMAND,
            vendor="audiocodes",
            priority=DiscoveryPriority.HIGH,
            reason="Media Realm state and RTP addressing are not available.",
            estimated_confidence_gain=14.0,
            estimated_minutes=2,
            related_hypotheses=related_hypothesis_titles(
                case,
                keywords=("media", "rtp", "one-way", "audio"),
            ),
            already_collected=False,
            optional=False,
        )


@dataclass(frozen=True)
class AudioCodesTlsContextMissingRule(DiscoveryPlannerRule):
    id: str = "audiocodes_tls_context_missing"
    title: str = "TLS context evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _audiocodes_case(case) or TLS_CONTEXT_COMMAND in collected_commands(case):
            return None
        related = related_hypothesis_titles(
            case,
            keywords=("tls", "certificate", "codec", "srtp"),
        )
        if not related and SIP_OPTIONS_COMMAND not in collected_commands(case):
            return None
        return DiscoveryRequest(
            request_id=_request_id(self.id),
            command=TLS_CONTEXT_COMMAND,
            vendor="audiocodes",
            priority=DiscoveryPriority.HIGH,
            reason="TLS negotiation state has not been validated.",
            estimated_confidence_gain=12.0,
            estimated_minutes=2,
            related_hypotheses=related,
            already_collected=False,
            optional=False,
        )


@dataclass(frozen=True)
class AudioCodesCertificatesMissingRule(DiscoveryPlannerRule):
    id: str = "audiocodes_certificates_missing"
    title: str = "Certificate evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _audiocodes_case(case) or CERTIFICATES_COMMAND in collected_commands(case):
            return None
        related = related_hypothesis_titles(
            case,
            keywords=("tls", "certificate"),
        )
        if not related and TLS_CONTEXT_COMMAND not in collected_commands(case):
            return None
        return DiscoveryRequest(
            request_id=_request_id(self.id),
            command=CERTIFICATES_COMMAND,
            vendor="audiocodes",
            priority=DiscoveryPriority.HIGH,
            reason="TLS certificate validity has not been confirmed.",
            estimated_confidence_gain=12.0,
            estimated_minutes=2,
            related_hypotheses=related,
            already_collected=False,
            optional=False,
        )


@dataclass(frozen=True)
class AudioCodesHaStatusMissingRule(DiscoveryPlannerRule):
    id: str = "audiocodes_ha_status_missing"
    title: str = "HA status evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _audiocodes_case(case) or HA_STATUS_COMMAND in collected_commands(case):
            return None
        return DiscoveryRequest(
            request_id=_request_id(self.id),
            command=HA_STATUS_COMMAND,
            vendor="audiocodes",
            priority=DiscoveryPriority.MEDIUM,
            reason="HA cluster synchronization state is not available.",
            estimated_confidence_gain=10.0,
            estimated_minutes=2,
            related_hypotheses=related_hypothesis_titles(
                case,
                keywords=("ha", "synchronization", "failover"),
            ),
            already_collected=False,
            optional=True,
        )


@dataclass(frozen=True)
class AudioCodesLicensesMissingRule(DiscoveryPlannerRule):
    id: str = "audiocodes_licenses_missing"
    title: str = "License evidence missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _audiocodes_case(case) or LICENSES_COMMAND in collected_commands(case):
            return None
        return DiscoveryRequest(
            request_id=_request_id(self.id),
            command=LICENSES_COMMAND,
            vendor="audiocodes",
            priority=DiscoveryPriority.MEDIUM,
            reason="Session license utilization is not confirmed.",
            estimated_confidence_gain=10.0,
            estimated_minutes=2,
            related_hypotheses=related_hypothesis_titles(
                case,
                keywords=("license", "capacity", "session"),
            ),
            already_collected=False,
            optional=True,
        )


AUDIOCODES_DISCOVERY_RULES: tuple[DiscoveryPlannerRule, ...] = (
    AudioCodesVoipStatusMissingRule(),
    AudioCodesSipOptionsMissingRule(),
    AudioCodesProxySetMissingRule(),
    AudioCodesIpGroupMissingRule(),
    AudioCodesRoutingTableMissingRule(),
    AudioCodesMediaRealmMissingRule(),
    AudioCodesTlsContextMissingRule(),
    AudioCodesCertificatesMissingRule(),
    AudioCodesHaStatusMissingRule(),
    AudioCodesLicensesMissingRule(),
)


def register_audiocodes_discovery_rules(registry) -> None:
    """Register AudioCodes SBC discovery planner rules."""
    for rule in AUDIOCODES_DISCOVERY_RULES:
        registry.register_rule(rule)
