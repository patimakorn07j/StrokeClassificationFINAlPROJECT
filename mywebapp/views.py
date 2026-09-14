from functools import wraps

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Count

from .models import Staff, Patient, PredictionRecord, Recommendation
from .forms import LoginForm, PatientCreateForm, AssessmentForm
from .classifier import classify_patient


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
    return Staff.objects.filter(pk=staff_id).first() if staff_id else None


def index(request):
    if request.session.get("staff_id"):
        return redirect("dashboard")
    return render(request, "mywebapp/index.html")


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            staff = Staff.objects.filter(username=form.cleaned_data["username"]).first()
            if staff and staff.check_password(form.cleaned_data["password"]):
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
# ขั้นที่ 1: ค้นหาผู้ป่วยที่มีอยู่ (แสดงจำนวนครั้งที่เคยประเมินด้วย)
# ---------------------------------------------------------------------------
@login_required
def patient_search_view(request):
    create_form = PatientCreateForm()

    query = request.GET.get("q", "").strip()
    results = None
    if query:
        results = (
            Patient.objects.filter(Q(full_name__icontains=query) | Q(hn__icontains=query))
            .annotate(record_count=Count("records"))[:20]
        )

    return render(request, "mywebapp/patient_search.html", {
        "create_form": create_form, "results": results, "query": query,
    })


# ---------------------------------------------------------------------------
# เพิ่มผู้ป่วยใหม่ — ตรวจสอบชื่อซ้ำก่อนสร้าง ป้องกันข้อมูลซ้ำซ้อน
# ระบบสุ่มรหัส HN ให้อัตโนมัติ (ไม่เรียงลำดับ)
# ---------------------------------------------------------------------------
@login_required
def patient_create_view(request):
    if request.method != "POST":
        return redirect("dashboard")

    full_name = request.POST.get("full_name", "").strip()
    confirmed = request.POST.get("confirm") == "1"

    if not full_name:
        messages.error(request, "กรุณากรอกชื่อ-นามสกุลผู้ป่วย")
        return redirect("dashboard")

    # ค้นหาชื่อใกล้เคียง/ซ้ำก่อนสร้างใหม่ เพื่อป้องกันข้อมูลผู้ป่วยซ้ำซ้อน
    possible_duplicates = Patient.objects.filter(full_name__icontains=full_name).annotate(
        record_count=Count("records"))

    if possible_duplicates.exists() and not confirmed:
        return render(request, "mywebapp/patient_confirm.html", {
            "full_name": full_name, "duplicates": possible_duplicates,
        })

    patient = Patient.objects.create(full_name=full_name)  # hn สุ่มให้อัตโนมัติใน model.save()
    messages.success(request, f"เพิ่มผู้ป่วยใหม่สำเร็จ รหัส {patient.hn}")
    return redirect("assess", patient_id=patient.patient_id)


# ---------------------------------------------------------------------------
# ขั้นที่ 2: กรอกข้อมูลอาการเพื่อจำแนกโรค
# ---------------------------------------------------------------------------
@login_required
def assessment_view(request, patient_id):
    staff = get_current_staff(request)
    patient = get_object_or_404(Patient, pk=patient_id)
    previous_count = patient.records.count()

    if request.method == "POST":
        form = AssessmentForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.patient = patient
            record.staff = staff
            record.result = classify_patient(form.cleaned_data)
            record.save()
            return redirect("result", record_id=record.record_id)
    else:
        form = AssessmentForm()

    return render(request, "mywebapp/assess.html", {
        "form": form, "patient": patient, "previous_count": previous_count,
    })


@login_required
def result_view(request, record_id):
    record = get_object_or_404(PredictionRecord, pk=record_id)
    recommendation = Recommendation.objects.filter(result_type=record.result).first()
    return render(request, "mywebapp/result.html", {"record": record, "recommendation": recommendation})


# ---------------------------------------------------------------------------
# ประวัติ — ค้นหา/กรอง + แสดงจำนวนรวมที่พบ
# ---------------------------------------------------------------------------
@login_required
def history_view(request):
    staff = get_current_staff(request)
    records = PredictionRecord.objects.filter(staff=staff).select_related("patient")

    q = request.GET.get("q", "").strip()
    result_filter = request.GET.get("result", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    if q:
        records = records.filter(Q(patient__full_name__icontains=q) | Q(patient__hn__icontains=q))
    if result_filter in ("STROKE", "NON_STROKE"):
        records = records.filter(result=result_filter)
    if date_from:
        records = records.filter(assessed_at__date__gte=date_from)
    if date_to:
        records = records.filter(assessed_at__date__lte=date_to)

    return render(request, "mywebapp/history.html", {
        "records": records, "record_count": records.count(),
        "q": q, "result_filter": result_filter, "date_from": date_from, "date_to": date_to,
    })


@login_required
def patient_detail_view(request, record_id):
    staff = get_current_staff(request)
    record = get_object_or_404(PredictionRecord, pk=record_id, staff=staff)
    recommendation = Recommendation.objects.filter(result_type=record.result).first()

    # ประวัติครั้งอื่นของผู้ป่วยรายเดียวกัน (รหัส HN เดิม)
    other_records = (
        PredictionRecord.objects.filter(patient=record.patient, staff=staff)
        .exclude(record_id=record.record_id)
    )

    return render(request, "mywebapp/patient_detail.html", {
        "record": record, "recommendation": recommendation, "other_records": other_records,
    })


# ---------------------------------------------------------------------------
# แก้ไขข้อมูล — กรอกผิดแล้วอยากกลับมาแก้ ประมวลผลจำแนกใหม่ทันที
# ---------------------------------------------------------------------------
@login_required
def edit_record_view(request, record_id):
    staff = get_current_staff(request)
    record = get_object_or_404(PredictionRecord, pk=record_id, staff=staff)

    if request.method == "POST":
        form = AssessmentForm(request.POST, instance=record)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.result = classify_patient(form.cleaned_data)
            updated.save()
            messages.success(request, "แก้ไขข้อมูลและประมวลผลใหม่เรียบร้อยแล้ว")
            return redirect("patient_detail", record_id=updated.record_id)
    else:
        form = AssessmentForm(instance=record)

    return render(request, "mywebapp/edit_record.html", {"form": form, "record": record})
