from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from collections import OrderedDict
import re
from pdl.decorators import role_required

from .models import (
    Medication, MedicationInventory, MedicationPrescription, 
    InventoryTransaction
)
from .forms import (
    MedicationForm, MedicationInventoryForm, InventoryUpdateForm,
    InventoryTransactionForm, MedicationPrescriptionForm
)

@login_required
def medication_list(request):
    """
    Ipinapakita ang prescriptions na naka-group by PDL.
    Tugma ito sa HTML template mo na gumagamit ng 'grouped_by_pdl'.
    Doctors only see their own prescriptions.
    """
    from django.core.paginator import Paginator
    from consultations.models import Physician
    
    q = (request.GET.get("q") or "").strip()

    qs = (
        MedicationPrescription.objects
        .select_related(
            "pdl_profile__username",
            "medication__generic_name",
            "prescribed_by",
        )
        .prefetch_related("medication__medicationinventory_set")
        .order_by(
            "pdl_profile__username__last_name",
            "pdl_profile__username__first_name",
            "medication__name",
        )
    )

    # Filter by logged-in doctor - doctors only see their own prescriptions
    try:
        physician = Physician.objects.get(username=request.user)
        qs = qs.filter(prescribed_by=physician)
    except Physician.DoesNotExist:
        # User is not a physician (admin/pharmacist) - can see all
        pass

    if q:
        qs = qs.filter(
            Q(pdl_profile__username__first_name__icontains=q) |
            Q(pdl_profile__username__last_name__icontains=q) |
            Q(pdl_profile__username__username__icontains=q) |
            Q(medication__name__icontains=q) |
            Q(medication__generic_name__name__icontains=q)
        )

    # Group by PDL
    grouped = OrderedDict()
    for rx in qs:
        key = rx.pdl_profile_id
        if key not in grouped:
            grouped[key] = {
                "pdl": rx.pdl_profile,
                "items": [],
            }
        grouped[key]["items"].append(rx)

    totals = {
        "pdl_count": len(grouped),
        "rx_count": qs.count(),
    }
    
    # Paginate grouped results
    grouped_list = list(grouped.values())
    paginator = Paginator(grouped_list, 10)  # 10 PDLs per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "medications/medication_list.html", {
        "grouped_by_pdl": {i: grp for i, grp in enumerate(page_obj)},
        "page_obj": page_obj,
        "q": q,
        "totals": totals,
    })

@login_required
def medication_inventory_list(request):
    """
    Display all medications with their inventory status.
    """
    from django.core.paginator import Paginator
    
    q = (request.GET.get("q") or "").strip()
    
    medications = (
        Medication.objects
        .select_related('generic_name', 'generic_name__medication_type')
        .prefetch_related('medicationinventory_set')
        .all()
    )
    
    if q:
        medications = medications.filter(
            Q(name__icontains=q) |
            Q(generic_name__name__icontains=q) |
            Q(manufacturer__icontains=q)
        )
    
    # Calculate statistics
    total_meds = medications.count()
    low_stock_count = 0
    expired_count = 0
    in_stock_count = 0
    
    for med in medications:
        inventory = med.medicationinventory_set.first()
        if inventory:
            if inventory.is_expired:
                expired_count += 1
            elif inventory.is_low_stock:
                low_stock_count += 1
            else:
                in_stock_count += 1
    
    # Pagination
    paginator = Paginator(medications, 10)  # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'medications': page_obj,
        'page_obj': page_obj,
        'q': q,
        'stats': {
            'total': total_meds,
            'low_stock': low_stock_count,
            'expired': expired_count,
            'in_stock': in_stock_count,
        }
    }
    
    return render(request, 'medications/inventory_list.html', context)

@role_required('admin', 'pharmacist', 'doctor')
def medication_add(request):
    """
    Add a new medication with initial inventory.
    """
    if request.method == 'POST':
        med_form = MedicationForm(request.POST)
        inv_form = MedicationInventoryForm(request.POST)
        
        if med_form.is_valid() and inv_form.is_valid():
            # Save medication
            medication = med_form.save()
            
            # Save inventory
            inventory = inv_form.save(commit=False)
            inventory.medication = medication
            inventory.save()
            
            # Create initial transaction
            InventoryTransaction.objects.create(
                inventory=inventory,
                transaction_type='addition',
                quantity_change=inventory.quantity,
                performed_by=request.user,
                notes='Initial stock'
            )
            
            messages.success(request, f'Medication "{medication.name}" added successfully!')
            return redirect('medications:inventory_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        med_form = MedicationForm()
        inv_form = MedicationInventoryForm()
    
    return render(request, 'medications/medication_form.html', {
        'med_form': med_form,
        'inv_form': inv_form,
        'title': 'Add New Medication'
    })

@login_required
def medication_detail(request, pk):
    """
    View medication details and inventory information.
    """
    medication = get_object_or_404(
        Medication.objects.select_related('generic_name', 'generic_name__medication_type'),
        pk=pk
    )
    inventory = medication.medicationinventory_set.first()
    transactions = InventoryTransaction.objects.filter(
        inventory=inventory
    ).select_related('performed_by')[:10] if inventory else []
    
    return render(request, 'medications/medication_detail.html', {
        'medication': medication,
        'inventory': inventory,
        'transactions': transactions,
    })

@role_required('admin', 'pharmacist', 'doctor')
def medication_update_inventory(request, pk):
    """
    Update medication inventory.
    """
    medication = get_object_or_404(Medication, pk=pk)
    inventory = medication.medicationinventory_set.first()
    
    if not inventory:
        messages.error(request, 'No inventory record found for this medication.')
        return redirect('medications:inventory_list')
    
    if request.method == 'POST':
        form = InventoryUpdateForm(request.POST, instance=inventory)
        trans_form = InventoryTransactionForm(request.POST)
        
        if form.is_valid() and trans_form.is_valid():
            old_quantity = inventory.quantity
            updated_inventory = form.save()
            
            # Create transaction if quantity changed
            if 'quantity_change' in request.POST and request.POST['quantity_change']:
                transaction = trans_form.save(commit=False)
                transaction.inventory = inventory
                transaction.performed_by = request.user
                transaction.save()
                
                # Update quantity based on transaction
                new_quantity = old_quantity + transaction.quantity_change
                updated_inventory.quantity = new_quantity
                updated_inventory.save()
            
            messages.success(request, 'Inventory updated successfully!')
            return redirect('medications:medication_detail', pk=pk)
    else:
        form = InventoryUpdateForm(instance=inventory)
        trans_form = InventoryTransactionForm()
    
    return render(request, 'medications/inventory_update.html', {
        'medication': medication,
        'inventory': inventory,
        'form': form,
        'trans_form': trans_form,
    })

@login_required
def medication_history(request, pk):
    """
    View medication transaction history.
    """
    medication = get_object_or_404(Medication, pk=pk)
    inventory = medication.medicationinventory_set.first()
    
    if not inventory:
        messages.warning(request, 'No inventory record found for this medication.')
        transactions = []
    else:
        transactions = InventoryTransaction.objects.filter(
            inventory=inventory
        ).select_related('performed_by', 'prescription').order_by('-timestamp')
    
    return render(request, 'medications/medication_history.html', {
        'medication': medication,
        'inventory': inventory,
        'transactions': transactions,
    })

@role_required('admin', 'doctor')
@login_required
def prescription_create(request):
    from consultations.models import Physician
    
    # Get Physician linked to logged-in user
    try:
        physician = Physician.objects.get(username=request.user)
    except Physician.DoesNotExist:
        messages.error(request, "You must be registered as a physician to create prescriptions.")
        return redirect("medications:medication_list")
    
    if request.method == "POST":
        form = MedicationPrescriptionForm(request.POST)
        if form.is_valid():
            presc = form.save(commit=False)
            presc.prescribed_by = physician  # Link prescription to logged-in doctor's Physician profile
            presc.save()
            messages.success(request, "Prescription recorded successfully.")
            return redirect(reverse("medications:prescription_detail", args=[presc.id]))
        messages.error(request, "Please correct the errors below.")
    else:
        form = MedicationPrescriptionForm()
    return render(request, "medications/prescription_form.html", {"form": form})

@login_required
def prescription_detail(request, pk):
    obj = get_object_or_404(MedicationPrescription, pk=pk)
    return render(request, "medications/prescription_detail.html", {"obj": obj})

def _clean(s: str) -> str:
    """Collapse whitespace and strip pipes so the barcode is parse-safe."""
    if s is None:
        return ""
    return re.sub(r"\s+", " ", str(s)).replace("|", "/").strip()

@login_required
def prescription_printable(request, pk: int):
    rx = get_object_or_404(MedicationPrescription.objects.select_related(
        "pdl_profile__username", "medication__generic_name", "prescribed_by"
    ), pk=pk)

    now = timezone.localtime()
    barcode_payload = "|".join([
        f"RX{rx.pk}",
        f"PDL{rx.pdl_profile.pk}",
        f"MED{rx.medication.pk}",
        _clean(rx.medication.name),
        _clean(rx.dosage),
        _clean(rx.frequency),
        _clean(rx.duration),
        f"DR{rx.prescribed_by.pk}",
        now.strftime("%Y%m%d"),
    ])

    return render(request, "medications/prescription_print.html", {
        "rx": rx,
        "now": now,
        "barcode_payload": barcode_payload,
    })


@role_required('admin', 'doctor')
@require_POST
def prescription_delete(request, pk: int):
    rx = get_object_or_404(MedicationPrescription, pk=pk)
    label = f"{rx.pdl_profile} — {rx.medication.name}" if hasattr(rx, "pdl_profile") else str(rx)
    rx.delete()
    messages.success(request, f"Prescription '{label}' was deleted.")
    return redirect("medications:medication_list")

@role_required('admin', 'doctor')
def prescription_update(request, pk):
    prescription = get_object_or_404(MedicationPrescription, pk=pk)
    if request.method == "POST":
        form = MedicationPrescriptionForm(request.POST, instance=prescription)
        if form.is_valid():
            form.save()
            messages.success(request, "Prescription updated successfully.")
            return redirect('medications:medication_list')
    else:
        form = MedicationPrescriptionForm(instance=prescription)
    
    return render(request, "medications/prescription_form.html", {
        "form": form,
        "title": "Edit Prescription"
        
    })


# ─────────────────────────────────────────────────────────────
#  MEDICATION CRUD (for Doctor)
# ─────────────────────────────────────────────────────────────

@role_required('admin', 'pharmacist', 'doctor')
def medication_edit(request, pk):
    """
    Edit an existing medication and its inventory.
    """
    medication = get_object_or_404(Medication, pk=pk)
    inventory = medication.medicationinventory_set.first()
    
    if request.method == 'POST':
        med_form = MedicationForm(request.POST, instance=medication)
        inv_form = MedicationInventoryForm(request.POST, instance=inventory) if inventory else MedicationInventoryForm(request.POST)
        
        if med_form.is_valid() and inv_form.is_valid():
            medication = med_form.save()
            
            if inventory:
                inv_form.save()
            else:
                # Create new inventory if none exists
                inventory = inv_form.save(commit=False)
                inventory.medication = medication
                inventory.save()
            
            messages.success(request, f'Medication "{medication.name}" updated successfully!')
            return redirect('medications:medication_detail', pk=pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        med_form = MedicationForm(instance=medication)
        inv_form = MedicationInventoryForm(instance=inventory) if inventory else MedicationInventoryForm()
    
    return render(request, 'medications/medication_form.html', {
        'med_form': med_form,
        'inv_form': inv_form,
        'title': f'Edit Medication: {medication.name}',
        'medication': medication,
        'is_edit': True
    })


@role_required('admin', 'pharmacist', 'doctor')
@require_POST
def medication_delete(request, pk):
    """
    Delete a medication and its associated inventory.
    """
    medication = get_object_or_404(Medication, pk=pk)
    name = medication.name
    
    try:
        # Check if there are any prescriptions using this medication
        prescription_count = MedicationPrescription.objects.filter(medication=medication).count()
        if prescription_count > 0:
            messages.error(
                request, 
                f'Cannot delete "{name}". It has {prescription_count} associated prescription(s). '
                f'Please delete or reassign the prescriptions first.'
            )
            return redirect('medications:medication_detail', pk=pk)
        
        medication.delete()
        messages.success(request, f'Medication "{name}" has been deleted successfully.')
    except Exception as e:
        messages.error(request, f'Error deleting medication: {str(e)}')
        return redirect('medications:medication_detail', pk=pk)
    
    return redirect('medications:inventory_list')
