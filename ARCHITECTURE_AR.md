## نظرة عامة على المشروع

هذا المشروع هو **نظام تفاعل بإيماءات اليد مع تنعيم بالحركة (Extended Kalman Filter - EKF)**، يسمح لك بـ:

- **متابعة اليد في الزمن الحقيقي** باستخدام MediaPipe.
- **تنعيم الحركة** والتقليل من الاهتزاز باستخدام EKF لكل نقطة من نقاط اليد الـ 21.
- **التعرف على الإيماءات (Gestures)** وتحويلها إلى:
  - **تحكم بالماوس** (تحريك، كلك يسار/يمين، سحب وإفلات، تمرير Scroll).
  - **رسم في الهواء**.
  - **التحكم في مستوى الصوت**.

التشغيل الرئيسي يكون عبر:

```text
python main.py --mode [demo|mouse|draw|volume] --camera N --no-ekf
```

حيث يقوم `main.py` بإنشاء الـ **Orchestrator** الذي يربط بين:
الكاميرا → `HandTracker` → `GestureRecognizer` → `Mode` (مثل `MouseMode`) → أنظمة التحكم `controllers`.

---

## خريطة الملفات والمجلدات

- **`main.py`**: نقطة الدخول الرئيسية للبرنامج (CLI).
- **`core/orchestrator.py`**: العقل الذي يربط بين التتبع، الإيماءات، وأنماط التفاعل (المودز).
- **`pipeline/threaded_pipeline.py`**: إدارة الكاميرا والمعالجة في ثريدات منفصلة (Real-time).
- **`hand_tracker.py`**: تتبع اليد + EKF لكل Landmark.
- **`gesture_recognizer.py`**: خوارزمية التعرف على الإيماءات (ثابتة + ديناميكية).
- **`modes/`**:
  - `base.py`: واجهة مجردة لجميع المودز.
  - `demo_mode.py`: عرض تتبع اليد فقط بدون تأثيرات جانبية.
  - `mouse_mode.py`: التحكم بالماوس.
  - `draw_mode.py`: الرسم في الهواء.
  - `volume_mode.py`: التحكم بالصوت.
- **`controllers.py`**:
  - `VirtualMouse`: التحكم الفعلي بالماوس (PyAutoGUI).
  - `VolumeController`: التحكم بالصوت (حاليًا مهيأ أكثر لأنظمة Linux).
  - `AirDrawing`: إدارة لوحة الرسم في وضع الرسم.
  - `VirtualKeyboard` / `GameController`: موجودة لكن **غير مستخدمة حاليًا** في الكود الرئيسي (جاهزة للتوسّع مستقبلاً).
- **`constants.py`**: جميع الثوابت المهمة (حساسية الإيماءات، أزمنة الـ debounce، إعدادات EKF، إلخ).
- **`utils.py`**: دوال مساعدة (حساب زوايا، مسافات، FPS، لوحات معلومات…).
- **`tests/test_gesture_recognizer.py`**: اختبارات لوحدة التعرف على الإيماءات.
- **`camera_diag.py`**: سكربت مستقل لاختبار الكاميرات المتاحة في النظام (تشخيص فقط).
- **`hand_model_demo.py`**: سكربت تجريبي لعرض نموذج 3D لليد باستخدام Vedo + MediaPipe (**تجريبي / غير مرتبط بالتشغيل الرئيسي**).
- **`app.py`**: سكربت بسيط يقوم بتجميع محتوى كل الملفات في ملف واحد (`all_codes.txt`) لغرض المراجعة أو الدراسة (**أداة مساعدة، غير مستخدم في التشغيل**).
- **`README.md`**: شرح عام للمشروع (عربي وإنجليزي مبسط).
- **`ARCHITECTURE_AR.md`**: هذا الملف – شرح معماري تفصيلي بالعربية.
- مجلدات **`__pycache__`** داخل المشروع:
  - تحتوي فقط على ملفات `.pyc` التي ينشئها Python تلقائيًا للتسريع.
  - **ليست جزءًا من منطق المشروع** ويمكن حذفها بأمان في أي وقت (يُعاد توليدها تلقائيًا).

### خلاصة الاستخدام الفعلي

- **يتم استخدام**:
  - `main.py`, `core/orchestrator.py`, `pipeline/threaded_pipeline.py`,
  - `hand_tracker.py`, `gesture_recognizer.py`,
  - `modes/*.py`, `controllers.py`, `utils.py`, `constants.py`.
- **تستخدم للاختبار أو التطوير فقط**:
  - `tests/`, `camera_diag.py`, `hand_model_demo.py`, `app.py`.
- **غير مستخدم حاليًا في التدفق الرئيسي لكن جاهز للتوسّع**:
  - `VirtualKeyboard`, `GameController` داخل `controllers.py`.

---

## مسار التنفيذ الكامل (من الكاميرا إلى الماوس)

### 1. نقطة الدخول `main.py`

- يقرأ بارامترات سطر الأوامر:
  - `--mode`: `demo`, `mouse`, `volume`, `draw`.
  - `--camera`: رقم الكاميرا (0 افتراضيًا).
  - `--no-ekf`: لتعطيل الـ EKF إن أردت مقارنة الحركة الخام بالحركة المنعّمة.
- ينشئ كائن:
  - `HandTrackingOrchestrator(mode=..., use_ekf=not args.no_ekf)`
- يستدعي:
  - `app.run(camera_id=args.camera)`

### 2. الـ Orchestrator: `core/orchestrator.py`

في `HandTrackingOrchestrator.__init__`:

- ينشئ:
  - `HandTracker(use_ekf=use_ekf)` → مسؤول عن تتبع اليد واستخراج الـ Landmarks.
  - `GestureRecognizer()` → مسؤول عن تحويل الـ Landmarks إلى اسم إيماءة + درجة ثقة.
  - كائنات المودز:
    - `"demo": DemoMode()`
    - `"mouse": MouseMode()`
    - `"draw": DrawMode()`
    - `"volume": VolumeMode()`
  - `FPSCounter()` لحساب عدد الإطارات/ثانية.

في `run()`:

- ينشئ `ThreadedPipeline(camera_id, orchestrator=self)`:
  - يبدأ ثريد للكاميرا + ثريد للمعالجة.
  - الحلقة الرئيسية في الـ main thread تعرض الإطارات وتتعامل مع ضغطات لوحة المفاتيح:
    - `M` → وضع الماوس.
    - `V` → وضع الصوت.
    - `D` → وضع الرسم.
    - `SPACE` → وضع الديمو.
    - `C` → مسح لوحة الرسم في وضع الرسم.
    - `Q` → الخروج.

في `process_frame(frame)`:

1. يعكس الصورة أفقيًا (`cv2.flip`) لتصبح مثل المرايا.
2. يمرر الصورة إلى `HandTracker.process_frame`:
   - يحصل على `self.landmarks` + حالة `is_tracking`.
   - يرسم السكلتون الخاص باليد على الإطار.
3. إذا كانت اليد متتبَّعة:
   - يستدعي `GestureRecognizer.update(self.tracker.landmarks, mode=mode_name)`:
     - يرجع `(gesture_name, confidence)` بعد التنعيم الزمني.
4. يحسب الـ FPS ويستدعي:
   - `draw_info_panel(frame, fps, gesture, mode_name, confidence)` من `utils.py`.
5. يستدعي مود التشغيل الحالي:
   - `frame = current_mode.on_frame(frame, tracker, gesture, confidence)`.
6. يرجع الإطار الجاهز لعرضه.

### 3. الـ Pipeline: `pipeline/threaded_pipeline.py`

- **CameraThread**:
  - يقرأ الإطارات من `cv2.VideoCapture`.
  - يحتفظ دومًا **بأحدث إطار فقط** في `Queue` بحجم 1 (لتقليل التأخير).
- **ProcessingThread**:
  - يأخذ آخر إطار متاح.
  - يستدعي `orchestrator.process_frame(frame)`.
  - يخزن الإطار المعالَج في `Queue` أخرى بحجم 1.
- **ThreadedPipeline.get_latest()**:
  - تُستدعى من الـ main loop في الـ Orchestrator.
  - تعيد آخر إطار جاهز للعرض.

بهذا الشكل، **الكاميرا**، **المعالجة**، و**عرض الإطار + قراءة الكيبورد** تكون منفصلة، مما يعطي:

- FPS أعلى.
- تأخير (Latency) أقل.

---

## خوارزمية تتبع اليد + EKF

### 1. تتبع اليد: `HandTracker` في `hand_tracker.py`

- يستخدم `mediapipe.solutions.hands.Hands` لاكتشاف اليد و 21 Landmark.
- عند نجاح الاكتشاف:
  - يخزن:
    - `self.landmarks`: قائمة من 21 نقطة `(x, y, z)` في مدى [0,1] (منسوبة لحجم الصورة).
    - `self.handedness`: يمين/يسار.
    - `self.measurement_confidence`: مستمدة من MediaPipe.
- يرسم نقاط واتصالات اليد عبر `mp_drawing`.

### 2. فلتر EKF التكيفي: `AdaptiveExtendedKalmanFilter`

- لكل Landmark (21 مرة) يوجد كائن EKF مستقل.
- حالة الفلتر:

  \[
  \mathbf{x} = [x, y, z, v_x, v_y, v_z]^T
  \]

- مصفوفة الانتقال \(F\) تفترض نموذج حركة خطي (position + velocity).
- الضجيج (Q,R) **يتغيّر ديناميكيًا** حسب:
  - **سرعة الحركة** (من الفروق بين القياسات).
  - **درجة ثقة القياس** من MediaPipe.

الفكرة:

- عندما تتحرك اليد **بسرعة**:
  - يزيد الفلتر \(Q\) (process noise) → **استجابة أسرع** للحركة.
  - يقلّل نسبيًا من \(R\) → يعتمد أكثر على القياس.
- عندما تكون اليد **ثابتة**:
  - يقلّل \(Q\) → يمنع تغييرات كبيرة غير منطقية.
  - يزيد \(R\) → يزيد التنعيم ويقلل الاهتزاز.

يمكن تعطيل الـ EKF بالكامل من سطر الأوامر:

```bash
python main.py --no-ekf
```

أو ضبط ثوابته من `constants.py`:

- `EKF_BASE_PROCESS_NOISE`
- `EKF_BASE_MEASUREMENT_NOISE`
- `EKF_INITIAL_COVARIANCE`
- `EKF_SPEED_FAST`

زيادة التنعيم (حركة أهدأ لكن أبطأ استجابة):

- **قلِّل** `EKF_BASE_PROCESS_NOISE` أو **زِد** `EKF_BASE_MEASUREMENT_NOISE`.

زيادة الاستجابة (حركة أسرع لكن قد تزيد الاهتزازات):

- **زِد** `EKF_BASE_PROCESS_NOISE` أو **قلِّل** `EKF_BASE_MEASUREMENT_NOISE`.

---

## خوارزمية التعرف على الإيماءات `GestureRecognizer`

الملف: `gesture_recognizer.py`.

### 1. مدخلات ومخرجات

- المدخل:
  - `landmarks`: قائمة 21 نقطة من `HandTracker`.
  - `mode`: اسم المود الحالي (`demo`, `mouse`, `draw`, `volume`).
- المخرج:
  - `gesture_name`: اسم الإيماءة مثل `"Point"`, `"Pinch_TI"`, `"TwoFinger_Scroll_Up"`, `"Open_Palm"`, ….
  - `confidence`: درجة ثقة في المدى `[0,1]`.

### 2. خطوات العمل

1. **حفظ التاريخ**:
   - `position_history`: تاريخ مواقع اليد لعدد من الإطارات (للإيماءات الديناميكية مثل السحب/التمرير).
2. **تنبؤ خام Frame-by-frame**:
   - `_predict_raw(landmarks)`:
     - يحسب عدة مرشحين (`candidates`) مع درجات ثقة:
       - `_pinch_confidence` → `Pinch_TI`, `Pinch_TM`.
       - `_pointing_confidence` → `Point`.
       - `_thumbs_up_confidence` → `Thumbs_Up`.
       - `_peace_confidence` → `Peace`.
       - `_ok_confidence` → `OK`.
       - `_fist_confidence` → `Fist`.
       - `_open_palm_confidence` → `Open_Palm`.
       - `_detect_swipe` → `Swipe_Up/Down/Left/Right`.
       - `_detect_two_finger_scroll` → `TwoFinger_Scroll_Up/Down`.
     - يختار المرشح صاحب أعلى ثقة.
3. **تصفية حسب المود (Context Filter)**:
   - `_apply_context_filter(name, conf, mode)`:
     - مثلًا في وضع الماوس `mouse` يسمح فقط بـ:
       - `Point`, `Pinch_TI`, `Pinch_TM`,
       - `TwoFinger_Scroll_Up/Down`, `None`.
     - الإيماءات الأخرى (مثل `Thumbs_Up`) تتحول إلى `"None"` لتجنب تفعيل أوامر غير مقصودة.
4. **تنعيم زمني (Temporal Smoothing)**:
   - `_temporal_smooth()`:
     - يحتفظ بنافذة من آخر `VOTE_WINDOW_FRAMES` تنبؤات.
     - يحسب مجموع الأوزان ويختار الإيماءة الغالبة.
     - يشترط:
       - عدد إطارات متتالية لا يقل عن `MIN_STABLE_FRAMES`.
       - وثقة ≥ `MIN_GESTURE_CONFIDENCE`.

### 3. الثوابت المهمة لضبط حساسية الإيماءات

جميعها في `constants.py`:

- **للمسافة بين الأصابع (Pinch)**:
  - `PINCH_DISTANCE_THRESHOLD`:
    - أصغر → تحتاج تقارب أكبر بين الأصابع → **أصعب** حدوث الإيماءة، لكن أقل التفعيل الخاطئ.
    - أكبر → تقبل مسافة أكبر → **أسهل** لكن قد تزداد الأخطاء.
- **لإصبع المؤشر في وضع Point**:
  - `POINTING_INDEX_DISTANCE_MIN`: أقل مسافة لازمة بين المعصم ورأس السبابة ليُعتبَر “مؤشر ممتد”.
  - `FINGER_CLOSED_DISTANCE_MAX`: أقصى مسافة لبقية الأصابع ليُعتبَر أنها “مغلقة”.
- **للإيماءات الديناميكية (Swipe / Scroll)**:
  - `SWIPE_HISTORY_FRAMES`, `SWIPE_DISTANCE_THRESHOLD`.
  - `SCROLL_MIN_DELTA_FRAMES`: عدد الإطارات الدنيا لكشف Scroll.
- **للتنعيم الزمني**:
  - `VOTE_WINDOW_FRAMES`: حجم نافذة التصويت.
  - `MIN_STABLE_FRAMES`: عدد الإطارات الدنيا لتثبيت الإيماءة.
  - `MIN_GESTURE_CONFIDENCE`: عتبة الثقة الدنيا.

**لجعل النظام أكثر تشددًا (أقل تفعيل خاطئ، لكن يتطلب حركة أوضح):**

- زِد `MIN_GESTURE_CONFIDENCE`.
- زِد `MIN_STABLE_FRAMES`.
- قلِّل `PINCH_DISTANCE_THRESHOLD`.

**لجعل النظام أكثر حساسية (يستجيب أسرع، لكن قد يزيد الـ noise):**

- قلِّل `MIN_GESTURE_CONFIDENCE`.
- قلِّل `MIN_STABLE_FRAMES`.
- زِد `PINCH_DISTANCE_THRESHOLD`.

---

## وضع الماوس والتحكم بالزر الأيسر/الأيمن والتمرير والسحب

### 1. VirtualMouse في `controllers.py`

الصف `VirtualMouse` هو المسؤول عن تحريك مؤشر الماوس الفعلي:

- **الدالة `move_cursor(x, y)`**:
  - `x`, `y` في المدى [0,1] (إحداثيات من MediaPipe).
  - يطبّق:
    - `margin` من الجوانب لتجنب الحواف (`MOUSE_MOVE_MARGIN` من `constants.py`).
    - تحويل إلى إحداثيات شاشة.
    - **تنعيم بسيط**:
      - `smooth_x = smoothing * screen_x + (1 - smoothing) * prev_x`
      - `smoothing` ∈ [0,1].
        - قيمة أعلى → حركة أنعم لكن أبطأ استجابة.
        - قيمة أقل → استجابة أسرع لكن أكثر اهتزازًا.

**للتلاعب بدقة حركة المؤشر**:

- افتح `modes/mouse_mode.py`، في `MouseMode.__init__`:
  - حاليًا يتم إنشاء الماوس هكذا:
    - `self.mouse = VirtualMouse()`
- يمكنك تعديلها مثلًا:

```python
self.mouse = VirtualMouse(smoothing=0.7, margin=0.05)
```

- **زيادة الدقة / النعومة**:
  - **smoothing أعلى** (مثل 0.7–0.85).
  - **margin أكبر قليلًا** ليبتعد المؤشر عن حواف الشاشة.
- **استجابة أسرع (لألعاب أو حركات سريعة)**:
  - **smoothing أقل** (مثل 0.3–0.4).
  - **margin أصغر** (لكن لا تجعلها 0 لتجنّب القفز قرب الحواف).

### 2. ربط الإيماءات بالماوس في `MouseMode`

الملف: `modes/mouse_mode.py`.

في `on_frame(frame, tracker, gesture, confidence)`:

1. **تحريك المؤشر**:
   - يحصل على رأس السبابة:
     - `index_tip = tracker.get_finger_tip("index")`
   - يمرر الإحداثيات إلى:
     - `self.mouse.move_cursor(index_tip[0], index_tip[1])`
2. **التمرير (Scroll)**:
   - إذا كان `gesture` هو:
     - `"TwoFinger_Scroll_Up"` أو `"TwoFinger_Scroll_Down"`.
   - ويكون `confidence >= SCROLL_GESTURE_CONFIDENCE_THRESHOLD`:
     - يستدعي `_maybe_scroll()`:
       - التي تستدعي `self.mouse.scroll(amount)`:
         - `SCROLL_AMOUNT_PER_TICK` يحدد قوة التمرير في كل نبضة.
3. **الكلك والـ Drag**:
   - الإيماءات المستخدمة:
     - `"Pinch_TI"`: إبهام + سبابة.
     - `"Pinch_TM"`: إبهام + وسطى.
   - الثوابت من `constants.py`:
     - `CLICK_CONFIDENCE_THRESHOLD`: أقل ثقة للسماح بالكلك.
     - `CLICK_MIN_HOLD_MS`: أقل زمن إمساك بالـ Pinch قبل تنفيذ الكلك.
     - `CLICK_DEBOUNCE_MS`: زمن منع تكرار الكلكات بسرعة.
     - `DRAG_START_HOLD_MS`: زمن إمساك أطول لبدء السحب (Drag).

**السلوك الحالي تقريبًا**:

- `"Pinch_TI"` (الإبهام + السبابة):
  - إمساك قصير ≥ `CLICK_MIN_HOLD_MS`:
    - ينفّذ **Left Click** مرة واحدة.
  - استمر في الإمساك ≥ `DRAG_START_HOLD_MS`:
    - ينفّذ `start_drag()` → **سحب** حتى تفتح الأصابع.
- `"Pinch_TM"` (الإبهام + الوسطى):
  - إمساك قصير:
    - ينفّذ **Right Click**.

### 3. كيف أغير دقة الكلك والسحب والتمرير؟

في `constants.py`:

- **للكلك (Left/Right Click)**:
  - `CLICK_CONFIDENCE_THRESHOLD`:
    - أكبر → يحتاج ثقة أعلى في الإيماءة → أقل تفعيل خاطئ.
    - أقل → استجابة أسرع لكن قد تحدث كلكات غير مقصودة.
  - `CLICK_MIN_HOLD_MS`:
    - أكبر → يجب إبقاء الـ Pinch مدة أطول قبل الكلك.
    - أقل → كلك أسرع.
  - `CLICK_DEBOUNCE_MS`:
    - يتحكم في المدة الدنيا بين كلك وآخر.

- **للسحب (Drag & Drop)**:
  - `DRAG_START_HOLD_MS`:
    - زِد القيمة إذا أردت أن يبدأ السحب بعد إمساك أطول (أكثر أمانًا).
    - قلّلها إذا أردت بدء السحب بسرعة أكبر.

- **للتمرير (Scroll)**:
  - `SCROLL_GESTURE_CONFIDENCE_THRESHOLD`:
    - أكبر → يحتاج إيماءة Scroll أوضح، فيقل التفعيل الخاطئ.
  - `SCROLL_AMOUNT_PER_TICK`:
    - يتحكم في مقدار التمرير في كل نبضة Scroll.

مثال لضبط أكثر احترافية لوضع الماوس:

- في `constants.py` اجعل مثلًا:

```python
CLICK_CONFIDENCE_THRESHOLD = 0.6
MIN_GESTURE_CONFIDENCE = 0.7
MIN_STABLE_FRAMES = 5
PINCH_DISTANCE_THRESHOLD = 0.075
DRAG_START_HOLD_MS = 300
SCROLL_GESTURE_CONFIDENCE_THRESHOLD = 0.8
SCROLL_AMOUNT_PER_TICK = 60
```

هذا يجعل النظام:

- متشددًا قليلًا في الكلكات والتمرير.
- يعطي سحب (Drag) أكثر أمانًا.

---

## وضع الرسم في الهواء `DrawMode`

الملف: `modes/draw_mode.py` + الصف `AirDrawing` في `controllers.py`.

- في كل إطار:
  - يأخذ `index_tip` من `HandTracker`.
  - إذا كانت الإيماءة `"Point"` والثقة ≥ `MIN_GESTURE_CONFIDENCE`:
    - يستدعي `self._drawer.update(index_tip[0], index_tip[1], is_drawing=True)`.
  - غير ذلك:
    - `is_drawing=False` فيتوقف الرسم.
- `AirDrawing`:
  - يحوّل الإحداثيات [0,1] إلى حجم اللوحة (عرض/ارتفاع).
  - يرسم خطوط بين آخر نقطة والحالية إذا كان `is_drawing=True`.

**التحكم في دقة الرسم/سماكته/لونه:**

- في `controllers.AirDrawing`:
  - `self.thickness`: سماكة الخط.
  - `self.color`: لون BGR (مثل `(0, 255, 0)`).

يمكنك تغييرها افتراضيًا أو إضافة إيماءات لتغيير الألوان/السماكة.

---

## وضع التحكم بالصوت `VolumeMode`

الملف: `modes/volume_mode.py`.

- يأخذ **مسافة الـ Pinch** من:
  - `tracker.get_pinch_distance()`.
- يمررها إلى:
  - `VolumeController.set_volume(distance)`.
    - يحول المسافة إلى مدى 0–100%.

**التحكم في حساسية الصوت:**

- في `controllers.VolumeController`:
  - `volume = int(np.clip(distance * 300, 0, 100))`:
    - رقم 300 هو "Gain" لتحويل المسافة إلى نسبة مئوية.
    - قلله أو زِده لتغيير حساسية الصوت للحركة.

---

## ما الذي يمكن اعتباره "تنظيفًا" في هذا المشروع؟

بحسب حالة المشروع الحالية:

- **ملفات يمكن حذفها بأمان إذا أردت مشروعًا نظيفًا للـ Production**:
  - جميع ملفات `.pyc` داخل مجلدات `__pycache__`:
    - لا تؤثر على الكود، ويعيد Python إنشاءها تلقائيًا.
  - `hand_model_demo.py`:
    - سكربت تجريبي خاص بنموذج 3D، لا يُستخدم في التشغيل العادي.
  - `camera_diag.py`:
    - مفيد للفحص، لكن ليس جزءًا من التطبيق النهائي.
  - `app.py`:
    - أداة لتجميع الكود في ملف واحد، ليست مطلوبة للتشغيل.
- **كلاسات غير مستخدمة حاليًا**:
  - `VirtualKeyboard`, `GameController`:
    - يمكن إبقاؤها للتوسّع المستقبلي، أو نقلها إلى ملف فرعي مثل `experimental_controllers.py` لو أردت تنظيمًا أعلى.

إذا أردت **أقصى نظافة**:

- احذف/انقل السكربتات التجريبية إلى مجلد فرعي مثل `experiments/`.
- احذف مجلدات `__pycache__` بالكامل (سيعاد توليدها تلقائيًا).

---

## خطوات عملية لضبط الدقة والحساسية (اقتراح عملي)

1. **ابدأ بوضع الماوس `mouse`**:
   - شغّل:

```bash
python main.py --mode mouse
```

2. **اختبر الاستجابة**:
   - جرّب:
     - حركة المؤشر.
     - الكلك بإيماءة Pinch.
     - السحب (Drag).
     - التمرير (Scroll).

3. **عدّل ثوابت الحساسية في `constants.py` تدريجيًا**:
   - للكلك والسحب:
     - `CLICK_CONFIDENCE_THRESHOLD`, `CLICK_MIN_HOLD_MS`, `DRAG_START_HOLD_MS`.
   - للإيماءات عامة:
     - `MIN_GESTURE_CONFIDENCE`, `MIN_STABLE_FRAMES`, `PINCH_DISTANCE_THRESHOLD`.
   - للتمرير:
     - `SCROLL_GESTURE_CONFIDENCE_THRESHOLD`, `SCROLL_AMOUNT_PER_TICK`.

4. **عدّل نعومة المؤشر في `MouseMode`**:

```python
self.mouse = VirtualMouse(smoothing=0.6, margin=0.08)
```

5. **اختبر مع EKF وبدونه**:
   - مع EKF (افتراضيًا).
   - بدون EKF:

```bash
python main.py --mode mouse --no-ekf
```

وشاهد الفرق في الاهتزاز والدقة.

باتباع هذه الخطوات، يمكنك التحكم بدقة وحساسية:

- اكتشاف الإيماءات.
- تحريك المؤشر.
- الكلك يمين/يسار.
- السحب والإفلات.
- التمرير (Scroll).

بدقة عالية وتناسب أسلوب استخدامك (لألعاب، عمل مكتبي، عروض، إلخ).

