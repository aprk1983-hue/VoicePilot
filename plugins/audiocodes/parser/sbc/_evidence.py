"""Evidence parsing helpers for AudioCodes SBC parsers."""

from __future__ import annotations

import configparser
import io
import re
import xml.etree.ElementTree as ET

from shared.types import JsonDict

FORMAT_TXT = "txt"
FORMAT_INI = "ini"
FORMAT_XML = "xml"

_LIST_LINE = re.compile(r"^([A-Za-z][\w\s\-]*?)\s*[:=]\s*(.*)$")
_INI_SECTION = re.compile(r"^\[.+\]$")


def normalize_property_key(key: str) -> str:
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key.strip())
    return normalized.replace(" ", "_").replace("-", "_").lower()


def detect_evidence_format(raw_text: str) -> str:
    stripped = raw_text.strip()
    if not stripped:
        return FORMAT_TXT
    if stripped.startswith("<?xml") or stripped.startswith("<"):
        return FORMAT_XML
    if any(_INI_SECTION.match(line.strip()) for line in stripped.splitlines()):
        return FORMAT_INI
    return FORMAT_TXT


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
        if stripped.lower().startswith("show "):
            continue
        match = _LIST_LINE.match(stripped)
        if match is None:
            continue
        key = normalize_property_key(match.group(1))
        current[key] = match.group(2).strip()
    if current:
        records.append(current)
    return records


def parse_ini_records(raw_text: str) -> list[JsonDict]:
    parser = configparser.ConfigParser()
    parser.optionxform = str  # type: ignore[method-assign]
    parser.read_string(raw_text)
    records: list[JsonDict] = []
    for section in parser.sections():
        record: JsonDict = {"section": section, "name": section}
        for key, value in parser.items(section):
            record[normalize_property_key(key)] = value.strip()
        records.append(record)
    return records


def parse_xml_records(raw_text: str) -> list[JsonDict]:
    root = ET.fromstring(raw_text)
    records: list[JsonDict] = []
    for child in root:
        if not list(child):
            continue
        record: JsonDict = {}
        for element in child:
            record[normalize_property_key(element.tag)] = (element.text or "").strip()
        identity = record.get("name") or record.get("identity") or record.get("index")
        if identity is not None:
            record["name"] = str(identity)
        records.append(record)
    return records


def parse_audiocodes_evidence(raw_text: str) -> tuple[str, list[JsonDict]]:
    evidence_format = detect_evidence_format(raw_text)
    if evidence_format == FORMAT_XML:
        return evidence_format, parse_xml_records(raw_text)
    if evidence_format == FORMAT_INI:
        return evidence_format, parse_ini_records(raw_text)
    return evidence_format, parse_txt_records(raw_text)


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
