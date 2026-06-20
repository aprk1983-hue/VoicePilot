"""Cisco ``show dial-peer voice summary`` command parser."""

from __future__ import annotations

import re

from model.dial_peer import DialPeer
from parser.interfaces import CommandParser
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding, ParserResult
from shared.types import JsonDict

COMMAND = "show dial-peer voice summary"
VENDOR = "cisco"
PARSER_ID = "cisco_show_dial_peer_voice_summary"
PARSER_VERSION = "1.0.0"

_DETECT_MARKERS: tuple[str, ...] = (
    "dial-peer",
    "destination-pattern",
    "peer tag",
    "show dial-peer voice summary",
)

_DIAL_PEER_LINE_RE = re.compile(
    r"^dial-peer\s+(\d+)\s+(voip|pots)\s+(.+)$",
    re.IGNORECASE,
)
_DESTINATION_PATTERN_RE = re.compile(
    r"destination-pattern\s+(\S+)",
    re.IGNORECASE,
)
_SESSION_TARGET_RE = re.compile(
    r"session[- ]target\s+(\S+)",
    re.IGNORECASE,
)
_EMPTY_SUMMARY_MARKERS: tuple[str, ...] = (
    "no dial peers",
    "no voip dial peers",
    "no matching dial peers",
)


class CiscoShowDialPeerVoiceSummaryParser(CommandParser):
    """Parse Cisco IOS / IOS-XE / CUBE ``show dial-peer voice summary`` output."""

    vendor = VENDOR
    command = COMMAND
    parser_version = PARSER_VERSION

    def detect(self, raw_text: str, context: ParserContext | None = None) -> bool:
        """Return whether raw output resembles ``show dial-peer voice summary``."""
        if not raw_text or not raw_text.strip():
            return False

        lower = raw_text.lower()
        if any(marker in lower for marker in _DETECT_MARKERS):
            return True

        if re.search(r"\bshow\s+dial-peer\s+voice\s+summary\b", lower):
            return True

        return False

    def parse(self, raw_text: str, context: ParserContext) -> ParserResult:
        """Parse raw CLI output into a structured ``ParserResult``."""
        raw_dial_peer_lines = _extract_dial_peer_lines(raw_text)
        structured_data = self._build_structured_data(raw_text, raw_dial_peer_lines)
        errors = self.validate(structured_data)
        warnings = self._collect_warnings(structured_data)
        findings = self.extract_findings(structured_data, context)
        metadata = self.extract_metadata(structured_data, context)
        confidence = _calculate_confidence(structured_data, errors)
        hostname = _extract_hostname(raw_text) or context.hostname
        voice_objects = self.extract_voice_objects(
            structured_data,
            context,
            hostname=hostname,
            confidence=confidence,
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
        return []

    def extract_findings(
        self,
        structured_data: JsonDict,
        context: ParserContext,
    ) -> list[ParserFinding]:
        """Derive investigation signals from structured dial-peer summary data."""
        findings: list[ParserFinding] = []

        if structured_data.get("dial_peer_summary_missing_or_empty"):
            findings.append(
                ParserFinding(
                    signal="dial_peer_summary_missing_or_empty",
                    confidence=92.0,
                    detail="Dial-peer voice summary is missing or empty",
                    source_field="dial_peer_summary_missing_or_empty",
                )
            )

        if structured_data.get("dial_peer_summary_present"):
            findings.append(
                ParserFinding(
                    signal="dial_peer_summary_present",
                    confidence=94.0,
                    detail="Dial-peer voice summary output detected",
                    source_field="dial_peer_summary_present",
                )
            )

        if structured_data.get("dial_peer_config_present"):
            findings.append(
                ParserFinding(
                    signal="dial_peer_config_present",
                    confidence=93.0,
                    detail="Dial-peer configuration entries detected",
                    source_field="dial_peer_config_present",
                )
            )

        if structured_data.get("down_dial_peer_count", 0) > 0:
            findings.append(
                ParserFinding(
                    signal="dial_peer_down",
                    confidence=91.0,
                    detail=(
                        f"{structured_data['down_dial_peer_count']} dial-peer(s) in down state"
                    ),
                    source_field="down_dial_peer_count",
                )
            )

        if structured_data.get("out_of_service_count", 0) > 0:
            findings.append(
                ParserFinding(
                    signal="dial_peer_out_of_service",
                    confidence=91.0,
                    detail=(
                        f"{structured_data['out_of_service_count']} dial-peer(s) out of service"
                    ),
                    source_field="out_of_service_count",
                )
            )

        if structured_data.get("outbound_dial_peer_candidates_present"):
            findings.append(
                ParserFinding(
                    signal="outbound_dial_peer_candidates_present",
                    confidence=89.0,
                    detail="Outbound VoIP dial-peer candidates with destination patterns detected",
                    source_field="outbound_dial_peer_candidates_present",
                )
            )

        if structured_data.get("session_targets"):
            findings.append(
                ParserFinding(
                    signal="session_target_present",
                    confidence=88.0,
                    detail="Session target configuration detected",
                    source_field="session_targets",
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
    ) -> list[DialPeer]:
        """Build canonical DialPeer objects from parsed dial-peer summary data."""
        parsed_peers = structured_data.get("parsed_dial_peers")
        if not isinstance(parsed_peers, list):
            return []

        dial_peers: list[DialPeer] = []
        for peer in parsed_peers:
            if not isinstance(peer, dict):
                continue

            status = peer.get("status")
            shutdown: bool | None = None
            if status in {"down", "out_of_service"}:
                shutdown = True
            elif status == "up":
                shutdown = False

            peer_type = peer.get("type") or "unknown"
            tag = peer.get("tag")
            raw_line = peer.get("raw_line")

            dial_peers.append(
                DialPeer.create(
                    vendor=context.vendor,
                    platform=context.platform or "unknown",
                    hostname=hostname or context.hostname or "unknown",
                    source_parser=PARSER_ID,
                    source_command=self.command,
                    source_evidence_id=context.evidence_id or "",
                    tag=tag,
                    peer_type=peer_type,
                    destination_pattern=peer.get("destination_pattern"),
                    session_target=peer.get("session_target"),
                    shutdown=shutdown,
                    status=status,
                    confidence=confidence,
                    metadata={"raw_line": raw_line} if raw_line else {},
                )
            )

        return dial_peers

    def extract_metadata(
        self,
        structured_data: JsonDict,
        context: ParserContext,
    ) -> JsonDict:
        """Derive collection metadata from structured dial-peer summary data."""
        return {
            "vendor": self.vendor,
            "command": self.command,
            "case_id": context.case_id,
            "device_id": context.device_id,
            "dial_peer_count": structured_data.get("dial_peer_count"),
            "voip_dial_peer_count": structured_data.get("voip_dial_peer_count"),
            "down_dial_peer_count": structured_data.get("down_dial_peer_count"),
        }

    def _build_structured_data(self, raw_text: str, raw_dial_peer_lines: list[str]) -> JsonDict:
        combined = "\n".join(raw_dial_peer_lines)
        lower = combined.lower()
        stripped = raw_text.strip()

        dial_peer_entries = _parse_dial_peer_entries(raw_dial_peer_lines)
        destination_patterns = _unique_preserve_order(_DESTINATION_PATTERN_RE.findall(combined))
        session_targets = _unique_preserve_order(_SESSION_TARGET_RE.findall(combined))

        dial_peer_count = len(dial_peer_entries)
        voip_dial_peer_count = sum(1 for entry in dial_peer_entries if entry["type"] == "voip")
        pots_dial_peer_count = sum(1 for entry in dial_peer_entries if entry["type"] == "pots")
        down_dial_peer_count = sum(1 for entry in dial_peer_entries if entry["status"] == "down")
        out_of_service_count = sum(
            1 for entry in dial_peer_entries if entry["status"] == "out_of_service"
        )

        dial_peer_summary_missing_or_empty = _is_missing_or_empty(stripped, lower, dial_peer_count)
        dial_peer_summary_present = (
            not dial_peer_summary_missing_or_empty
            and (
                dial_peer_count > 0
                or any(marker in lower for marker in _DETECT_MARKERS[:3])
            )
        )
        dial_peer_config_present = dial_peer_count > 0 or bool(destination_patterns) or (
            "dial-peer" in lower or "peer tag" in lower
        )
        outbound_dial_peer_candidates_present = voip_dial_peer_count > 0 and bool(destination_patterns)

        return {
            "dial_peer_summary_present": dial_peer_summary_present,
            "dial_peer_summary_missing_or_empty": dial_peer_summary_missing_or_empty,
            "dial_peer_config_present": dial_peer_config_present,
            "dial_peer_count": dial_peer_count,
            "voip_dial_peer_count": voip_dial_peer_count,
            "pots_dial_peer_count": pots_dial_peer_count,
            "down_dial_peer_count": down_dial_peer_count,
            "out_of_service_count": out_of_service_count,
            "destination_patterns": destination_patterns,
            "session_targets": session_targets,
            "parsed_dial_peers": dial_peer_entries,
            "raw_dial_peer_lines": raw_dial_peer_lines,
            "outbound_dial_peer_candidates_present": outbound_dial_peer_candidates_present,
        }

    def _collect_warnings(self, structured_data: JsonDict) -> list[str]:
        warnings: list[str] = []
        if structured_data.get("dial_peer_summary_present") and structured_data.get("dial_peer_count", 0) == 0:
            warnings.append("summary markers present but no dial-peer entries parsed")
        if structured_data.get("dial_peer_count", 0) > 0 and not structured_data.get("destination_patterns"):
            warnings.append("dial-peers found without destination-pattern values")
        return warnings


def _extract_dial_peer_lines(raw_text: str) -> list[str]:
    lines: list[str] = []
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^\S+#\s*show\s+dial-peer\s+voice\s+summary", stripped, re.IGNORECASE):
            continue
        lines.append(stripped)
    return lines


def _extract_hostname(raw_text: str) -> str | None:
    for line in raw_text.splitlines():
        match = re.match(
            r"^(\S+)#\s*show\s+dial-peer\s+voice\s+summary",
            line.strip(),
            re.IGNORECASE,
        )
        if match:
            return match.group(1)
    return None


def _parse_dial_peer_entries(lines: list[str]) -> list[dict[str, str | None]]:
    entries: list[dict[str, str | None]] = []
    current: dict[str, str | None] | None = None

    for line in lines:
        match = _DIAL_PEER_LINE_RE.match(line)
        if match:
            if current is not None:
                entries.append(current)
            status = _normalize_peer_status(match.group(3))
            current = {
                "tag": match.group(1),
                "type": match.group(2).lower(),
                "status": status,
                "destination_pattern": None,
                "session_target": None,
                "raw_line": line,
            }
            continue

        if current is None:
            continue

        destination_match = _DESTINATION_PATTERN_RE.search(line)
        if destination_match:
            current["destination_pattern"] = destination_match.group(1)

        session_match = _SESSION_TARGET_RE.search(line)
        if session_match:
            current["session_target"] = session_match.group(1)

    if current is not None:
        entries.append(current)

    return entries


def _normalize_peer_status(raw_status: str) -> str:
    status = raw_status.strip().lower()
    if "out of service" in status or "out-of-service" in status:
        return "out_of_service"
    if status.startswith("down"):
        return "down"
    if status.startswith("up"):
        return "up"
    return status.split()[0] if status else "unknown"


def _is_missing_or_empty(stripped_text: str, lower_combined: str, dial_peer_count: int) -> bool:
    if not stripped_text:
        return True
    if len(stripped_text) < 10 and dial_peer_count == 0:
        return True
    if any(marker in lower_combined for marker in _EMPTY_SUMMARY_MARKERS):
        return True
    return dial_peer_count == 0 and "dial-peer" not in lower_combined


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
    if structured_data.get("dial_peer_summary_present"):
        score += 20.0
    if structured_data.get("dial_peer_count", 0) > 0:
        score += 20.0
    if structured_data.get("destination_patterns"):
        score += 10.0
    if structured_data.get("session_targets"):
        score += 10.0
    return min(score, 100.0)
