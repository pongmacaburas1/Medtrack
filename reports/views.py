# reports/views.py
from datetime import date, timedelta
from collections import defaultdict

from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncWeek, TruncMonth, TruncYear
from django.db.models import DateField
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.timezone import localdate
from django.contrib.auth.decorators import login_required

from consultations.models import Consultation
from medications.models import MedicationPrescription, MedicationInventory, Medication
from pdl.models import HealthCondition, PDLProfile

# --- helpers ---------------------------------------------------------------

def _daterange_list(period: str, n: int, today: date):
    """Return a reverse-chronological list of period-start dates for last n periods (including current)."""
    if period == "week":
        # Normalize to Monday of this ISO week
        start = today - timedelta(days=today.weekday())
        return [start - timedelta(weeks=i) for i in range(n)][::-1]
    if period == "month":
        start = today.replace(day=1)
        out = []
        y, m = start.year, start.month
        for _ in range(n):
            out.append(date(y, m, 1))
            # go back one month
            m -= 1
            if m == 0:
                m = 12
                y -= 1
        return out[::-1]
    if period == "year":
        start = date(today.year, 1, 1)
        return [date(start.year - (n - 1 - i), 1, 1) for i in range(n)]
    raise ValueError("bad period")

def _label_for_period(period: str, d: date) -> str:
    if period == "week":
        # e.g., 2025-W39 (Mon 2025-09-22)
        iso = d.isocalendar()
        return f"{iso.year}-W{iso.week:02d} ({d.strftime('%Y-%m-%d')})"
    if period == "month":
        return d.strftime("%Y-%m")
    if period == "year":
        return d.strftime("%Y")
    return str(d)

def _aggregate(period: str, since: date):
    qs = Consultation.objects.filter(consultation_date_date_only__gte=since)

    if period == "week":
        trunc = TruncWeek("consultation_date_date_only", output_field=DateField())
    elif period == "month":
        trunc = TruncMonth("consultation_date_date_only", output_field=DateField())
    else:
        trunc = TruncYear("consultation_date_date_only", output_field=DateField())

    agg = (
        qs.annotate(bucket=trunc)
          .values("bucket")
          .annotate(
              total=Count("id"),
              completed=Count("id", filter=Q(status="completed")),
              scheduled=Count("id", filter=Q(status="scheduled")),
              canceled=Count("id", filter=Q(status="canceled")),
              emergencies=Count("id", filter=Q(is_an_emergency=True)),
          )
          .order_by("bucket")
    )
    return list(agg)

def _fill_missing(period: str, raw_rows: list, frame: list[date]):
    # row["bucket"] is already a date; no .date() call
    idx = {row["bucket"]: row for row in raw_rows}
    filled = []
    for d in frame:
        r = idx.get(d)
        if r is None:
            filled.append({
                "bucket": d,
                "total": 0, "completed": 0, "scheduled": 0, "canceled": 0, "emergencies": 0
            })
        else:
            r["bucket"] = d
            filled.append(r)
    return filled

def _csv_response(filename: str, rows: list, period: str):
    import csv
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    w = csv.writer(resp)
    w.writerow(["Period", "Total", "Completed", "Scheduled", "Canceled", "Emergencies"])
    for r in rows:
        w.writerow([
            _label_for_period(period, r["bucket"]),
            r["total"], r["completed"], r["scheduled"], r["canceled"], r["emergencies"]
        ])
    return resp

# --- main view -------------------------------------------------------------

@login_required
def report_center(request):
    """
    Standalone 'Report Center' page with a late-90s minimal look.
    Shows:
      - last 12 weeks
      - last 12 months
      - last 5 years
    Supports CSV export via ?export=csv&period=week|month|year
    """
    today = localdate()

    # configurable, but hard-coded to keep it simple/minimal
    weeks_n = 12
    months_n = 12
    years_n = 5

    week_frame = _daterange_list("week", weeks_n, today)
    month_frame = _daterange_list("month", months_n, today)
    year_frame = _daterange_list("year", years_n, today)

    week_rows = _fill_missing("week", _aggregate("week", since=week_frame[0]), week_frame)
    month_rows = _fill_missing("month", _aggregate("month", since=month_frame[0]), month_frame)
    year_rows = _fill_missing("year", _aggregate("year", since=year_frame[0]), year_frame)

    if request.GET.get("export") == "csv":
        period = request.GET.get("period", "week")
        if period == "month":
            return _csv_response("consultations-monthly.csv", month_rows, "month")
        if period == "year":
            return _csv_response("consultations-yearly.csv", year_rows, "year")
        return _csv_response("consultations-weekly.csv", week_rows, "week")

    ctx = {
    "today": today,
    "weeks": [{"label": _label_for_period("week", r["bucket"]), "bucket": r["bucket"], **r} for r in week_rows],
    "months": [{"label": _label_for_period("month", r["bucket"]), "bucket": r["bucket"], **r} for r in month_rows],
    "years": [{"label": _label_for_period("year", r["bucket"]), "bucket": r["bucket"], **r} for r in year_rows],
    }

    return render(request, "reports/report_center.html", ctx)

# reports/views.py (add below your existing code)

from datetime import date, timedelta, datetime
from django.utils.dateparse import parse_date
from django.db.models import F
from django.shortcuts import render
from django.http import Http404
from django.db.models import DateField
from django.db.models.functions import TruncWeek, TruncMonth, TruncYear

# ensure truncs output dates (keeps .date() bugs away)
def _trunc_for(period):
    if period == "week":
        return TruncWeek("consultation_date_date_only", output_field=DateField())
    if period == "month":
        return TruncMonth("consultation_date_date_only", output_field=DateField())
    if period == "year":
        return TruncYear("consultation_date_date_only", output_field=DateField())
    raise ValueError("bad period")

def _period_end_exclusive(period: str, start: date) -> date:
    if period == "week":
        return start + timedelta(days=7)
    if period == "month":
        # first of next month
        y, m = start.year, start.month
        m += 1
        if m == 13:
            m, y = 1, y + 1
        return date(y, m, 1)
    if period == "year":
        return date(start.year + 1, 1, 1)
    raise ValueError("bad period")

def _all_consults_between(start: date, end_excl: date):
    return (Consultation.objects
            .filter(consultation_date_date_only__gte=start,
                    consultation_date_date_only__lt=end_excl)
            .select_related("pdl_profile",
                            "physician", "physician__username",
                            "location", "reason")
            .order_by("consultation_date_date_only", "consultation_time_block"))

def _row_to_dict(c: Consultation):
    """
    Produce a dict with ALL concrete fields from Consultation,
    rendering FKs as readable strings alongside their IDs.
    """
    data = {}
    for f in Consultation._meta.get_fields():
        if not getattr(f, "concrete", False) or getattr(f, "many_to_many", False) or getattr(f, "one_to_many", False):
            continue
        name = f.name
        val = getattr(c, name, None)

        # pretty-print for FKs
        if f.is_relation and getattr(f, "many_to_one", False):
            data[name] = getattr(val, "pk", None)
            data[name + "__str"] = "" if val is None else str(val)
        else:
            data[name] = val

    # Extras that are handy to read
    data["consultation_time_block_display"] = c.consultation_time_block_display
    data["__str__"] = str(c)
    return data

@login_required
def report_details(request):
    """
    Details page.
    Modes:
      1) ?period=week|month|year&start=YYYY-MM-DD     -> one bucket
      2) ?frame=week|month|year                       -> entire section frame from report_center
    """
    today = localdate()
    title = "Details"

    # Mode 2: whole frame
    frame = request.GET.get("frame")
    if frame in {"week", "month", "year"}:
        # reuse frames from report_center lengths
        weeks_n, months_n, years_n = 12, 12, 5
        if frame == "week":
            starts = _daterange_list("week", weeks_n, today)
            start, end = starts[0], _period_end_exclusive("week", starts[-1])  # end of last bucket + 1 week
        elif frame == "month":
            starts = _daterange_list("month", months_n, today)
            # end of last month bucket
            end = _period_end_exclusive("month", starts[-1])
            start = starts[0]
        else:
            starts = _daterange_list("year", years_n, today)
            end = _period_end_exclusive("year", starts[-1])
            start = starts[0]

        qs = _all_consults_between(start, end)
        rows = [_row_to_dict(c) for c in qs]
        # after: rows = [_row_to_dict(c) for c in qs]
        all_cols = list(rows[0].keys()) if rows else []

        # If a foo__str exists, drop the raw foo (or foo_id) column from display.
        readable = set([c for c in all_cols if c.endswith("__str")])
        drop = set()
        for c in all_cols:
            base = c
            if c.endswith("_id"):
                base = c[:-3]  # strip _id
            if f"{base}__str" in readable:
                drop.add(c)

        columns = [c for c in all_cols if c not in drop]

        # Prefer readable columns (already as you set `columns`)
        # Build a display matrix so the template doesn't need dict indexing
        table_rows = [[row.get(c, "") for c in columns] for row in rows]

        return render(request, "reports/report_center_details.html", {
            "title": title,
            "generated": today,
            "rows": table_rows,   # <— pass matrix instead of dicts
            "columns": columns,
        })


    # Mode 1: single bucket
    period = request.GET.get("period")
    start_str = request.GET.get("start")
    if period not in {"week", "month", "year"} or not start_str:
        raise Http404("Invalid details parameters.")

    start = parse_date(start_str)
    if not start:
        raise Http404("Bad start date.")

    end = _period_end_exclusive(period, start)
    qs = _all_consults_between(start, end)
    rows = [_row_to_dict(c) for c in qs]
    title = f"{period.capitalize()} details for {_label_for_period(period, start)}"

    return render(request, "reports/report_center_details.html", {
        "title": title,
        "generated": today,
        "rows": rows,
        "columns": list(rows[0].keys()) if rows else [],
    })


# ── Health Conditions Report ────────────────────────────────────────────────

@login_required
def health_conditions_report(request):
    today = localdate()

    condition_choices = HealthCondition.CONDITION_CHOICES

    # Count active conditions per type
    counts = (
        HealthCondition.objects
        .filter(is_active=True)
        .values('condition')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    count_map = {row['condition']: row['total'] for row in counts}

    # Build rows with display names
    rows = [
        {
            'code':    code,
            'label':   label,
            'total':   count_map.get(code, 0),
        }
        for code, label in condition_choices
    ]
    rows.sort(key=lambda r: -r['total'])

    # PDLs with multiple conditions
    multi_condition_pdls = (
        HealthCondition.objects
        .filter(is_active=True)
        .values('pdl_profile')
        .annotate(cond_count=Count('condition', distinct=True))
        .filter(cond_count__gte=2)
        .order_by('-cond_count')
    )

    total_pdls_with_conditions = (
        HealthCondition.objects
        .filter(is_active=True)
        .values('pdl_profile')
        .distinct()
        .count()
    )

    # CSV export
    if request.GET.get('export') == 'csv':
        import csv
        resp = HttpResponse(content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = 'attachment; filename="health-conditions-report.csv"'
        w = csv.writer(resp)
        w.writerow(['Condition', 'Active Cases'])
        for r in rows:
            w.writerow([r['label'], r['total']])
        return resp

    return render(request, 'reports/health_conditions_report.html', {
        'rows': rows,
        'today': today,
        'total_pdls_with_conditions': total_pdls_with_conditions,
        'multi_condition_count': multi_condition_pdls.count(),
    })


# ── Fast-Moving Medications Report ─────────────────────────────────────────

@login_required
def fast_moving_medications(request):
    today = localdate()

    top_prescribed = (
        MedicationPrescription.objects
        .values('medication__id', 'medication__name', 'medication__generic_name__name')
        .annotate(
            prescription_count=Count('id'),
            total_dispensed=Sum('quantity_dispensed'),
        )
        .order_by('-prescription_count')[:20]
    )

    # Dispensation rate per medication
    rows = []
    for row in top_prescribed:
        inv = MedicationInventory.objects.filter(medication_id=row['medication__id']).first()
        rows.append({
            'name':               row['medication__name'],
            'generic':            row['medication__generic_name__name'],
            'prescription_count': row['prescription_count'],
            'total_dispensed':    row['total_dispensed'] or 0,
            'current_stock':      inv.quantity if inv else '—',
            'is_low_stock':       inv.is_low_stock if inv else False,
        })

    # CSV export
    if request.GET.get('export') == 'csv':
        import csv
        resp = HttpResponse(content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = 'attachment; filename="fast-moving-medications.csv"'
        w = csv.writer(resp)
        w.writerow(['Medication', 'Generic Name', 'Times Prescribed', 'Total Dispensed', 'Current Stock'])
        for r in rows:
            w.writerow([r['name'], r['generic'], r['prescription_count'], r['total_dispensed'], r['current_stock']])
        return resp

    return render(request, 'reports/fast_moving_medications.html', {
        'rows': rows,
        'today': today,
    })


# ── Inventory Report ────────────────────────────────────────────────────────

@login_required
def inventory_report(request):
    today = localdate()

    inventories = (
        MedicationInventory.objects
        .select_related('medication', 'medication__generic_name')
        .order_by('medication__name')
    )

    low_stock  = [i for i in inventories if i.is_low_stock and not i.is_expired]
    expired    = [i for i in inventories if i.is_expired]
    adequate   = [i for i in inventories if not i.is_low_stock and not i.is_expired]

    # Dispensation totals per medication
    dispensed_map = dict(
        MedicationPrescription.objects
        .values('medication')
        .annotate(total=Sum('quantity_dispensed'))
        .values_list('medication', 'total')
    )

    # CSV export
    if request.GET.get('export') == 'csv':
        import csv
        resp = HttpResponse(content_type='text/csv; charset=utf-8')
        resp['Content-Disposition'] = 'attachment; filename="inventory-report.csv"'
        w = csv.writer(resp)
        w.writerow(['Medication', 'Generic Name', 'Stock Qty', 'Reorder Level', 'Status', 'Expiry Date', 'Location'])
        for inv in inventories:
            status = 'Expired' if inv.is_expired else ('Low Stock' if inv.is_low_stock else 'Adequate')
            w.writerow([
                inv.medication.name,
                inv.medication.generic_name.name,
                inv.quantity,
                inv.reorder_level,
                status,
                inv.expiration_date,
                inv.location,
            ])
        return resp

    return render(request, 'reports/inventory_report.html', {
        'inventories': inventories,
        'low_stock':   low_stock,
        'expired':     expired,
        'adequate':    adequate,
        'dispensed_map': dispensed_map,
        'today':       today,
    })


# ── Health Monitoring Dashboard ─────────────────────────────────────────────

@login_required
def health_monitoring_dashboard(request):
    """
    Comprehensive health monitoring statistics dashboard showing:
    - Total PDLs with illnesses
    - Types of illnesses recorded
    - Most commonly prescribed medicines
    - Total patients per illness
    """
    from django.db.models import Count, Sum, F
    from collections import defaultdict
    import pandas as pd
    from io import BytesIO
    
    today = localdate()
    
    # Total PDLs with health conditions
    total_pdls_with_conditions = (
        HealthCondition.objects
        .filter(is_active=True)
        .values('pdl_profile')
        .distinct()
        .count()
    )
    
    # Total PDLs in the system
    total_pdls = PDLProfile.objects.count()
    
    # Health conditions breakdown (patients per illness type)
    condition_stats = (
        HealthCondition.objects
        .filter(is_active=True)
        .values('condition')
        .annotate(
            patient_count=Count('pdl_profile', distinct=True),
            total_cases=Count('id')
        )
        .order_by('-patient_count')
    )
    
    # Map condition codes to display names
    condition_choices = dict(HealthCondition.CONDITION_CHOICES)
    illness_breakdown = []
    for stat in condition_stats:
        illness_breakdown.append({
            'code': stat['condition'],
            'name': condition_choices.get(stat['condition'], stat['condition']),
            'patient_count': stat['patient_count'],
            'total_cases': stat['total_cases'],
        })
    
    # Most commonly prescribed medications
    top_medications = (
        MedicationPrescription.objects
        .values('medication__id', 'medication__name', 'medication__generic_name__name')
        .annotate(
            prescription_count=Count('id'),
            total_patients=Count('pdl_profile', distinct=True),
            total_dispensed=Sum('quantity_dispensed'),
        )
        .order_by('-prescription_count')[:10]
    )
    
    medications_list = []
    for med in top_medications:
        medications_list.append({
            'name': med['medication__name'],
            'generic_name': med['medication__generic_name__name'] or '',
            'prescription_count': med['prescription_count'],
            'total_patients': med['total_patients'],
            'total_dispensed': med['total_dispensed'] or 0,
        })
    
    # PDLs with multiple conditions
    multi_condition_count = (
        HealthCondition.objects
        .filter(is_active=True)
        .values('pdl_profile')
        .annotate(cond_count=Count('condition', distinct=True))
        .filter(cond_count__gte=2)
        .count()
    )
    
    # Recent health conditions (last 30 days)
    from datetime import timedelta
    thirty_days_ago = today - timedelta(days=30)
    recent_conditions = (
        HealthCondition.objects
        .filter(created_at__date__gte=thirty_days_ago)
        .count()
    )
    
    # Consultation statistics with health-related reasons
    consultation_stats = {
        'total': Consultation.objects.count(),
        'with_conditions': Consultation.objects.filter(
            pdl_profile__health_conditions__is_active=True
        ).distinct().count(),
        'emergency': Consultation.objects.filter(is_an_emergency=True).count(),
    }
    
    # Monthly health condition trends (last 6 months)
    from django.db.models.functions import TruncMonth
    monthly_trends = (
        HealthCondition.objects
        .filter(created_at__date__gte=today - timedelta(days=180))
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    
    trends_data = list(monthly_trends)
    
    # Excel export
    if request.GET.get('export') == 'excel':
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = [{
                'Metric': 'Total PDLs in System',
                'Value': total_pdls,
            }, {
                'Metric': 'PDLs with Health Conditions',
                'Value': total_pdls_with_conditions,
            }, {
                'Metric': 'PDLs with Multiple Conditions',
                'Value': multi_condition_count,
            }, {
                'Metric': 'New Conditions (Last 30 Days)',
                'Value': recent_conditions,
            }, {
                'Metric': 'Total Consultations',
                'Value': consultation_stats['total'],
            }, {
                'Metric': 'Emergency Consultations',
                'Value': consultation_stats['emergency'],
            }]
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # Illness breakdown sheet
            if illness_breakdown:
                illness_data = [{
                    'Condition Code': i['code'],
                    'Condition Name': i['name'],
                    'Number of Patients': i['patient_count'],
                    'Total Cases': i['total_cases'],
                } for i in illness_breakdown]
                pd.DataFrame(illness_data).to_excel(writer, sheet_name='Illnesses by Type', index=False)
            
            # Top medications sheet
            if medications_list:
                med_data = [{
                    'Medication': m['name'],
                    'Generic Name': m['generic_name'],
                    'Times Prescribed': m['prescription_count'],
                    'Patients Treated': m['total_patients'],
                    'Total Dispensed': m['total_dispensed'],
                } for m in medications_list]
                pd.DataFrame(med_data).to_excel(writer, sheet_name='Top Medications', index=False)
            
            # Monthly trends sheet
            if trends_data:
                trend_rows = [{
                    'Month': t['month'].strftime('%Y-%m') if t['month'] else '',
                    'New Conditions': t['count'],
                } for t in trends_data]
                pd.DataFrame(trend_rows).to_excel(writer, sheet_name='Monthly Trends', index=False)
        
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="health_monitoring_statistics.xlsx"'
        return response
    
    return render(request, 'reports/health_monitoring_dashboard.html', {
        'today': today,
        'total_pdls': total_pdls,
        'total_pdls_with_conditions': total_pdls_with_conditions,
        'multi_condition_count': multi_condition_count,
        'recent_conditions': recent_conditions,
        'illness_breakdown': illness_breakdown,
        'medications_list': medications_list,
        'consultation_stats': consultation_stats,
        'trends_data': trends_data,
    })
