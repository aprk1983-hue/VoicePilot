"""Genesys Cloud export evidence parsing helpers."""

from __future__ import annotations

import csv
import io
import json
import re
from typing import Any

import yaml

from shared.types import JsonDict

FORMAT_JSON = "json"
FORMAT_CSV = "csv"
FORMAT_YAML = "yaml"
FORMAT_TXT = "txt"

_LIST_LINE = re.compile(r"^([A-Za-z][\w\s\-]*?)\s*[:=]\s*(.*)$")
_EXPORT_HEADER = re.compile(r"^#?\s*genesys\s+cloud\s+export", re.I)


def normalize_property_key(key: str) -> str:
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key.strip())
    return normalized.replace(" ", "_").replace("-", "_").lower()


def detect_evidence_format(raw_text: str) -> str:
    stripped = raw_text.strip()
    if not stripped:
        return FORMAT_TXT
    if stripped[0] in {"[", "{"}:
        return FORMAT_JSON
    if _EXPORT_HEADER.match(stripped.splitlines()[0].strip()):
        return FORMAT_TXT
    if stripped.startswith("---") or stripped.startswith("- ") or re.match(
        r"^[a-zA-Z_][\w-]*:\s", stripped
    ):
        try:
            payload = yaml.safe_load(stripped)
            if isinstance(payload, (list, dict)):
                return FORMAT_YAML
        except yaml.YAMLError:
            pass
    lines = [line for line in stripped.splitlines() if line.strip()]
    if not lines:
        return FORMAT_TXT
    if "," in lines[0] and len(lines) > 1:
        return FORMAT_CSV
    if _LIST_LINE.match(lines[0].strip()):
        return FORMAT_TXT
    return FORMAT_TXT


def parse_json_records(raw_text: str) -> list[JsonDict]:
    payload = json.loads(raw_text)
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        records = payload.get("records") or payload.get("items") or [payload]
    else:
        raise ValueError("JSON evidence must be an object or array")
    return [_normalize_record(record) for record in records if isinstance(record, dict)]


def parse_csv_records(raw_text: str) -> list[JsonDict]:
    reader = csv.DictReader(io.StringIO(raw_text.strip()))
    if reader.fieldnames is None:
        return []
    return [_normalize_record(dict(row)) for row in reader]


def parse_yaml_records(raw_text: str) -> list[JsonDict]:
    payload = yaml.safe_load(raw_text)
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        records = payload.get("records") or payload.get("items") or [payload]
    else:
        raise ValueError("YAML evidence must be an object or array")
    return [_normalize_record(record) for record in records if isinstance(record, dict)]


def parse_txt_records(raw_text: str) -> list[JsonDict]:
    records: list[JsonDict] = []
    current: JsonDict = {}
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            if current:
                records.append(current)
                current = {}
            continue
        if stripped.lower().startswith("genesys cloud export"):
            continue
        match = _LIST_LINE.match(stripped)
        if match is None:
            continue
        key = normalize_property_key(match.group(1))
        current[key] = match.group(2).strip()
    if current:
        records.append(current)
    return records


def parse_genesys_evidence(raw_text: str) -> tuple[str, list[JsonDict]]:
    evidence_format = detect_evidence_format(raw_text)
    if evidence_format == FORMAT_JSON:
        return evidence_format, parse_json_records(raw_text)
    if evidence_format == FORMAT_CSV:
        return evidence_format, parse_csv_records(raw_text)
    if evidence_format == FORMAT_YAML:
        return evidence_format, parse_yaml_records(raw_text)
    return evidence_format, parse_txt_records(raw_text)


def _normalize_record(record: dict[str, Any]) -> JsonDict:
    normalized: JsonDict = {}
    for key, value in record.items():
        if key is None:
            continue
        normalized_key = normalize_property_key(str(key))
        if isinstance(value, str):
            normalized[normalized_key] = value.strip()
        else:
            normalized[normalized_key] = value
    return normalized


def dedupe_records(
    records: list[JsonDict],
    identity_field: str,
) -> tuple[list[JsonDict], list[str]]:
    warnings: list[str] = []
    ordered: list[JsonDict] = []
    index_by_key: dict[str, int] = {}
    for record in records:
        identity = record.get(identity_field)
        if identity is None:
            ordered.append(record)
            continue
        key = str(identity)
        if key in index_by_key:
            warnings.append(f"duplicate {identity_field}: {key}")
            ordered[index_by_key[key]] = record
        else:
            index_by_key[key] = len(ordered)
            ordered.append(record)
    return ordered, warnings


def record_identity(record: JsonDict, *fields: str) -> str | None:
    for field in fields:
        value = record.get(field)
        if value not in (None, ""):
            return str(value)
    return None


def calculate_record_confidence(
    record: JsonDict,
    required_fields: tuple[str, ...],
    *,
    base: float = 60.0,
    per_field: float = 10.0,
) -> float:
    score = base
    for field in required_fields:
        if record.get(field) not in (None, ""):
            score += per_field
    return min(score, 100.0)
