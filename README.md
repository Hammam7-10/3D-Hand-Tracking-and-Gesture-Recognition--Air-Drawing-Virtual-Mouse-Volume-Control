# 🚀 Hand Gesture Interaction System with Extended Kalman Filter (EKF)
### Real‑time Hand Tracking • Gesture Recognition • Air Drawing • Virtual Mouse • Volume Control

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8.1.78-success)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.8-orange)
![NumPy](https://img.shields.io/badge/NumPy-1.24.3-informational)
![SciPy](https://img.shields.io/badge/SciPy-1.11.4-informational)

A modular **Computer Vision + HCI** project that turns hand movements into touchless control.
It tracks **3D hand landmarks** in real time, recognizes gestures, and stabilizes motion using an **Adaptive Extended Kalman Filter (EKF)** for smoother interaction.

---

## ✨ Features

- 🖱 **Virtual Mouse**: smooth cursor movement + click/drag + two‑finger scroll
- 🎨 **Air Drawing**: draw in the air with an on‑screen canvas + clear canvas shortcut
- 🔊 **Volume Control**: pinch distance → volume mapping *(Linux `amixer` integration)*
- ✋ **Gesture Recognition**: static + dynamic gestures with **temporal smoothing**
- 📉 **Adaptive EKF Stabilization**: reduces jitter and improves reliability
- 🧩 **Mode‑based architecture**: easy to add new interaction modes

---

## 🧠 How it works

**Camera → HandTracker → ThreadedPipeline → GestureRecognizer → Mode → Controller → OS**

- `hand_tracker.py` extracts MediaPipe’s 21 hand landmarks and smooths motion using `AdaptiveExtendedKalmanFilter`.
- `gesture_recognizer.py` computes gesture confidence from landmark geometry and applies **temporal voting** for stability.
- `modes/` define interaction behavior (mouse/draw/volume/demo).
- `controllers.py` translates mode outputs to OS actions (mouse movement/clicks/scroll and volume control).

---

## 🎮 Keyboard shortcuts (OpenCV window)

| Key | Action |
|---:|---|
| `m` | Mouse mode |
| `d` | Draw mode |
| `v` | Volume mode |
| `Space` | Demo mode *(no side effects)* |
| `c` | Clear canvas *(draw mode)* |
| `q` | Quit |

*(Handled in `core/orchestrator.py`.)*

---

## ✋ Supported gestures

Implemented in `gesture_recognizer.py`:

### Static
- `Point`
- `Thumbs_Up`
- `Peace`
- `OK`
- `Fist`
- `Open_Palm`

### Pinch
- `Pinch_TI` *(thumb–index)*
- `Pinch_TM` *(thumb–middle)*

### Dynamic
- `TwoFinger_Scroll_Up`, `TwoFinger_Scroll_Down`
- `Swipe_Left`, `Swipe_Right`, `Swipe_Up`, `Swipe_Down`

> Modes apply context filtering (e.g., volume mode focuses on `Pinch_TI`).

---

## 📦 Installation

### 1) Clone
```bash
git clone <YOUR_REPO_URL>
cd hand-tracking-3d
```

### 2) Create and activate a virtual environment
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

## ▶️ Run
```bash
python main.py
```

A window will open. Use the keyboard shortcuts to switch modes.

---

## 🔊 Volume control (important note)

Volume control is implemented in `controllers.py` via Linux command:

- `amixer set Master <N>%`

✅ Works on Linux **when** `amixer` exists and the mixer control is named `Master`.  
⚠️ On Windows/macOS, the on‑screen volume indicator still updates, but system volume may not change.

---

## 🧪 Tests
```bash
python -m pytest -q
```

Tests are in `tests/test_gesture_recognizer.py`.

---

## 🗂️ Project structure

```
hand-tracking-3d/
├── main.py                 # Entry point
├── app.py                  # App wiring/lifecycle helpers
├── gui.py                  # UI overlays and drawing helpers
├── hand_tracker.py         # MediaPipe landmarks + EKF smoothing + pinch metrics
├── gesture_recognizer.py   # Gesture classification + temporal smoothing
├── controllers.py          # OS actions (mouse/scroll/volume)
├── constants.py            # Tunable thresholds and constants
├── utils.py                # Shared helpers
├── camera_diag.py          # Camera diagnostics tool
├── hand_model_demo.py      # Hand model / visualization demo
│
├── core/
│   └── orchestrator.py     # Main runtime loop + mode switching + rendering
│
├── pipeline/
│   └── threaded_pipeline.py# Threaded capture/processing for stable latency
│
├── modes/
│   ├── base.py             # Mode interface
│   ├── mouse_mode.py       # Virtual mouse logic
│   ├── draw_mode.py        # Air drawing logic
│   ├── volume_mode.py      # Volume mapping logic
│   └── demo_mode.py        # Read-only demo mode
│
└── tests/
    └── test_gesture_recognizer.py
```

---

## 🧹 GitHub: what NOT to commit

Add this `.gitignore` (recommended):

```gitignore
__pycache__/
*.pyc
.pytest_cache/
.venv/
.vscode/
.DS_Store
Thumbs.db
```

---

## 📄 License

Add a `LICENSE` file (MIT is a common choice) and update this section accordingly.

