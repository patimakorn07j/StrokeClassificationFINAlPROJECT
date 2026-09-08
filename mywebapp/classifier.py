"""
classifier.py
--------------
โหลดโมเดล AdaBoost ที่ผ่านการคัดเลือกเป็น Best Model
และทำนายผลการจำแนกโรคหลอดเลือดสมอง

Features ที่โมเดลใช้ (10 ตัว คัดเลือกด้วย Information Gain):
    typept_id, is_receive, stroke_f, age, cause_referout_id,
    stroke_a, stroke_s, gender, agegroup, is_referboard

หมายเหตุ:
    ชุดข้อมูลที่ใช้เทรนไม่มีบางค่าที่ปรากฏใน Data Dictionary
    จึงมีการ map ค่าที่โมเดลไม่เคยเห็นไปยังค่าที่ใกล้เคียงที่สุด
    เพื่อให้ระบบทำงานได้โดยไม่เกิดข้อผิดพลาด
"""

import os
import joblib
from django.conf import settings


# ---------------------------------------------------------------------------
# โหลดโมเดลครั้งเดียวตอน Django เริ่มทำงาน
# ---------------------------------------------------------------------------
MODEL_DIR = os.path.join(settings.BASE_DIR, "ml_models")

try:
    _model    = joblib.load(os.path.join(MODEL_DIR, "adaboost_model.pkl"))
    _scaler   = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
    _encoders = joblib.load(os.path.join(MODEL_DIR, "encoders.pkl"))
    _features = joblib.load(os.path.join(MODEL_DIR, "features.pkl"))
    MODEL_LOADED = True
    print(f"[classifier] โหลดโมเดลสำเร็จ | Features: {_features}")
except Exception as e:
    _model = _scaler = _encoders = _features = None
    MODEL_LOADED = False
    print(f"[classifier] โหลดโมเดลไม่สำเร็จ: {e}")


# ---------------------------------------------------------------------------
# แปลงชื่อฟิลด์จาก Django Form → ชื่อ Feature ที่โมเดลรู้จัก
# ---------------------------------------------------------------------------
FIELD_MAP = {
    "gender":           "gender",
    "age":              "age",
    "age_group":        "agegroup",
    "patient_type":     "typept_id",
    "referral_reason":  "cause_referout_id",
    "is_receive":       "is_receive",
    "is_referboard":    "is_referboard",
    "f_face":           "stroke_f",
    "a_arm":            "stroke_a",
    "s_speech":         "stroke_s",
}


# ---------------------------------------------------------------------------
# แปลงค่าที่โมเดลไม่เคยเห็นไปยังค่าที่ใกล้เคียงที่สุด
# ---------------------------------------------------------------------------
FALLBACK_MAP = {
    # ชุดข้อมูลที่เทรนมีเฉพาะ Childhood / Workforce / Elderly
    "agegroup": {
        "Early Childhood":     "Childhood",
        "School-Age Children": "Childhood",
    },
    # ชุดข้อมูลที่เทรนมีเฉพาะ typept_id = 1, 2
    # ค่า 3 (เบิกจ่ายตรง) จัดเป็นผู้ป่วยทั่วไป
    "typept_id": {
        3: 1,
    },
    # ชุดข้อมูลที่เทรนมี cause_referout_id = 1,2,3,6,7,8,17,99
    # ค่า 4 (ดูแลต่อใกล้บ้าน) ใกล้เคียงกับ 3 (รักษาต่อเนื่อง)
    # ค่า 5 (ตามความต้องการผู้ป่วย) ใกล้เคียงกับ 7
    "cause_referout_id": {
        4: 3,
        5: 7,
    },
}


def _apply_fallback(feature_name, value):
    """แปลงค่าที่โมเดลไม่เคยเห็นให้เป็นค่าที่ใกล้เคียงที่สุด"""
    mapping = FALLBACK_MAP.get(feature_name)
    if mapping and value in mapping:
        return mapping[value]
    return value


def classify_patient(form_data: dict) -> str:
    """
    รับข้อมูลจากฟอร์ม (cleaned_data) แล้วคืนค่า "STROKE" หรือ "NON_STROKE"
    """
    if not MODEL_LOADED:
        raise RuntimeError(
            "ไม่พบไฟล์โมเดล กรุณาตรวจสอบว่าไฟล์ .pkl "
            f"อยู่ในโฟลเดอร์ {MODEL_DIR} ครบทั้ง 4 ไฟล์"
        )

    # แปลงชื่อฟิลด์ + จัดการค่าที่โมเดลไม่รู้จัก
    model_input = {}
    for form_field, model_field in FIELD_MAP.items():
        raw_value = form_data.get(form_field)
        model_input[model_field] = _apply_fallback(model_field, raw_value)

    # เรียงค่าตามลำดับ Feature ที่โมเดลต้องการ
    row = []
    for feat in _features:
        val = model_input[feat]
        if feat in _encoders:
            try:
                val = _encoders[feat].transform([str(val)])[0]
            except ValueError:
                # เผื่อกรณีค่ายังไม่อยู่ใน encoder — ใช้ค่าแรกเป็นค่าเริ่มต้น
                val = 0
        row.append(val)

    # Scale แล้ว Predict
    x_scaled = _scaler.transform([row])
    pred     = _model.predict(x_scaled)[0]

    return "STROKE" if pred == 1 else "NON_STROKE"
