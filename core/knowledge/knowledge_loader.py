"""YAML loader for VKF knowledge packs."""

from __future__ import annotations

from pathlib import Path

from infrastructure.yaml_loader import YamlLoader
from knowledge.knowledge_exceptions import KnowledgeLoadError
from knowledge.knowledge_models import KnowledgePack
from knowledge.knowledge_pack import build_knowledge_pack
from knowledge.knowledge_registry import KnowledgeRegistry
from shared.types import JsonDict


class KnowledgeLoader:
    """Load, validate, and register knowledge packs from YAML files."""

    def __init__(
        self,
        registry: KnowledgeRegistry | None = None,
        yaml_loader: YamlLoader | None = None,
    ) -> None:
        self._registry = registry or KnowledgeRegistry()
        self._yaml_loader = yaml_loader or YamlLoader()

    @property
    def registry(self) -> KnowledgeRegistry:
        """Return the loader's registry."""
        return self._registry

    def load_file(self, path: Path) -> KnowledgePack:
        """Load and register one knowledge pack from a YAML file."""
        try:
            data = self._yaml_loader.load_file(path)
        except Exception as exc:
            raise KnowledgeLoadError(f"Failed to load knowledge pack from {path}: {exc}") from exc

        return self.load_data(data)

    def load_data(self, data: JsonDict) -> KnowledgePack:
        """Validate, build, and register one knowledge pack from mapping data."""
        try:
            pack = build_knowledge_pack(data)
        except Exception as exc:
            raise KnowledgeLoadError(f"Invalid knowledge pack: {exc}") from exc

        self._registry.register(pack)
        return pack

    def load_directory(self, directory: Path, *, pattern: str = "*.yaml") -> tuple[KnowledgePack, ...]:
        """Load and register all YAML knowledge packs in a directory."""
        if not directory.is_dir():
            raise KnowledgeLoadError(f"Knowledge directory not found: {directory}")

        loaded: list[KnowledgePack] = []
        for path in sorted(directory.glob(pattern)):
            if path.is_file():
                loaded.append(self.load_file(path))
        return tuple(loaded)
