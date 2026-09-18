from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import make_password, check_password


hn_validator = RegexValidator(
    regex=r"^HN\d{9}$",
    message="รหัส HN ต้องเป็นตัวอักษร HN ตามด้วยตัวเลข 9 หลัก เช่น HN123456789",
)


class Staff(models.Model):
    staff_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)
    full_name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.username} ({self.full_name})"

    class Meta:
        db_table = "staff"


# ---------------------------------------------------------------------------
# Patient — เก็บข้อมูลตัวบุคคล รวมทั้งเพศ/อายุ/กลุ่มอายุ ซึ่งไม่ถามซ้ำ
# หลังจากกรอกครั้งแรกแล้ว รหัส HN กรอกโดยเจ้าหน้าที่เอง (ไม่ใช่ระบบสุ่มให้)
# ---------------------------------------------------------------------------
class Patient(models.Model):

    GENDER_CHOICES = [(1, "ชาย"), (2, "หญิง")]

    AGE_GROUP_CHOICES = [
        ("Early Childhood",     "เด็ก 0-5 ปี (Early Childhood)"),
        ("School-Age Children", "วัยเรียน 5-15 ปี (School-Age Children)"),
        ("Workforce",           "วัยทำงาน 15-59 ปี (Workforce)"),
        ("Elderly",             "ผู้สูงอายุ 60 ปีขึ้นไป (Elderly)"),
    ]

    patient_id = models.AutoField(primary_key=True)
    hn = models.CharField(
        max_length=11, unique=True, validators=[hn_validator],
        verbose_name="รหัส HN",
        help_text="รหัส HN ของโรงพยาบาล รูปแบบ HN ตามด้วยตัวเลข 9 หลัก",
    )
    full_name = models.CharField(max_length=150, verbose_name="ชื่อ-นามสกุลผู้ป่วย")

    # กรอกแค่ครั้งแรกที่ประเมิน ครั้งต่อไปใช้ค่าเดิมอัตโนมัติ
    gender = models.PositiveSmallIntegerField(choices=GENDER_CHOICES, null=True, blank=True, verbose_name="เพศ")
    age = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="อายุ")
    age_group = models.CharField(max_length=30, choices=AGE_GROUP_CHOICES, null=True, blank=True, verbose_name="กลุ่มอายุ")

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def has_demographics(self):
        """True ถ้าเคยกรอกเพศ/อายุ/กลุ่มอายุแล้ว (ประเมินมาแล้วอย่างน้อย 1 ครั้ง)"""
        return self.gender is not None and self.age is not None and bool(self.age_group)

    def __str__(self):
        return f"{self.hn} - {self.full_name}"

    class Meta:
        db_table = "patient"
        ordering = ["-created_at"]


# ---------------------------------------------------------------------------
# PredictionRecord — ผลการประเมินแต่ละครั้ง เก็บเฉพาะแอตทริบิวต์ที่เปลี่ยนได้ทุกครั้ง
# ---------------------------------------------------------------------------
class PredictionRecord(models.Model):

    PATIENT_TYPE_CHOICES = [
        (1, "ผู้ป่วยทั่วไป"),
        (2, "ผู้ป่วยฉุกเฉินวิกฤต"),
        (3, "ผู้ป่วยเบิกจ่ายตรง"),
    ]

    REFERRAL_REASON_CHOICES = [
        (1, "เพื่อการวินิจฉัยและรักษา"),
        (2, "เพื่อการวินิจฉัย"),
        (3, "เพื่อการรักษาต่อเนื่อง"),
        (4, "เพื่อการดูแลต่อใกล้บ้าน"),
        (5, "ตามความต้องการผู้ป่วย"),
    ]

    IS_RECEIVE_CHOICES = [
        (0, "ยังไม่ได้ส่งข้อมูลออนไลน์"),
        (1, "ส่งข้อมูลออนไลน์แล้ว"),
    ]

    YES_NO_CHOICES = [("N", "ไม่ใช่"), ("Y", "ใช่")]
    RESULT_CHOICES = [("STROKE", "Stroke"), ("NON_STROKE", "Non-Stroke")]

    record_id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="records", verbose_name="ผู้ป่วย")
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name="records")

    patient_type = models.PositiveSmallIntegerField(choices=PATIENT_TYPE_CHOICES, verbose_name="ประเภทผู้ป่วย")
    referral_reason = models.PositiveSmallIntegerField(choices=REFERRAL_REASON_CHOICES, verbose_name="สาเหตุการส่งต่อ")
    is_receive = models.PositiveSmallIntegerField(choices=IS_RECEIVE_CHOICES, default=1, verbose_name="สถานะการส่งข้อมูลออนไลน์")
    is_referboard = models.CharField(max_length=1, choices=YES_NO_CHOICES, default="N", verbose_name="แสดงผลใน Refer Board")
    f_face = models.CharField(max_length=1, choices=YES_NO_CHOICES, default="N", verbose_name="F: หน้าเบี้ยว")
    a_arm = models.CharField(max_length=1, choices=YES_NO_CHOICES, default="N", verbose_name="A: แขนขาอ่อนแรง")
    s_speech = models.CharField(max_length=1, choices=YES_NO_CHOICES, default="N", verbose_name="S: พูดไม่ชัด")

    result = models.CharField(max_length=10, choices=RESULT_CHOICES, blank=True, null=True)
    assessed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.patient.hn} - {self.get_result_display() or 'ยังไม่ประเมิน'}"

    class Meta:
        db_table = "prediction_record"
        ordering = ["-assessed_at"]


class Recommendation(models.Model):
    RESULT_TYPE_CHOICES = [("STROKE", "Stroke"), ("NON_STROKE", "Non-Stroke")]
    recommendation_id = models.AutoField(primary_key=True)
    result_type = models.CharField(max_length=10, choices=RESULT_TYPE_CHOICES, unique=True)
    content = models.TextField()

    def __str__(self):
        return f"คำแนะนำสำหรับ {self.get_result_type_display()}"

    class Meta:
        db_table = "recommendation"
