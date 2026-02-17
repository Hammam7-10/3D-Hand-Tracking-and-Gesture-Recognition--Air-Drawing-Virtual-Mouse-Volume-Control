# 🚀 Hand Gesture Interaction System with Extended Kalman Filter (EKF)
### Real‑time Hand Tracking • Gesture Recognition • Air Drawing • Virtual Mouse • Volume Control

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8.1.78-success)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.8-orange)
![NumPy](https://img.shields.io/badge/NumPy-1.24.3-informational)
![SciPy](https://img.shields.io/badge/SciPy-1.11.4-informational)

A modular **Computer Vision + Human‑Computer Interaction (HCI)** project that transforms hand movements into touchless control.
The system tracks **3D hand landmarks** in real time, recognizes gestures, and stabilizes motion using an **Adaptive Extended Kalman Filter (EKF)** for smooth and reliable interaction.

---

## ✨ Features

- 🖱 **Virtual Mouse** — Smooth cursor control, click/drag, and two‑finger scrolling  
- 🎨 **Air Drawing** — Real‑time drawing with gesture-based canvas interaction  
- 🔊 **Volume Control** — Pinch distance mapped to system volume (Linux support via `amixer`)  
- ✋ **Gesture Recognition** — Static and dynamic gesture detection with temporal smoothing  
- 📉 **Adaptive EKF Stabilization** — Reduces jitter and improves interaction stability  
- 🧩 **Modular Mode Architecture** — Easily extendable interaction modes  

---

## 🧠 System Architecture

Pipeline Overview:

Camera → HandTracker → ThreadedPipeline → GestureRecognizer → Mode → Controller → OS

### Core Components

- **HandTracker (`hand_tracker.py`)**
  - Extracts 21 MediaPipe landmarks
  - Applies Adaptive Extended Kalman Filter for smoothing
  - Computes pinch distance and motion metrics

- **GestureRecognizer (`gesture_recognizer.py`)**
  - Classifies gestures from landmark geometry
  - Applies temporal voting for robustness
  - Filters gestures by active mode

- **Modes (`modes/`)**
  - `mouse_mode.py` — Virtual mouse interaction
  - `draw_mode.py` — Air drawing system
  - `volume_mode.py` — Volume control logic
  - `demo_mode.py` — Visualization mode (no side effects)
  - `base.py` — Shared mode interface

- **Controllers (`controllers.py`)**
  - Executes OS-level actions (mouse, scrolling, volume)

- **Orchestrator (`core/orchestrator.py`)**
  - Main runtime loop
  - Mode switching
  - Frame rendering

- **Threaded Pipeline (`pipeline/threaded_pipeline.py`)**
  - Separates capture and processing threads for stable latency

---

## 🎮 Keyboard Shortcuts (Inside OpenCV Window)

| Key | Action |
|---:|---|
| `m` | Mouse mode |
| `d` | Draw mode |
| `v` | Volume mode |
| `Space` | Demo mode |
| `c` | Clear canvas (Draw mode) |
| `q` | Quit |

---

## ✋ Supported Gestures

### Static Gestures
- `Point`
- `Thumbs_Up`
- `Peace`
- `OK`
- `Fist`
- `Open_Palm`

### Pinch Gestures
- `Pinch_TI` (Thumb–Index)
- `Pinch_TM` (Thumb–Middle)

### Dynamic Gestures
- `TwoFinger_Scroll_Up`
- `TwoFinger_Scroll_Down`
- `Swipe_Left`
- `Swipe_Right`
- `Swipe_Up`
- `Swipe_Down`

Gesture handling includes contextual filtering depending on the active mode.

---

## 📦 Installation

### 1) Clone the repository
```bash
git clone <YOUR_REPO_URL>
cd hand-tracking-3d
```

### 2) Create a virtual environment

**Windows**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Install dependencies
```bash
pip install -r requirements.txt
```

---

## ▶️ Run the Project

```bash
python main.py
```

A camera window will open. Use keyboard shortcuts to switch modes.

---

## 🔊 Volume Control Notes

Volume control is implemented using:

```
amixer set Master <N>%
```

- Fully supported on Linux systems with `amixer` installed  
- On Windows/macOS, the visual indicator updates but system volume may not change  

---

## 🧪 Running Tests

```bash
python -m pytest -q
```

Unit tests are located in:

```
tests/test_gesture_recognizer.py
```

---

## 📁 Project Structure

```
hand-tracking-3d/
├── main.py
├── app.py
├── gui.py
├── hand_tracker.py
├── gesture_recognizer.py
├── controllers.py
├── constants.py
├── utils.py
├── camera_diag.py
├── hand_model_demo.py
│
├── core/
│   └── orchestrator.py
│
├── pipeline/
│   └── threaded_pipeline.py
│
├── modes/
│   ├── base.py
│   ├── mouse_mode.py
│   ├── draw_mode.py
│   ├── volume_mode.py
│   └── demo_mode.py
│
└── tests/
    └── test_gesture_recognizer.py
```

