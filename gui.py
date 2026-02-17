"""
واجهة رسومية عصرية وبسيطة لتشغيل نظام تتبع اليد.

- اختيار وضع التشغيل: Demo / Mouse / Volume / Draw
- اختيار رقم الكاميرا
- تفعيل/إلغاء EKF
- زر "ابدأ" لتشغيل النظام مع نافذة OpenCV المعتادة

ملاحظة:
- نافذة الفيديو ما زالت تُعرض بواسطة OpenCV (كما في السابق) لضمان الأداء.
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk, messagebox

from core.orchestrator import HandTrackingOrchestrator


class HandTrackingGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        # ===== إعدادات النافذة الأساسية =====
        self.title("Hand Gesture Interaction - GUI")
        self.geometry("520x360")
        self.resizable(False, False)

        # ألوان وخطوط بسيطة تعطي شعوراً عصرياً
        self.configure(bg="#121212")

        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure(
            "TLabel",
            background="#121212",
            foreground="#EEEEEE",
            font=("Segoe UI", 11),
        )
        style.configure(
            "TButton",
            font=("Segoe UI", 11, "bold"),
            padding=6,
        )
        style.configure(
            "TCombobox",
            padding=4,
            relief="flat",
        )

        # ===== حالة التشغيل =====
        self._runner_thread: threading.Thread | None = None
        self._orchestrator: HandTrackingOrchestrator | None = None
        self._running = False

        self._build_layout()

    # ------------------------------------------------------------------ #
    # بناء الواجهة
    # ------------------------------------------------------------------ #
    def _build_layout(self) -> None:
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill="both", expand=True)

        # عنوان علوي
        title_lbl = ttk.Label(
            main_frame,
            text="نظام التفاعل بإيماءات اليد",
            font=("Segoe UI", 14, "bold"),
            foreground="#00E676",
        )
        title_lbl.pack(anchor="center", pady=(0, 10))

        subtitle_lbl = ttk.Label(
            main_frame,
            text="واجهة تحكم عصرية وسلسة",
            foreground="#B0BEC5",
        )
        subtitle_lbl.pack(anchor="center", pady=(0, 15))

        # خط فاصل
        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=10)

        # شبكة الخيارات
        grid = ttk.Frame(main_frame)
        grid.pack(fill="x", pady=10)

        # وضع التشغيل
        ttk.Label(grid, text="وضع التشغيل:").grid(row=0, column=0, sticky="w", pady=5)
        self.mode_var = tk.StringVar(value="demo")
        self.mode_combo = ttk.Combobox(
            grid,
            textvariable=self.mode_var,
            state="readonly",
            values=["demo", "mouse", "volume", "draw"],
            width=15,
        )
        self.mode_combo.grid(row=0, column=1, sticky="w", pady=5, padx=(10, 0))

        # رقم الكاميرا
        ttk.Label(grid, text="رقم الكاميرا:").grid(row=1, column=0, sticky="w", pady=5)
        self.cam_var = tk.IntVar(value=0)
        self.cam_spin = ttk.Spinbox(
            grid,
            from_=0,
            to=10,
            textvariable=self.cam_var,
            width=5,
        )
        self.cam_spin.grid(row=1, column=1, sticky="w", pady=5, padx=(10, 0))

        # EKF
        self.ekf_var = tk.BooleanVar(value=True)
        self.ekf_check = ttk.Checkbutton(
            grid,
            text="تنعيم الحركة باستخدام EKF",
            variable=self.ekf_var,
        )
        self.ekf_check.grid(row=2, column=0, columnspan=2, sticky="w", pady=5)

        # مساحة فارغة
        grid.columnconfigure(2, weight=1)

        # خط فاصل
        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=10)

        # أزرار التشغيل
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)

        self.start_btn = ttk.Button(
            btn_frame,
            text="بدء التتبع",
            command=self._on_start,
        )
        self.start_btn.pack(side="left", padx=(0, 10))

        self.stop_btn = ttk.Button(
            btn_frame,
            text="إيقاف",
            command=self._on_stop,
            state="disabled",
        )
        self.stop_btn.pack(side="left")

        # حالة النظام
        self.status_var = tk.StringVar(
            value="الحالة: جاهز. اختر الإعدادات واضغط (بدء التتبع)."
        )
        status_lbl = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            foreground="#CFD8DC",
            wraplength=460,
            justify="right",
        )
        status_lbl.pack(fill="x", pady=(10, 5))

        # خط فاصل
        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=10)

        # تذييل (حقوق وتطوير)
        footer_text = (
            "تطوير: م/عبدالعليم القانص & م/همام الذيباني\n"
            "تحت إشراف: م/أيمن طينة"
        )
        footer_lbl = ttk.Label(
            main_frame,
            text=footer_text,
            foreground="#78909C",
            font=("Segoe UI", 9),
            justify="center",
        )
        footer_lbl.pack(anchor="center", pady=(0, 0))

    # ------------------------------------------------------------------ #
    # تشغيل/إيقاف الأوركستريتور
    # ------------------------------------------------------------------ #
    def _run_orchestrator(self, mode: str, camera_id: int, use_ekf: bool) -> None:
        """
        تُشغَّل في Thread منفصل حتى لا تُجمّد واجهة tkinter.
        """
        try:
            self._orchestrator = HandTrackingOrchestrator(mode=mode, use_ekf=use_ekf)
            self._set_status(
                f"الحالة: يعمل ({mode}) على الكاميرا {camera_id}. "
                f"أغلق نافذة الفيديو أو اضغط Q من داخلها للإيقاف."
            )
            self._orchestrator.run(camera_id=camera_id)
        except Exception as exc:
            self._set_status(f"حدث خطأ أثناء التشغيل: {exc}")
            messagebox.showerror("خطأ", f"حدث خطأ أثناء التشغيل:\n{exc}")
        finally:
            # عند انتهاء التشغيل (عاديًا أو بخطأ) نعيد الأزرار لوضعها الطبيعي
            self._running = False
            self._orchestrator = None
            self._update_buttons()

    def _on_start(self) -> None:
        if self._running:
            return

        mode = self.mode_var.get()
        camera_id = int(self.cam_var.get())
        use_ekf = bool(self.ekf_var.get())

        self._running = True
        self._update_buttons()
        self._set_status("جاري تشغيل النظام... سيتم فتح نافذة الفيديو خلال لحظات.")

        self._runner_thread = threading.Thread(
            target=self._run_orchestrator,
            args=(mode, camera_id, use_ekf),
            daemon=True,
        )
        self._runner_thread.start()

    def _on_stop(self) -> None:
        if not self._running:
            return
        if self._orchestrator is not None:
            self._orchestrator.request_stop()
            self._set_status("جاري إيقاف النظام... الرجاء الانتظار أو إغلاق نافذة الفيديو.")

    def _update_buttons(self) -> None:
        if self._running:
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.mode_combo.configure(state="disabled")
            self.cam_spin.configure(state="disabled")
            self.ekf_check.configure(state="disabled")
        else:
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.mode_combo.configure(state="readonly")
            self.cam_spin.configure(state="normal")
            self.ekf_check.configure(state="normal")

    def _set_status(self, text: str) -> None:
        self.status_var.set(text)


def main() -> None:
    app = HandTrackingGUI()
    app.mainloop()


if __name__ == "__main__":
    main()

