"""Runtime configuration for the VoicePilot kernel."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class RuntimeConfig:
    """Configuration values for the Runtime Kernel.

    Attributes:
        playbooks_path: Root directory containing ``.vpb.yaml`` playbook files.
        cases_path: Root directory for persisted case artifacts.
        log_level: Logging level name (e.g. ``INFO``).
        schema_version: Canonical data model schema version.
    """

    playbooks_path: Path = field(default_factory=lambda: Path("plugins"))
    cases_path: Path = field(default_factory=lambda: Path("data/cases"))
    log_level: str = "INFO"
    schema_version: str = "1.0"

    @classmethod
    def from_env(cls) -> RuntimeConfig:
        """Build configuration from environment defaults.

        TODO: Load overrides from environment variables in a future sprint.
        """
        return cls()
