from django.contrib import admin
from .models import Staff, Patient, Recommendation


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("staff_id", "username", "full_name", "created_at")
    search_fields = ("username", "full_name")

    def save_model(self, request, obj, form, change):
        # hash รหัสผ่านก่อนบันทึกลงฐานข้อมูล
        if not change or "password" in form.changed_data:
            obj.set_password(obj.password)
        super().save_model(request, obj, form, change)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("patient_id", "gender", "age", "result", "assessed_at", "staff")
    list_filter = ("result", "gender", "age_group")
    search_fields = ("patient_id",)


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ("recommendation_id", "result_type")