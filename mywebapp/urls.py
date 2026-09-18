from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("dashboard/", views.patient_search_view, name="dashboard"),
    path("dashboard/register/", views.patient_register_view, name="patient_register"),
    path("dashboard/assess/<int:patient_id>/", views.assessment_view, name="assess"),

    path("result/<int:record_id>/", views.result_view, name="result"),

    path("history/", views.history_view, name="history"),
    path("history/patient/<int:patient_id>/", views.patient_history_view, name="patient_history"),
    path("history/record/<int:record_id>/", views.record_detail_view, name="record_detail"),
    path("history/record/<int:record_id>/edit/", views.edit_record_view, name="edit_record"),
    path("history/record/<int:record_id>/delete/", views.delete_record_view, name="delete_record"),
]
