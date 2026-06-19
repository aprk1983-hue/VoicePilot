"""Cisco ``debug ccsip messages`` lightweight parser."""

from __future__ import annotations

import re

from parser.interfaces import CommandParser
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding, ParserResult
from shared.types import JsonDict

COMMAND = "debug ccsip messages"
VENDOR = "cisco"
PARSER_VERSION = "1.0.0"

_DETECT_MARKERS: tuple[str, ...] = (
    "debug ccsip",
    "ccsipdisplaymsg",
    "ccsip displaymsg",
    "/sip/msg/ccsip",
    "sip/msg/ccsip",
)

_RESPONSE_CODE_FINDINGS: dict[int, str] = {
    403: "sip_403_detected",
    404: "sip_404_detected",
    408: "sip_408_detected",
    488: "sip_488_detected",
    503: "sip_503_detected",
}

_SIP_RESPONSE_RE = re.compile(r"SIP/2\.0\s+(\d{3})\s*(.*)", re.IGNORECASE)
_CALL_ID_RE = re.compile(r"^Call-ID:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
_FROM_RE = re.compile(r"^From:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
_TO_RE = re.compile(r"^To:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
_CSEQ_RE = re.compile(r"^CSeq:\s*\d+\s+(\w+)", re.IGNORECASE | re.MULTILINE)


class CiscoDebugCcsipMessagesParser(CommandParser):
    """Lightweight parser for Cisco ``debug ccsip messages`` SIP trace output."""

    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION

    def detect(self, raw_text: str, context: ParserContext | None = None) -> bool:
        """Return whether raw output resembles ``debug ccsip messages``."""
        if not raw_text or not raw_text.strip():
            return False

        lower = raw_text.lower()
        if any(marker in lower for marker in _DETECT_MARKERS):
            return True

        if _SIP_RESPONSE_RE.search(raw_text):
            return True

        if "from:" in lower and "call-id:" in lower:
            return True

        if re.search(r"\binvite\b", raw_text) and "sip/" in lower:
            return True

        return False

    def parse(self, raw_text: str, context: ParserContext) -> ParserResult:
        """Parse raw CLI output into a structured ``ParserResult``."""
        structured_data = self._build_structured_data(raw_text)
        errors = self.validate(structured_data)
        warnings = self._collect_warnings(structured_data)
        findings = self.extract_findings(structured_data, context)
        metadata = self.extract_metadata(structured_data, context)
        confidence = _calculate_confidence(structured_data, errors)

        return ParserResult(
            command=self.command,
            hostname=_extract_hostname(raw_text) or context.hostname,
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
        has_content = (
            structured_data.get("sip_trace_present")
            or structured_data.get("response_codes")
            or structured_data.get("call_ids")
            or structured_data.get("has_invite")
            or structured_data.get("has_bye")
            or structured_data.get("has_cancel")
        )
        if not has_content:
            errors.append("no recognizable SIP trace or response content found")
        return errors

    def extract_findings(
        self,
        structured_data: JsonDict,
        context: ParserContext,
    ) -> list[ParserFinding]:
        """Derive investigation signals from structured CCSIP debug data."""
        findings: list[ParserFinding] = []

        if structured_data.get("sip_trace_present"):
            findings.append(
                ParserFinding(
                    signal="sip_trace_present",
                    confidence=92.0,
                    detail="SIP message trace markers detected",
                    source_field="sip_trace_present",
                )
            )

        for code in structured_data.get("response_codes", []):
            signal = _RESPONSE_CODE_FINDINGS.get(code)
            if signal is None:
                continue
            phrase = _phrase_for_code(structured_data, code)
            findings.append(
                ParserFinding(
                    signal=signal,
                    confidence=94.0,
                    detail=f"SIP response {code}" + (f" {phrase}" if phrase else ""),
                    source_field="response_codes",
                )
            )

        if structured_data.get("call_ids"):
            findings.append(
                ParserFinding(
                    signal="sip_call_id_present",
                    confidence=90.0,
                    detail="Call-ID header detected in SIP trace",
                    source_field="call_ids",
                )
            )

        if structured_data.get("has_invite"):
            findings.append(
                ParserFinding(
                    signal="sip_invite_present",
                    confidence=88.0,
                    detail="INVITE method detected in SIP trace",
                    source_field="has_invite",
                )
            )

        if structured_data.get("has_bye"):
            findings.append(
                ParserFinding(
                    signal="sip_bye_present",
                    confidence=88.0,
                    detail="BYE method detected in SIP trace",
                    source_field="has_bye",
                )
            )

        if structured_data.get("has_cancel"):
            findings.append(
                ParserFinding(
                    signal="sip_cancel_present",
                    confidence=88.0,
                    detail="CANCEL method detected in SIP trace",
                    source_field="has_cancel",
                )
            )

        return findings

    def extract_metadata(
        self,
        structured_data: JsonDict,
        context: ParserContext,
    ) -> JsonDict:
        """Derive collection metadata from structured CCSIP debug data."""
        return {
            "vendor": self.vendor,
            "command": self.command,
            "case_id": context.case_id,
            "device_id": context.device_id,
            "response_codes": list(structured_data.get("response_codes", [])),
            "call_id_count": len(structured_data.get("call_ids", [])),
            "sip_trace_present": structured_data.get("sip_trace_present"),
        }

    def _build_structured_data(self, raw_text: str) -> JsonDict:
        response_codes, response_phrases = _parse_response_lines(raw_text)
        call_ids = _unique_preserve_order(_CALL_ID_RE.findall(raw_text))
        from_headers = _unique_preserve_order(_FROM_RE.findall(raw_text))
        to_headers = _unique_preserve_order(_TO_RE.findall(raw_text))
        cseq_methods = _unique_preserve_order(_CSEQ_RE.findall(raw_text))

        has_invite = _has_sip_method(raw_text, "INVITE", cseq_methods)
        has_bye = _has_sip_method(raw_text, "BYE", cseq_methods)
        has_cancel = _has_sip_method(raw_text, "CANCEL", cseq_methods)
        has_ack = _has_sip_method(raw_text, "ACK", cseq_methods)
        sip_trace_present = _detect_sip_trace(from_headers, to_headers, call_ids, raw_text)

        return {
            "sip_trace_present": sip_trace_present,
            "response_codes": response_codes,
            "response_phrases": response_phrases,
            "call_ids": call_ids,
            "from_headers": from_headers,
            "to_headers": to_headers,
            "cseq_methods": cseq_methods,
            "has_invite": has_invite,
            "has_bye": has_bye,
            "has_cancel": has_cancel,
            "has_ack": has_ack,
        }

    def _collect_warnings(self, structured_data: JsonDict) -> list[str]:
        warnings: list[str] = []
        if structured_data.get("response_codes") and not structured_data.get("sip_trace_present"):
            warnings.append("response codes found without full SIP trace headers")
        if structured_data.get("sip_trace_present") and not structured_data.get("call_ids"):
            warnings.append("SIP trace markers present but no Call-ID extracted")
        return warnings


def _parse_response_lines(raw_text: str) -> tuple[list[int], list[str]]:
    codes: list[int] = []
    phrases: list[str] = []
    seen_codes: set[int] = set()

    for match in _SIP_RESPONSE_RE.finditer(raw_text):
        code = int(match.group(1))
        phrase = match.group(2).strip()
        if code not in seen_codes:
            seen_codes.add(code)
            codes.append(code)
            phrases.append(phrase)
    return codes, phrases


def _detect_sip_trace(
    from_headers: list[str],
    to_headers: list[str],
    call_ids: list[str],
    raw_text: str,
) -> bool:
    lower = raw_text.lower()
    if from_headers and to_headers and call_ids:
        return True
    if "from:" in lower and "to:" in lower and "call-id:" in lower:
        return True
    if "/sip/msg/ccsip" in lower or "ccsipdisplaymsg" in lower.replace(" ", ""):
        return True
    return False


def _has_sip_method(raw_text: str, method: str, cseq_methods: list[str]) -> bool:
    if any(item.upper() == method for item in cseq_methods):
        return True
    return bool(re.search(rf"\b{method}\b", raw_text))


def _phrase_for_code(structured_data: JsonDict, code: int) -> str | None:
    codes = structured_data.get("response_codes", [])
    phrases = structured_data.get("response_phrases", [])
    try:
        index = codes.index(code)
    except ValueError:
        return None
    if index < len(phrases):
        return phrases[index] or None
    return None


def _extract_hostname(raw_text: str) -> str | None:
    for line in raw_text.splitlines():
        match = re.match(r"^(\S+)#\s*debug\s+ccsip\s+messages", line.strip(), re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        cleaned = value.strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        unique.append(cleaned)
    return unique


def _calculate_confidence(structured_data: JsonDict, errors: list[str]) -> float:
    if errors:
        return 0.0

    score = 40.0
    if structured_data.get("sip_trace_present"):
        score += 20.0
    if structured_data.get("response_codes"):
        score += 20.0
    if structured_data.get("call_ids"):
        score += 10.0
    if structured_data.get("has_invite") or structured_data.get("has_bye"):
        score += 10.0
    return min(score, 100.0)
