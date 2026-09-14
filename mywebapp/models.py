import random
from django.db import models
from django.contrib.auth.hashers import make_password, check_password


# ---------------------------------------------------------------------------
# ตารางที่ 1: เจ้าหน้าที่ผู้ใช้งานระบบ
# ---------------------------------------------------------------------------
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
# ตารางที่ 2: ข้อมูลตัวบุคคลของผู้ป่วย (Master Data)
# รหัส HN สร้างโดยระบบอัตโนมัติแบบสุ่ม (ไม่เรียงลำดับ) รูปแบบ HN + เลข 9 หลัก
# ผู้ป่วย 1 คน มี HN เดียวตลอดไป ไม่ว่าจะถูกจำแนกกี่ครั้งก็เห็นรหัสเดิม
# ---------------------------------------------------------------------------
class Patient(models.Model):
    patient_id = models.AutoField(primary_key=True)
    hn = models.CharField(max_length=11, unique=True, editable=False, verbose_name="รหัส HN")
    full_name = models.CharField(max_length=150, verbose_name="ชื่อ-นามสกุลผู้ป่วย")
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def generate_hn():
        """สุ่มรหัส HN + เลข 9 หลัก ไม่เรียงลำดับ และตรวจสอบไม่ให้ซ้ำ"""
        while True:
            candidate = f"HN{random.randint(0, 999999999):09d}"
            if not Patient.objects.filter(hn=candidate).exists():
                return candidate

    def save(self, *args, **kwargs):
        if not self.hn:
            self.hn = Patient.generate_hn()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.hn} - {self.full_name}"

    class Meta:
        db_table = "patient"
        ordering = ["-created_at"]


# ---------------------------------------------------------------------------
# ตารางที่ 3: ผลการประเมินแต่ละครั้ง (ใช้ 10 Features ที่คัดเลือกด้วย IG)
# ผู้ป่วย 1 คน (Patient) มีผลการประเมินได้หลายครั้ง (One-to-Many)
# ---------------------------------------------------------------------------
class PredictionRecord(models.Model):

    GENDER_CHOICES = [(1, "ชาย"), (2, "หญิง")]

    AGE_GROUP_CHOICES = [
        ("Early Childhood",     "เด็ก 0-5 ปี (Early Childhood)"),
        ("School-Age Children", "วัยเรียน 5-15 ปี (School-Age Children)"),
        ("Workforce",           "วัยทำงาน 15-59 ปี (Workforce)"),
        ("Elderly",             "ผู้สูงอายุ 60 ปีขึ้นไป (Elderly)"),
    ]

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
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="records", verbose_name="ผู้ป่วย")
    staff = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name="records")

    gender = models.PositiveSmallIntegerField(choices=GENDER_CHOICES, verbose_name="เพศ")
    age = models.PositiveSmallIntegerField(verbose_name="อายุ")
    age_group = models.CharField(max_length=30, choices=AGE_GROUP_CHOICES, verbose_name="กลุ่มอายุ")
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


# ---------------------------------------------------------------------------
# ตารางที่ 4: คำแนะนำในการเตรียมตัวรับมือ
# ---------------------------------------------------------------------------
class Recommendation(models.Model):
    RESULT_TYPE_CHOICES = [("STROKE", "Stroke"), ("NON_STROKE", "Non-Stroke")]

    recommendation_id = models.AutoField(primary_key=True)
    result_type = models.CharField(max_length=10, choices=RESULT_TYPE_CHOICES, unique=True)
    content = models.TextField()

    def __str__(self):
        return f"คำแนะนำสำหรับ {self.get_result_type_display()}"

    class Meta:
        db_table = "recommendation"
