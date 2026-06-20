"""Cisco ``show run | sec voice service voip`` command parser."""

from __future__ import annotations

import re

from model.voice_service import VoiceService
from parser.interfaces import CommandParser
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding, ParserResult
from shared.types import JsonDict

COMMAND = "show run | sec voice service voip"
VENDOR = "cisco"
PARSER_ID = "cisco_show_run_voice_service_voip"
PARSER_VERSION = "1.0.0"

_DETECT_MARKERS: tuple[str, ...] = (
    "voice service voip",
    "bind control source-interface",
    "bind media source-interface",
    "allow-connections sip to sip",
    "no supplementary-service sip moved-temporarily",
    "no supplementary-service sip refer",
    "options-ping",
    "show run | sec voice service voip",
)

_BIND_CONTROL_RE = re.compile(
    r"bind\s+control\s+source-interface\s+(\S+)",
    re.IGNORECASE,
)
_BIND_MEDIA_RE = re.compile(
    r"bind\s+media\s+source-interface\s+(\S+)",
    re.IGNORECASE,
)
_TRUSTED_IPV4_RE = re.compile(
    r"ipv4\s+(\S+)\s+(\S+)",
    re.IGNORECASE,
)
_NO_SUPPLEMENTARY_MOVED_RE = re.compile(
    r"no\s+supplementary-service\s+sip\s+moved-temporarily",
    re.IGNORECASE,
)
_NO_SUPPLEMENTARY_REFER_RE = re.compile(
    r"no\s+supplementary-service\s+sip\s+refer",
    re.IGNORECASE,
)
_NO_SIP_RE = re.compile(r"^\s*no\s+sip\b", re.IGNORECASE | re.MULTILINE)
_NO_VOICE_SERVICE_VOIP_RE = re.compile(
    r"^no\s+voice\s+service\s+voip\b",
    re.IGNORECASE | re.MULTILINE,
)


class CiscoShowRunVoiceServiceVoipParser(CommandParser):
    """Parse Cisco running-config voice service voip section output."""

    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION

    def detect(self, raw_text: str, context: ParserContext | None = None) -> bool:
        """Return whether raw output resembles voice service voip config."""
        if not raw_text or not raw_text.strip():
            return False

        lower = raw_text.lower()
        if "sip-ua status:" in lower and "bind control source-interface" not in lower:
            return False

        if any(marker in lower for marker in _DETECT_MARKERS):
            return True

        if re.search(r"\bshow\s+run\s*\|\s*sec\s+voice\s+service\s+voip\b", lower):
            return True

        return False

    def parse(self, raw_text: str, context: ParserContext) -> ParserResult:
        """Parse raw CLI output into a structured ``ParserResult``."""
        raw_voice_service_lines = _extract_voice_service_lines(raw_text)
        structured_data = self._build_structured_data(raw_text, raw_voice_service_lines)
        errors = self.validate(structured_data)
        warnings = self._collect_warnings(structured_data)
        findings = self.extract_findings(structured_data, context)
        metadata = self.extract_metadata(structured_data, context)
        confidence = _calculate_confidence(structured_data, errors)
        hostname = _extract_hostname(raw_text) or context.hostname
        voice_objects = (
            self.extract_voice_objects(
                structured_data,
                context,
                hostname=hostname,
                confidence=confidence,
            )
            if not errors
            else []
        )

        return ParserResult(
            command=self.command,
            hostname=hostname,
            platform=context.platform,
            ios_version=context.ios_version,
            parser_version=self.parser_version,
            warnings=warnings,
            errors=errors,
            metadata=metadata,
            structured_data=structured_data,
            findings=findings,
            voice_objects=voice_objects,
            confidence=confidence,
        )

    def validate(self, structured_data: JsonDict) -> list[str]:
        """Return blocking validation errors for structured parse output."""
        errors: list[str] = []
        if not structured_data.get("raw_voice_service_lines"):
            errors.append("no voice service voip configuration lines found")
        return errors

    def extract_findings(
        self,
        structured_data: JsonDict,
        context: ParserContext,
    ) -> list[ParserFinding]:
        """Derive investigation signals from voice service voip config data."""
        findings: list[ParserFinding] = []

        if structured_data.get("voice_service_voip_present"):
            findings.append(
                ParserFinding(
                    signal="voice_service_voip_present",
                    confidence=95.0,
                    detail="voice service voip configuration present",
                    source_field="voice_service_voip_present",
                )
            )

        if structured_data.get("sip_section_present"):
            findings.append(
                ParserFinding(
                    signal="sip_section_present",
                    confidence=93.0,
                    detail="sip subsection present under voice service voip",
                    source_field="sip_section_present",
                )
            )

        sip_disabled = structured_data.get("sip_ua_disabled_by_config")
        if sip_disabled is True:
            findings.append(
                ParserFinding(
                    signal="sip_ua_disabled_by_config",
                    confidence=94.0,
                    detail="SIP user agent disabled by configuration",
                    source_field="sip_ua_disabled_by_config",
                )
            )

        if structured_data.get("bind_control_interface"):
            findings.append(
                ParserFinding(
                    signal="sip_bind_control_present",
                    confidence=90.0,
                    detail="bind control source-interface configured",
                    source_field="bind_control_interface",
                )
            )

        if structured_data.get("bind_media_interface"):
            findings.append(
                ParserFinding(
                    signal="sip_bind_media_present",
                    confidence=90.0,
                    detail="bind media source-interface configured",
                    source_field="bind_media_interface",
                )
            )

        if structured_data.get("trusted_ip_list_present"):
            findings.append(
                ParserFinding(
                    signal="trusted_ip_list_present",
                    confidence=88.0,
                    detail="ip address trusted list configured",
                    source_field="trusted_ip_list_present",
                )
            )

        if structured_data.get("allow_connections_sip_to_sip"):
            findings.append(
                ParserFinding(
                    signal="allow_connections_sip_to_sip_present",
                    confidence=88.0,
                    detail="allow-connections sip to sip configured",
                    source_field="allow_connections_sip_to_sip",
                )
            )

        if structured_data.get("early_offer_forced"):
            findings.append(
                ParserFinding(
                    signal="early_offer_forced",
                    confidence=86.0,
                    detail="forced early offer configuration detected",
                    source_field="early_offer_forced",
                )
            )

        if structured_data.get("options_ping_present"):
            findings.append(
                ParserFinding(
                    signal="options_ping_present",
                    confidence=86.0,
                    detail="options-ping configured under sip",
                    source_field="options_ping_present",
                )
            )

        return findings

    def extract_voice_objects(
        self,
        structured_data: JsonDict,
        context: ParserContext,
        *,
        hostname: str | None,
        confidence: float,
    ) -> list[VoiceService]:
        """Build canonical VoiceService object from structured config data."""
        supplementary = structured_data.get("supplementary_services")
        supplementary_tuple: tuple[str, ...] = ()
        if isinstance(supplementary, list):
            supplementary_tuple = tuple(str(item) for item in supplementary)

        trusted_ips = structured_data.get("trusted_ips")
        trusted_tuple: tuple[str, ...] = ()
        if isinstance(trusted_ips, list):
            trusted_tuple = tuple(str(item) for item in trusted_ips)

        voice_service = VoiceService.create(
            vendor=context.vendor,
            platform=context.platform or "unknown",
            hostname=hostname or context.hostname or "unknown",
            source_parser=PARSER_ID,
            source_command=self.command,
            source_evidence_id=context.evidence_id or "",
            allow_connections=structured_data.get("allow_connections_sip_to_sip"),
            bind_control=structured_data.get("bind_control_interface"),
            bind_media=structured_data.get("bind_media_interface"),
            trusted_ips=trusted_tuple,
            early_offer=structured_data.get("early_offer_forced"),
            options_ping=structured_data.get("options_ping_present"),
            supplementary_services=supplementary_tuple,
            confidence=confidence,
            metadata={
                "sip_ua_disabled_by_config": structured_data.get("sip_ua_disabled_by_config"),
                "sip_section_present": structured_data.get("sip_section_present"),
            },
        )
        return [voice_service]

    def extract_metadata(
        self,
        structured_data: JsonDict,
        context: ParserContext,
    ) -> JsonDict:
        """Derive collection metadata from voice service voip config data."""
        return {
            "vendor": self.vendor,
            "command": self.command,
            "case_id": context.case_id,
            "device_id": context.device_id,
            "voice_service_voip_present": structured_data.get("voice_service_voip_present"),
            "sip_ua_disabled_by_config": structured_data.get("sip_ua_disabled_by_config"),
            "bind_control_interface": structured_data.get("bind_control_interface"),
            "bind_media_interface": structured_data.get("bind_media_interface"),
        }

    def _build_structured_data(self, raw_text: str, raw_voice_service_lines: list[str]) -> JsonDict:
        combined = "\n".join(raw_voice_service_lines)
        lower = combined.lower()

        voice_service_voip_present = "voice service voip" in lower
        sip_section_present = _sip_section_present(raw_voice_service_lines)
        sip_ua_disabled_by_config = _parse_sip_ua_disabled_by_config(lower, sip_section_present)

        bind_control_match = _BIND_CONTROL_RE.search(combined)
        bind_media_match = _BIND_MEDIA_RE.search(combined)
        trusted_ips = _parse_trusted_ips(combined)
        supplementary_services = _parse_supplementary_services(combined)

        return {
            "voice_service_voip_present": voice_service_voip_present,
            "sip_section_present": sip_section_present,
            "sip_ua_disabled_by_config": sip_ua_disabled_by_config,
            "bind_control_interface": bind_control_match.group(1) if bind_control_match else None,
            "bind_media_interface": bind_media_match.group(1) if bind_media_match else None,
            "trusted_ip_list_present": bool(trusted_ips),
            "trusted_ips": trusted_ips,
            "allow_connections_sip_to_sip": (
                True if "allow-connections sip to sip" in lower else None
            ),
            "early_offer_forced": (
                True if "forced" in lower and "early-offer" in lower else None
            ),
            "options_ping_present": True if "options-ping" in lower else None,
            "supplementary_services": supplementary_services,
            "raw_voice_service_lines": raw_voice_service_lines,
        }

    def _collect_warnings(self, structured_data: JsonDict) -> list[str]:
        warnings: list[str] = []
        if structured_data.get("voice_service_voip_present") and not structured_data.get(
            "sip_section_present"
        ):
            if structured_data.get("sip_ua_disabled_by_config") is not True:
                warnings.append("voice service voip present without sip subsection")
        if structured_data.get("sip_ua_disabled_by_config") is None:
            warnings.append("could not determine SIP-UA disabled state from configuration")
        return warnings


def _extract_voice_service_lines(raw_text: str) -> list[str]:
    lines: list[str] = []
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(
            r"^\S+#\s*show\s+run\s*\|\s*sec\s+voice\s+service\s+voip",
            stripped,
            re.IGNORECASE,
        ):
            continue
        lines.append(stripped)
    return lines


def _extract_hostname(raw_text: str) -> str | None:
    for line in raw_text.splitlines():
        match = re.match(
            r"^(\S+)#\s*show\s+run\s*\|\s*sec\s+voice\s+service\s+voip",
            line.strip(),
            re.IGNORECASE,
        )
        if match:
            return match.group(1)
    return None


def _sip_section_present(lines: list[str]) -> bool:
    for line in lines:
        if re.match(r"^sip\s*$", line, re.IGNORECASE):
            return True
        if re.match(r"^\s+sip\s*$", line, re.IGNORECASE):
            return True
    return False


def _parse_sip_ua_disabled_by_config(lower_text: str, sip_section_present: bool) -> bool | None:
    if "voice service voip" not in lower_text:
        return None
    if _NO_VOICE_SERVICE_VOIP_RE.search(lower_text):
        return True
    if _NO_SIP_RE.search(lower_text):
        return True
    if sip_section_present:
        return False
    return None


def _calculate_confidence(structured_data: JsonDict, errors: list[str]) -> float:
    if errors:
        return 0.0

    score = 40.0
    if structured_data.get("voice_service_voip_present"):
        score += 20.0
    if structured_data.get("sip_section_present"):
        score += 15.0
    if structured_data.get("sip_ua_disabled_by_config") is not None:
        score += 10.0
    if structured_data.get("bind_control_interface") or structured_data.get("bind_media_interface"):
        score += 10.0
    if structured_data.get("trusted_ip_list_present"):
        score += 5.0
    if structured_data.get("supplementary_services"):
        score += 5.0
    return min(score, 100.0)


def _parse_trusted_ips(combined: str) -> list[str]:
    trusted_ips: list[str] = []
    for match in _TRUSTED_IPV4_RE.finditer(combined):
        trusted_ips.append(f"{match.group(1)} {match.group(2)}")
    return trusted_ips


def _parse_supplementary_services(combined: str) -> list[str]:
    services: list[str] = []
    if _NO_SUPPLEMENTARY_MOVED_RE.search(combined):
        services.append("no supplementary-service sip moved-temporarily")
    if _NO_SUPPLEMENTARY_REFER_RE.search(combined):
        services.append("no supplementary-service sip refer")
    return services
