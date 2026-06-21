"""YAML serialization for generated engineering assets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def write_asset_yaml(path: Path, asset: dict[str, Any]) -> None:
    """Write one asset dictionary as YAML."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(asset, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def load_asset_yaml(path: Path) -> dict[str, Any]:
    """Load one generated asset YAML file."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data
