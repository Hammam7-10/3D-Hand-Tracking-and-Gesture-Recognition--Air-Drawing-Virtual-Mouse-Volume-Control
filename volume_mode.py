"""
Volume control mode.

Volume is mapped from pinch distance (thumb-index) for an intuitive control.
"""

from __future__ import annotations

import cv2
import numpy as np

from constants import VOLUME_BAR_HEIGHT, VOLUME_BAR_MARGIN_PX, VOLUME_BAR_WIDTH
from controllers import VolumeController
from modes.base import BaseMode


class VolumeMode(BaseMode):
    """System volume controller mode."""

    name = "volume"

    def __init__(self):
        self._controller = VolumeController()

    def on_frame(self, frame: np.ndarray, tracker, gesture: str, confidence: float) -> np.ndarray:
        pinch_distance = tracker.get_pinch_distance()
        if pinch_distance is not None:
            self._controller.set_volume(pinch_distance)

        self._draw_volume_bar(frame, self._controller.get_volume())
        return frame

    def _draw_volume_bar(self, frame: np.ndarray, volume: int) -> None:
        h, w, _ = frame.shape

        bar_x = w - VOLUME_BAR_WIDTH - VOLUME_BAR_MARGIN_PX
        bar_y = h - VOLUME_BAR_HEIGHT - VOLUME_BAR_MARGIN_PX

        # Background
        cv2.rectangle(
            frame,
            (bar_x, bar_y),
            (bar_x + VOLUME_BAR_WIDTH, bar_y + VOLUME_BAR_HEIGHT),
            (50, 50, 50),
            -1,
        )

        # Fill
        fill_width = int((volume / 100) * VOLUME_BAR_WIDTH)
        color = (0, 255, 0) if volume > 30 else (0, 165, 255)
        cv2.rectangle(
            frame,
            (bar_x, bar_y),
            (bar_x + fill_width, bar_y + VOLUME_BAR_HEIGHT),
            color,
            -1,
        )

        # Border
        cv2.rectangle(
            frame,
            (bar_x, bar_y),
            (bar_x + VOLUME_BAR_WIDTH, bar_y + VOLUME_BAR_HEIGHT),
            (255, 255, 255),
            2,
        )

