"""
Demo mode: tracking + overlays only (no side effects).
"""

from __future__ import annotations

import numpy as np

from modes.base import BaseMode


class DemoMode(BaseMode):
    """Read-only demo mode."""

    name = "demo"

    def on_frame(self, frame: np.ndarray, tracker, gesture: str, confidence: float) -> np.ndarray:
        return frame

