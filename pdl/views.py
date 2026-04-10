from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib.auth.models import User

from .models import PDLProfile, DetentionInstance, HealthCondition, UserProfile, UserRole
from medications.models import MedicationPrescription
from consultations.models import Consultation
from .filters import PDLFilter
from .forms import UserForm, PDLProfileForm, DetentionInstanceForm
from .decorators import role_required


# ─────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────

# Statuses excluded from active counts and profile views
_INACTIVE_STATUSES = Q(status__iexact='Canceled') | Q(status__iexact='Completed')


# ─────────────────────────────────────────────────────────────
#  PDL LIST
# ─────────────────────────────────────────────────────────────

@login_required
def pdl_list(request):
    """
    Lists all PDL detention instances with active consultation counts.
    Excludes 'Canceled' and 'Completed' consultations from the count.
    Supports filtering via PDLFilter and paginates at 10 rows per page.
    """
    detention_instances = (
        DetentionInstance.objects
        .select_related('pdl_profile', 'detention_status', 'detention_reason')
        .annotate(
            consult_count=Count(
                'pdl_profile__consultation',
                filter=(
                    ~Q(pdl_profile__consultation__status__iexact='Canceled') &
                    ~Q(pdl_profile__consultation__status__iexact='Completed')
                ),
                distinct=True,
            )
        )
        .order_by('-created_at')
    )

    pdl_filter = PDLFilter(request.GET, queryset=detention_instances)
    qs = pdl_filter.qs

    summary = {
        'total_pdl_rows':   qs.count(),
        'total_consults':   qs.filter(consult_count__gt=0).count(),
        'male_consulted':   qs.filter(pdl_profile__sex='M', consult_count__gt=0).count(),
        'female_consulted': qs.filter(pdl_profile__sex='F', consult_count__gt=0).count(),
    }

    page_obj = Paginator(qs, 10).get_page(request.GET.get('page'))

    return render(request, 'pdl/pdl_list.html', {
        'filter':   pdl_filter,
        'page_obj': page_obj,
        'summary':  summary,
    })


# ─────────────────────────────────────────────────────────────
#  PDL PROFILE
# ─────────────────────────────────────────────────────────────

@login_required
def pdl_profile(request, username):
    user = get_object_or_404(User, username=username)

    pdl = get_object_or_404(
        PDLProfile.objects.prefetch_related('health_conditions'),
        username=user
    )

    consultations = (
        Consultation.objects
        .filter(pdl_profile=pdl)
        .exclude(_INACTIVE_STATUSES)
        .order_by('-consultation_date_date_only')
    )

    prescriptions = (
        MedicationPrescription.objects
        .filter(pdl_profile=pdl)
        .exclude(_INACTIVE_STATUSES)
        .order_by('-created_at')
    )

    detention_instance = (
        DetentionInstance.objects
        .filter(pdl_profile=pdl)
        .order_by('-detention_start_date')
        .first()
    )

    return render(request, 'pdl/pdl_profile.html', {
        'pdl': pdl,
        'detention_instance': detention_instance,
        'consultations': consultations,
        'prescriptions': prescriptions,
        'condition_choices': HealthCondition.CONDITION_CHOICES,
        'health_conditions': pdl.health_conditions.all(),
    })


# ─────────────────────────────────────────────────────────────
#  ADD PDL
# ─────────────────────────────────────────────────────────────

@role_required('doctor')
@transaction.atomic
def add_pdl(request):
    """
    Creates a new PDL by saving a User, PDLProfile, and DetentionInstance
    atomically. Rolls back all three if any form is invalid.
    """
    if request.method == 'POST':
        user_form      = UserForm(request.POST)
        profile_form   = PDLProfileForm(request.POST)
        detention_form = DetentionInstanceForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid() and detention_form.is_valid():
            user              = user_form.save()
            profile           = profile_form.save(commit=False)
            profile.username  = user
            profile.save()

            detention             = detention_form.save(commit=False)
            detention.pdl_profile = profile
            detention.save()

            messages.success(request, "PDL added successfully.")
            return redirect('pdl:pdl_list')
    else:
        user_form      = UserForm()
        profile_form   = PDLProfileForm()
        detention_form = DetentionInstanceForm()

    return render(request, 'pdl/add_pdl.html', {
        'user_form':            user_form,
        'pdl_profile_form':     profile_form,
        'detention_instance_form': detention_form,
    })


# ─────────────────────────────────────────────────────────────
#  EDIT PDL
# ─────────────────────────────────────────────────────────────

@role_required('admin', 'doctor')
@transaction.atomic
def edit_pdl(request, pdl_id):
    """
    Edits an existing PDL's User, PDLProfile, and most recent DetentionInstance
    atomically. Rolls back all three if any form is invalid.
    """
    profile    = get_object_or_404(PDLProfile, pk=pdl_id)
    user       = profile.username
    detention  = profile.detention_instances.order_by('-created_at').first()

    if request.method == 'POST':
        user_form      = UserForm(request.POST, instance=user)
        profile_form   = PDLProfileForm(request.POST, instance=profile)
        detention_form = DetentionInstanceForm(request.POST, instance=detention)

        if user_form.is_valid() and profile_form.is_valid() and detention_form.is_valid():
            user_form.save()
            profile_form.save()
            detention_form.save()
            messages.success(request, "PDL updated successfully.")
            return redirect('pdl:pdl_list')
    else:
        user_form      = UserForm(instance=user)
        profile_form   = PDLProfileForm(instance=profile)
        detention_form = DetentionInstanceForm(instance=detention)

    return render(request, 'pdl/edit_pdl.html', {
        'user_form':               user_form,
        'pdl_profile_form':        profile_form,
        'detention_instance_form': detention_form,
        'pdl_profile':             profile,
    })


# ─────────────────────────────────────────────────────────────
#  DELETE PDL
# ─────────────────────────────────────────────────────────────

@role_required('admin', 'doctor')
@require_POST
def delete_pdl(request, pk):
    """
    Deletes a PDL and their associated User account.
    Cascades to related consultations, prescriptions, health conditions, etc.
    Restricted to POST requests only.
    """
    profile = get_object_or_404(PDLProfile, pk=pk)
    pdl_name = str(profile)
    user = profile.username
    
    try:
        with transaction.atomic():
            # Get counts of related records for informational message
            consultation_count = Consultation.objects.filter(pdl_profile=profile).count()
            prescription_count = MedicationPrescription.objects.filter(pdl_profile=profile).count()
            health_condition_count = HealthCondition.objects.filter(pdl_profile=profile).count()
            
            # Delete the profile (cascades to related records)
            profile.delete()
            # Delete the associated user account
            user.delete()
            
            # Build success message with details
            deleted_items = []
            if consultation_count > 0:
                deleted_items.append(f"{consultation_count} consultation(s)")
            if prescription_count > 0:
                deleted_items.append(f"{prescription_count} prescription(s)")
            if health_condition_count > 0:
                deleted_items.append(f"{health_condition_count} health condition(s)")
            
            if deleted_items:
                messages.success(request, f"PDL '{pdl_name}' and related records ({', '.join(deleted_items)}) deleted successfully.")
            else:
                messages.success(request, f"PDL '{pdl_name}' deleted successfully.")
                
    except Exception as e:
        messages.error(request, f"Error deleting PDL '{pdl_name}': {str(e)}. Please contact system administrator.")
        return redirect('pdl:pdl_list')
    
    return redirect('pdl:pdl_list')


# ─────────────────────────────────────────────────────────────
#  HEALTH CONDITIONS
# ─────────────────────────────────────────────────────────────

@role_required('admin', 'doctor')
def health_condition_add(request, pdl_id):
    pdl = get_object_or_404(PDLProfile, pk=pdl_id)
    if request.method == 'POST':
        condition    = request.POST.get('condition')
        date_diag    = request.POST.get('date_diagnosed') or None
        notes        = request.POST.get('notes', '')
        is_active    = request.POST.get('is_active') == 'on'
        if not condition:
            messages.error(request, "Condition is required.")
            return redirect('pdl:pdl_profile', username=pdl.username.username)

        if not date_diag:
            messages.warning(request, "Date diagnosed is recommended but not required.")

        HealthCondition.objects.create(
            pdl_profile=pdl,
            condition=condition,
            date_diagnosed=date_diag,
            notes=notes,
            is_active=is_active,
            recorded_by=request.user,
        )
        messages.success(request, "Health condition recorded.")
    return redirect('pdl:pdl_profile', username=pdl.username.username)


@role_required('admin', 'doctor')
def health_condition_edit(request, pk):
    hc  = get_object_or_404(HealthCondition, pk=pk)
    pdl = hc.pdl_profile
    if request.method == 'POST':
        hc.condition      = request.POST.get('condition', hc.condition)
        hc.date_diagnosed = request.POST.get('date_diagnosed') or None
        hc.notes          = request.POST.get('notes', '')
        hc.is_active      = request.POST.get('is_active') == 'on'
        hc.save()
        messages.success(request, "Health condition updated.")
    return redirect('pdl:pdl_profile', username=pdl.username.username)


@role_required('admin', 'doctor')
@require_POST
def health_condition_delete(request, pk):
    hc  = get_object_or_404(HealthCondition, pk=pk)
    username = hc.pdl_profile.username.username
    hc.delete()
    messages.success(request, "Health condition removed.")
    return redirect('pdl:pdl_profile', username=username)


# ─────────────────────────────────────────────────────────────
#  JSON API
# ─────────────────────────────────────────────────────────────

@login_required
def pdl_detention_room_api(request, pk):
    """
    Returns the most recent non-empty detention room number for a PDL.
    Used by the consultation quick-add form.
    """
    pdl    = get_object_or_404(PDLProfile, pk=pk)
    latest = (
        DetentionInstance.objects
        .filter(pdl_profile=pdl)
        .exclude(detention_room_number='')
        .order_by('-created_at')
        .first()
    )
    return JsonResponse({'room_number': latest.detention_room_number if latest else None})


# ─────────────────────────────────────────────────────────────
#  IT ADMIN DASHBOARD
# ─────────────────────────────────────────────────────────────

@role_required('admin')
def admin_dashboard(request):
    """Ensure only Admin users can access the Administrator dashboard."""
    from consultations.models import MedicalSpecialty
    from django.core.paginator import Paginator
    from django.db.models import Q
    
    pdl_user_ids = PDLProfile.objects.values_list('username_id', flat=True)
    system_users = (
        User.objects
        .exclude(id__in=pdl_user_ids)
        .select_related('userprofile')
        .order_by('last_name', 'first_name', 'username')
    )
    
    # Search functionality
    search_query = request.GET.get('search', '').strip()
    if search_query:
        system_users = system_users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    stats = {
        'total':      system_users.count(),
        'admin':      system_users.filter(userprofile__role='admin').count(),
        'doctor':     system_users.filter(userprofile__role='doctor').count(),
        'pharmacist': system_users.filter(userprofile__role='pharmacist').count(),
    }
    
    # Pagination
    paginator = Paginator(system_users, 10)  # 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'pdl/admin_dashboard.html', {
        'system_users': page_obj,
        'page_obj':     page_obj,
        'stats':        stats,
        'role_choices': UserRole.choices,
        'specialties':  MedicalSpecialty.objects.order_by('name'),
        'search_query': search_query,
    })


@role_required('admin')
def admin_create_user(request):
    from consultations.models import Physician, MedicalSpecialty
    if request.method == 'POST':
        username   = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        email      = request.POST.get('email', '').strip()
        password   = request.POST.get('password', '').strip()
        role       = request.POST.get('role', 'doctor')

        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return redirect('pdl:admin_dashboard')

        if User.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" is already taken.')
            return redirect('pdl:admin_dashboard')

        user = User.objects.create_user(
            username=username, first_name=first_name,
            last_name=last_name, email=email, password=password,
        )
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = role
        profile.save()

        # For doctors, always create a Physician record
        if role == 'doctor':
            specialty_id   = request.POST.get('specialty_id')
            phone_number   = request.POST.get('phone_number', '').strip()
            address        = request.POST.get('address', '').strip()
            employee_type  = request.POST.get('employee_type', 'full_time')
            specialty = MedicalSpecialty.objects.filter(pk=specialty_id).first() if specialty_id else None
            Physician.objects.create(
                username=user,
                specialty=specialty,
                phone_number=phone_number,
                address=address,
                employee_type=employee_type,
            )

        messages.success(request, f'User "{username}" created with role "{role}".')
    return redirect('pdl:admin_dashboard')


@role_required('admin')
@require_POST
def admin_edit_role(request, pk):
    from consultations.models import Physician
    user = get_object_or_404(User, pk=pk)
    role = request.POST.get('role', 'doctor')
    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.role = role
    profile.save()
    
    # If changing to doctor role, ensure Physician record exists
    if role == 'doctor' and not Physician.objects.filter(username=user).exists():
        Physician.objects.create(username=user)
    
    messages.success(request, f'Role updated for "{user.get_full_name() or user.username}".')
    return redirect('pdl:admin_dashboard')


@role_required('admin')
@require_POST
def admin_delete_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('pdl:admin_dashboard')
    name = user.get_full_name() or user.username
    user.delete()
    messages.success(request, f'User "{name}" has been deleted.')
    return redirect('pdl:admin_dashboard')


@role_required('admin')
@require_POST
def admin_reset_password(request, pk):
    """Reset a user's password (IT Admin action)."""
    user = get_object_or_404(User, pk=pk)
    new_password = request.POST.get('new_password', '').strip()
    confirm_password = request.POST.get('confirm_password', '').strip()
    
    if not new_password:
        messages.error(request, 'Password cannot be empty.')
        return redirect('pdl:admin_dashboard')
    
    if new_password != confirm_password:
        messages.error(request, 'Passwords do not match.')
        return redirect('pdl:admin_dashboard')
    
    if len(new_password) < 8:
        messages.error(request, 'Password must be at least 8 characters.')
        return redirect('pdl:admin_dashboard')
    
    user.set_password(new_password)
    user.save()
    messages.success(request, f'Password reset successfully for "{user.get_full_name() or user.username}".')
    return redirect('pdl:admin_dashboard')


@role_required('admin')
def admin_user_history(request, pk):
    """Show full activity history for a system user."""
    from consultations.models import Physician, Consultation
    from medications.models import MedicationPrescription, InventoryTransaction, Pharmacist
    from django.http import HttpResponse
    import pandas as pd
    from io import BytesIO

    target_user = get_object_or_404(User, pk=pk)

    # Physician profile (doctor role)
    try:
        physician = Physician.objects.get(username=target_user)
    except Physician.DoesNotExist:
        physician = None

    # Pharmacist profile
    try:
        pharmacist = Pharmacist.objects.get(username=target_user)
    except (Pharmacist.DoesNotExist, Exception):
        pharmacist = None

    # Consultations conducted (if doctor)
    consultations = []
    if physician:
        consultations = list(
            Consultation.objects
            .filter(physician=physician)
            .select_related('pdl_profile__username', 'reason', 'location')
            .order_by('-consultation_date_date_only')[:50]
        )

    # Prescriptions written (if doctor)
    prescriptions_written = []
    if physician:
        prescriptions_written = list(
            MedicationPrescription.objects
            .filter(prescribed_by=physician)
            .select_related('pdl_profile__username', 'medication')
            .order_by('-created_at')[:50]
        )

    # Prescriptions dispensed (if pharmacist)
    prescriptions_dispensed = []
    if pharmacist:
        prescriptions_dispensed = list(
            MedicationPrescription.objects
            .filter(dispensed_by=pharmacist)
            .select_related('pdl_profile__username', 'medication')
            .order_by('-dispensed_at')[:50]
        )

    # Inventory transactions
    inventory_transactions = list(
        InventoryTransaction.objects
        .filter(performed_by=target_user)
        .select_related('inventory__medication')
        .order_by('-timestamp')[:50]
    )

    # Health conditions recorded
    health_conditions_recorded = list(
        HealthCondition.objects
        .filter(recorded_by=target_user)
        .select_related('pdl_profile__username')
        .order_by('-created_at')[:50]
    )

    # Summary counts
    summary = {
        'consultations':            len(consultations),
        'prescriptions_written':    len(prescriptions_written),
        'prescriptions_dispensed':  len(prescriptions_dispensed),
        'inventory_transactions':   len(inventory_transactions),
        'health_conditions':        len(health_conditions_recorded),
    }

    # Excel export
    if request.GET.get('export') == 'excel':
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Summary sheet (always first)
            summary_data = [{
                'Category': 'Consultations Conducted',
                'Count': summary['consultations'],
            }, {
                'Category': 'Prescriptions Written',
                'Count': summary['prescriptions_written'],
            }, {
                'Category': 'Prescriptions Dispensed',
                'Count': summary['prescriptions_dispensed'],
            }, {
                'Category': 'Inventory Transactions',
                'Count': summary['inventory_transactions'],
            }, {
                'Category': 'Health Conditions Recorded',
                'Count': summary['health_conditions'],
            }]
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # Consultations sheet
            if consultations:
                consult_data = [{
                    'Date': c.consultation_date_date_only,
                    'PDL': str(c.pdl_profile),
                    'Reason': str(c.reason) if c.reason else '',
                    'Location': str(c.location) if c.location else '',
                    'Status': c.get_status_display(),
                } for c in consultations]
            else:
                consult_data = [{'Date': '', 'PDL': '', 'Reason': '', 'Location': '', 'Status': 'No data'}]
            pd.DataFrame(consult_data).to_excel(writer, sheet_name='Consultations', index=False)
            
            # Prescriptions Written sheet
            if prescriptions_written:
                rx_written_data = [{
                    'Date': rx.created_at.date() if rx.created_at else '',
                    'PDL': str(rx.pdl_profile),
                    'Medication': rx.medication.name if rx.medication else '',
                    'Dosage': rx.dosage,
                    'Frequency': rx.frequency,
                    'Quantity': rx.quantity_prescribed,
                    'Status': rx.get_status_display(),
                } for rx in prescriptions_written]
            else:
                rx_written_data = [{'Date': '', 'PDL': '', 'Medication': '', 'Dosage': '', 'Frequency': '', 'Quantity': '', 'Status': 'No data'}]
            pd.DataFrame(rx_written_data).to_excel(writer, sheet_name='Prescriptions Written', index=False)
            
            # Prescriptions Dispensed sheet
            if prescriptions_dispensed:
                rx_disp_data = [{
                    'Dispensed At': rx.dispensed_at if rx.dispensed_at else '',
                    'PDL': str(rx.pdl_profile),
                    'Medication': rx.medication.name if rx.medication else '',
                    'Quantity Dispensed': rx.quantity_dispensed,
                    'Status': rx.get_status_display(),
                } for rx in prescriptions_dispensed]
            else:
                rx_disp_data = [{'Dispensed At': '', 'PDL': '', 'Medication': '', 'Quantity Dispensed': '', 'Status': 'No data'}]
            pd.DataFrame(rx_disp_data).to_excel(writer, sheet_name='Prescriptions Dispensed', index=False)
            
            # Inventory Transactions sheet
            if inventory_transactions:
                inv_data = [{
                    'Timestamp': txn.timestamp,
                    'Medication': txn.inventory.medication.name if txn.inventory and txn.inventory.medication else '',
                    'Type': txn.get_transaction_type_display(),
                    'Quantity Change': txn.quantity_change,
                    'Notes': txn.notes or '',
                } for txn in inventory_transactions]
            else:
                inv_data = [{'Timestamp': '', 'Medication': '', 'Type': '', 'Quantity Change': '', 'Notes': 'No data'}]
            pd.DataFrame(inv_data).to_excel(writer, sheet_name='Inventory Transactions', index=False)
            
            # Health Conditions sheet
            if health_conditions_recorded:
                hc_data = [{
                    'Date Recorded': hc.created_at.date() if hc.created_at else '',
                    'PDL': str(hc.pdl_profile),
                    'Condition': hc.get_condition_display(),
                    'Date Diagnosed': hc.date_diagnosed or '',
                    'Active': 'Yes' if hc.is_active else 'No',
                } for hc in health_conditions_recorded]
            else:
                hc_data = [{'Date Recorded': '', 'PDL': '', 'Condition': '', 'Date Diagnosed': '', 'Active': 'No data'}]
            pd.DataFrame(hc_data).to_excel(writer, sheet_name='Health Conditions', index=False)
        
        output.seek(0)
        filename = f"user_history_{target_user.username}.xlsx"
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    return render(request, 'pdl/admin_user_history.html', {
        'target_user':               target_user,
        'physician':                 physician,
        'pharmacist':                pharmacist,
        'consultations':             consultations,
        'prescriptions_written':     prescriptions_written,
        'prescriptions_dispensed':   prescriptions_dispensed,
        'inventory_transactions':    inventory_transactions,
        'health_conditions_recorded': health_conditions_recorded,
        'summary':                   summary,
    })