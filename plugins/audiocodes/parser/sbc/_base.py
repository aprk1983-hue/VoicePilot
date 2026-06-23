"""Base parser utilities for AudioCodes SBC evidence."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from model.voice_graph import VoiceObject
from parser.interfaces import CommandParser
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding, ParserResult
from plugins.audiocodes.parser.sbc._evidence import (
    calculate_record_confidence,
    dedupe_records,
    parse_audiocodes_evidence,
)
from plugins.audiocodes.parser.sbc._helpers import (
    PLATFORM,
    VENDOR,
    default_audiocodes_metadata,
    sbc_hostname,
)
from shared.types import JsonDict


class AudioCodesSbcParser(CommandParser):
    """Shared parse flow for exported AudioCodes SBC evidence."""

    detect_markers: tuple[str, ...] = ()
    identity_fields: tuple[str, ...] = ("name",)
    required_fields: tuple[str, ...] = ("name",)

    def detect(self, raw_text: str, context: ParserContext | None = None) -> bool:
        if not raw_text or not raw_text.strip():
            return False
        lower = raw_text.lower()
        command_token = self.command.replace("-", " ")
        if command_token in lower:
            return True
        return any(marker in lower for marker in self.detect_markers)

    def parse(self, raw_text: str, context: ParserContext) -> ParserResult:
        try:
            evidence_format, records = parse_audiocodes_evidence(raw_text)
        except (ValueError, ET.ParseError) as exc:
            return ParserResult(
                command=self.command,
                hostname=sbc_hostname(context),
                platform=context.platform or PLATFORM,
                parser_version=self.parser_version,
                errors=[str(exc)],
                confidence=0.0,
            )

        identity_field = self.identity_fields[0] if self.identity_fields else "name"
        deduped, dedupe_warnings = dedupe_records(records, identity_field)
        structured_data: JsonDict = {
            "format": evidence_format,
            "records": deduped,
            "record_count": len(deduped),
        }
        errors = self.validate(structured_data)
        warnings = self._collect_warnings(structured_data) + dedupe_warnings
        findings = self.extract_findings(structured_data, context) if not errors else []
        metadata = self.extract_metadata(structured_data, context)
        confidence = self._calculate_confidence(structured_data, errors)
        voice_objects = (
            self.extract_voice_objects(structured_data, context, confidence=confidence)
            if not errors
            else []
        )
        return ParserResult(
            command=self.command,
            hostname=sbc_hostname(context),
            platform=context.platform or PLATFORM,
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
        errors: list[str] = []
        records = structured_data.get("records") or []
        if not records:
            errors.append("no records found in AudioCodes SBC evidence")
            return errors
        for index, record in enumerate(records):
            if not any(record.get(field) not in (None, "") for field in self.required_fields):
                errors.append(
                    f"record {index} missing required fields: {', '.join(self.required_fields)}"
                )
        return errors

    def extract_metadata(
        self,
        structured_data: JsonDict,
        context: ParserContext,
    ) -> JsonDict:
        return default_audiocodes_metadata(self, structured_data, context)

    def extract_findings(
        self,
        structured_data: JsonDict,
        context: ParserContext,
    ) -> list[ParserFinding]:
        return []

    def extract_voice_objects(
        self,
        structured_data: JsonDict,
        context: ParserContext,
        *,
        confidence: float,
    ) -> list[VoiceObject]:
        raise NotImplementedError

    def _collect_warnings(self, structured_data: JsonDict) -> list[str]:
        return []

    def _calculate_confidence(self, structured_data: JsonDict, errors: list[str]) -> float:
        if errors:
            return 0.0
        records = structured_data.get("records") or []
        if not records:
            return 0.0
        scores = [
            calculate_record_confidence(record, self.required_fields)
            for record in records
        ]
        return sum(scores) / len(scores)

    def _records(self, structured_data: JsonDict) -> list[JsonDict]:
        return list(structured_data.get("records") or [])
