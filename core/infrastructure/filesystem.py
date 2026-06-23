"""Filesystem utilities and repository adapters."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from domain.interfaces import CaseRepository, PlaybookRepository
from domain.models import Case
from infrastructure.yaml_loader import YamlLoader
from runtime.exceptions import CaseNotFoundError, CasePersistenceError
from shared.types import CaseId, JsonDict


class FilesystemPlaybookRepository(PlaybookRepository):
    """Loads playbook YAML documents from the filesystem."""

    def __init__(self, yaml_loader: YamlLoader | None = None) -> None:
        self._yaml_loader = yaml_loader or YamlLoader()

    def load_by_path(self, path: Path) -> JsonDict:
        return self._yaml_loader.load_file(path)


class InMemoryCaseRepository(CaseRepository):
    """In-memory case repository for kernel skeleton and tests.

    TODO: Replace with filesystem or database repository.
    """

    def __init__(self) -> None:
        self._store: dict[CaseId, Case] = {}

    def save(self, case: Case) -> None:
        try:
            self._store[case.case_id] = case
        except Exception as exc:
            raise CasePersistenceError(str(exc)) from exc

    def load(self, case_id: CaseId) -> Case:
        if case_id not in self._store:
            raise CaseNotFoundError(case_id)
        return self._store[case_id]

    def delete(self, case_id: CaseId) -> None:
        if case_id not in self._store:
            raise CaseNotFoundError(case_id)
        del self._store[case_id]


class FilesystemCaseRepository(CaseRepository):
    """Persists cases as JSON files under a root directory.

    TODO: Implement full canonical model serialization.
    """

    def __init__(self, root_path: Path) -> None:
        self._root_path = root_path
        self._root_path.mkdir(parents=True, exist_ok=True)

    def save(self, case: Case) -> None:
        path = self._root_path / f"{case.case_id}.json"
        try:
            path.write_text(
                json.dumps(_case_to_dict(case), indent=2, default=_json_default),
                encoding="utf-8",
            )
        except Exception as exc:
            raise CasePersistenceError(str(exc)) from exc

    def load(self, case_id: CaseId) -> Case:
        path = self._root_path / f"{case_id}.json"
        if not path.exists():
            raise CaseNotFoundError(case_id)
        # TODO: Deserialize JSON back to Case aggregate.
        raise CasePersistenceError("Case deserialization not yet implemented")


def _case_to_dict(case: Case) -> dict[str, Any]:
    """Serialize case to dict for persistence skeleton."""
    if is_dataclass(case):
        return asdict(case)
    raise TypeError("Expected dataclass Case instance")


def _json_default(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    raise TypeError(f"Object of type {type(value)!r} is not JSON serializable")
