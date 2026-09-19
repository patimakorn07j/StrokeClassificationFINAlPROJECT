"""
admin_views.py
--------------
Views สำหรับหน้า Admin UI ที่ออกแบบเอง (แยกจาก Django /admin/ มาตรฐาน)
Login ใช้ Django auth (auth_user / superuser) แต่หน้าตาออกแบบเข้าธีมของเว็บ
"""

from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required as django_login_required
from django.shortcuts import render, redirect, get_object_or_404

from .models import Staff, Patient, PredictionRecord, Recommendation
from .forms import StaffForm, RecommendationForm


def admin_required(view_func):
    """อนุญาตเฉพาะ superuser เท่านั้น"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.is_superuser):
            messages.warning(request, "กรุณาเข้าสู่ระบบผู้ดูแลระบบก่อนใช้งาน")
            return redirect("admin_login")
        return view_func(request, *args, **kwargs)
    return wrapper


# ---------------------------------------------------------------------------
# เข้าสู่ระบบ / ออกจากระบบผู้ดูแลระบบ (ใช้ auth_user เดิม)
# ---------------------------------------------------------------------------
def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect("admin_panel")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect("admin_panel")
        messages.error(request, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง หรือไม่มีสิทธิ์ผู้ดูแลระบบ")

    return render(request, "mywebapp/admin_login.html")


def admin_logout_view(request):
    logout(request)
    messages.success(request, "ออกจากระบบผู้ดูแลระบบเรียบร้อยแล้ว")
    return redirect("index")


# ---------------------------------------------------------------------------
# หน้าแรกของ Admin — สรุปภาพรวมระบบ
# ---------------------------------------------------------------------------
@admin_required
def admin_panel_view(request):
    total_staff = Staff.objects.count()
    total_patients = Patient.objects.count()
    total_records = PredictionRecord.objects.count()
    stroke_count = PredictionRecord.objects.filter(result="STROKE").count()
    non_stroke_count = PredictionRecord.objects.filter(result="NON_STROKE").count()

    return render(request, "mywebapp/admin_panel.html", {
        "total_staff": total_staff,
        "total_patients": total_patients,
        "total_records": total_records,
        "stroke_count": stroke_count,
        "non_stroke_count": non_stroke_count,
    })


# ---------------------------------------------------------------------------
# จัดการเจ้าหน้าที่ — เพิ่ม / แก้ไข / ลบ
# ---------------------------------------------------------------------------
@admin_required
def admin_staff_list_view(request):
    staff_list = Staff.objects.all().order_by("-created_at")
    return render(request, "mywebapp/admin_staff_list.html", {"staff_list": staff_list})


@admin_required
def admin_staff_add_view(request):
    if request.method == "POST":
        form = StaffForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "เพิ่มบัญชีเจ้าหน้าที่สำเร็จ")
            return redirect("admin_staff_list")
    else:
        form = StaffForm()
    return render(request, "mywebapp/admin_staff_form.html", {"form": form, "is_edit": False})


@admin_required
def admin_staff_edit_view(request, staff_id):
    staff = get_object_or_404(Staff, pk=staff_id)
    if request.method == "POST":
        form = StaffForm(request.POST, instance=staff)
        if form.is_valid():
            form.save()
            messages.success(request, "แก้ไขข้อมูลเจ้าหน้าที่สำเร็จ")
            return redirect("admin_staff_list")
    else:
        form = StaffForm(instance=staff)
    return render(request, "mywebapp/admin_staff_form.html", {"form": form, "is_edit": True, "staff": staff})


@admin_required
def admin_staff_delete_view(request, staff_id):
    staff = get_object_or_404(Staff, pk=staff_id)
    if request.method == "POST" and request.POST.get("confirm") == "1":
        staff.delete()
        messages.success(request, "ลบบัญชีเจ้าหน้าที่เรียบร้อยแล้ว")
        return redirect("admin_staff_list")
    return render(request, "mywebapp/admin_staff_delete_confirm.html", {"staff": staff})


# ---------------------------------------------------------------------------
# จัดการคำแนะนำ — เพิ่ม / แก้ไข / ลบ
# ระบบเก็บได้ผลลัพธ์ละ 1 รายการเท่านั้น (STROKE และ NON_STROKE)
# ปุ่มเพิ่มจึงโผล่เฉพาะตอนที่ยังมีประเภทที่ว่างอยู่ เช่น เพิ่งลบไป
# ---------------------------------------------------------------------------
def _missing_result_types():
    """ประเภทผลลัพธ์ที่ยังไม่มีคำแนะนำในระบบ"""
    used = set(Recommendation.objects.values_list("result_type", flat=True))
    return [(value, label) for value, label in Recommendation.RESULT_TYPE_CHOICES if value not in used]


@admin_required
def admin_recommendation_list_view(request):
    # เรียงจากมากไปน้อยเพื่อให้ STROKE ซึ่งเร่งด่วนกว่าขึ้นก่อน NON_STROKE
    recommendations = Recommendation.objects.all().order_by("-result_type")
    missing = _missing_result_types()
    return render(request, "mywebapp/admin_recommendation_list.html", {
        "recommendations": recommendations,
        "missing_labels": [label for _, label in missing],
        "can_add": bool(missing),
    })


@admin_required
def admin_recommendation_add_view(request):
    if not _missing_result_types():
        messages.warning(request, "มีคำแนะนำครบทั้ง Stroke และ Non-Stroke แล้ว หากต้องการเปลี่ยนเนื้อหาให้กดแก้ไข")
        return redirect("admin_recommendation_list")

    if request.method == "POST":
        form = RecommendationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "เพิ่มคำแนะนำสำเร็จ")
            return redirect("admin_recommendation_list")
    else:
        form = RecommendationForm()
    return render(request, "mywebapp/admin_recommendation_form.html", {"form": form, "is_edit": False})


@admin_required
def admin_recommendation_edit_view(request, rec_id):
    rec = get_object_or_404(Recommendation, pk=rec_id)
    if request.method == "POST":
        form = RecommendationForm(request.POST, instance=rec)
        if form.is_valid():
            form.save()
            messages.success(request, "แก้ไขคำแนะนำสำเร็จ")
            return redirect("admin_recommendation_list")
    else:
        form = RecommendationForm(instance=rec)
    return render(request, "mywebapp/admin_recommendation_form.html", {"form": form, "rec": rec, "is_edit": True})


@admin_required
def admin_recommendation_delete_view(request, rec_id):
    rec = get_object_or_404(Recommendation, pk=rec_id)
    if request.method == "POST" and request.POST.get("confirm") == "1":
        rec.delete()
        messages.success(request, "ลบคำแนะนำเรียบร้อยแล้ว")
        return redirect("admin_recommendation_list")
    return render(request, "mywebapp/admin_recommendation_delete_confirm.html", {"rec": rec})
