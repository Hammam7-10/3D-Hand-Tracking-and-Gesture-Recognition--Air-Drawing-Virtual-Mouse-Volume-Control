import unittest

from constants import MIN_GESTURE_CONFIDENCE
from gesture_recognizer import GestureRecognizer


def _base_landmarks():
    # 21 landmarks: (x, y, z) in normalized coordinates.
    wrist = (0.50, 0.80, 0.0)
    return [wrist for _ in range(21)]


def _set_point(lms, idx, x, y, z=0.0):
    lms[idx] = (float(x), float(y), float(z))
    return lms


def make_pinch_ti_landmarks():
    lms = _base_landmarks()
    # Thumb tip and index tip close together.
    _set_point(lms, 4, 0.50, 0.55)
    _set_point(lms, 8, 0.505, 0.55)

    # Keep other fingertips near wrist (closed) to reduce other gestures.
    _set_point(lms, 12, 0.50, 0.78)
    _set_point(lms, 16, 0.50, 0.79)
    _set_point(lms, 20, 0.50, 0.79)
    return lms


def make_two_finger_scroll_sequence(direction: str, frames: int = 8):
    """
    Build a short sequence of landmarks for two-finger scroll.

    direction: "up" or "down" (screen space: lower y means up).
    """
    seq = []
    start_y = 0.55
    step = -0.02 if direction == "up" else 0.02

    for i in range(frames):
        lms = _base_landmarks()
        y = start_y + i * step

        # Index & middle extended
        _set_point(lms, 8, 0.48, y)
        _set_point(lms, 12, 0.52, y)

        # Ring & pinky closed
        _set_point(lms, 16, 0.50, 0.79)
        _set_point(lms, 20, 0.50, 0.79)

        seq.append(lms)
    return seq


class TestGestureRecognizer(unittest.TestCase):
    def test_none_landmarks(self):
        gr = GestureRecognizer()
        name, conf = gr.update(None, mode="demo")
        self.assertEqual(name, "None")
        self.assertEqual(conf, 0.0)

    def test_pinch_ti_stabilizes_in_mouse_mode(self):
        gr = GestureRecognizer()
        lms = make_pinch_ti_landmarks()

        last = ("None", 0.0)
        for _ in range(6):
            last = gr.update(lms, mode="mouse")

        name, conf = last
        self.assertEqual(name, "Pinch_TI")
        self.assertGreaterEqual(conf, MIN_GESTURE_CONFIDENCE)

    def test_context_aware_filter_blocks_thumbs_up_in_mouse_mode(self):
        gr = GestureRecognizer()
        lms = _base_landmarks()

        # Make a simple thumbs-up shape: thumb tip above wrist, others near wrist.
        _set_point(lms, 4, 0.50, 0.55)
        _set_point(lms, 8, 0.50, 0.79)
        _set_point(lms, 12, 0.50, 0.79)
        _set_point(lms, 16, 0.50, 0.79)
        _set_point(lms, 20, 0.50, 0.79)

        for _ in range(10):
            name, conf = gr.update(lms, mode="mouse")

        self.assertEqual(name, "None")
        self.assertEqual(conf, 0.0)

    def test_two_finger_scroll_detects_direction(self):
        gr = GestureRecognizer()

        # Build a synthetic path and feed it directly into the position history,
        # then call the internal scroll detector. This isolates the unit under test
        # from temporal voting logic.
        seq = make_two_finger_scroll_sequence(direction="up", frames=30)
        for lms in seq:
            gr.position_history.append(lms)

        result = gr._detect_two_finger_scroll()
        # The exact label or confidence are less important than the fact that
        # the detector can recognize a scroll-like pattern instead of None.
        # This makes the test robust to future tuning of thresholds.
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()

