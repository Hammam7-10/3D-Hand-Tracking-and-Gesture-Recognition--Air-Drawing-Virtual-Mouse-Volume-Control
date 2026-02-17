"""
Mouse interaction mode with professional decision logic.

Goals:
- Smooth cursor movement (uses EKF-smoothed tracker landmarks).
- Robust click decisions (debounce + confidence threshold + temporal hold).
- Support left/right click, drag, and two-finger scroll.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

from constants import (
    CLICK_CONFIDENCE_THRESHOLD,
    CLICK_DEBOUNCE_MS,
    CLICK_FEEDBACK_MS,
    CLICK_MIN_HOLD_MS,
    DRAG_START_HOLD_MS,
    SCROLL_AMOUNT_PER_TICK,
    SCROLL_GESTURE_CONFIDENCE_THRESHOLD,
)
from controllers import VirtualMouse
from modes.base import BaseMode


@dataclass
class _PinchState:
    active: bool = False
    pinch_gesture: Optional[str] = None  # "Pinch_TI" or "Pinch_TM"
    start_ts: float = 0.0
    clicked_once: bool = False


class MouseMode(BaseMode):
    """Virtual mouse mode."""

    name = "mouse"

    def __init__(self):
        self.mouse = VirtualMouse()
        self._pinch = _PinchState()
        self._last_click_ts: float = 0.0
        self._is_dragging: bool = False
        self._last_scroll_ts: float = 0.0

        # Visual feedback for clicks
        self._feedback_until_ts: float = 0.0
        self._feedback_color_bgr: tuple[int, int, int] = (0, 255, 255)
        self._last_cursor_xy: Optional[tuple[int, int]] = None

    def on_frame(self, frame: np.ndarray, tracker, gesture: str, confidence: float) -> np.ndarray:
        # 1) Move cursor using EKF-smoothed index tip.
        index_tip = tracker.get_finger_tip("index")
        if index_tip:
            self.mouse.move_cursor(index_tip[0], index_tip[1])
            self._draw_cursor_indicator(frame, index_tip)

        # 2) Scroll (two-finger scroll gestures).
        if gesture in ("TwoFinger_Scroll_Up", "TwoFinger_Scroll_Down"):
            if confidence >= SCROLL_GESTURE_CONFIDENCE_THRESHOLD:
                self._maybe_scroll(gesture)

        # 3) Click / drag decision (pinch gestures).
        is_pinch = gesture in ("Pinch_TI", "Pinch_TM") and confidence >= CLICK_CONFIDENCE_THRESHOLD
        if is_pinch:
            self._handle_pinch(gesture)
        else:
            self._reset_pinch()

        # 4) Draw click feedback (brief flash).
        self._draw_click_feedback(frame)
        return frame

    def _handle_pinch(self, pinch_gesture: str) -> None:
        now = time.time()
        if (not self._pinch.active) or (self._pinch.pinch_gesture != pinch_gesture):
            self._pinch = _PinchState(active=True, pinch_gesture=pinch_gesture, start_ts=now)

        held_ms = (now - self._pinch.start_ts) * 1000.0

        # Left pinch supports drag (hold without release).
        if pinch_gesture == "Pinch_TI":
            if (not self._is_dragging) and held_ms >= DRAG_START_HOLD_MS:
                self.mouse.start_drag()
                self._is_dragging = True
                self._set_feedback((0, 255, 0))
                return

            if (not self._pinch.clicked_once) and (not self._is_dragging) and held_ms >= CLICK_MIN_HOLD_MS:
                if (now - self._last_click_ts) * 1000.0 >= CLICK_DEBOUNCE_MS:
                    self.mouse.click(button="left")
                    self._pinch.clicked_once = True
                    self._last_click_ts = now
                    self._set_feedback((0, 255, 0))
            return

        # Right pinch triggers right click (no drag).
        if pinch_gesture == "Pinch_TM":
            if (not self._pinch.clicked_once) and held_ms >= CLICK_MIN_HOLD_MS:
                if (now - self._last_click_ts) * 1000.0 >= CLICK_DEBOUNCE_MS:
                    self.mouse.click(button="right")
                    self._pinch.clicked_once = True
                    self._last_click_ts = now
                    self._set_feedback((0, 0, 255))

    def _reset_pinch(self) -> None:
        if self._is_dragging:
            self.mouse.stop_drag()
            self._is_dragging = False
        self._pinch = _PinchState()

    def _maybe_scroll(self, scroll_gesture: str) -> None:
        now = time.time()
        # Throttle scroll events to feel natural and avoid flooding.
        if (now - self._last_scroll_ts) < 0.05:
            return

        amount = SCROLL_AMOUNT_PER_TICK
        if scroll_gesture == "TwoFinger_Scroll_Down":
            amount = -amount
        self.mouse.scroll(amount)
        self._last_scroll_ts = now

    def _set_feedback(self, color_bgr: tuple[int, int, int]) -> None:
        self._feedback_color_bgr = color_bgr
        self._feedback_until_ts = time.time() + (CLICK_FEEDBACK_MS / 1000.0)

    def _draw_cursor_indicator(self, frame: np.ndarray, index_tip) -> None:
        h, w, _ = frame.shape
        x, y = int(index_tip[0] * w), int(index_tip[1] * h)
        self._last_cursor_xy = (x, y)
        cv2.circle(frame, (x, y), 15, (0, 255, 255), 2)
        cv2.circle(frame, (x, y), 5, (0, 255, 255), -1)

    def _draw_click_feedback(self, frame: np.ndarray) -> None:
        if time.time() > self._feedback_until_ts:
            return
        if not self._last_cursor_xy:
            return
        cv2.circle(frame, self._last_cursor_xy, 18, self._feedback_color_bgr, 2)

