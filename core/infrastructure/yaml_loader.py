"""YAML document loading infrastructure."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from shared.types import JsonDict

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


class YamlLoader:
    """Loads YAML files into Python dictionaries."""

    def load_file(self, path: Path) -> JsonDict:
        """Load and parse a YAML file from ``path``."""
        if yaml is None:
            raise ImportError(
                "PyYAML is required to load playbook files. Install with: pip install pyyaml"
            )
        text = path.read_text(encoding="utf-8")
        data: Any = yaml.safe_load(text)
        if not isinstance(data, dict):
            raise ValueError(f"Expected YAML mapping at root of {path}")
        return data
