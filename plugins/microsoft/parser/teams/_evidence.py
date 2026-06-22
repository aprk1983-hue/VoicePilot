"""PowerShell evidence parsing helpers for Microsoft Teams parsers."""

from __future__ import annotations

import csv
import io
import json
import re
from typing import Any

from shared.types import JsonDict

FORMAT_JSON = "json"
FORMAT_CSV = "csv"
FORMAT_LIST = "format_list"

_LIST_LINE = re.compile(r"^([A-Za-z][\w]*)\s*:\s*(.*)$")


def normalize_property_key(key: str) -> str:
    """Convert PowerShell property names to snake_case keys."""
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key.strip())
    return normalized.replace(" ", "_").replace("-", "_").lower()


def parse_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "yes", "1"}:
        return True
    if text in {"false", "no", "0"}:
        return False
    return None


def parse_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def parse_list_value(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, list):
        return tuple(str(item).strip() for item in value if str(item).strip())
    text = str(value).strip()
    if not text:
        return ()
    if text.startswith("{") and text.endswith("}"):
        inner = text[1:-1].strip()
        if not inner:
            return ()
        return tuple(part.strip() for part in inner.split(",") if part.strip())
    return (text,)


def detect_evidence_format(raw_text: str) -> str:
    """Detect whether evidence is JSON, CSV, or Format-List text."""
    stripped = raw_text.strip()
    if not stripped:
        return FORMAT_LIST
    if stripped[0] in {"[", "{"}:
        return FORMAT_JSON
    lines = [line for line in stripped.splitlines() if line.strip()]
    if not lines:
        return FORMAT_LIST
    if _LIST_LINE.match(lines[0].strip()):
        return FORMAT_LIST
    if "," in lines[0] and len(lines) > 1:
        return FORMAT_CSV
    return FORMAT_LIST


def parse_json_records(raw_text: str) -> list[JsonDict]:
    payload = json.loads(raw_text)
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        records = [payload]
    else:
        raise ValueError("JSON evidence must be an object or array")
    return [_normalize_record(record) for record in records if isinstance(record, dict)]


def parse_csv_records(raw_text: str) -> list[JsonDict]:
    reader = csv.DictReader(io.StringIO(raw_text.strip()))
    if reader.fieldnames is None:
        return []
    return [_normalize_record(dict(row)) for row in reader]


def parse_format_list_records(raw_text: str) -> list[JsonDict]:
    records: list[JsonDict] = []
    current: JsonDict = {}
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            if current:
                records.append(current)
                current = {}
            continue
        if stripped.lower().startswith("get-cs"):
            continue
        match = _LIST_LINE.match(stripped)
        if match is None:
            continue
        key = normalize_property_key(match.group(1))
        current[key] = match.group(2).strip()
    if current:
        records.append(current)
    return records


def parse_powershell_evidence(raw_text: str) -> tuple[str, list[JsonDict]]:
    """Parse exported PowerShell evidence into normalized records."""
    evidence_format = detect_evidence_format(raw_text)
    if evidence_format == FORMAT_JSON:
        return evidence_format, parse_json_records(raw_text)
    if evidence_format == FORMAT_CSV:
        return evidence_format, parse_csv_records(raw_text)
    return evidence_format, parse_format_list_records(raw_text)


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
    """Deduplicate records by identity field, keeping the last occurrence."""
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
    """Return the first populated identity field from a record."""
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
