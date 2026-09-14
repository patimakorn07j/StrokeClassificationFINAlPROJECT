from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # ขั้นตอนประเมินผู้ป่วย
    path("dashboard/", views.patient_search_view, name="dashboard"),
    path("dashboard/patient/new/", views.patient_create_view, name="patient_create"),
    path("dashboard/assess/<int:patient_id>/", views.assessment_view, name="assess"),

    path("result/<int:record_id>/", views.result_view, name="result"),

    # ประวัติ / ค้นหา / ดูรายละเอียด / แก้ไข
    path("history/", views.history_view, name="history"),
    path("history/<int:record_id>/", views.patient_detail_view, name="patient_detail"),
    path("history/<int:record_id>/edit/", views.edit_record_view, name="edit_record"),

]
