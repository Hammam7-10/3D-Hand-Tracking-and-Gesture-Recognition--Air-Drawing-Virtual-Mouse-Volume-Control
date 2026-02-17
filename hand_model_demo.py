import cv2
import mediapipe as mp
from vedo import Plotter, load
import numpy as np


hand = load(
    r"D:\AI_Courss\level2_term2\project_tenah\hand-tracking-3d\models\3d\X Bot.fbx"
)

hand.scale(0.1)
hand.color("lightblue")
hand.rotate_x(-90)

plt = Plotter(title="Hand Gesture Simulation", bg="black", axes=1)
plt.show(hand, interactive=False)

# =========================
# Mediapipe Hand Tracking
# =========================
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
)

cap = cv2.VideoCapture(0)

prev_x, prev_y = 0, 0

# =========================
# Loop
# =========================
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        lm = result.multi_hand_landmarks[0].landmark

        # نستخدم نقطة المعصم (0)
        x = lm[0].x
        y = lm[0].y

        dx = (x - prev_x) * 200
        dy = (y - prev_y) * 200

        # تدوير اليد الصناعية
        hand.rotate_y(dx)
        hand.rotate_x(-dy)

        prev_x, prev_y = x, y

    # تحديث نافذة 3D
    plt.render()

    # عرض الكاميرا
    cv2.putText(
        frame,
        "Real Hand",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 255, 0),
        2,
    )
    cv2.imshow("Webcam", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

# =========================
# Cleanup
# =========================
cap.release()
cv2.destroyAllWindows()
plt.close()

