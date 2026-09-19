# ---------------------------------------------------------------------------
# เพิ่มเข้าไปใน forms.py เดิม (ต่อท้ายไฟล์)
# ---------------------------------------------------------------------------

class StaffForm(forms.ModelForm):
    """ฟอร์มเพิ่ม/แก้ไขเจ้าหน้าที่ สำหรับหน้า Admin UI เอง"""
    new_password = forms.CharField(
        required=False, widget=forms.PasswordInput(attrs={"class": "form-input"}),
        label="รหัสผ่านใหม่", help_text="เว้นว่างไว้หากไม่ต้องการเปลี่ยนรหัสผ่าน")

    class Meta:
        model = Staff
        fields = ["username", "full_name"]
        widgets = {
            "username":  forms.TextInput(attrs={"class": "form-input"}),
            "full_name": forms.TextInput(attrs={"class": "form-input"}),
        }

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        qs = Staff.objects.filter(username=username)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("ชื่อผู้ใช้นี้มีอยู่ในระบบแล้ว")
        return username

    def save(self, commit=True):
        staff = super().save(commit=False)
        new_password = self.cleaned_data.get("new_password")
        if new_password:
            staff.set_password(new_password)
        elif not staff.pk:
            # กรณีสร้างใหม่แต่ไม่กรอกรหัสผ่าน — ไม่อนุญาต
            raise forms.ValidationError("กรุณากำหนดรหัสผ่านสำหรับบัญชีใหม่")
        if commit:
            staff.save()
        return staff


class RecommendationForm(forms.ModelForm):
    """ฟอร์มแก้ไขคำแนะนำ สำหรับหน้า Admin UI เอง"""
    class Meta:
        model = Recommendation
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={"class": "form-input", "rows": 10}),
        }
