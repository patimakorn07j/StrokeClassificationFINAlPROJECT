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
# ตารางที่ 2: ข้อมูลผู้ป่วยและผลการประเมิน
# ตัวเลือกทั้งหมดอ้างอิงตาม Data Dictionary ของชุดข้อมูล
# ---------------------------------------------------------------------------
class Patient(models.Model):

    GENDER_CHOICES = [
        (1, "ชาย"),
        (2, "หญิง"),
    ]

    AGE_GROUP_CHOICES = [
        ("Early Childhood",       "เด็ก 0-5 ปี (Early Childhood)"),
        ("School-Age Children",   "วัยเรียน 5-15 ปี (School-Age Children)"),
        ("Workforce",             "วัยทำงาน 15-59 ปี (Workforce)"),
        ("Elderly",               "ผู้สูงอายุ 60 ปีขึ้นไป (Elderly)"),
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

    YES_NO_CHOICES = [
        ("N", "ไม่ใช่"),
        ("Y", "ใช่"),
    ]

    RESULT_CHOICES = [
        ("STROKE", "Stroke"),
        ("NON_STROKE", "Non-Stroke"),
    ]

    patient_id = models.AutoField(primary_key=True)

    # ── 10 Features ที่โมเดลใช้ ──────────────────────────────────────────
    gender = models.PositiveSmallIntegerField(
        choices=GENDER_CHOICES, verbose_name="เพศ")

    age = models.PositiveSmallIntegerField(
        verbose_name="อายุ")

    age_group = models.CharField(
        max_length=30, choices=AGE_GROUP_CHOICES, verbose_name="กลุ่มอายุ")

    patient_type = models.PositiveSmallIntegerField(
        choices=PATIENT_TYPE_CHOICES, verbose_name="ประเภทผู้ป่วย")

    referral_reason = models.PositiveSmallIntegerField(
        choices=REFERRAL_REASON_CHOICES, verbose_name="สาเหตุการส่งต่อ")

    is_receive = models.PositiveSmallIntegerField(
        choices=IS_RECEIVE_CHOICES, default=1,
        verbose_name="สถานะการส่งข้อมูลออนไลน์")

    is_referboard = models.CharField(
        max_length=1, choices=YES_NO_CHOICES, default="N",
        verbose_name="แสดงผลใน Refer Board")

    f_face = models.CharField(
        max_length=1, choices=YES_NO_CHOICES, default="N",
        verbose_name="F: หน้าเบี้ยว")

    a_arm = models.CharField(
        max_length=1, choices=YES_NO_CHOICES, default="N",
        verbose_name="A: แขนขาอ่อนแรง")

    s_speech = models.CharField(
        max_length=1, choices=YES_NO_CHOICES, default="N",
        verbose_name="S: พูดไม่ชัด")

    # ── ผลการจำแนก ──────────────────────────────────────────────────────
    result = models.CharField(
        max_length=10, choices=RESULT_CHOICES, blank=True, null=True)

    assessed_at = models.DateTimeField(auto_now_add=True)

    staff = models.ForeignKey(
        Staff, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="patients")

    def __str__(self):
        return f"ผู้ป่วย #{self.patient_id} - {self.get_result_display() or 'ยังไม่ประเมิน'}"

    class Meta:
        db_table = "patient"
        ordering = ["-assessed_at"]


# ---------------------------------------------------------------------------
# ตารางที่ 3: คำแนะนำในการเตรียมตัวรับมือ
# ---------------------------------------------------------------------------
class Recommendation(models.Model):
    RESULT_TYPE_CHOICES = [
        ("STROKE", "Stroke"),
        ("NON_STROKE", "Non-Stroke"),
    ]

    recommendation_id = models.AutoField(primary_key=True)
    result_type = models.CharField(
        max_length=10, choices=RESULT_TYPE_CHOICES, unique=True)
    content = models.TextField()

    def __str__(self):
        return f"คำแนะนำสำหรับ {self.get_result_type_display()}"

    class Meta:
        db_table = "recommendation"
