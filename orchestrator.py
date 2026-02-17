"""
Application orchestrator.

`main.py` should stay thin: parse args -> create orchestrator -> run.
This module owns wiring between tracker, gesture recognition, and modes.
"""

from __future__ import annotations

import threading
import time
from typing import Dict

import cv2
import numpy as np

from constants import (
    CAMERA_FRAME_HEIGHT,
    CAMERA_FRAME_WIDTH,
    CAMERA_TARGET_FPS,
    WINDOW_TITLE,
)
from gesture_recognizer import GestureRecognizer
from hand_tracker import HandTracker
from modes.demo_mode import DemoMode
from modes.draw_mode import DrawMode
from modes.mouse_mode import MouseMode
from modes.volume_mode import VolumeMode
from pipeline.threaded_pipeline import ThreadedPipeline
from utils import FPSCounter, draw_info_panel


class HandTrackingOrchestrator:
    """Main orchestrator for the hand tracking application."""

    def __init__(self, mode: str = "demo", use_ekf: bool = True):
        self.mode_name = mode
        self._state_lock = threading.Lock()
        self._stop_requested = False

        print(" Initializing Hand Tracking System...")
        self.tracker = HandTracker(use_ekf=use_ekf)
        self.gesture_recognizer = GestureRecognizer()

        self.modes: Dict[str, object] = {
            "demo": DemoMode(),
            "mouse": MouseMode(),
            "draw": DrawMode(),
            "volume": VolumeMode(),
        }
        if self.mode_name not in self.modes:
            self.mode_name = "demo"

        self.fps_counter = FPSCounter()
        print("Initialization Complete!")

    @property
    def current_mode(self):
        with self._state_lock:
            return self.modes[self.mode_name]

    def set_mode(self, mode_name: str) -> None:
        if mode_name not in self.modes:
            return
        with self._state_lock:
            self.mode_name = mode_name
        print(f" Switched to {mode_name.capitalize()} Mode")

    def request_stop(self) -> None:
        """Signal the main run loop to exit gracefully."""
        self._stop_requested = True

    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Process a raw camera frame into a display frame.

        This method is safe to call from the processing thread.
        """
        frame = cv2.flip(frame, 1)
        frame, is_tracking = self.tracker.process_frame(frame)

        with self._state_lock:
            mode_name = self.mode_name
            mode = self.modes[self.mode_name]

        gesture, confidence = "None", 0.0
        if is_tracking:
            gesture, confidence = self.gesture_recognizer.update(
                self.tracker.landmarks, mode=mode_name
            )

        fps = self.fps_counter.update(time.time())
        frame = draw_info_panel(frame, fps, gesture, mode_name, confidence)

        # Mode-specific work (can draw overlays and trigger actions).
        with self._state_lock:
            frame = mode.on_frame(frame, self.tracker, gesture, confidence)

        return frame

    def clear_current_mode(self) -> None:
        """Clear/Reset current mode (e.g., drawing canvas)."""
        with self._state_lock:
            mode = self.modes[self.mode_name]
            if hasattr(mode, "clear"):
                mode.clear()

    def run(self, camera_id: int = 0) -> None:
        self._print_controls()

        pipeline = ThreadedPipeline(camera_id=camera_id, orchestrator=self)
        print(f" Opening camera {camera_id}...")
        if not pipeline.start():
            print(" Error: Could not open camera")
            return
        print(" Camera opened successfully!")

        try:
            while not self._stop_requested:
                pkt = pipeline.get_latest(timeout=1.0)
                if pkt is None:
                    continue

                cv2.imshow(WINDOW_TITLE, pkt.frame)
                key = cv2.waitKey(1) & 0xFF

                if key == ord("q"):
                    print("Quitting...")
                    break
                if key == ord("m"):
                    self.set_mode("mouse")
                elif key == ord("v"):
                    self.set_mode("volume")
                elif key == ord("d"):
                    self.set_mode("draw")
                elif key == ord("c"):
                    self.clear_current_mode()
                    print(" Canvas Cleared")
                elif key == ord(" "):
                    self.set_mode("demo")

        except KeyboardInterrupt:
            print("\n Interrupted by user")
        finally:
            pipeline.stop()
            self._cleanup()

    def _print_controls(self) -> None:
        print("\n" + "=" * 50)
        print(" CONTROLS:")
        print("  Q - Quit")
        print("  M - Mouse Mode")
        print("  V - Volume Mode")
        print("  D - Drawing Mode")
        print("  C - Clear Drawing (in draw mode)")
        print("  SPACE - Demo Mode")
        print("=" * 50 + "\n")

    def _cleanup(self) -> None:
        print("\n Cleaning up...")
        cv2.destroyAllWindows()
        if self.tracker:
            self.tracker.release()
        print("Cleanup complete!")

