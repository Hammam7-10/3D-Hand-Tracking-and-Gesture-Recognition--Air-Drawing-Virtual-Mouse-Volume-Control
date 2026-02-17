"""
Controllers for Hand Tracking System
Virtual Mouse, Keyboard, and Game Controller
"""
import pyautogui
import numpy as np
from typing import Optional, Tuple
import time
from pynput.keyboard import Key, Controller as KeyboardController
import cv2

from constants import CLICK_DEBOUNCE_MS, MOUSE_MOVE_MARGIN


# Disable PyAutoGUI failsafe
pyautogui.FAILSAFE = False


class VirtualMouse:
    """
    Virtual Mouse Controller using hand gestures
    """
    
    def __init__(self, 
                 screen_width: Optional[int] = None, 
                 screen_height: Optional[int] = None,
                 smoothing: float = 0.5,
                 margin: float = MOUSE_MOVE_MARGIN):
        """
        Initialize Virtual Mouse
        
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            smoothing: Smoothing factor (0-1)
        """
        if screen_width is None or screen_height is None:
            w, h = pyautogui.size()
            screen_width = int(w)
            screen_height = int(h)

        self.screen_width = int(screen_width)
        self.screen_height = int(screen_height)
        self.smoothing = smoothing
        
        # Previous position for smoothing
        self.prev_x = screen_width // 2
        self.prev_y = screen_height // 2
        
        # Click state
        self.is_clicking = False
        self.last_click_time = 0
        self.click_cooldown = CLICK_DEBOUNCE_MS / 1000.0
        
        # Drag state
        self.is_dragging = False
        
        # Active region (to avoid edges)
        self.margin = float(margin)
    
    def move_cursor(self, x: float, y: float):
        """
        Move cursor based on normalized coordinates (0-1)
        
        Args:
            x: Normalized x coordinate
            y: Normalized y coordinate
        """
        # Apply margins
        x = np.clip(x, self.margin, 1 - self.margin)
        y = np.clip(y, self.margin, 1 - self.margin)
        
        # Normalize to active region
        x = (x - self.margin) / (1 - 2 * self.margin)
        y = (y - self.margin) / (1 - 2 * self.margin)
        
        # Convert to screen coordinates
        screen_x = int(x * self.screen_width)
        screen_y = int(y * self.screen_height)
        
        # Apply smoothing
        smooth_x = int(self.smoothing * screen_x + (1 - self.smoothing) * self.prev_x)
        smooth_y = int(self.smoothing * screen_y + (1 - self.smoothing) * self.prev_y)
        
        # Move cursor
        pyautogui.moveTo(smooth_x, smooth_y, duration=0)
        
        # Update previous position
        self.prev_x = smooth_x
        self.prev_y = smooth_y
    
    def click(self, button: str = 'left'):
        """
        Perform mouse click
        
        Args:
            button: 'left', 'right', or 'middle'
        """
        current_time = time.time()
        if current_time - self.last_click_time > self.click_cooldown:
            pyautogui.click(button=button)
            self.last_click_time = current_time
    
    def double_click(self):
        """Perform double click"""
        current_time = time.time()
        if current_time - self.last_click_time > self.click_cooldown:
            pyautogui.doubleClick()
            self.last_click_time = current_time
    
    def start_drag(self):
        """Start dragging"""
        if not self.is_dragging:
            pyautogui.mouseDown()
            self.is_dragging = True
    
    def stop_drag(self):
        """Stop dragging"""
        if self.is_dragging:
            pyautogui.mouseUp()
            self.is_dragging = False
    
    def scroll(self, amount: int):
        """
        Scroll mouse wheel
        
        Args:
            amount: Scroll amount (positive = up, negative = down)
        """
        pyautogui.scroll(amount)


class VirtualKeyboard:
    """
    Virtual Keyboard Controller using hand gestures
    """
    
    def __init__(self):
        """Initialize Virtual Keyboard"""
        self.keyboard = KeyboardController()
        self.last_key_time = 0
        self.key_cooldown = 0.2  # seconds
    
    def press_key(self, key: str):
        """
        Press a key
        
        Args:
            key: Key to press (e.g., 'a', 'space', 'enter')
        """
        current_time = time.time()
        if current_time - self.last_key_time > self.key_cooldown:
            try:
                if hasattr(Key, key):
                    self.keyboard.press(getattr(Key, key))
                    self.keyboard.release(getattr(Key, key))
                else:
                    self.keyboard.press(key)
                    self.keyboard.release(key)
                self.last_key_time = current_time
            except Exception as e:
                print(f"Error pressing key {key}: {e}")
    
    def type_text(self, text: str):
        """
        Type text
        
        Args:
            text: Text to type
        """
        for char in text:
            self.keyboard.press(char)
            self.keyboard.release(char)
            time.sleep(0.05)


class VolumeController:
    """
    System Volume Controller using hand gestures
    """
    
    def __init__(self):
        """Initialize Volume Controller"""
        self.current_volume = 50  # 0-100
        self.last_update_time = 0
        self.update_cooldown = 0.1  # seconds
    
    def set_volume(self, distance: float):
        """
        Set volume based on hand distance
        
        Args:
            distance: Distance between fingers (0-1)
        """
        current_time = time.time()
        if current_time - self.last_update_time > self.update_cooldown:
            # Map distance to volume (0-100)
            volume = int(np.clip(distance * 300, 0, 100))
            
            if abs(volume - self.current_volume) > 5:
                self.current_volume = volume
                self.last_update_time = current_time
                
                # On Linux, use amixer
                try:
                    import subprocess
                    subprocess.run(['amixer', 'set', 'Master', f'{volume}%'], 
                                 capture_output=True)
                except:
                    pass
    
    def get_volume(self) -> int:
        """Get current volume"""
        return self.current_volume


class GameController:
    """
    Game Controller using hand gestures
    Maps gestures to game controls
    """
    
    def __init__(self):
        """Initialize Game Controller"""
        self.keyboard = KeyboardController()
        self.last_action_time = 0
        self.action_cooldown = 0.2
        
        # Key mappings
        self.key_map = {
            'up': 'w',
            'down': 's',
            'left': 'a',
            'right': 'd',
            'jump': 'space',
            'action': 'e',
            'attack': 'f'
        }
    
    def move(self, direction: str):
        """
        Move in direction
        
        Args:
            direction: 'up', 'down', 'left', 'right'
        """
        if direction in self.key_map:
            key = self.key_map[direction]
            self.keyboard.press(key)
            time.sleep(0.1)
            self.keyboard.release(key)
    
    def action(self, action_name: str):
        """
        Perform game action
        
        Args:
            action_name: 'jump', 'action', 'attack'
        """
        current_time = time.time()
        if current_time - self.last_action_time > self.action_cooldown:
            if action_name in self.key_map:
                key = self.key_map[action_name]
                self.keyboard.press(key)
                time.sleep(0.05)
                self.keyboard.release(key)
                self.last_action_time = current_time


class AirDrawing:
    """
    Air Drawing using hand tracking - IMPROVED VERSION
    """
    
    def __init__(self, canvas_size: Tuple[int, int] = (640, 480)):
        """
        Initialize Air Drawing
        
        Args:
            canvas_size: (width, height) of drawing canvas
        """
        self.canvas_width, self.canvas_height = canvas_size
        self.canvas = np.zeros((self.canvas_height, self.canvas_width, 3), dtype=np.uint8)
        
        # Drawing state
        self.is_drawing = False
        self.prev_point = None
        
        # Drawing settings
        self.color = (0, 255, 0)  # Green
        self.thickness = 5  # زيادة السمك لرؤية أفضل
        
        # ===== إضافات جديدة للتحسين =====
        
        # Buffer للنقاط لجعل الخط أكثر سلاسة
        self.point_buffer = []
        self.buffer_size = 5  # عدد النقاط للتنعيم
        
        # Smoothing factor
        self.smoothing_alpha = 0.7  # معامل التنعيم (0.5-0.9 أفضل)
        
        # تتبع آخر نقطة مرسومة فعلياً
        self.last_drawn_point = None
        
        # الحد الأدنى للمسافة بين النقاط لتجنب النقاط المتراكمة
        self.min_distance = 3  # بكسل
        
        # تتبع الوقت لحساب السرعة
        self.last_update_time = time.time()
        
        # تكيف السمك بناءً على السرعة
        self.adaptive_thickness = True
        self.min_thickness = 3
        self.max_thickness = 8
    
    def _smooth_point(self, new_point: Tuple[int, int]) -> Tuple[int, int]:
        """
        تنعيم النقطة باستخدام buffer من النقاط السابقة
        """
        self.point_buffer.append(new_point)
        
        # الحفاظ على حجم الـ buffer
        if len(self.point_buffer) > self.buffer_size:
            self.point_buffer.pop(0)
        
        # حساب المتوسط المرجح (النقاط الأحدث لها وزن أكبر)
        if len(self.point_buffer) == 0:
            return new_point
        
        weights = np.linspace(0.5, 1.0, len(self.point_buffer))
        weights = weights / weights.sum()
        
        smooth_x = sum(p[0] * w for p, w in zip(self.point_buffer, weights))
        smooth_y = sum(p[1] * w for p, w in zip(self.point_buffer, weights))
        
        return (int(smooth_x), int(smooth_y))
    
    def _calculate_distance(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
        """حساب المسافة بين نقطتين"""
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    def _adaptive_thickness_based_on_speed(self, distance: float, time_delta: float) -> int:
        """
        حساب سمك الخط بناءً على سرعة الحركة
        الحركة السريعة = خط أرفع
        الحركة البطيئة = خط أسمك
        """
        if time_delta <= 0:
            return self.thickness
        
        speed = distance / time_delta  # بكسل/ثانية
        
        # تطبيع السرعة (0-1000 بكسل/ثانية)
        normalized_speed = np.clip(speed / 1000.0, 0, 1)
        
        # عكس العلاقة: سرعة عالية = سمك قليل
        thickness = int(self.max_thickness - normalized_speed * (self.max_thickness - self.min_thickness))
        
        return max(self.min_thickness, thickness)
    
    def _draw_smooth_line(self, p1: Tuple[int, int], p2: Tuple[int, int], thickness: int):
        """
        رسم خط ناعم باستخدام Anti-aliasing
        """
        cv2.line(self.canvas, p1, p2, self.color, thickness, cv2.LINE_AA)
    
    def update(self, x: float, y: float, is_drawing: bool):
        """
        Update drawing - IMPROVED VERSION
        
        Args:
            x: Normalized x coordinate (0-1)
            y: Normalized y coordinate (0-1)
            is_drawing: Whether to draw
        """
        current_time = time.time()
        time_delta = current_time - self.last_update_time
        
        # Convert to canvas coordinates
        canvas_x = int(np.clip(x * self.canvas_width, 0, self.canvas_width - 1))
        canvas_y = int(np.clip(y * self.canvas_height, 0, self.canvas_height - 1))
        current_point = (canvas_x, canvas_y)
        
        # تنعيم النقطة
        smoothed_point = self._smooth_point(current_point)
        
        if is_drawing:
            # إذا كانت هذه أول نقطة في السكتة
            if self.last_drawn_point is None:
                self.last_drawn_point = smoothed_point
                # رسم نقطة صغيرة للبداية
                cv2.circle(self.canvas, smoothed_point, self.thickness // 2, self.color, -1)
            else:
                # حساب المسافة من آخر نقطة مرسومة
                distance = self._calculate_distance(self.last_drawn_point, smoothed_point)
                
                # رسم فقط إذا كانت المسافة كافية (لتجنب النقاط المتراكمة)
                if distance >= self.min_distance:
                    # حساب السمك التكيفي بناءً على السرعة
                    if self.adaptive_thickness:
                        thickness = self._adaptive_thickness_based_on_speed(distance, time_delta)
                    else:
                        thickness = self.thickness
                    
                    # رسم خط ناعم
                    self._draw_smooth_line(self.last_drawn_point, smoothed_point, thickness)
                    
                    # تحديث آخر نقطة مرسومة
                    self.last_drawn_point = smoothed_point
        else:
            # إيقاف الرسم - إعادة تعيين الحالة
            self.last_drawn_point = None
            self.point_buffer.clear()
        
        self.last_update_time = current_time
    
    def clear_canvas(self):
        """Clear drawing canvas"""
        self.canvas = np.zeros((self.canvas_height, self.canvas_width, 3), dtype=np.uint8)
        self.point_buffer.clear()
        self.last_drawn_point = None
    
    def change_color(self, color: Tuple[int, int, int]):
        """
        Change drawing color
        
        Args:
            color: BGR color tuple
        """
        self.color = color
    
    def change_thickness(self, thickness: int):
        """
        Change drawing thickness
        
        Args:
            thickness: Line thickness in pixels
        """
        self.thickness = max(1, thickness)
        self.min_thickness = max(1, thickness - 2)
        self.max_thickness = thickness + 3
    
    def set_adaptive_thickness(self, enabled: bool):
        """
        Enable or disable adaptive thickness based on speed
        
        Args:
            enabled: True to enable adaptive thickness
        """
        self.adaptive_thickness = enabled
    
    def get_canvas(self) -> np.ndarray:
        """Get current canvas"""
        return self.canvas.copy()
