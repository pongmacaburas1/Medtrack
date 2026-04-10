from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from pdl.decorators import role_required
from django.views.generic import CreateView
from django.utils import timezone
from django.utils.dateparse import parse_date
from datetime import date, timedelta
import datetime as dt
import calendar

from .models import (
    Consultation,
    Physician,
    ConsultationLocation,
    ConsultationReason,
    ConsultationTimeBlock,
)
from .forms import ScheduleConsultationForm
from pdl.models import PDLProfile


# ─────────────────────────────────────────────────────────────
#  HELPER: build calendar context from a consultations queryset
# ─────────────────────────────────────────────────────────────

def consultation_calendar(request, consultations):
    """
    Generates a calendar context dict for a given consultations queryset.

    Returns a dict with:
        calendar_data  – list of weeks; each week is a list of day dicts:
                            { day, weekday, consultations }
        year, month, month_name
        prev_month, prev_year, next_month, next_year
    """
    today = date.today()
    year  = int(request.GET.get('year',  today.year))
    month = int(request.GET.get('month', today.month))

    if year < 1 or month < 1 or month > 12:
        messages.error(request, "Invalid year or month. Defaulting to today.")
        year, month = today.year, today.month

    cal        = calendar.Calendar()
    month_days = cal.itermonthdays2(year, month)   # (day, weekday) tuples

    # Map day-of-month → list of consultations
    consultation_map = {}
    for c in consultations:
        d = c.consultation_date_date_only
        if d.year == year and d.month == month:
            consultation_map.setdefault(d.day, []).append(c)

    # Build flat list then chunk into weeks
    flat = []
    for day, weekday in month_days:
        flat.append({
            'day':           day if day else None,
            'weekday':       weekday,
            'consultations': consultation_map.get(day, []) if day else [],
        })

    weeks, week = [], []
    for cell in flat:
        week.append(cell)
        if len(week) == 7:
            weeks.append(week)
            week = []
    if week:
        weeks.append(week)

    return {
        'calendar_data': weeks,
        'year':          year,
        'month':         month,
        'month_name':    calendar.month_name[month],
        'prev_month':    (month - 1) if month > 1 else 12,
        'prev_year':     year if month > 1 else year - 1,
        'next_month':    (month + 1) if month < 12 else 1,
        'next_year':     year if month < 12 else year + 1,
    }


# ─────────────────────────────────────────────────────────────
#  CALENDAR VIEWS
# ─────────────────────────────────────────────────────────────

@login_required
def all_consultations(request):
    """Show every consultation on the calendar."""
    consultations = Consultation.objects.all()
    context = consultation_calendar(request, consultations)
    return render(request, "consultations/consultation_calendar.html", context)


@login_required
def consultations_by_physician(request, physician_id):
    """Show only consultations for a specific physician."""
    physician     = get_object_or_404(Physician, id=physician_id)
    consultations = Consultation.objects.filter(physician=physician)
    context       = consultation_calendar(request, consultations)
    return render(request, "consultations/consultation_calendar.html", context)


# ─────────────────────────────────────────────────────────────
#  DOCTOR DASHBOARD
# ─────────────────────────────────────────────────────────────

@login_required
def doctor_dashboard(request):
    """
    Dashboard for the logged-in user.

    • If the logged-in user is a Physician → show their own upcoming consultations.
    • Otherwise (admin / staff) → show all upcoming consultations so the
      dashboard is still useful without raising a 404.
    """
    today = date.today()
    fourteen_days_later = today + timedelta(days=14)  # Extended to show follow-ups scheduled 7 days out
    
    try:
        physician = Physician.objects.get(username=request.user)
        upcoming_consultations = (
            Consultation.objects
            .filter(
                physician=physician,
                consultation_date_date_only__gte=today,
                status="scheduled",
            )
            .order_by('consultation_date_date_only', 'consultation_time_block')[:5]
        )
        # Follow-up consultations due within next 14 days for this physician
        followup_due = (
            Consultation.objects
            .filter(
                physician=physician,
                is_followup=True,
                status="scheduled",
                consultation_date_date_only__gte=today,
                consultation_date_date_only__lte=fourteen_days_later,
            )
            .select_related('pdl_profile__username', 'parent_consultation')
            .order_by('consultation_date_date_only')
        )
    except Physician.DoesNotExist:
        physician = None
        # Admin / staff fallback: all upcoming consultations
        upcoming_consultations = (
            Consultation.objects
            .filter(
                consultation_date_date_only__gte=today,
                status="scheduled",
            )
            .select_related('physician', 'pdl_profile', 'location')
            .order_by('consultation_date_date_only', 'consultation_time_block')[:5]
        )
        # All follow-ups due within next 14 days
        followup_due = (
            Consultation.objects
            .filter(
                is_followup=True,
                status="scheduled",
                consultation_date_date_only__gte=today,
                consultation_date_date_only__lte=fourteen_days_later,
            )
            .select_related('pdl_profile__username', 'physician', 'parent_consultation')
            .order_by('consultation_date_date_only')
        )

    context = {
        'physician':              physician,
        'upcoming_consultations': upcoming_consultations,
        'followup_due':           followup_due,
        'followup_count':         followup_due.count() if followup_due else 0,
    }
    return render(request, "consultations/doctor_dashboard.html", context)


# ─────────────────────────────────────────────────────────────
#  SCHEDULE / CREATE
# ─────────────────────────────────────────────────────────────

@role_required('admin', 'doctor')
def schedule_consultation(request):
    """Simple function-based create view (legacy; prefer ConsultationCreateView)."""
    if request.method == 'POST':
        form = ScheduleConsultationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Consultation scheduled successfully.")
            return redirect('consultations:consultation_calendar')
    else:
        form = ScheduleConsultationForm()

    return render(request, 'consultations/schedule_consultation.html', {'form': form})


@role_required('admin', 'doctor')
def create_consultation(request):
    """JSON-driven create endpoint (called from the calendar quick-add form)."""
    if request.method == 'POST':
        try:
            date_str   = request.POST.get('date')
            time_block = request.POST.get('time')

            consultation_date = dt.datetime.strptime(date_str, '%Y-%m-%d').date()

            if not time_block:
                messages.error(request, "Time block is required.")
                return redirect('consultations:create')

            if not physician:
                messages.error(request, "Physician is required.")
                return redirect('consultations:create')

            if not reason:
                messages.error(request, "Reason is required.")
                return redirect('consultations:create')

            if not hasattr(ConsultationTimeBlock, time_block):
                raise ValueError(f"Invalid time block: {time_block}")

            pdl      = get_object_or_404(PDLProfile,            id=request.POST.get('pdl'))
            location = get_object_or_404(ConsultationLocation,  id=request.POST.get('location'))
            physician = get_object_or_404(Physician,            id=request.POST.get('physician'))
            reason   = get_object_or_404(ConsultationReason,    id=request.POST.get('reason'))

            Consultation.objects.create(
                consultation_date_date_only=consultation_date,
                consultation_time_block=time_block,
                pdl_profile=pdl,
                location=location,
                physician=physician,
                reason=reason,
                status='scheduled',
                is_an_emergency=request.POST.get('is_an_emergency') == 'on',
                notes=request.POST.get('notes', ''),
            )

            messages.success(request, "Consultation scheduled successfully.")
            return redirect('consultations:consultation_calendar')

        except Exception as e:
            messages.error(request, f"Error scheduling consultation: {e}")
            return redirect('consultations:create_consultation')

    return render(request, 'consultations/create_consultation.html')


class ConsultationCreateView(CreateView):
    """Class-based create view; supports pre-filling date from ?date=YYYY-MM-DD."""
    model         = Consultation
    form_class    = ScheduleConsultationForm
    template_name = "consultations/consultation_form.html"
    success_url   = reverse_lazy("consultations:consultation_calendar")

    def get_initial(self):
        initial = super().get_initial()
        qd = self.request.GET.get("date")
        d  = parse_date(qd) if qd else None
        if d:
            initial["consultation_date_date_only"] = d
        return initial

    def form_valid(self, form):
        messages.success(self.request, "Consultation scheduled.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please correct the errors below.")
        return super().form_invalid(form)


# ─────────────────────────────────────────────────────────────
#  CANCEL / RESCHEDULE / COMPLETE
# ─────────────────────────────────────────────────────────────

@role_required('admin', 'doctor')
def cancel_consultation(request, consultation_id):
    """Confirm then cancel a consultation."""
    consultation = get_object_or_404(
        Consultation.objects.select_related('physician'), id=consultation_id
    )

    if request.method == 'POST':
        consultation.status = Consultation.Status.CANCELED
        consultation.save()
        messages.success(
            request,
            f"Consultation with {consultation.physician} on "
            f"{consultation.consultation_date_date_only} has been cancelled."
        )
        return redirect('consultations:consultation_calendar')

    return render(request, 'consultations/cancel_consultation.html', {'consultation': consultation})


@role_required('admin', 'doctor')
def reschedule_consultation(request, consultation_id):
    """Confirm then reschedule a consultation."""
    consultation = get_object_or_404(Consultation, id=consultation_id)

    if request.method == 'POST':
        form = ScheduleConsultationForm(request.POST, instance=consultation)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Consultation with {consultation.physician} has been rescheduled."
            )
            return redirect('consultations:consultation_calendar')
    else:
        form = ScheduleConsultationForm(instance=consultation)

    return render(
        request,
        'consultations/reschedule_consultation.html',
        {'form': form, 'consultation': consultation},
    )


@role_required('admin', 'doctor')
def complete_consultation(request, consultation_id):
    """Mark a consultation as completed. Doctor can optionally add a follow-up."""
    consultation = get_object_or_404(
        Consultation.objects.select_related('physician'), id=consultation_id
    )

    if request.method == "POST":
        # Save form data
        consultation.fr_conclusion = request.POST.get('fr_conclusion') or None
        consultation.fr_other_impressions = request.POST.get('fr_other_impressions') or None
        consultation.fr_recommendation = request.POST.get('fr_recommendation') or None
        consultation.notes = request.POST.get('notes') or consultation.notes
        
        # Support both Enum and plain-string status fields
        if hasattr(Consultation, "Status") and hasattr(Consultation.Status, "COMPLETED"):
            consultation.status = Consultation.Status.COMPLETED
        else:
            consultation.status = "completed"

        if hasattr(consultation, "completed_at"):
            consultation.completed_at = timezone.now()

        consultation.save()
        
        # Check if doctor wants to add a follow-up consultation
        add_followup = request.POST.get('add_followup') == '1'
        
        if add_followup and not consultation.followup_scheduled:
            # Get follow-up details from form
            followup_days = int(request.POST.get('followup_days', 7) or 7)
            followup_date = consultation.consultation_date_date_only + timedelta(days=followup_days)
            followup_notes = request.POST.get('followup_notes', '').strip()
            
            try:
                # Get a "Follow-up" reason
                followup_reason, _ = ConsultationReason.objects.get_or_create(
                    reason="Follow-up Consultation",
                    defaults={"description": "Scheduled follow-up consultation"}
                )
                
                # Create the follow-up consultation
                followup = Consultation.objects.create(
                    pdl_profile=consultation.pdl_profile,
                    physician=consultation.physician,
                    location=consultation.location,
                    reason=followup_reason,
                    consultation_date_date_only=followup_date,
                    consultation_time_block=consultation.consultation_time_block,
                    status='scheduled',
                    is_followup=True,
                    parent_consultation=consultation,
                    notes=followup_notes or f"Follow-up for consultation on {consultation.consultation_date_date_only}",
                )
                
                # Mark the original consultation as having a follow-up scheduled
                consultation.followup_scheduled = True
                consultation.save()
                
                messages.info(
                    request,
                    f"Follow-up consultation scheduled for {followup_date.strftime('%B %d, %Y')}."
                )
            except Exception as e:
                messages.warning(request, f"Could not schedule follow-up: {e}")
        
        messages.success(
            request,
            f"Consultation with {consultation.physician} on "
            f"{consultation.consultation_date_date_only} marked as completed."
        )
        return redirect("consultations:consultation_calendar")

    return render(
        request,
        "consultations/complete_consultation.html",
        {"consultation": consultation},
    )


# ─────────────────────────────────────────────────────────────
#  PRINTABLE
# ─────────────────────────────────────────────────────────────

@login_required
def consultation_printable(request, pk):
    """Render a printable form for a single consultation."""
    obj = get_object_or_404(Consultation, pk=pk)
    return render(
        request,
        "consultations/consultation_printable.html",
        {"c": obj, "now": timezone.localtime()},
    )


# ─────────────────────────────────────────────────────────────
#  JSON APIs  (used by the calendar quick-add dropdowns)
# ─────────────────────────────────────────────────────────────

@login_required
def pdl_list_api(request):
    data = [
        {
            'id':    pdl.id,
            'name':  f"{pdl.username.first_name} {pdl.username.last_name}",
            'email': pdl.username.email,
        }
        for pdl in PDLProfile.objects.all()
    ]
    return JsonResponse(data, safe=False)


@login_required
def physician_list_api(request):
    data = [
        {
            'id':    p.id,
            'name':  f"{p.username.first_name} {p.username.last_name}",
            'email': p.username.email,
        }
        for p in Physician.objects.all()
    ]
    return JsonResponse(data, safe=False)


@login_required
def location_list_api(request):
    data = [
        {'id': loc.id, 'room_number': loc.room_number}
        for loc in ConsultationLocation.objects.all()
    ]
    return JsonResponse(data, safe=False)


@login_required
def consultation_reason_list_api(request):
    data = [
        {'id': r.id, 'reason': r.reason, 'description': r.description}
        for r in ConsultationReason.objects.all()
    ]
    return JsonResponse(data, safe=False)


@login_required
def consultation_time_block_list_api(request):
    data = [
        {'value': block.name, 'display': block.value[1]}
        for block in ConsultationTimeBlock
        if "08:00" <= block.value[0] <= "17:00"
    ]
    return JsonResponse(data, safe=False)


# ─────────────────────────────────────────────────────────────
#  CONSULTATION HISTORY
# ─────────────────────────────────────────────────────────────

@login_required
def consultation_history(request):
    """
    Display consultation history - all consultations with filtering options.
    Shows completed, cancelled and all past consultations.
    """
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')
    
    consultations = (
        Consultation.objects
        .select_related('pdl_profile__username', 'physician__username', 'location', 'reason')
        .order_by('-consultation_date_date_only', '-id')
    )
    
    # Search filter
    if q:
        consultations = consultations.filter(
            Q(pdl_profile__username__first_name__icontains=q) |
            Q(pdl_profile__username__last_name__icontains=q) |
            Q(physician__username__first_name__icontains=q) |
            Q(physician__username__last_name__icontains=q) |
            Q(reason__reason__icontains=q)
        )
    
    # Status filter
    if status_filter:
        consultations = consultations.filter(status=status_filter)
    
    # Stats
    total_count = consultations.count()
    completed_count = consultations.filter(status='completed').count()
    cancelled_count = consultations.filter(status='canceled').count()
    scheduled_count = consultations.filter(status='scheduled').count()
    
    # Pagination
    paginator = Paginator(consultations, 15)  # 15 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'consultations': page_obj,
        'page_obj': page_obj,
        'q': q,
        'status_filter': status_filter,
        'stats': {
            'total': total_count,
            'completed': completed_count,
            'cancelled': cancelled_count,
            'scheduled': scheduled_count,
        }
    }
    return render(request, 'consultations/consultation_history.html', context)