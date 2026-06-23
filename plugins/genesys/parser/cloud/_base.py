"""Base parser utilities for Genesys Cloud export evidence."""

from __future__ import annotations

import json

import yaml

from model.voice_graph import VoiceObject
from parser.interfaces import CommandParser
from parser.parser_context import ParserContext
from parser.parser_result import ParserFinding, ParserResult
from plugins.genesys.parser.cloud._evidence import (
    calculate_record_confidence,
    dedupe_records,
    parse_genesys_evidence,
)
from plugins.genesys.parser.cloud._helpers import (
    PLATFORM,
    VENDOR,
    default_genesys_metadata,
    genesys_hostname,
)
from shared.types import JsonDict


class GenesysCloudParser(CommandParser):
    """Shared parse flow for exported Genesys Cloud evidence."""

    detect_markers: tuple[str, ...] = ()
    identity_fields: tuple[str, ...] = ("id", "name")
    required_fields: tuple[str, ...] = ("id", "name")

    def detect(self, raw_text: str, context: ParserContext | None = None) -> bool:
        if not raw_text or not raw_text.strip():
            return False
        lower = raw_text.lower()
        command_token = self.command.replace("-", " ")
        if command_token in lower or self.command in lower:
            return True
        return any(marker in lower for marker in self.detect_markers)

    def parse(self, raw_text: str, context: ParserContext) -> ParserResult:
        try:
            evidence_format, records = parse_genesys_evidence(raw_text)
        except (ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
            return ParserResult(
                command=self.command,
                hostname=genesys_hostname(context),
                platform=context.platform or PLATFORM,
                parser_version=self.parser_version,
                errors=[str(exc)],
                confidence=0.0,
            )

        identity_field = self.identity_fields[0] if self.identity_fields else "id"
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
            hostname=genesys_hostname(context),
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
            errors.append("no records found in Genesys Cloud evidence")
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
        return default_genesys_metadata(self, structured_data, context)

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
        warnings: list[str] = []
        for record in structured_data.get("records") or []:
            unknown = record.get("_unknown_fields")
            if unknown:
                warnings.append(f"ignored unknown fields: {unknown}")
        return warnings

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
