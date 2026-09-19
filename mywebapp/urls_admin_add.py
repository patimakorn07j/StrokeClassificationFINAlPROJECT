# ---------------------------------------------------------------------------
# เพิ่มเข้าไปใน urls.py เดิม — import และ urlpatterns เพิ่ม
# ---------------------------------------------------------------------------

# เพิ่มบรรทัด import ด้านบนไฟล์ urls.py
# from . import admin_views

# เพิ่ม path เหล่านี้เข้าไปใน urlpatterns เดิม (ต่อท้าย list)

    path("system-admin/login/", admin_views.admin_login_view, name="admin_login"),
    path("system-admin/logout/", admin_views.admin_logout_view, name="admin_logout"),
    path("system-admin/", admin_views.admin_panel_view, name="admin_panel"),

    path("system-admin/staff/", admin_views.admin_staff_list_view, name="admin_staff_list"),
    path("system-admin/staff/add/", admin_views.admin_staff_add_view, name="admin_staff_add"),
    path("system-admin/staff/<int:staff_id>/edit/", admin_views.admin_staff_edit_view, name="admin_staff_edit"),
    path("system-admin/staff/<int:staff_id>/delete/", admin_views.admin_staff_delete_view, name="admin_staff_delete"),

    path("system-admin/recommendations/", admin_views.admin_recommendation_list_view, name="admin_recommendation_list"),
    path("system-admin/recommendations/<int:rec_id>/edit/", admin_views.admin_recommendation_edit_view, name="admin_recommendation_edit"),
