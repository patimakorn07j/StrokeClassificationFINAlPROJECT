from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("result/<int:patient_id>/", views.result_view, name="result"),
    path("history/", views.history_view, name="history"),
    path("history/<int:patient_id>/", views.patient_detail_view, name="patient_detail"),
]
