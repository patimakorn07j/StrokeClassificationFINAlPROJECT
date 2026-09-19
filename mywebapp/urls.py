from django.urls import path
from . import views
from . import admin_views

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

    # ── Admin UI ที่สร้างเอง ──────────────────────────────────
    path("system-admin/login/", admin_views.admin_login_view, name="admin_login"),
    path("system-admin/logout/", admin_views.admin_logout_view, name="admin_logout"),
    path("system-admin/", admin_views.admin_panel_view, name="admin_panel"),

    path("system-admin/staff/", admin_views.admin_staff_list_view, name="admin_staff_list"),
    path("system-admin/staff/add/", admin_views.admin_staff_add_view, name="admin_staff_add"),
    path("system-admin/staff/<int:staff_id>/edit/", admin_views.admin_staff_edit_view, name="admin_staff_edit"),
    path("system-admin/staff/<int:staff_id>/delete/", admin_views.admin_staff_delete_view, name="admin_staff_delete"),

    path("system-admin/recommendations/", admin_views.admin_recommendation_list_view, name="admin_recommendation_list"),
    path("system-admin/recommendations/<int:rec_id>/edit/", admin_views.admin_recommendation_edit_view, name="admin_recommendation_edit"),
]
