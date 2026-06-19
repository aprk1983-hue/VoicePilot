"""Loads and validates VoicePilot DSL playbook documents."""

from __future__ import annotations

from pathlib import Path

from domain.events import PlaybookLoadedEvent
from domain.interfaces import EventBusPort, LoggerPort, PlaybookRepository
from domain.models import Playbook
from runtime.event_bus import EventBus
from runtime.exceptions import PlaybookNotFoundError, PlaybookValidationError
from shared.constants import DSL_API_VERSION


class PlaybookLoader:
    """Loads ``.vpb.yaml`` playbooks and returns domain ``Playbook`` objects.

    Performs structural validation only. No investigation logic.
    """

    _REQUIRED_ROOT_KEYS = frozenset({"api_version", "kind", "metadata"})
    _REQUIRED_METADATA_KEYS = frozenset({"id", "version", "title", "status"})

    def __init__(
        self,
        repository: PlaybookRepository,
        event_bus: EventBusPort | None = None,
        logger: LoggerPort | None = None,
    ) -> None:
        self._repository = repository
        self._event_bus = event_bus or EventBus()
        self._logger = logger

    def load(self, path: Path) -> Playbook:
        """Load and validate a playbook from ``path``."""
        if not path.exists():
            raise PlaybookNotFoundError(str(path))

        document = self._repository.load_by_path(path)
        self._validate(document)

        metadata = document["playbook"]["metadata"]
        playbook = Playbook(
            playbook_id=metadata["id"],
            version=metadata["version"],
            title=metadata["title"],
            status=metadata["status"],
            raw_document=document,
            vendor=metadata.get("vendor"),
            category=metadata.get("category"),
        )

        if self._logger:
            self._logger.info(
                "Playbook loaded",
                playbook_id=playbook.playbook_id,
                version=playbook.version,
            )

        self._event_bus.publish(
            PlaybookLoadedEvent.from_playbook(playbook.playbook_id, playbook.version)
        )
        return playbook

    def _validate(self, document: dict) -> None:
        """Validate playbook document structure.

        TODO: Replace with JSON Schema validation against DSL spec.
        """
        errors: list[str] = []

        if "playbook" not in document:
            errors.append("Missing root key: playbook")
            raise PlaybookValidationError("Invalid playbook document", errors)

        playbook = document["playbook"]

        for key in self._REQUIRED_ROOT_KEYS:
            if key not in playbook:
                errors.append(f"Missing playbook key: {key}")

        if playbook.get("api_version") != DSL_API_VERSION:
            errors.append(
                f"Unsupported api_version: {playbook.get('api_version')!r} "
                f"(expected {DSL_API_VERSION!r})"
            )

        if playbook.get("kind") != "Playbook":
            errors.append(f"Invalid kind: {playbook.get('kind')!r}")

        metadata = playbook.get("metadata", {})
        for key in self._REQUIRED_METADATA_KEYS:
            if key not in metadata:
                errors.append(f"Missing metadata key: {key}")

        if errors:
            raise PlaybookValidationError("Playbook validation failed", errors)
