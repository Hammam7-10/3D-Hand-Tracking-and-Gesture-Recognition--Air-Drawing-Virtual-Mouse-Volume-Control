"""
Project-wide constants.

This module centralizes configuration values (magic numbers) to improve
maintainability and make tuning easier.
"""

# -----------------------------
# Camera
# -----------------------------
CAMERA_FRAME_WIDTH = 1280
CAMERA_FRAME_HEIGHT = 720
CAMERA_TARGET_FPS = 30

# -----------------------------
# UI / Overlay
# -----------------------------
WINDOW_TITLE = "Hand Gesture Interaction - EKF"
INFO_PANEL_X1Y1 = (10, 10)
INFO_PANEL_X2Y2 = (320, 120)

# -----------------------------
# Gesture recognition
# -----------------------------
# Base thresholds (normalized MediaPipe coordinates)
PINCH_DISTANCE_THRESHOLD = 0.085
POINTING_INDEX_DISTANCE_MIN = 0.20
FINGER_CLOSED_DISTANCE_MAX = 0.15

SWIPE_HISTORY_FRAMES = 10
SWIPE_DISTANCE_THRESHOLD = 0.30

# Temporal smoothing
VOTE_WINDOW_FRAMES = 7
MIN_STABLE_FRAMES = 4
MIN_GESTURE_CONFIDENCE = 0.65

# -----------------------------
# Mouse mode (HCI decision logic)
# -----------------------------
MOUSE_MOVE_MARGIN = 0.10

# Click decision
CLICK_MIN_HOLD_MS = 80
CLICK_DEBOUNCE_MS = 300
CLICK_CONFIDENCE_THRESHOLD = 0.50

# Drag decision
DRAG_START_HOLD_MS = 250

# Scroll
SCROLL_GESTURE_CONFIDENCE_THRESHOLD = 0.75
SCROLL_AMOUNT_PER_TICK = 80
SCROLL_MIN_DELTA_FRAMES = 6

# Feedback
CLICK_FEEDBACK_MS = 120

# -----------------------------
# Volume overlay
# -----------------------------
VOLUME_BAR_WIDTH = 300
VOLUME_BAR_HEIGHT = 30
VOLUME_BAR_MARGIN_PX = 20

# -----------------------------
# Adaptive EKF
# -----------------------------
EKF_INITIAL_COVARIANCE = 1000.0
EKF_BASE_PROCESS_NOISE = 0.10
EKF_BASE_MEASUREMENT_NOISE = 10.0

# Speed normalization (normalized units / second)
EKF_SPEED_FAST = 0.50

