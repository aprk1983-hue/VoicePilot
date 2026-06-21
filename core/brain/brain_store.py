"""Local Brain session persistence for cross-process CLI workflows.

Dev-only storage under ``.voicepilot/sessions/``. Uses JSON for BrainSession
metadata and pickle for the Case aggregate until full JSON round-trip exists.
"""

from __future__ import annotations

import json
import pickle
import re
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any

from brain.brain_exceptions import BrainSessionNotFoundError
from brain.brain_models import BrainJourneyEntry, BrainSession, BrainStage
from domain.models import Case

STORE_VERSION = 1
DEFAULT_STORE_ROOT = Path(".voicepilot/sessions")

_SENSITIVE_KEY_PATTERN = re.compile(
    r"(password|secret|token|api[_-]?key|credential|auth)",
    re.IGNORECASE,
)


class BrainSessionStore:
    """Persist Brain sessions and associated cases for local CLI resume."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or DEFAULT_STORE_ROOT
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        """Return the storage root directory."""
        return self._root

    def save(self, session: BrainSession, case: Case) -> None:
        """Persist a Brain session and its associated case."""
        safe_case = sanitize_case_for_storage(case)
        session_path = self._session_path(session.session_id)
        case_path = self._case_path(session.session_id)
        session_path.write_text(
            json.dumps(
                {"version": STORE_VERSION, "session": _session_to_dict(session)},
                indent=2,
            ),
            encoding="utf-8",
        )
        case_path.write_bytes(pickle.dumps(safe_case, protocol=pickle.HIGHEST_PROTOCOL))

    def load(self, session_id: str) -> tuple[BrainSession, Case]:
        """Load a persisted Brain session and case."""
        session_path = self._session_path(session_id)
        case_path = self._case_path(session_id)
        if not session_path.exists() or not case_path.exists():
            raise BrainSessionNotFoundError(session_id)

        payload = json.loads(session_path.read_text(encoding="utf-8"))
        session = _session_from_dict(payload["session"])
        case = pickle.loads(case_path.read_bytes())  # noqa: S301 - local dev store only
        return session, case

    def list_sessions(self) -> tuple[BrainSession, ...]:
        """Return all persisted Brain sessions in deterministic order."""
        sessions: list[BrainSession] = []
        for path in sorted(self._root.glob("*.json")):
            session_id = path.stem
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                sessions.append(_session_from_dict(payload["session"]))
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
        return tuple(sessions)

    def delete(self, session_id: str) -> None:
        """Remove a persisted Brain session."""
        session_path = self._session_path(session_id)
        case_path = self._case_path(session_id)
        if not session_path.exists():
            raise BrainSessionNotFoundError(session_id)
        session_path.unlink(missing_ok=True)
        case_path.unlink(missing_ok=True)

    def _session_path(self, session_id: str) -> Path:
        return self._root / f"{session_id}.json"

    def _case_path(self, session_id: str) -> Path:
        return self._root / f"{session_id}.case.pkl"


def sanitize_case_for_storage(case: Case) -> Case:
    """Return a case copy with sensitive metadata keys removed before persistence."""
    if not case.metadata:
        return case
    sanitized_metadata = {
        key: value
        for key, value in case.metadata.items()
        if not _is_sensitive_key(key)
    }
    if sanitized_metadata == case.metadata:
        return case
    return replace(case, metadata=sanitized_metadata)


def restore_brain_session_to_runtime(runtime, store: BrainSessionStore, session_id: str) -> BrainSession:
    """Load a persisted session into a fresh runtime process when not in memory."""
    try:
        return runtime.get_brain_session(session_id)
    except BrainSessionNotFoundError:
        pass

    session, case = store.load(session_id)
    runtime.case_manager._cases[case.case_id] = case
    runtime.case_manager._repository.save(case)
    runtime.brain_engine.registry.register_session(session)
    return session


def persist_brain_session(runtime, store: BrainSessionStore, session_id: str) -> None:
    """Save the current in-memory Brain session and case to local storage."""
    session = runtime.get_brain_session(session_id)
    case = runtime.case_manager.load_case(session.case_id)
    store.save(session, case)


def merge_brain_sessions(
    in_memory: tuple[BrainSession, ...],
    persisted: tuple[BrainSession, ...],
) -> tuple[BrainSession, ...]:
    """Merge in-memory and persisted sessions, preferring in-memory copies."""
    merged: dict[str, BrainSession] = {session.session_id: session for session in persisted}
    for session in in_memory:
        merged[session.session_id] = session
    return tuple(merged[session_id] for session_id in sorted(merged))


def _is_sensitive_key(key: str) -> bool:
    return bool(_SENSITIVE_KEY_PATTERN.search(key))


def _session_to_dict(session: BrainSession) -> dict[str, Any]:
    return {
        "session_id": session.session_id,
        "case_id": session.case_id,
        "playbook": session.playbook,
        "current_stage": session.current_stage.value,
        "started_at": session.started_at.isoformat(),
        "last_updated": session.last_updated.isoformat(),
        "current_confidence": session.current_confidence,
        "current_quality_score": session.current_quality_score,
        "completed": session.completed,
        "failed": session.failed,
        "decision_log_ids": list(session.decision_log_ids),
        "journey": [_journey_entry_to_dict(entry) for entry in session.journey],
    }


def _session_from_dict(data: dict[str, Any]) -> BrainSession:
    return BrainSession(
        session_id=data["session_id"],
        case_id=data["case_id"],
        playbook=data["playbook"],
        current_stage=BrainStage(data["current_stage"]),
        started_at=datetime.fromisoformat(data["started_at"]),
        last_updated=datetime.fromisoformat(data["last_updated"]),
        current_confidence=data.get("current_confidence"),
        current_quality_score=data.get("current_quality_score"),
        completed=bool(data.get("completed", False)),
        failed=bool(data.get("failed", False)),
        decision_log_ids=tuple(data.get("decision_log_ids", [])),
        journey=tuple(_journey_entry_from_dict(entry) for entry in data.get("journey", [])),
    )


def _journey_entry_to_dict(entry: BrainJourneyEntry) -> dict[str, Any]:
    return {
        "sequence": entry.sequence,
        "timestamp": entry.timestamp.isoformat(),
        "stage": entry.stage.value,
        "summary": entry.summary,
        "decision_log_id": entry.decision_log_id,
    }


def _journey_entry_from_dict(data: dict[str, Any]) -> BrainJourneyEntry:
    return BrainJourneyEntry(
        sequence=data["sequence"],
        timestamp=datetime.fromisoformat(data["timestamp"]),
        stage=BrainStage(data["stage"]),
        summary=data["summary"],
        decision_log_id=data.get("decision_log_id"),
    )
