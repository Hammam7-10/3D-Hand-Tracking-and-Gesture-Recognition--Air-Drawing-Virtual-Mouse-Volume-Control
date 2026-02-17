"""
Threaded real-time pipeline.

Design goals:
- Stable FPS and lower latency by always processing the *latest* frame.
- Decouple camera capture from processing.
- Keep UI (imshow / waitKey) in the main thread for best compatibility.
"""

from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np
import sys

from constants import CAMERA_FRAME_HEIGHT, CAMERA_FRAME_WIDTH, CAMERA_TARGET_FPS


@dataclass(frozen=True)
class ProcessedPacket:
    """One processed output packet."""

    frame: np.ndarray
    timestamp: float


class CameraThread(threading.Thread):
    """
    Camera reader thread that pushes the newest frame into a size-1 queue.
    Older frames are dropped automatically (smart frame skipping).
    """

    def __init__(self, camera_id: int, out_queue: "queue.Queue[np.ndarray]", cap: Optional[cv2.VideoCapture] = None):
        super().__init__(daemon=True)
        self.camera_id = camera_id
        self.out_queue = out_queue
        self._stop_event = threading.Event()
        self._cap: Optional[cv2.VideoCapture] = cap
        self.open_ok: bool = cap is not None and cap.isOpened() if cap is not None else False

    def run(self) -> None:
        if self._cap is None or not self.open_ok:
            return

        # Settings are already applied if cap was passed from main thread

        while not self._stop_event.is_set():
            ret, frame = self._cap.read()
            if not ret:
                time.sleep(0.005)
                continue

            # Keep only the newest frame.
            try:
                _ = self.out_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.out_queue.put_nowait(frame)
            except queue.Full:
                pass

    def stop(self) -> None:
        self._stop_event.set()
        # Note: Camera release is handled by ThreadedPipeline.stop() in main thread


class ProcessingThread(threading.Thread):
    """
    Processing thread: consumes newest frames and produces newest processed frames.
    """

    def __init__(
        self,
        in_queue: "queue.Queue[np.ndarray]",
        out_queue: "queue.Queue[ProcessedPacket]",
        orchestrator,
    ):
        super().__init__(daemon=True)
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.orchestrator = orchestrator
        self._stop_event = threading.Event()

    def run(self) -> None:
        while not self._stop_event.is_set():
            try:
                frame = self.in_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            processed = self.orchestrator.process_frame(frame)
            pkt = ProcessedPacket(frame=processed, timestamp=time.time())

            # Keep only the newest processed output.
            try:
                _ = self.out_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                self.out_queue.put_nowait(pkt)
            except queue.Full:
                pass

    def stop(self) -> None:
        self._stop_event.set()


class ThreadedPipeline:
    """
    Convenience wrapper to manage camera + processing threads.
    """

    def __init__(self, camera_id: int, orchestrator):
        self.camera_id = camera_id
        self.orchestrator = orchestrator

        self._raw_queue: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=1)
        self._out_queue: "queue.Queue[ProcessedPacket]" = queue.Queue(maxsize=1)
        
        # Open camera in main thread for better reliability on Windows
        self._cap: Optional[cv2.VideoCapture] = None
        if sys.platform.startswith("win") and hasattr(cv2, "CAP_DSHOW"):
            self._cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
        else:
            self._cap = cv2.VideoCapture(camera_id)
        
        if self._cap.isOpened():
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_FRAME_WIDTH)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_FRAME_HEIGHT)
            self._cap.set(cv2.CAP_PROP_FPS, CAMERA_TARGET_FPS)
            self.camera_thread = CameraThread(camera_id=camera_id, out_queue=self._raw_queue, cap=self._cap)
        else:
            self.camera_thread = CameraThread(camera_id=camera_id, out_queue=self._raw_queue, cap=None)
        
        self.processing_thread = ProcessingThread(
            in_queue=self._raw_queue, out_queue=self._out_queue, orchestrator=orchestrator
        )

    def start(self) -> bool:
        if not self.camera_thread.open_ok:
            if self._cap is not None:
                self._cap.release()
            return False
        
        self.camera_thread.start()
        # Give the camera thread a moment to start reading
        time.sleep(0.1)
        self.processing_thread.start()
        return True

    def get_latest(self, timeout: float = 0.5) -> Optional[ProcessedPacket]:
        try:
            return self._out_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def stop(self) -> None:
        self.camera_thread.stop()
        self.processing_thread.stop()
        # Wait for threads to finish
        self.camera_thread.join(timeout=1.0)
        self.processing_thread.join(timeout=1.0)
        # Release camera in main thread
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass

