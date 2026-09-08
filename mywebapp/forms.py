from django import forms
from .models import Staff, Patient


class LoginForm(forms.Form):
    username = forms.CharField(max_length=50, label="ชื่อผู้ใช้")
    password = forms.CharField(widget=forms.PasswordInput, label="รหัสผ่าน")


class PatientForm(forms.ModelForm):
    """
    ฟอร์มกรอกข้อมูลผู้ป่วย ใช้เฉพาะ 10 Features
    ที่ผ่านการคัดเลือกด้วย Information Gain (IG > 0)
    """

    class Meta:
        model = Patient
        fields = [
            "gender",           # → gender
            "age",              # → age
            "age_group",        # → agegroup
            "patient_type",     # → typept_id
            "referral_reason",  # → cause_referout_id
            "is_receive",       # → is_receive
            "is_referboard",    # → is_referboard
            "f_face",           # → stroke_f
            "a_arm",            # → stroke_a
            "s_speech",         # → stroke_s
        ]
        widgets = {
            "gender":          forms.Select(attrs={"class": "form-input"}),
            "age":             forms.NumberInput(attrs={"min": 1, "max": 100, "class": "form-input"}),
            "age_group":       forms.Select(attrs={"class": "form-input"}),
            "patient_type":    forms.Select(attrs={"class": "form-input"}),
            "referral_reason": forms.Select(attrs={"class": "form-input"}),
            "is_receive":      forms.Select(attrs={"class": "form-input"}),
            "is_referboard":   forms.Select(attrs={"class": "form-input"}),
            # FAST — ใช้ hidden input + JS toggle เพื่อให้กดการ์ดได้
            "f_face":          forms.HiddenInput(),
            "a_arm":           forms.HiddenInput(),
            "s_speech":        forms.HiddenInput(),
        }
