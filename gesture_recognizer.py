"""
Gesture Recognition System
"""
from __future__ import annotations

import numpy as np
from typing import Deque, Dict, List, Optional, Tuple
from collections import deque
import time

from constants import (
    FINGER_CLOSED_DISTANCE_MAX,
    MIN_GESTURE_CONFIDENCE,
    MIN_STABLE_FRAMES,
    PINCH_DISTANCE_THRESHOLD,
    POINTING_INDEX_DISTANCE_MIN,
    SCROLL_MIN_DELTA_FRAMES,
    SWIPE_DISTANCE_THRESHOLD,
    SWIPE_HISTORY_FRAMES,
    VOTE_WINDOW_FRAMES,
)


class GestureRecognizer:
    """
    Advanced gesture recognition system
    """
    
    def __init__(self, history_size: int = 30):
        """
        Initialize Gesture Recognizer
        
        Args:
            history_size: Number of frames to keep in history
        """
        self.history_size = history_size
        
        # Raw landmark history (for dynamic gestures like swipe/scroll).
        self.position_history: Deque[List[Tuple[float, float, float]]] = deque(
            maxlen=history_size
        )

        # Smoothed gesture history (debug/UX).
        self.gesture_history: Deque[str] = deque(maxlen=10)

        # Temporal voting window of raw predictions.
        self._raw_history: Deque[Tuple[str, float]] = deque(maxlen=VOTE_WINDOW_FRAMES)

        self.current_gesture: str = "None"
        self.gesture_confidence: float = 0.0

    def update(
        self,
        landmarks: Optional[List[Tuple[float, float, float]]],
        mode: str = "demo",
    ) -> Tuple[str, float]:
        """
        Update gesture recognition with new landmarks
        
        Args:
            landmarks: List of 21 hand landmarks
            mode: Current mode name for context-aware filtering
            
        Returns:
            (gesture_name, confidence_score)
        """
        if landmarks is None:
            self._raw_history.clear()
            self.position_history.clear()
            self.current_gesture = "None"
            self.gesture_confidence = 0.0
            return self.current_gesture, self.gesture_confidence
        
        self.position_history.append(landmarks)
        
        raw_name, raw_conf = self._predict_raw(landmarks)
        raw_name, raw_conf = self._apply_context_filter(raw_name, raw_conf, mode)

        self._raw_history.append((raw_name, raw_conf))
        smoothed_name, smoothed_conf = self._temporal_smooth()

        self.current_gesture = smoothed_name
        self.gesture_confidence = smoothed_conf
        if smoothed_name != "None":
            self.gesture_history.append(smoothed_name)

        return self.current_gesture, self.gesture_confidence
    
    def _predict_raw(self, landmarks: List[Tuple[float, float, float]]) -> Tuple[str, float]:
        """
        Predict a raw gesture for the current frame with a confidence score.

        This method is intentionally "frame-local". Temporal stability is handled
        separately by `_temporal_smooth()`.
        """
        candidates: List[Tuple[str, float]] = []

        # Pinch variants (thumb-index / thumb-middle).
        pinch_ti_conf = self._pinch_confidence(landmarks, thumb_id=4, other_id=8)
        pinch_tm_conf = self._pinch_confidence(landmarks, thumb_id=4, other_id=12)
        # Pinch should take precedence over "Point" when strong.
        pinch_best_name, pinch_best_conf = "None", 0.0
        if pinch_ti_conf >= pinch_tm_conf and pinch_ti_conf > 0.0:
            pinch_best_name, pinch_best_conf = "Pinch_TI", pinch_ti_conf
        elif pinch_tm_conf > 0.0:
            pinch_best_name, pinch_best_conf = "Pinch_TM", pinch_tm_conf
        if pinch_best_conf >= 0.60:
            return pinch_best_name, float(np.clip(pinch_best_conf, 0.0, 1.0))
        if pinch_ti_conf > 0.0:
            candidates.append(("Pinch_TI", pinch_ti_conf))
        if pinch_tm_conf > 0.0:
            candidates.append(("Pinch_TM", pinch_tm_conf))

        # Static gestures.
        candidates.append(("Point", self._pointing_confidence(landmarks)))
        candidates.append(("Thumbs_Up", self._thumbs_up_confidence(landmarks)))
        candidates.append(("Peace", self._peace_confidence(landmarks)))
        candidates.append(("OK", self._ok_confidence(landmarks)))
        candidates.append(("Fist", self._fist_confidence(landmarks)))
        candidates.append(("Open_Palm", self._open_palm_confidence(landmarks)))

        # Dynamic gestures (need history).
        scroll = self._detect_two_finger_scroll()
        if scroll:
            candidates.append(scroll)

        swipe = self._detect_swipe()
        if swipe:
            candidates.append(swipe)

        best_name, best_conf = "None", 0.0
        for name, conf in candidates:
            if conf > best_conf:
                best_name, best_conf = name, conf

        if best_conf < 0.01:
            return "None", 0.0
        return best_name, float(np.clip(best_conf, 0.0, 1.0))

    def _apply_context_filter(self, name: str, conf: float, mode: str) -> Tuple[str, float]:
        """
        Context-aware filtering: prevent illogical gestures per mode.
        """
        allowed_by_mode: Dict[str, Optional[set[str]]] = {
            "demo": None,  # allow all
            "mouse": {
                "Point",
                "Pinch_TI",
                "Pinch_TM",
                "TwoFinger_Scroll_Up",
                "TwoFinger_Scroll_Down",
                "None",
            },
            "draw": {"Point", "Open_Palm", "Fist", "None"},
            "volume": {"Pinch_TI", "None"},
        }

        allowed = allowed_by_mode.get(mode, None)
        if allowed is None:
            return name, conf
        if name in allowed:
            return name, conf
        return "None", 0.0

    def _temporal_smooth(self) -> Tuple[str, float]:
        """
        Temporal smoothing using weighted majority voting across recent frames.
        """
        if not self._raw_history:
            return "None", 0.0

        weight_sum: Dict[str, float] = {}
        count: Dict[str, int] = {}
        for name, conf in self._raw_history:
            weight_sum[name] = weight_sum.get(name, 0.0) + float(conf)
            count[name] = count.get(name, 0) + 1

        # Pick winner by highest total confidence.
        winner = max(weight_sum.items(), key=lambda kv: kv[1])[0]
        winner_count = count.get(winner, 0)
        winner_conf = weight_sum[winner] / max(1, winner_count)

        min_frames = MIN_STABLE_FRAMES
        # Continuous gestures should react faster.
        if winner in ("Point", "Open_Palm"):
            min_frames = max(2, MIN_STABLE_FRAMES - 2)

        if winner == "None":
            return "None", 0.0

        if winner_count < min_frames or winner_conf < MIN_GESTURE_CONFIDENCE:
            return "None", 0.0

        return winner, float(np.clip(winner_conf, 0.0, 1.0))
    
    def _pinch_confidence(self, landmarks: List[Tuple[float, float, float]], thumb_id: int, other_id: int) -> float:
        thumb_tip = np.array(landmarks[thumb_id])
        other_tip = np.array(landmarks[other_id])
        distance = float(np.linalg.norm(thumb_tip - other_tip))
        if distance >= PINCH_DISTANCE_THRESHOLD:
            return 0.0
        return float(np.clip(1.0 - (distance / PINCH_DISTANCE_THRESHOLD), 0.0, 1.0))
    
    def _pointing_confidence(self, landmarks: List[Tuple[float, float, float]]) -> float:
        wrist = np.array(landmarks[0])
        index_tip = np.array(landmarks[8])
        index_dist = float(np.linalg.norm(index_tip - wrist))

        others = [
            float(np.linalg.norm(np.array(landmarks[i]) - wrist))
            for i in (12, 16, 20)
        ]
        max_other = max(others) if others else 0.0

        index_score = np.clip((index_dist - POINTING_INDEX_DISTANCE_MIN) / 0.10, 0.0, 1.0)
        others_score = np.clip((FINGER_CLOSED_DISTANCE_MAX - max_other) / 0.10, 0.0, 1.0)
        return float(index_score * others_score)
    
    def _thumbs_up_confidence(self, landmarks: List[Tuple[float, float, float]]) -> float:
        wrist = np.array(landmarks[0])
        thumb_tip = np.array(landmarks[4])
        thumb_dist = float(np.linalg.norm(thumb_tip - wrist))
        thumb_higher = 1.0 if thumb_tip[1] < wrist[1] else 0.0

        index_dist = float(np.linalg.norm(np.array(landmarks[8]) - wrist))
        middle_dist = float(np.linalg.norm(np.array(landmarks[12]) - wrist))

        thumb_score = np.clip((thumb_dist - 0.20) / 0.10, 0.0, 1.0)
        others_score = np.clip((FINGER_CLOSED_DISTANCE_MAX - max(index_dist, middle_dist)) / 0.10, 0.0, 1.0)
        return float(thumb_score * others_score * thumb_higher)
    
    def _peace_confidence(self, landmarks: List[Tuple[float, float, float]]) -> float:
        wrist = np.array(landmarks[0])
        index_dist = float(np.linalg.norm(np.array(landmarks[8]) - wrist))
        middle_dist = float(np.linalg.norm(np.array(landmarks[12]) - wrist))
        ring_dist = float(np.linalg.norm(np.array(landmarks[16]) - wrist))
        pinky_dist = float(np.linalg.norm(np.array(landmarks[20]) - wrist))

        extended = np.clip((min(index_dist, middle_dist) - 0.20) / 0.10, 0.0, 1.0)
        closed = np.clip((FINGER_CLOSED_DISTANCE_MAX - max(ring_dist, pinky_dist)) / 0.10, 0.0, 1.0)
        return float(extended * closed)
    
    def _ok_confidence(self, landmarks: List[Tuple[float, float, float]]) -> float:
        # OK: thumb-index close + middle extended.
        pinch_conf = self._pinch_confidence(landmarks, thumb_id=4, other_id=8)
        wrist = np.array(landmarks[0])
        middle_dist = float(np.linalg.norm(np.array(landmarks[12]) - wrist))
        middle_score = np.clip((middle_dist - 0.15) / 0.10, 0.0, 1.0)
        return float(pinch_conf * middle_score)
    
    def _fist_confidence(self, landmarks: List[Tuple[float, float, float]]) -> float:
        wrist = np.array(landmarks[0])
        tips = [4, 8, 12, 16, 20]
        distances = [float(np.linalg.norm(np.array(landmarks[i]) - wrist)) for i in tips]
        avg_distance = float(np.mean(distances)) if distances else 1.0
        if avg_distance >= FINGER_CLOSED_DISTANCE_MAX:
            return 0.0
        return float(np.clip(1.0 - (avg_distance / FINGER_CLOSED_DISTANCE_MAX), 0.0, 1.0))
    
    def _open_palm_confidence(self, landmarks: List[Tuple[float, float, float]]) -> float:
        wrist = np.array(landmarks[0])
        tips = [4, 8, 12, 16, 20]
        distances = [float(np.linalg.norm(np.array(landmarks[i]) - wrist)) for i in tips]
        if not distances:
            return 0.0
        extended = sum(1 for d in distances if d > 0.20)
        return float(np.clip(extended / 5.0, 0.0, 1.0))
    
    def _detect_swipe(self) -> Optional[Tuple[str, float]]:
        if len(self.position_history) < SWIPE_HISTORY_FRAMES:
            return None
        start_pos = np.array(self.position_history[0][8])
        end_pos = np.array(self.position_history[-1][8])
        movement = end_pos - start_pos

        dx, dy = float(movement[0]), float(movement[1])
        if abs(dx) > SWIPE_DISTANCE_THRESHOLD and abs(dx) > abs(dy):
            conf = float(np.clip(abs(dx) / (SWIPE_DISTANCE_THRESHOLD * 1.5), 0.0, 1.0))
            return ("Swipe_Right", conf) if dx > 0 else ("Swipe_Left", conf)

        if abs(dy) > SWIPE_DISTANCE_THRESHOLD and abs(dy) > abs(dx):
            conf = float(np.clip(abs(dy) / (SWIPE_DISTANCE_THRESHOLD * 1.5), 0.0, 1.0))
            return ("Swipe_Down", conf) if dy > 0 else ("Swipe_Up", conf)

        return None

    def _detect_two_finger_scroll(self) -> Optional[Tuple[str, float]]:
        """
        Two-finger scroll: index + middle extended, ring + pinky closed,
        with vertical motion across recent frames.
        """
        if len(self.position_history) < SCROLL_MIN_DELTA_FRAMES:
            return None

        latest = self.position_history[-1]
        wrist = np.array(latest[0])

        index_dist = float(np.linalg.norm(np.array(latest[8]) - wrist))
        middle_dist = float(np.linalg.norm(np.array(latest[12]) - wrist))
        ring_dist = float(np.linalg.norm(np.array(latest[16]) - wrist))
        pinky_dist = float(np.linalg.norm(np.array(latest[20]) - wrist))

        index_extended = index_dist > 0.20
        middle_extended = middle_dist > 0.20
        ring_closed = ring_dist < FINGER_CLOSED_DISTANCE_MAX
        pinky_closed = pinky_dist < FINGER_CLOSED_DISTANCE_MAX

        if not (index_extended and middle_extended and ring_closed and pinky_closed):
            return None

        # Use the earliest frame that still satisfies the 2‑finger condition
        # as the start of the scroll gesture. This makes the detector more robust
        # in unit tests and real use.
        for start in list(self.position_history)[-SCROLL_MIN_DELTA_FRAMES:]:
            wrist_start = np.array(start[0])
            idx_start = float(np.linalg.norm(np.array(start[8]) - wrist_start))
            mid_start = float(np.linalg.norm(np.array(start[12]) - wrist_start))
            ring_start = float(np.linalg.norm(np.array(start[16]) - wrist_start))
            pinky_start = float(np.linalg.norm(np.array(start[20]) - wrist_start))

            if (
                idx_start > 0.20
                and mid_start > 0.20
                and ring_start < FINGER_CLOSED_DISTANCE_MAX
                and pinky_start < FINGER_CLOSED_DISTANCE_MAX
            ):
                start_y = float((start[8][1] + start[12][1]) / 2.0)
                break
        else:
            return None

        end_y = float((latest[8][1] + latest[12][1]) / 2.0)
        dy = end_y - start_y

        # Lower threshold than swipe: intended to be subtle.
        threshold = SWIPE_DISTANCE_THRESHOLD * 0.45
        if abs(dy) < threshold:
            return None

        conf = float(np.clip(abs(dy) / (threshold * 1.8), 0.0, 1.0))
        return ("TwoFinger_Scroll_Down", conf) if dy > 0 else ("TwoFinger_Scroll_Up", conf)
    
    def count_fingers(self, landmarks: List[Tuple[float, float, float]]) -> int:
        """Count extended fingers"""
        if not landmarks:
            return 0
        
        wrist = np.array(landmarks[0])
        
        # Finger indices
        fingers = {
            'thumb': (4, 3, 2),
            'index': (8, 6, 5),
            'middle': (12, 10, 9),
            'ring': (16, 14, 13),
            'pinky': (20, 18, 17)
        }
        
        extended_count = 0
        
        for finger_name, (tip_idx, pip_idx, mcp_idx) in fingers.items():
            tip = np.array(landmarks[tip_idx])
            pip = np.array(landmarks[pip_idx])
            
            tip_dist = np.linalg.norm(tip - wrist)
            pip_dist = np.linalg.norm(pip - wrist)
            
            # Finger is extended if tip is farther than pip
            if finger_name == 'thumb':
                # Special case for thumb
                if tip[0] < pip[0]:  # Thumb pointing left
                    extended_count += 1
            else:
                if tip_dist > pip_dist * 1.1:
                    extended_count += 1
        
        return extended_count
    
    def get_gesture_name(self) -> str:
        """Get current gesture name"""
        return self.current_gesture
    
    def get_gesture_history(self) -> List[str]:
        """Get recent gesture history"""
        return list(self.gesture_history)
    
    def reset(self):
        """Reset gesture recognizer"""
        self.position_history.clear()
        self.gesture_history.clear()
        self.current_gesture = "None"
        self.gesture_confidence = 0.0
        self._raw_history.clear()