"""Backward compatibility shim for VoicePilot imports.

Adds ``core/`` to ``sys.path`` so legacy scripts using ``backend/`` as entry
point can still resolve ``domain``, ``runtime``, and related packages.
"""

from __future__ import annotations

import sys
from pathlib import Path

_CORE_ROOT = Path(__file__).resolve().parent.parent / "core"
_SDK_ROOT = Path(__file__).resolve().parent.parent / "sdk"

for path in (_CORE_ROOT, _SDK_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
