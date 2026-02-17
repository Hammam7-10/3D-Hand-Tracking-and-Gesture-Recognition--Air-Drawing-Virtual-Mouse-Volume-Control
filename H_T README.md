# 🚀 Hand Gesture Interaction System with Extended Kalman Filter

A modular, real-time 3D hand tracking and gesture-based human--computer
interaction framework built using computer vision and probabilistic
filtering techniques.

This system enables touchless interaction through:

-   🖱 Virtual Mouse Control\
-   🎨 Air Drawing\
-   🔊 Volume Control (Linux support via amixer)\
-   ✋ Real-time Gesture Recognition\
-   📐 Extended Kalman Filter (EKF) Motion Stabilization\
-   🧩 Modular Mode-Based Architecture

------------------------------------------------------------------------

## 📌 Overview

This project implements a real-time hand tracking and gesture
interaction system designed with a research-oriented, modular
architecture.

The system integrates:

-   Landmark-based hand tracking\
-   Geometric gesture recognition\
-   Extended Kalman Filtering for jitter reduction\
-   Mode-based behavior abstraction\
-   OS-level control through controller interfaces

The architecture emphasizes scalability, clarity, and separation of
concerns.

------------------------------------------------------------------------

## 🏗 System Architecture

Pipeline Overview:

Camera → Hand Tracker → Processing Pipeline → EKF → Gesture Recognizer →
Mode → Controller → OS

### Layers

**Tracking Layer** - Extracts hand landmarks - Computes pinch distance -
Normalizes coordinates

**Filtering Layer** - Applies Extended Kalman Filter to smooth landmark
motion - Reduces jitter and improves interaction stability

**Gesture Layer** - Detects finger states - Recognizes pinch gestures -
Interprets interaction patterns

**Mode Layer** - Defines interaction behavior (Mouse, Draw, Volume,
Demo)

**Controller Layer** - Executes OS-level commands (mouse movement,
clicks, volume)

------------------------------------------------------------------------

## 📂 Project Structure

    hand-tracking-3d/
    │
    ├── main.py
    ├── app.py
    ├── gui.py
    ├── constants.py
    ├── utils.py
    ├── controllers.py
    ├── gesture_recognizer.py
    ├── hand_tracker.py
    ├── camera_diag.py
    ├── hand_model_demo.py
    │
    ├── core/
    │   ├── orchestrator.py
    │   └── __init__.py
    │
    ├── pipeline/
    │   └── __init__.py
    │
    ├── modes/
    │   ├── base.py
    │   ├── mouse_mode.py
    │   ├── draw_mode.py
    │   ├── demo_mode.py
    │   ├── volume_mode.py
    │   └── __init__.py
    │
    ├── tests/
    │   ├── test_gesture_recognizer.py
    │   └── __init__.py
    │
    ├── requirements.txt
    └── README.md

------------------------------------------------------------------------

## 🔍 Module Explanation

### main.py

Entry point of the application. Launches the orchestrator and
initializes system flow.

### app.py

Handles application lifecycle and integrates tracker, GUI, and modes.

### gui.py

Responsible for visual overlays: - Drawing strokes - Displaying
feedback - Rendering system indicators

### constants.py

Contains tunable system parameters: - Gesture thresholds - Scaling
factors - Drawing configurations - Volume mapping ranges

### utils.py

Utility functions: - Distance calculations - Coordinate
transformations - Normalization helpers

### hand_tracker.py

Core hand tracking module: - Extracts hand landmarks - Computes pinch
distance - Provides structured landmark data

### gesture_recognizer.py

Implements geometric gesture logic: - Pinch detection - Finger state
recognition - Gesture mapping to interaction states

Includes unit tests in: `tests/test_gesture_recognizer.py`

### controllers.py

Abstracts OS-level interaction: - Mouse control - Click actions - Volume
control (Linux via amixer)

### core/orchestrator.py

Central system coordinator: - Connects all modules - Manages active
mode - Controls data flow

### modes/

**base.py** Defines abstract interface for interaction modes.

**mouse_mode.py** Maps hand motion to cursor movement and click
gestures.

**draw_mode.py** Implements air drawing with persistent stroke
rendering.

**volume_mode.py** Maps pinch distance to system volume (Linux
amixer-based).

**demo_mode.py** Visualization and testing mode.

------------------------------------------------------------------------

## 🧠 Extended Kalman Filter (EKF)

The EKF stabilizes 2D landmark coordinates by:

-   Modeling state transitions
-   Updating predictions with measurement correction
-   Reducing jitter
-   Ensuring smooth cursor motion

This significantly improves interaction quality and user experience.

------------------------------------------------------------------------

## ⚙ Installation

### 1️⃣ Clone Repository

    git clone <your-repo-url>
    cd hand-tracking-3d

### 2️⃣ Create Virtual Environment

    python -m venv venv
    source venv/bin/activate

### 3️⃣ Install Dependencies

    pip install -r requirements.txt

------------------------------------------------------------------------

## ▶ Running the Project

    python main.py

Ensure camera permissions are enabled.

------------------------------------------------------------------------

## 💻 Platform Support

  Feature          Windows   Linux   macOS
  ---------------- --------- ------- ---------
  Hand Tracking    ✓         ✓       ✓
  Virtual Mouse    ✓         ✓       ✓
  Air Drawing      ✓         ✓       ✓
  Volume Control   Limited   ✓       Limited

Volume control currently uses Linux `amixer`.

------------------------------------------------------------------------

## 🚀 Future Improvements

-   Cross-platform volume control
-   Multi-hand support
-   Deep learning gesture classification
-   Dynamic gesture sequences
-   GPU acceleration
-   Adaptive filtering models

------------------------------------------------------------------------

## 📚 Academic Value

This project demonstrates:

-   Real-time computer vision systems
-   Landmark-based gesture recognition
-   Probabilistic filtering in HCI
-   Modular CV architecture design

Suitable for:

-   Computer Vision coursework
-   HCI research
-   Gesture-based system prototyping

------------------------------------------------------------------------

## 📄 License

Add your preferred license (MIT recommended).

------------------------------------------------------------------------

## 👤 Author

Developed as a modular computer vision and human--computer interaction
research project.
