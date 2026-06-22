"""Built-in discovery planner rules."""

from __future__ import annotations

from dataclasses import dataclass

from domain.enums import HypothesisStatus
from domain.models import Case
from discovery.planner_models import DiscoveryPriority, DiscoveryRequest
from discovery.planner_rule import DiscoveryPlannerRule

VP_CUBE_0001_PLAYBOOK_ID = "VP-CUBE-0001"

DIAL_PEER_SUMMARY_COMMAND = "show dial-peer voice summary"
SIP_UA_STATUS_COMMAND = "show sip-ua status"
VOICE_SERVICE_VOIP_COMMAND = "show run | sec voice service voip"
CCSIP_DEBUG_COMMAND = "debug ccsip messages"


def collected_commands(case: Case) -> set[str]:
    """Return CLI commands already collected on the case."""
    commands: set[str] = set()
    for evidence in case.evidence:
        command = evidence.source.command
        if command:
            commands.add(command)
    return commands


def related_hypothesis_titles(
    case: Case,
    *,
    keywords: tuple[str, ...] = (),
) -> tuple[str, ...]:
    """Return active hypothesis titles optionally filtered by keywords."""
    titles: list[str] = []
    for hypothesis in case.hypotheses:
        if hypothesis.status == HypothesisStatus.ELIMINATED:
            continue
        title_lower = hypothesis.title.lower()
        if keywords and not any(keyword in title_lower for keyword in keywords):
            continue
        titles.append(hypothesis.title)
    return tuple(sorted(titles))


def _request_id(rule_id: str) -> str:
    return f"DISC-{rule_id}"


def _cube_playbook_case(case: Case) -> bool:
    if not case.playbook_id:
        return True
    return case.playbook_id == VP_CUBE_0001_PLAYBOOK_ID


@dataclass(frozen=True)
class DialPeerSummaryMissingRule(DiscoveryPlannerRule):
    """Recommend dial-peer summary when routing evidence is missing."""

    id: str = "dial_peer_summary_missing"
    title: str = "Dial-peer summary missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _cube_playbook_case(case) or DIAL_PEER_SUMMARY_COMMAND in collected_commands(case):
            return None
        return DiscoveryRequest(
            request_id=_request_id(self.id),
            command=DIAL_PEER_SUMMARY_COMMAND,
            vendor="cisco",
            priority=DiscoveryPriority.CRITICAL,
            reason="Outbound routing has not yet been verified.",
            estimated_confidence_gain=18.0,
            estimated_minutes=1,
            related_hypotheses=related_hypothesis_titles(
                case,
                keywords=("routing", "dial", "404", "peer"),
            ),
            already_collected=False,
            optional=False,
        )


@dataclass(frozen=True)
class SipUaStatusMissingRule(DiscoveryPlannerRule):
    """Recommend SIP-UA status when registration evidence is missing."""

    id: str = "sip_ua_status_missing"
    title: str = "SIP-UA status missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _cube_playbook_case(case) or SIP_UA_STATUS_COMMAND in collected_commands(case):
            return None
        return DiscoveryRequest(
            request_id=_request_id(self.id),
            command=SIP_UA_STATUS_COMMAND,
            vendor="cisco",
            priority=DiscoveryPriority.HIGH,
            reason="SIP user agent operational state has not been confirmed.",
            estimated_confidence_gain=15.0,
            estimated_minutes=1,
            related_hypotheses=related_hypothesis_titles(
                case,
                keywords=("sip", "registration", "user agent", "trunk", "provider"),
            ),
            already_collected=False,
            optional=False,
        )


@dataclass(frozen=True)
class VoiceServiceVoipMissingRule(DiscoveryPlannerRule):
    """Recommend running-config voice service evidence when absent."""

    id: str = "voice_service_voip_missing"
    title: str = "Voice service voip config missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _cube_playbook_case(case) or VOICE_SERVICE_VOIP_COMMAND in collected_commands(case):
            return None
        return DiscoveryRequest(
            request_id=_request_id(self.id),
            command=VOICE_SERVICE_VOIP_COMMAND,
            vendor="cisco",
            priority=DiscoveryPriority.HIGH,
            reason="Voice service voip configuration has not been reviewed.",
            estimated_confidence_gain=12.0,
            estimated_minutes=2,
            related_hypotheses=related_hypothesis_titles(
                case,
                keywords=("sip", "user agent", "voice service", "codec"),
            ),
            already_collected=False,
            optional=False,
        )


@dataclass(frozen=True)
class CcsipDebugMissingRule(DiscoveryPlannerRule):
    """Recommend SIP debug trace when signaling evidence is missing."""

    id: str = "ccsip_debug_missing"
    title: str = "SIP debug trace missing"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _cube_playbook_case(case) or CCSIP_DEBUG_COMMAND in collected_commands(case):
            return None
        return DiscoveryRequest(
            request_id=_request_id(self.id),
            command=CCSIP_DEBUG_COMMAND,
            vendor="cisco",
            priority=DiscoveryPriority.MEDIUM,
            reason="SIP response codes and trace markers are not yet available.",
            estimated_confidence_gain=20.0,
            estimated_minutes=3,
            related_hypotheses=related_hypothesis_titles(
                case,
                keywords=("provider", "codec", "503", "488", "404", "trunk"),
            ),
            already_collected=False,
            optional=False,
        )


@dataclass(frozen=True)
class SupplementalDialPeerConfigRule(DiscoveryPlannerRule):
    """Recommend dial-peer running config when routing hypotheses remain uncertain."""

    id: str = "supplemental_dial_peer_config"
    title: str = "Supplemental dial-peer configuration"

    def evaluate(self, case: Case) -> DiscoveryRequest | None:
        if not _cube_playbook_case(case):
            return None
        command = "show run | sec dial-peer"
        if command in collected_commands(case):
            return None
        related = related_hypothesis_titles(
            case,
            keywords=("routing", "dial", "404", "peer"),
        )
        if not related:
            return None
        return DiscoveryRequest(
            request_id=_request_id(self.id),
            command=command,
            vendor="cisco",
            priority=DiscoveryPriority.MEDIUM,
            reason="Dial-peer running configuration can confirm pattern and session targets.",
            estimated_confidence_gain=8.0,
            estimated_minutes=2,
            related_hypotheses=related,
            already_collected=False,
            optional=True,
        )


BUILTIN_DISCOVERY_RULES: tuple[DiscoveryPlannerRule, ...] = (
    DialPeerSummaryMissingRule(),
    SipUaStatusMissingRule(),
    VoiceServiceVoipMissingRule(),
    CcsipDebugMissingRule(),
    SupplementalDialPeerConfigRule(),
)


def register_builtin_rules(registry) -> None:
    """Register built-in discovery planner rules."""
    for rule in BUILTIN_DISCOVERY_RULES:
        registry.register_rule(rule)
    from discovery.teams_planner_rules import register_teams_discovery_rules

    register_teams_discovery_rules(registry)
