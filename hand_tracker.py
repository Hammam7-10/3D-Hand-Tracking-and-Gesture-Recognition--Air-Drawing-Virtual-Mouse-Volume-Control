
import numpy as np
import cv2
import mediapipe as mp
from typing import Optional, List, Tuple
import time

from constants import (
    EKF_BASE_MEASUREMENT_NOISE,
    EKF_BASE_PROCESS_NOISE,
    EKF_INITIAL_COVARIANCE,
    EKF_SPEED_FAST,
)


class AdaptiveExtendedKalmanFilter:
    def __init__(self):
        # State vector: [x, y, z, vx, vy, vz]
        self.state = np.zeros(6)
        
        # Covariance matrix
        self.P = np.eye(6) * EKF_INITIAL_COVARIANCE
        
        # Base noise covariances (adapted per step)
        self.base_Q = np.eye(6) * EKF_BASE_PROCESS_NOISE
        self.base_R = np.eye(3) * EKF_BASE_MEASUREMENT_NOISE
        self.Q = self.base_Q.copy()
        
        # Measurement noise covariance
        self.R = self.base_R.copy()
        
        # Last update time
        self.last_time = time.time()
        self._last_measurement = None
        
        # Measurement matrix
        self.H = np.array([
            [1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0]
        ])
    
    def predict(self, dt: float):
        """Predict next state"""
        if dt <= 0:
            dt = 1e-3
        # State transition matrix
        F = np.array([
            [1, 0, 0, dt, 0, 0],
            [0, 1, 0, 0, dt, 0],
            [0, 0, 1, 0, 0, dt],
            [0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 1]
        ])
        
        # Predict state
        self.state = F @ self.state
        
        # Predict covariance
        self.P = F @ self.P @ F.T + self.Q
    
    def update(self, measurement: np.ndarray, dt: float, measurement_confidence: float = 1.0):
        """
        Update state with measurement (adaptive Q/R).

        Args:
            measurement: np.ndarray shape (3,) -> (x,y,z) in normalized coords.
            dt: seconds since last update.
            measurement_confidence: proxy confidence in [0,1].
        """
        self._adapt_noise(measurement, dt, measurement_confidence)

        # Innovation
        y = measurement - self.H @ self.state
        
        # Innovation covariance
        S = self.H @ self.P @ self.H.T + self.R
        
        # Kalman gain
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # Update state
        self.state = self.state + K @ y
        
        # Update covariance
        self.P = (np.eye(6) - K @ self.H) @ self.P

    def _adapt_noise(self, measurement: np.ndarray, dt: float, measurement_confidence: float) -> None:
        """
        Adapt Q/R based on estimated motion speed and measurement confidence.

        - When the hand is steady: increase R (more smoothing), reduce Q (stability).
        - When the hand moves fast: increase Q (responsiveness), reduce R (follow).
        - Low confidence always increases R.
        """
        if dt <= 0:
            dt = 1e-3

        if self._last_measurement is None:
            speed = 0.0
        else:
            speed = float(np.linalg.norm(measurement - self._last_measurement) / dt)

        motion_factor = float(np.clip(speed / EKF_SPEED_FAST, 0.0, 1.0))
        q_scale = 0.05 + 1.95 * motion_factor  # 0.05..2.0
        r_motion_scale = 5.0 - 4.2 * motion_factor  # 5.0..0.8

        conf = float(np.clip(measurement_confidence, 0.2, 1.0))
        r_conf_scale = 1.0 / conf

        self.Q = self.base_Q * q_scale
        self.R = self.base_R * (r_motion_scale * r_conf_scale)

        self._last_measurement = measurement.copy()
    
    def get_position(self) -> np.ndarray:
        """Get current position estimate"""
        return self.state[:3]
    
    def get_velocity(self) -> np.ndarray:
        """Get current velocity estimate"""
        return self.state[3:]


class HandTracker:
    """
    Advanced Hand Gesture Tracking System with EKF smoothing
    """
    
    def __init__(self, 
                 max_num_hands: int = 1,
                 min_detection_confidence: float = 0.7,
                 min_tracking_confidence: float = 0.5,
                 use_ekf: bool = True):
        """
        Initialize Hand Tracker
        
        Args:
            max_num_hands: Maximum number of hands to detect
            min_detection_confidence: Minimum confidence for detection
            min_tracking_confidence: Minimum confidence for tracking
            use_ekf: Whether to use Extended Kalman Filter
        """
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        # MediaPipe drawing utilities
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # EKF for each landmark (21 landmarks)
        self.use_ekf = use_ekf
        self.ekf_filters = [AdaptiveExtendedKalmanFilter() for _ in range(21)]
        
        # Hand landmarks
        self.landmarks = None
        self.handedness = None
        self.measurement_confidence = 0.0
        
        # Tracking state
        self.is_tracking = False
        self.last_detection_time = 0
    
    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, bool]:
        """
        Process video frame and detect hands
        
        Args:
            frame: Input BGR image
            
        Returns:
            Processed frame and detection status
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process frame
        results = self.hands.process(rgb_frame)
        
        # Update tracking state
        if results.multi_hand_landmarks:
            self.is_tracking = True
            self.last_detection_time = time.time()
            
            # Get first hand
            hand_landmarks = results.multi_hand_landmarks[0]
            handed = results.multi_handedness[0].classification[0]
            self.handedness = handed.label
            # Proxy confidence (0..1). MediaPipe exposes a handedness score,
            # which is not perfect but improves adaptive filtering vs a constant.
            self.measurement_confidence = float(getattr(handed, "score", 0.8))
            
            # Extract and smooth landmarks
            self.landmarks = self._extract_landmarks(hand_landmarks, frame.shape)
            
            # Draw landmarks
            self.mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                self.mp_hands.HAND_CONNECTIONS,
                self.mp_drawing_styles.get_default_hand_landmarks_style(),
                self.mp_drawing_styles.get_default_hand_connections_style()
            )
        else:
            self.is_tracking = False
            self.landmarks = None
            self.measurement_confidence = 0.0
        
        return frame, self.is_tracking
    
    def _extract_landmarks(self, 
                          hand_landmarks, 
                          frame_shape: Tuple[int, int, int]) -> List[Tuple[float, float, float]]:
        """Extract and optionally smooth landmarks using EKF"""
        h, w, _ = frame_shape
        landmarks = []
        
        current_time = time.time()
        meas_conf = float(np.clip(self.measurement_confidence, 0.0, 1.0))
        
        for idx, landmark in enumerate(hand_landmarks.landmark):
            # Raw measurement
            measurement = np.array([
                landmark.x,
                landmark.y,
                landmark.z
            ])
            
            if self.use_ekf:
                # Calculate time delta
                dt = current_time - self.ekf_filters[idx].last_time
                self.ekf_filters[idx].last_time = current_time
                
                # Predict and update
                self.ekf_filters[idx].predict(dt)
                self.ekf_filters[idx].update(measurement, dt=dt, measurement_confidence=meas_conf)
                
                # Get smoothed position
                smoothed_pos = self.ekf_filters[idx].get_position()
                landmarks.append(tuple(smoothed_pos))
            else:
                landmarks.append((landmark.x, landmark.y, landmark.z))
        
        return landmarks
    
    def get_landmark(self, landmark_id: int) -> Optional[Tuple[float, float, float]]:
        """Get specific landmark by ID (0-20)"""
        if self.landmarks and 0 <= landmark_id < len(self.landmarks):
            return self.landmarks[landmark_id]
        return None
    
    def get_finger_tip(self, finger_name: str) -> Optional[Tuple[float, float, float]]:
        """
        Get finger tip position
        
        Args:
            finger_name: 'thumb', 'index', 'middle', 'ring', or 'pinky'
        """
        finger_tips = {
            'thumb': 4,
            'index': 8,
            'middle': 12,
            'ring': 16,
            'pinky': 20
        }
        
        if finger_name.lower() in finger_tips:
            return self.get_landmark(finger_tips[finger_name.lower()])
        return None
    
    def get_palm_center(self) -> Optional[Tuple[float, float, float]]:
        """Calculate palm center position"""
        if not self.landmarks:
            return None
        
        # Average of wrist and base of middle finger
        wrist = np.array(self.landmarks[0])
        middle_base = np.array(self.landmarks[9])
        
        palm_center = (wrist + middle_base) / 2
        return tuple(palm_center)
    
    def get_hand_bounding_box(self, 
                             frame_shape: Tuple[int, int, int]) -> Optional[Tuple[int, int, int, int]]:
        """Get bounding box around hand"""
        if not self.landmarks:
            return None
        
        h, w, _ = frame_shape
        
        x_coords = [lm[0] * w for lm in self.landmarks]
        y_coords = [lm[1] * h for lm in self.landmarks]
        
        x_min, x_max = int(min(x_coords)), int(max(x_coords))
        y_min, y_max = int(min(y_coords)), int(max(y_coords))
        
        # Add padding
        padding = 20
        x_min = max(0, x_min - padding)
        y_min = max(0, y_min - padding)
        x_max = min(w, x_max + padding)
        y_max = min(h, y_max + padding)
        
        return (x_min, y_min, x_max, y_max)
    
    def is_fist(self) -> bool:
        """Detect if hand is making a fist"""
        if not self.landmarks:
            return False
        
        # Check if all fingers are closed
        wrist = np.array(self.landmarks[0])
        
        # Check each finger tip distance to wrist
        finger_tips = [4, 8, 12, 16, 20]
        distances = []
        
        for tip_id in finger_tips:
            tip = np.array(self.landmarks[tip_id])
            distance = np.linalg.norm(tip - wrist)
            distances.append(distance)
        
        # If all fingertips are close to wrist, it's a fist
        avg_distance = np.mean(distances)
        return avg_distance < 0.15
    
    def is_open_palm(self) -> bool:
        """Detect if hand is showing open palm"""
        if not self.landmarks:
            return False
        
        # Check if all fingers are extended
        wrist = np.array(self.landmarks[0])
        
        finger_tips = [4, 8, 12, 16, 20]
        extended_count = 0
        
        for tip_id in finger_tips:
            tip = np.array(self.landmarks[tip_id])
            distance = np.linalg.norm(tip - wrist)
            if distance > 0.2:
                extended_count += 1
        
        return extended_count >= 4
    
    def get_pinch_distance(self) -> Optional[float]:
        """Get distance between thumb and index finger (for pinch gesture)"""
        thumb_tip = self.get_finger_tip('thumb')
        index_tip = self.get_finger_tip('index')
        
        if thumb_tip and index_tip:
            distance = np.linalg.norm(
                np.array(thumb_tip) - np.array(index_tip)
            )
            return distance
        return None
    
    def release(self):
        """Release resources"""
        self.hands.close()
