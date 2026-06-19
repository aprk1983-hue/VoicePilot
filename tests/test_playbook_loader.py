"""Tests for PlaybookLoader."""

from __future__ import annotations

from pathlib import Path

import pytest

from domain.enums import DomainEventType
from domain.events import DomainEvent
from runtime.exceptions import PlaybookNotFoundError, PlaybookValidationError


PLAYBOOK_PATH = (
    Path(__file__).resolve().parents[1]
    / "plugins"
    / "cisco"
    / "playbooks"
    / "cube"
    / "vp-cube-0001-outbound-calls-fail.vpb.yaml"
)


class TestPlaybookLoader:
    def test_load_real_playbook(self, playbook_loader) -> None:
        if not PLAYBOOK_PATH.exists():
            pytest.skip("VP-CUBE-0001 playbook not found in repository")
        playbook = playbook_loader.load(PLAYBOOK_PATH)
        assert playbook.playbook_id == "VP-CUBE-0001"
        assert playbook.version == "1.0.0"
        assert "playbook" in playbook.raw_document

    def test_load_missing_file_raises(self, playbook_loader, tmp_path: Path) -> None:
        missing = tmp_path / "missing.vpb.yaml"
        with pytest.raises(PlaybookNotFoundError):
            playbook_loader.load(missing)

    def test_invalid_document_raises(self, playbook_loader, tmp_path: Path) -> None:
        invalid = tmp_path / "invalid.vpb.yaml"
        invalid.write_text("not_a_mapping: true\n", encoding="utf-8")
        # YamlLoader will load it but missing playbook key
        invalid2 = tmp_path / "invalid2.vpb.yaml"
        invalid2.write_text("foo: bar\n", encoding="utf-8")
        with pytest.raises(PlaybookValidationError):
            playbook_loader.load(invalid2)

    def test_load_publishes_event(self, playbook_loader, event_bus) -> None:
        if not PLAYBOOK_PATH.exists():
            pytest.skip("VP-CUBE-0001 playbook not found in repository")
        received: list[DomainEvent] = []
        event_bus.subscribe(DomainEventType.PLAYBOOK_LOADED, received.append)
        playbook_loader.load(PLAYBOOK_PATH)
        assert len(received) == 1
        assert received[0].payload["playbook_id"] == "VP-CUBE-0001"
