"""Cisco ``show sip-ua status`` command parser."""

from __future__ import annotations

import re

from parser.interfaces import CommandParser
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding, ParserResult
from shared.types import JsonDict

COMMAND = "show sip-ua status"
VENDOR = "cisco"
PARSER_VERSION = "1.0.0"

_DETECT_MARKERS: tuple[str, ...] = (
    "sip-ua status",
    "sip user agent",
    "sip-ua status:",
    "voice service voip sip",
)

_REGISTRATION_REGISTERED = "registered"
_REGISTRATION_UNREGISTERED = "unregistered"
_REGISTRATION_FAILED = "failed"
_REGISTRATION_UNKNOWN = "unknown"

_TRANSPORT_UDP = "udp"
_TRANSPORT_TCP = "tcp"
_TRANSPORT_TLS = "tls"
_TRANSPORT_UNKNOWN = "unknown"


class CiscoShowSipUaStatusParser(CommandParser):
    """Parse Cisco IOS / IOS-XE ``show sip-ua status`` CLI output."""

    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION

    def detect(self, raw_text: str, context: ParserContext | None = None) -> bool:
        """Return whether raw output resembles ``show sip-ua status``."""
        if not raw_text or not raw_text.strip():
            return False

        lower = raw_text.lower()
        if any(marker in lower for marker in _DETECT_MARKERS):
            return True

        if re.search(r"\bshow\s+sip-ua\s+status\b", lower):
            return True

        return False

    def parse(self, raw_text: str, context: ParserContext) -> ParserResult:
        """Parse raw CLI output into a structured ``ParserResult``."""
        raw_status_lines = _extract_status_lines(raw_text)
        structured_data = self._build_structured_data(raw_text, raw_status_lines)
        errors = self.validate(structured_data)
        warnings = self._collect_warnings(structured_data)
        findings = self.extract_findings(structured_data, context)
        metadata = self.extract_metadata(structured_data, context)

        hostname = _extract_hostname(raw_text) or context.hostname
        confidence = _calculate_confidence(structured_data, errors)

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
            confidence=confidence,
        )

    def validate(self, structured_data: JsonDict) -> list[str]:
        """Return blocking validation errors for structured parse output."""
        errors: list[str] = []
        if not structured_data.get("raw_status_lines"):
            errors.append("no SIP-UA status lines found in output")
        return errors

    def extract_findings(
        self,
        structured_data: JsonDict,
        context: ParserContext,
    ) -> list[ParserFinding]:
        """Derive investigation signals from structured SIP-UA status data."""
        findings: list[ParserFinding] = []
        sip_ua_enabled = structured_data.get("sip_ua_enabled")

        if sip_ua_enabled is True:
            findings.append(
                ParserFinding(
                    signal="sip_ua_enabled",
                    confidence=95.0,
                    detail="SIP user agent is enabled",
                    source_field="sip_ua_enabled",
                )
            )
        elif sip_ua_enabled is False:
            findings.append(
                ParserFinding(
                    signal="sip_ua_disabled",
                    confidence=95.0,
                    detail="SIP user agent is disabled",
                    source_field="sip_ua_enabled",
                )
            )

        registration_state = structured_data.get("registration_state", _REGISTRATION_UNKNOWN)
        if registration_state == _REGISTRATION_REGISTERED:
            findings.append(
                ParserFinding(
                    signal="sip_registration_present",
                    confidence=92.0,
                    detail="SIP registration is present",
                    source_field="registration_state",
                )
            )
        elif registration_state in {_REGISTRATION_UNREGISTERED, _REGISTRATION_FAILED}:
            findings.append(
                ParserFinding(
                    signal="sip_registration_issue",
                    confidence=90.0,
                    detail=f"SIP registration state: {registration_state}",
                    source_field="registration_state",
                )
            )

        if structured_data.get("registrar_present"):
            findings.append(
                ParserFinding(
                    signal="sip_registrar_present",
                    confidence=88.0,
                    detail="Registrar configuration detected",
                    source_field="registrar_present",
                )
            )

        if structured_data.get("transport") == _TRANSPORT_TLS:
            findings.append(
                ParserFinding(
                    signal="sip_transport_tls_detected",
                    confidence=90.0,
                    detail="TLS transport detected for SIP-UA",
                    source_field="transport",
                )
            )

        return findings

    def extract_metadata(
        self,
        structured_data: JsonDict,
        context: ParserContext,
    ) -> JsonDict:
        """Derive collection metadata from structured SIP-UA status data."""
        return {
            "vendor": self.vendor,
            "command": self.command,
            "case_id": context.case_id,
            "device_id": context.device_id,
            "sip_ua_enabled": structured_data.get("sip_ua_enabled"),
            "registration_state": structured_data.get("registration_state"),
            "registrar_host": structured_data.get("registrar_host"),
            "transport": structured_data.get("transport"),
        }

    def _build_structured_data(self, raw_text: str, raw_status_lines: list[str]) -> JsonDict:
        lower = raw_text.lower()
        combined = "\n".join(raw_status_lines).lower()

        return {
            "sip_ua_enabled": _parse_sip_ua_enabled(lower, combined),
            "registration_state": _parse_registration_state(lower, combined),
            "registrar_present": _parse_registrar_present(lower, combined),
            "registrar_host": _parse_registrar_host(raw_text),
            "transport": _parse_transport(lower, combined),
            "raw_status_lines": raw_status_lines,
        }

    def _collect_warnings(self, structured_data: JsonDict) -> list[str]:
        warnings: list[str] = []
        if structured_data.get("sip_ua_enabled") is None:
            warnings.append("could not determine SIP-UA enabled state")
        if structured_data.get("registration_state") == _REGISTRATION_UNKNOWN:
            if structured_data.get("registrar_present"):
                warnings.append("registrar present but registration state is unknown")
        if structured_data.get("transport") == _TRANSPORT_UNKNOWN:
            warnings.append("transport type not identified")
        return warnings


def _extract_status_lines(raw_text: str) -> list[str]:
    lines: list[str] = []
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^\S+#\s*show\s+sip-ua\s+status", stripped, re.IGNORECASE):
            continue
        lines.append(stripped)
    return lines


def _extract_hostname(raw_text: str) -> str | None:
    for line in raw_text.splitlines():
        match = re.match(r"^(\S+)#\s*show\s+sip-ua\s+status", line.strip(), re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def _parse_sip_ua_enabled(lower_text: str, combined: str) -> bool | None:
    if re.search(r"sip-ua\s+status:\s*enabled", combined):
        return True
    if re.search(r"sip\s+user\s+agent\s+status:\s*enabled", combined):
        return True
    if re.search(r"sip-ua\s+status:\s*disabled", combined):
        return False
    if "sip user agent is not enabled" in combined:
        return False
    if "voice service voip sip is administratively down" in combined:
        return False
    if re.search(r"\badministratively\s+down\b", combined) and "sip" in combined:
        return False
    return None


def _parse_registration_state(lower_text: str, combined: str) -> str:
    if "unregistered" in combined:
        return _REGISTRATION_UNREGISTERED
    if "registration failed" in combined or re.search(r"\bregistration:\s*failed\b", combined):
        return _REGISTRATION_FAILED
    if re.search(r"\bfailed\b", combined) and "registr" in combined:
        return _REGISTRATION_FAILED
    if re.search(r"\bregistered\b", combined):
        return _REGISTRATION_REGISTERED
    return _REGISTRATION_UNKNOWN


def _parse_registrar_present(lower_text: str, combined: str) -> bool:
    return "registrar" in combined


def _parse_registrar_host(raw_text: str) -> str | None:
    patterns = (
        r"registrar\s+host:\s*(\S+)",
        r"registrar:\s*(\S+)",
    )
    for line in raw_text.splitlines():
        lower_line = line.lower()
        for pattern in patterns:
            match = re.search(pattern, lower_line, re.IGNORECASE)
            if match:
                return match.group(1).strip()
    return None


def _parse_transport(lower_text: str, combined: str) -> str:
    if re.search(r"transport(?:\s+type)?:\s*tls\b", combined):
        return _TRANSPORT_TLS
    if re.search(r"transport(?:\s+type)?:\s*tcp\b", combined):
        return _TRANSPORT_TCP
    if re.search(r"transport(?:\s+type)?:\s*udp\b", combined):
        return _TRANSPORT_UDP
    if re.search(r"\btls\b", combined) and "transport" in combined:
        return _TRANSPORT_TLS
    if re.search(r"\btcp\b", combined) and "transport" in combined:
        return _TRANSPORT_TCP
    if re.search(r"\budp\b", combined) and "transport" in combined:
        return _TRANSPORT_UDP
    return _TRANSPORT_UNKNOWN


def _calculate_confidence(structured_data: JsonDict, errors: list[str]) -> float:
    if errors:
        return 0.0

    score = 50.0
    if structured_data.get("sip_ua_enabled") is not None:
        score += 20.0
    if structured_data.get("registration_state") != _REGISTRATION_UNKNOWN:
        score += 10.0
    if structured_data.get("registrar_present"):
        score += 10.0
    if structured_data.get("transport") != _TRANSPORT_UNKNOWN:
        score += 10.0
    return min(score, 100.0)
