"""Infrastructure package.

Keep this package lightweight to avoid runtime circular imports.
Import concrete repositories directly from infrastructure.filesystem when needed.
"""

from infrastructure.yaml_loader import YamlLoader

__all__ = ["YamlLoader"]
