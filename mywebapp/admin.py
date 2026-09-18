from django.contrib import admin
from .models import Staff, Patient, PredictionRecord, Recommendation


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ("staff_id", "username", "full_name", "created_at")
    search_fields = ("username", "full_name")

    def save_model(self, request, obj, form, change):
        if not change or "password" in form.changed_data:
            obj.set_password(obj.password)
        super().save_model(request, obj, form, change)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("hn", "full_name", "gender", "age", "age_group", "created_at")
    search_fields = ("hn", "full_name")


@admin.register(PredictionRecord)
class PredictionRecordAdmin(admin.ModelAdmin):
    list_display = ("record_id", "patient", "result", "assessed_at", "staff")
    list_filter = ("result",)
    search_fields = ("patient__hn", "patient__full_name")


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ("recommendation_id", "result_type")
