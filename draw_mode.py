"""
Air drawing mode.

نسخة مبسّطة وثابتة للرسم في الهواء:
- ترسم عندما تكون الإيماءة "Point" بثقة معقولة.
- تتوقف عند "Fist" أو "Open_Palm".
- تحتفظ بخط مستمر مع فترة سماح قصيرة لتقليل التقطّع.
"""

from __future__ import annotations

import cv2
import numpy as np
import time

from typing import Optional

from controllers import AirDrawing
from modes.base import BaseMode


class DrawMode(BaseMode):
    """Air drawing mode (simple and robust)."""

    name = "draw"

    def __init__(self):
        # Canvas size will be adapted on first frame.
        self._drawer: Optional[AirDrawing] = None

        # حالة الرسم الحالية
        self._is_drawing_active: bool = False
        self._last_point_ts: float = 0.0
        # فترة سماح بسيطة لتجنّب تقطّع الخط (بالثواني)
        self._grace_period_sec: float = 0.15

    def ensure_canvas(self, frame: np.ndarray) -> None:
        if self._drawer is not None:
            return
        h, w, _ = frame.shape
        self._drawer = AirDrawing((w, h))
        # إذا كانت النسخة المحسّنة من AirDrawing متوفرة فعّل السمك التكيفي
        if hasattr(self._drawer, "set_adaptive_thickness"):
            self._drawer.set_adaptive_thickness(True)

    def clear(self) -> None:
        if self._drawer:
            self._drawer.clear_canvas()
        self._is_drawing_active = False
        self._last_point_ts = 0.0

    def on_frame(self, frame: np.ndarray, tracker, gesture: str, confidence: float) -> np.ndarray:
        self.ensure_canvas(frame)
        assert self._drawer is not None

        now = time.time()
        index_tip = tracker.get_finger_tip("index")

        if index_tip:
            # في وضع الرسم نجعل المنطق بسيطًا قدر الإمكان:
            # إذا كانت اليد (الإصبع) متتبَّعة → ارسم.
            # إيقاف الرسم فقط عندما تختفي اليد لفترة قصيرة.
            self._is_drawing_active = True
            self._last_point_ts = now

            # تحديث لوحة الرسم بناءً على حالة الرسم
            self._drawer.update(index_tip[0], index_tip[1], self._is_drawing_active)

            # مؤشر بسيط على طرف الإصبع
            h, w = frame.shape[:2]
            tip_x = int(index_tip[0] * w)
            tip_y = int(index_tip[1] * h)
            color = (0, 255, 0) if self._is_drawing_active else (0, 0, 255)
            cv2.circle(frame, (tip_x, tip_y), 10, color, 2)
            cv2.circle(frame, (tip_x, tip_y), 3, color, -1)
        else:
            # لا يوجد إصبع مكتشف لفترة أطول من فترة السماح → أوقف الرسم
            if (now - self._last_point_ts) > self._grace_period_sec:
                self._is_drawing_active = False

        # دمج اللوحة مع الإطار
        canvas = self._drawer.get_canvas()
        frame = cv2.addWeighted(frame, 0.7, canvas, 0.3, 0)

        # نص حالة بسيط
        status_text = f"Drawing: {'ON' if self._is_drawing_active else 'OFF'} | Gesture: {gesture} ({confidence:.2f})"
        cv2.putText(
            frame,
            status_text,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )

        return frame
