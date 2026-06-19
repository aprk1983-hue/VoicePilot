"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import pytest

from domain.enums import Severity
from domain.value_objects import (
    AffectedScope,
    CaseIntake,
    PlatformRef,
    SymptomSummary,
)
from infrastructure.filesystem import InMemoryCaseRepository, FilesystemPlaybookRepository
from infrastructure.yaml_loader import YamlLoader
from runtime.case_manager import CaseManager
from runtime.event_bus import EventBus
from runtime.playbook_loader import PlaybookLoader
from runtime.state_machine import InvestigationStateMachine


@pytest.fixture
def event_bus() -> EventBus:
    bus = EventBus()
    yield bus
    bus.clear()


@pytest.fixture
def case_repository() -> InMemoryCaseRepository:
    return InMemoryCaseRepository()


@pytest.fixture
def case_manager(case_repository: InMemoryCaseRepository, event_bus: EventBus) -> CaseManager:
    return CaseManager(
        repository=case_repository,
        state_machine=InvestigationStateMachine(),
        event_bus=event_bus,
    )


@pytest.fixture
def sample_intake() -> CaseIntake:
    return CaseIntake(
        title="Outbound PSTN failure",
        symptom=SymptomSummary(summary="Outbound calls fail"),
        severity=Severity.HIGH,
        business_impact="Users cannot call externally",
        affected_scope=AffectedScope(sites=("HQ",)),
        platform=PlatformRef(vendor="cisco", products=("cube",)),
        playbook_id="VP-CUBE-0001",
    )


@pytest.fixture
def playbook_loader(event_bus: EventBus) -> PlaybookLoader:
    return PlaybookLoader(
        repository=FilesystemPlaybookRepository(YamlLoader()),
        event_bus=event_bus,
    )
