"""
Simple camera diagnostics script for Windows/Linux.

Run:
    python camera_diag.py

It will try camera indices 0..5 and print which ones can be opened.
Use a working index with:
    python main.py --camera <index>
"""

import cv2


def main() -> None:
    print(">>> Camera diagnostics (indices 0..5)")
    for idx in range(6):
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW) if hasattr(cv2, "CAP_DSHOW") else cv2.VideoCapture(idx)
        opened = cap.isOpened()
        print(f"Index {idx}: opened={opened}")
        if opened:
            ret, frame = cap.read()
            print(f"  read_ok={ret}, shape={getattr(frame, 'shape', None)}")
        cap.release()


if __name__ == "__main__":
    main()

