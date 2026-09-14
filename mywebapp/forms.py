from django import forms
from .models import Staff, Patient, PredictionRecord


class LoginForm(forms.Form):
    username = forms.CharField(max_length=50, label="ชื่อผู้ใช้")
    password = forms.CharField(widget=forms.PasswordInput, label="รหัสผ่าน")


class PatientCreateForm(forms.ModelForm):
    """
    เพิ่มผู้ป่วยใหม่ — กรอกแค่ชื่อ ระบบสร้างรหัส HN แบบสุ่มให้อัตโนมัติ
    """
    class Meta:
        model = Patient
        fields = ["full_name"]
        widgets = {
            "full_name": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "ชื่อ-นามสกุลผู้ป่วย",
            }),
        }


class AssessmentForm(forms.ModelForm):
    """
    ฟอร์มประเมินอาการผู้ป่วย ใช้เฉพาะ 10 Features
    ที่ผ่านการคัดเลือกด้วย Information Gain (IG > 0)
    """
    class Meta:
        model = PredictionRecord
        fields = [
            "gender", "age", "age_group", "patient_type", "referral_reason",
            "is_receive", "is_referboard", "f_face", "a_arm", "s_speech",
        ]
        widgets = {
            "gender":          forms.Select(attrs={"class": "form-input"}),
            "age":             forms.NumberInput(attrs={"min": 1, "max": 100, "class": "form-input"}),
            "age_group":       forms.Select(attrs={"class": "form-input"}),
            "patient_type":    forms.Select(attrs={"class": "form-input"}),
            "referral_reason": forms.Select(attrs={"class": "form-input"}),
            "is_receive":      forms.Select(attrs={"class": "form-input"}),
            "is_referboard":   forms.Select(attrs={"class": "form-input"}),
            "f_face":          forms.HiddenInput(),
            "a_arm":           forms.HiddenInput(),
            "s_speech":        forms.HiddenInput(),
        }
