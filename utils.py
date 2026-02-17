"""
Utility Functions for Hand Tracking System
"""
import numpy as np
import cv2
from typing import List, Tuple, Optional


def calculate_distance(point1: Tuple[float, float, float], 
                       point2: Tuple[float, float, float]) -> float:
    """Calculate Euclidean distance between two 3D points"""
    return np.sqrt(sum((a - b) ** 2 for a, b in zip(point1, point2)))


def calculate_angle(point1: np.ndarray, 
                   point2: np.ndarray, 
                   point3: np.ndarray) -> float:
    """Calculate angle between three points in degrees"""
    vector1 = point1 - point2
    vector2 = point3 - point2
    
    cos_angle = np.dot(vector1, vector2) / (
        np.linalg.norm(vector1) * np.linalg.norm(vector2) + 1e-6
    )
    angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
    return np.degrees(angle)


def smooth_value(current: float, previous: float, alpha: float = 0.5) -> float:
    """Exponential smoothing for values"""
    return alpha * current + (1 - alpha) * previous


def normalize_coordinates(x: float, y: float, 
                         width: int, height: int) -> Tuple[float, float]:
    """Normalize coordinates to [0, 1] range"""
    return x / width, y / height


def denormalize_coordinates(x: float, y: float, 
                           width: int, height: int) -> Tuple[int, int]:
    """Convert normalized coordinates back to pixel coordinates"""
    return int(x * width), int(y * height)


def is_finger_extended(finger_tip: np.ndarray, 
                      finger_pip: np.ndarray, 
                      finger_mcp: np.ndarray, 
                      wrist: np.ndarray) -> bool:
    """Check if a finger is extended based on joint positions"""
    # Calculate distances
    tip_to_wrist = np.linalg.norm(finger_tip - wrist)
    pip_to_wrist = np.linalg.norm(finger_pip - wrist)
    
    # Finger is extended if tip is farther from wrist than PIP joint
    return tip_to_wrist > pip_to_wrist * 1.1


def count_extended_fingers(landmarks: List[Tuple[float, float, float]]) -> int:
    """Count number of extended fingers"""
    if len(landmarks) < 21:
        return 0
    
    landmarks_array = np.array(landmarks)
    wrist = landmarks_array[0]
    
    # Finger tip and joint indices
    fingers = {
        'thumb': (4, 3, 2),
        'index': (8, 6, 5),
        'middle': (12, 10, 9),
        'ring': (16, 14, 13),
        'pinky': (20, 18, 17)
    }
    
    extended_count = 0
    for finger_name, (tip_idx, pip_idx, mcp_idx) in fingers.items():
        if finger_name == 'thumb':
            # Special case for thumb (horizontal movement)
            if landmarks_array[tip_idx][0] < landmarks_array[pip_idx][0]:
                extended_count += 1
        else:
            if is_finger_extended(
                landmarks_array[tip_idx],
                landmarks_array[pip_idx],
                landmarks_array[mcp_idx],
                wrist
            ):
                extended_count += 1
    
    return extended_count


def draw_hand_landmarks(image: np.ndarray, 
                       landmarks: List[Tuple[float, float, float]], 
                       connections: List[Tuple[int, int]]) -> np.ndarray:
    """Draw hand landmarks and connections on image"""
    h, w, _ = image.shape
    
    # Draw connections
    for connection in connections:
        start_idx, end_idx = connection
        if start_idx < len(landmarks) and end_idx < len(landmarks):
            start_point = denormalize_coordinates(
                landmarks[start_idx][0], 
                landmarks[start_idx][1], 
                w, h
            )
            end_point = denormalize_coordinates(
                landmarks[end_idx][0], 
                landmarks[end_idx][1], 
                w, h
            )
            cv2.line(image, start_point, end_point, (0, 255, 0), 2)
    
    # Draw landmarks
    for landmark in landmarks:
        point = denormalize_coordinates(landmark[0], landmark[1], w, h)
        cv2.circle(image, point, 5, (255, 0, 0), -1)
    
    return image


def draw_info_panel(image: np.ndarray, 
                   fps: float, 
                   gesture: str, 
                   mode: str,
                   confidence: float = 0.0) -> np.ndarray:
    """Draw information panel on image"""
    # Semi-transparent background
    overlay = image.copy()
    cv2.rectangle(overlay, (10, 10), (300, 120), (0, 0, 0), -1)
    image = cv2.addWeighted(overlay, 0.6, image, 0.4, 0)
    
    # Text information
    cv2.putText(image, f"FPS: {fps:.1f}", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    if gesture != "None":
        gesture_text = f"Gesture: {gesture} ({confidence:.2f})"
    else:
        gesture_text = "Gesture: None"
    cv2.putText(image, gesture_text, (20, 70), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    cv2.putText(image, f"Mode: {mode}", (20, 100), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    return image


class MovingAverageFilter:
    """Simple moving average filter for smoothing"""
    
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.values = []
    
    def update(self, value: float) -> float:
        """Add new value and return filtered result"""
        self.values.append(value)
        if len(self.values) > self.window_size:
            self.values.pop(0)
        return np.mean(self.values)
    
    def reset(self):
        """Reset the filter"""
        self.values = []


class FPSCounter:
    """FPS counter for performance monitoring"""
    
    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self.timestamps = []
    
    def update(self, timestamp: float) -> float:
        """Update with new timestamp and return current FPS"""
        self.timestamps.append(timestamp)
        if len(self.timestamps) > self.window_size:
            self.timestamps.pop(0)
        
        if len(self.timestamps) < 2:
            return 0.0
        
        time_diff = self.timestamps[-1] - self.timestamps[0]
        return (len(self.timestamps) - 1) / (time_diff + 1e-6)
