"""DuaWise recommendation engine.

Research code. See docs/SPEC.md for the design this implements and
docs/EXPERIMENTS.md for results.
"""

from __future__ import annotations

__version__ = "1.0.0"

from .config import Settings, settings

__all__ = ["Settings", "settings", "__version__"]