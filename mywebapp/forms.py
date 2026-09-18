from django import forms
from .models import Staff, Patient, PredictionRecord


class LoginForm(forms.Form):
    username = forms.CharField(max_length=50, label="ชื่อผู้ใช้")
    password = forms.CharField(widget=forms.PasswordInput, label="รหัสผ่าน")


class PatientRegisterForm(forms.ModelForm):
    """ขึ้นทะเบียนผู้ป่วยใหม่ — กรอกแค่ชื่อและรหัส HN เดิมของโรงพยาบาล"""
    class Meta:
        model = Patient
        fields = ["full_name", "hn"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-input", "placeholder": "ชื่อ-นามสกุลผู้ป่วย"}),
            "hn": forms.TextInput(attrs={"class": "form-input", "placeholder": "เช่น HN123456789", "maxlength": 11}),
        }

    def clean_hn(self):
        hn = self.cleaned_data["hn"].strip().upper()
        if Patient.objects.filter(hn=hn).exists():
            raise forms.ValidationError("รหัส HN นี้มีอยู่ในระบบแล้ว กรุณาค้นหาผู้ป่วยแทนการเพิ่มใหม่")
        return hn


class PatientDemographicForm(forms.ModelForm):
    """กรอกเฉพาะครั้งแรกที่ประเมิน — เพศ อายุ กลุ่มอายุ"""
    class Meta:
        model = Patient
        fields = ["gender", "age", "age_group"]
        widgets = {
            "gender":    forms.Select(attrs={"class": "form-input"}),
            "age":       forms.NumberInput(attrs={"min": 1, "max": 100, "class": "form-input"}),
            "age_group": forms.Select(attrs={"class": "form-input"}),
        }


class AssessmentForm(forms.ModelForm):
    """กรอกทุกครั้งที่ประเมิน — แอตทริบิวต์ที่เปลี่ยนได้ในแต่ละครั้ง"""
    class Meta:
        model = PredictionRecord
        fields = [
            "patient_type", "referral_reason", "is_receive",
            "is_referboard", "f_face", "a_arm", "s_speech",
        ]
        widgets = {
            "patient_type":    forms.Select(attrs={"class": "form-input"}),
            "referral_reason": forms.Select(attrs={"class": "form-input"}),
            "is_receive":      forms.Select(attrs={"class": "form-input"}),
            "is_referboard":   forms.Select(attrs={"class": "form-input"}),
            "f_face":          forms.HiddenInput(),
            "a_arm":           forms.HiddenInput(),
            "s_speech":        forms.HiddenInput(),
        }
