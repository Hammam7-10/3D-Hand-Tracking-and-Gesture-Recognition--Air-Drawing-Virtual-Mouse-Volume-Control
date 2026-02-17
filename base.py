"""
Mode base class.

Each mode implements a consistent interface for per-frame logic:
    on_frame(frame, tracker, gesture, confidence) -> frame
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Set

import numpy as np


class BaseMode(ABC):
    """Base interface for all interaction modes."""

    name: str = "demo"
    allowed_gestures: Optional[Set[str]] = None

    @abstractmethod
    def on_frame(
        self,
        frame: np.ndarray,
        tracker,
        gesture: str,
        confidence: float,
    ) -> np.ndarray:
        """
        Handle one processed frame.

        Args:
            frame: BGR frame (may already contain MediaPipe drawings).
            tracker: HandTracker instance (provides landmarks and helpers).
            gesture: Smoothed gesture name.
            confidence: Smoothed confidence score in [0, 1].

        Returns:
            The (optionally) modified frame to display.
        """
        raise NotImplementedError

