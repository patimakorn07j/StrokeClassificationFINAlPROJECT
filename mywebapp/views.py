from functools import wraps

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from .models import Staff, Patient, Recommendation
from .forms import LoginForm, PatientForm
from .classifier import classify_patient


# ---------------------------------------------------------------------------
# ใช้ session ของ Django เก็บ staff_id แทนระบบ auth ของ Django
# ---------------------------------------------------------------------------
def login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("staff_id"):
            messages.warning(request, "กรุณาเข้าสู่ระบบก่อนใช้งาน")
            return redirect("login")
        return view_func(request, *args, **kwargs)
    return wrapper


def get_current_staff(request):
    staff_id = request.session.get("staff_id")
    if not staff_id:
        return None
    return Staff.objects.filter(pk=staff_id).first()


# ---------------------------------------------------------------------------
# หน้าแรก
# ---------------------------------------------------------------------------
def index(request):
    if request.session.get("staff_id"):
        return redirect("dashboard")
    return render(request, "mywebapp/index.html")


# ---------------------------------------------------------------------------
# เข้าสู่ระบบ / ออกจากระบบ
# ---------------------------------------------------------------------------
def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            staff = Staff.objects.filter(username=username).first()
            if staff and staff.check_password(password):
                request.session["staff_id"] = staff.staff_id
                request.session["staff_name"] = staff.full_name
                return redirect("dashboard")
            messages.error(request, "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    else:
        form = LoginForm()
    return render(request, "mywebapp/login.html", {"form": form})


def logout_view(request):
    request.session.flush()
    messages.success(request, "ออกจากระบบเรียบร้อยแล้ว")
    return redirect("index")


# ---------------------------------------------------------------------------
# หน้ากรอกข้อมูลผู้ป่วยเพื่อจำแนกโรคหลอดเลือดสมอง
# ---------------------------------------------------------------------------
@login_required
def dashboard_view(request):
    staff = get_current_staff(request)
    if request.method == "POST":
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.staff = staff
            patient.result = classify_patient(form.cleaned_data)
            patient.save()
            return redirect("result", patient_id=patient.patient_id)
    else:
        form = PatientForm()
    return render(request, "mywebapp/dashboard.html", {"form": form, "staff": staff})


# ---------------------------------------------------------------------------
# หน้าแสดงผลการจำแนกและคำแนะนำ (แสดงทันทีหลังกรอกฟอร์ม)
# ---------------------------------------------------------------------------
@login_required
def result_view(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    recommendation = Recommendation.objects.filter(result_type=patient.result).first()
    return render(
        request,
        "mywebapp/result.html",
        {"patient": patient, "recommendation": recommendation},
    )


# ---------------------------------------------------------------------------
# ประวัติการจำแนกโรคหลอดเลือดสมองย้อนหลัง (รายการทั้งหมด)
# ---------------------------------------------------------------------------
@login_required
def history_view(request):
    patients = Patient.objects.filter(staff=get_current_staff(request))
    return render(request, "mywebapp/history.html", {"patients": patients})


# ---------------------------------------------------------------------------
# รายละเอียดการประเมินรายบุคคล — ดูได้อย่างเดียว แก้ไขไม่ได้
# เจ้าหน้าที่ดูได้เฉพาะประวัติที่ตนเองบันทึกไว้เท่านั้น
# ---------------------------------------------------------------------------
@login_required
def patient_detail_view(request, patient_id):
    staff = get_current_staff(request)
    patient = get_object_or_404(Patient, pk=patient_id, staff=staff)
    recommendation = Recommendation.objects.filter(result_type=patient.result).first()
    return render(
        request,
        "mywebapp/patient_detail.html",
        {"patient": patient, "recommendation": recommendation},
    )
