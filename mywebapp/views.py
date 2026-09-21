from functools import wraps

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db.models import Q

from .models import Staff, Patient, PredictionRecord, Recommendation
from .forms import (
    LoginForm, PatientRegisterForm, PatientDemographicForm,
    PatientEditForm, AssessmentForm,
)
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
# ค้นหาผู้ป่วย — พบแล้วเข้าประเมินได้เลย / ไม่พบชื่อนี้ค่อยเพิ่มใหม่
# ---------------------------------------------------------------------------
@login_required
def patient_search_view(request):
    query = request.GET.get("q", "").strip()
    results = None
    exact_match = False

    if query:
        results = Patient.objects.filter(Q(full_name__icontains=query) | Q(hn__icontains=query))[:20]
        exact_match = any(p.full_name.strip().lower() == query.lower() for p in results)

    return render(request, "mywebapp/patient_search.html", {
        "results": results, "query": query, "exact_match": exact_match,
    })


# ---------------------------------------------------------------------------
# ขึ้นทะเบียนผู้ป่วยใหม่ — ชื่อ + รหัส HN เดิมของโรงพยาบาล (2 ช่องเท่านั้น)
# ---------------------------------------------------------------------------
@login_required
def patient_register_view(request):
    if request.method == "POST":
        form = PatientRegisterForm(request.POST)
        if form.is_valid():
            patient = form.save()
            messages.success(request, f"ขึ้นทะเบียนผู้ป่วยสำเร็จ รหัส {patient.hn}")
            return redirect("assess", patient_id=patient.patient_id)
    else:
        initial_name = request.GET.get("name", "")
        form = PatientRegisterForm(initial={"full_name": initial_name})

    return render(request, "mywebapp/patient_register.html", {"form": form})


def _next_qs(request):
    """ส่งต่อปลายทางเดิมไปกับลิงก์ยกเลิก เพื่อให้กดยกเลิกแล้วกลับไปหน้าที่กดเข้ามา"""
    return "?next=assess" if request.GET.get("next") == "assess" else ""


def _return_url(request, patient):
    """
    กลับไปหน้าที่กดเข้ามา — ถ้ามาจากหน้าประเมินให้กลับไปหน้าประเมินของผู้ป่วยรายนั้น
    ถ้าไม่ใช่ก็กลับไปหน้าค้นหาพร้อมคำค้นเดิม เพื่อให้เห็นการ์ดของผู้ป่วยรายนั้นทันที
    """
    if request.GET.get("next") == "assess":
        return reverse("assess", args=[patient.patient_id])
    return f"{reverse('dashboard')}?q={patient.hn}"


def _record_to_features(record):
    """รวมข้อมูลผู้ป่วยกับแบบประเมินที่บันทึกไว้แล้ว ให้อยู่ในรูปที่ classify_patient ต้องการ"""
    return {
        "gender":          record.patient.gender,
        "age":             record.patient.age,
        "age_group":       record.patient.age_group,
        "patient_type":    record.patient_type,
        "referral_reason": record.referral_reason,
        "is_receive":      record.is_receive,
        "is_referboard":   record.is_referboard,
        "f_face":          record.f_face,
        "a_arm":           record.a_arm,
        "s_speech":        record.s_speech,
    }


# ---------------------------------------------------------------------------
# แก้ไขข้อมูลผู้ป่วย — ถ้าแก้เพศ/อายุ/กลุ่มอายุ ซึ่งเป็นค่าที่แบบจำลองใช้
# ต้องประมวลผลการประเมินเดิมของผู้ป่วยรายนั้นใหม่ทั้งหมด ผลลัพธ์จึงจะตรงกับข้อมูลล่าสุด
# ---------------------------------------------------------------------------
@login_required
def patient_edit_view(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)

    if request.method == "POST":
        form = PatientEditForm(request.POST, instance=patient)
        if form.is_valid():
            rerun = form.demographics_changed
            patient = form.save()

            recomputed = 0
            if rerun:
                for record in patient.records.all():
                    record.result = classify_patient(_record_to_features(record))
                    record.save(update_fields=["result", "updated_at"])
                    recomputed += 1

            if recomputed:
                messages.success(
                    request,
                    f"แก้ไขข้อมูลผู้ป่วยสำเร็จ และประมวลผลการประเมินเดิมใหม่ {recomputed} รายการ",
                )
            else:
                messages.success(request, "แก้ไขข้อมูลผู้ป่วยสำเร็จ")
            return redirect(_return_url(request, patient))
    else:
        form = PatientEditForm(instance=patient)

    return render(request, "mywebapp/patient_edit.html", {
        "form": form, "patient": patient, "record_count": patient.records.count(),
        "back_url": _return_url(request, patient), "next_qs": _next_qs(request),
    })


# ---------------------------------------------------------------------------
# ลบผู้ป่วย — อนุญาตเฉพาะรายที่ยังไม่มีผลการประเมิน
# เพราะการลบผู้ป่วยจะลบผลการประเมินของเจ้าหน้าที่ทุกคนที่เคยประเมินรายนั้นไปด้วย
# ---------------------------------------------------------------------------
@login_required
def patient_delete_view(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    record_count = patient.records.count()

    if record_count == 0 and request.method == "POST" and request.POST.get("confirm") == "1":
        hn = patient.hn
        patient.delete()
        messages.success(request, f"ลบผู้ป่วยรหัส {hn} ออกจากระบบเรียบร้อยแล้ว")
        return redirect("dashboard")

    return render(request, "mywebapp/patient_delete_confirm.html", {
        "patient": patient, "record_count": record_count,
        "back_url": _return_url(request, patient), "next_qs": _next_qs(request),
    })


# ---------------------------------------------------------------------------
# ประเมินอาการ — ครั้งแรกกรอกเพศ/อายุ/กลุ่มอายุด้วย ครั้งต่อไปข้ามไปเลย
# ---------------------------------------------------------------------------
@login_required
def assessment_view(request, patient_id):
    staff = get_current_staff(request)
    patient = get_object_or_404(Patient, pk=patient_id)
    first_time = not patient.has_demographics

    if request.method == "POST":
        assess_form = AssessmentForm(request.POST)
        demo_form = PatientDemographicForm(request.POST, instance=patient) if first_time else None

        assess_valid = assess_form.is_valid()
        demo_valid = demo_form.is_valid() if first_time else True

        if assess_valid and demo_valid:
            if first_time:
                demo_form.save()

            combined = {
                "gender": patient.gender,
                "age": patient.age,
                "age_group": patient.age_group,
                **assess_form.cleaned_data,
            }
            record = assess_form.save(commit=False)
            record.patient = patient
            record.staff = staff
            record.result = classify_patient(combined)
            record.save()
            return redirect("result", record_id=record.record_id)
    else:
        assess_form = AssessmentForm()
        demo_form = PatientDemographicForm(instance=patient) if first_time else None

    return render(request, "mywebapp/assess.html", {
        "assess_form": assess_form, "demo_form": demo_form,
        "patient": patient, "first_time": first_time,
    })


@login_required
def result_view(request, record_id):
    record = get_object_or_404(PredictionRecord, pk=record_id)
    recommendation = Recommendation.objects.filter(result_type=record.result).first()
    return render(request, "mywebapp/result.html", {"record": record, "recommendation": recommendation})


# ---------------------------------------------------------------------------
# หน้าประวัติรวม — แสดงรายชื่อผู้ป่วยทั้งหมด พร้อมจำนวนครั้งที่ประเมิน
# ---------------------------------------------------------------------------
@login_required
def history_view(request):
    staff = get_current_staff(request)
    q = request.GET.get("q", "").strip()

    patient_ids = PredictionRecord.objects.filter(staff=staff).values_list("patient_id", flat=True).distinct()
    patients_qs = Patient.objects.filter(patient_id__in=patient_ids)
    if q:
        patients_qs = patients_qs.filter(Q(full_name__icontains=q) | Q(hn__icontains=q))

    rows = []
    for p in patients_qs:
        records = PredictionRecord.objects.filter(patient=p, staff=staff)
        last = records.order_by("-assessed_at").first()
        rows.append({"patient": p, "count": records.count(), "last_assessed": last.assessed_at if last else None})
    rows.sort(key=lambda r: r["last_assessed"] or "", reverse=True)

    return render(request, "mywebapp/history.html", {"rows": rows, "q": q})


# ---------------------------------------------------------------------------
# ประวัติของผู้ป่วยรายบุคคล — ทุกครั้งที่เคยประเมิน พร้อมลำดับ
# ---------------------------------------------------------------------------
@login_required
def patient_history_view(request, patient_id):
    staff = get_current_staff(request)
    patient = get_object_or_404(Patient, pk=patient_id)

    records = list(PredictionRecord.objects.filter(patient=patient, staff=staff).order_by("assessed_at"))
    for i, r in enumerate(records, 1):
        r.seq = i
    records.reverse()

    return render(request, "mywebapp/patient_history.html", {"patient": patient, "records": records})


@login_required
def record_detail_view(request, record_id):
    staff = get_current_staff(request)
    record = get_object_or_404(PredictionRecord, pk=record_id, staff=staff)
    recommendation = Recommendation.objects.filter(result_type=record.result).first()
    return render(request, "mywebapp/record_detail.html", {"record": record, "recommendation": recommendation})


@login_required
def edit_record_view(request, record_id):
    staff = get_current_staff(request)
    record = get_object_or_404(PredictionRecord, pk=record_id, staff=staff)

    if request.method == "POST":
        form = AssessmentForm(request.POST, instance=record)
        if form.is_valid():
            updated = form.save(commit=False)
            combined = {
                "gender": record.patient.gender,
                "age": record.patient.age,
                "age_group": record.patient.age_group,
                **form.cleaned_data,
            }
            updated.result = classify_patient(combined)
            updated.save()
            messages.success(request, "แก้ไขข้อมูลและประมวลผลใหม่เรียบร้อยแล้ว")
            return redirect("record_detail", record_id=updated.record_id)
    else:
        form = AssessmentForm(instance=record)

    return render(request, "mywebapp/edit_record.html", {"form": form, "record": record})


# ---------------------------------------------------------------------------
# ลบข้อมูลการประเมิน — ต้องกดยืนยันซ้ำก่อนลบจริง
# ---------------------------------------------------------------------------
@login_required
def delete_record_view(request, record_id):
    staff = get_current_staff(request)
    record = get_object_or_404(PredictionRecord, pk=record_id, staff=staff)

    if request.method == "POST" and request.POST.get("confirm") == "1":
        patient_id = record.patient_id
        record.delete()
        messages.success(request, "ลบข้อมูลการจำแนกเรียบร้อยแล้ว")
        return redirect("patient_history", patient_id=patient_id)

    return render(request, "mywebapp/delete_confirm.html", {"record": record})
