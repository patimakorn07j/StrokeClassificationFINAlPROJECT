from django import forms
from .models import Staff, Patient, PredictionRecord, Recommendation


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


class PatientEditForm(forms.ModelForm):
    """
    แก้ไขข้อมูลผู้ป่วย — ชื่อและรหัส HN แก้ได้เสมอ
    ส่วนเพศ/อายุ/กลุ่มอายุ จะแสดงเฉพาะผู้ป่วยที่เคยประเมินแล้ว เพราะยังไม่เคยกรอกมาก่อน
    """
    class Meta:
        model = Patient
        fields = ["full_name", "hn", "gender", "age", "age_group"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-input", "placeholder": "ชื่อ-นามสกุลผู้ป่วย"}),
            "hn":        forms.TextInput(attrs={"class": "form-input", "maxlength": 11}),
            "gender":    forms.Select(attrs={"class": "form-input"}),
            "age":       forms.NumberInput(attrs={"min": 1, "max": 100, "class": "form-input"}),
            "age_group": forms.Select(attrs={"class": "form-input"}),
        }

    DEMOGRAPHIC_FIELDS = ("gender", "age", "age_group")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.has_demographics:
            for name in self.DEMOGRAPHIC_FIELDS:
                self.fields[name].required = True
        else:
            for name in self.DEMOGRAPHIC_FIELDS:
                del self.fields[name]

    def clean_hn(self):
        hn = self.cleaned_data["hn"].strip().upper()
        if Patient.objects.filter(hn=hn).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("รหัส HN นี้เป็นของผู้ป่วยรายอื่นในระบบแล้ว กรุณาตรวจสอบอีกครั้ง")
        return hn

    @property
    def demographics_changed(self):
        """True ถ้าแก้ค่าที่แบบจำลองใช้ ซึ่งทำให้ผลการประเมินเดิมต้องประมวลผลใหม่"""
        return any(name in self.changed_data for name in self.DEMOGRAPHIC_FIELDS)


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


class StaffForm(forms.ModelForm):
    """เพิ่ม/แก้ไขบัญชีเจ้าหน้าที่ — ตอนแก้ไข ปล่อยรหัสผ่านว่างไว้ถ้าไม่ต้องการเปลี่ยน"""
    new_password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-input", "placeholder": "รหัสผ่าน"}),
        label="รหัสผ่าน",
    )

    class Meta:
        model = Staff
        fields = ["username", "full_name"]
        widgets = {
            "username":  forms.TextInput(attrs={"class": "form-input", "placeholder": "ชื่อผู้ใช้"}),
            "full_name": forms.TextInput(attrs={"class": "form-input", "placeholder": "ชื่อ-นามสกุล"}),
        }

    def clean_new_password(self):
        password = self.cleaned_data.get("new_password", "")
        # เพิ่มบัญชีใหม่ต้องตั้งรหัสผ่านเสมอ ส่วนการแก้ไขจะเว้นว่างไว้ก็ได้
        if not self.instance.pk and not password:
            raise forms.ValidationError("กรุณากำหนดรหัสผ่านสำหรับบัญชีใหม่")
        if password and len(password) < 6:
            raise forms.ValidationError("รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร")
        return password

    def save(self, commit=True):
        staff = super().save(commit=False)
        password = self.cleaned_data.get("new_password")
        if password:
            staff.set_password(password)
        if commit:
            staff.save()
        return staff


class RecommendationForm(forms.ModelForm):
    """
    เพิ่ม/แก้ไขคำแนะนำ — ระบบเก็บได้ผลลัพธ์ละ 1 รายการเท่านั้น (STROKE และ NON_STROKE)
    ตอนเพิ่มใหม่จึงเลือกได้เฉพาะประเภทที่ยังไม่มีในระบบ
    ส่วนตอนแก้ไขจะซ่อนช่องประเภทไว้ เพราะเปลี่ยนแล้วจะไปชนกับอีกรายการหนึ่ง
    """
    class Meta:
        model = Recommendation
        fields = ["result_type", "content"]
        widgets = {
            "result_type": forms.Select(attrs={"class": "form-input"}),
            "content":     forms.Textarea(attrs={"class": "form-input", "rows": 8}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            del self.fields["result_type"]
        else:
            used = set(Recommendation.objects.values_list("result_type", flat=True))
            field = self.fields["result_type"]
            field.choices = [("", "— เลือกประเภทผลลัพธ์ —")] + [
                (value, label)
                for value, label in Recommendation.RESULT_TYPE_CHOICES
                if value not in used
            ]
            field.error_messages["required"] = "กรุณาเลือกประเภทผลลัพธ์"
            # เกิดเมื่อส่งประเภทที่มีคำแนะนำอยู่แล้วเข้ามา (ไม่ได้เลือกจากรายการที่ให้ไว้)
            field.error_messages["invalid_choice"] = "ประเภทผลลัพธ์นี้มีคำแนะนำอยู่แล้ว กรุณาเลือกประเภทที่ยังว่าง"
