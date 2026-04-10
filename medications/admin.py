from django.contrib import admin

from .models import (
    Pharmacist,
    MedicationType,
    MedicationGenericName,
    Medication,
    MedicationInventory,
    MedicationPrescription,
    InventoryTransaction
)

# Registering all models in the admin site
@admin.register(Pharmacist)
class PharmacistAdmin(admin.ModelAdmin):
    list_display = ('username', 'employee_type', 'phone_number', 'address')
    search_fields = ('username__username', 'username__first_name', 'username__last_name', 'phone_number')

@admin.register(MedicationType)
class MedicationTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(MedicationGenericName)
class MedicationGenericNameAdmin(admin.ModelAdmin):
    list_display = ('name', 'medication_type')
    search_fields = ('name', 'medication_type__name')

@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'generic_name', 'dosage_form', 'strength', 'route_of_administration', 'manufacturer')
    search_fields = ('name', 'generic_name__name', 'manufacturer')
    list_filter = ('dosage_form', 'route_of_administration')

@admin.register(MedicationInventory)
class MedicationInventoryAdmin(admin.ModelAdmin):
    list_display = ['medication', 'quantity', 'reorder_level', 'is_low_stock', 'expiration_date', 'location', 'last_updated']
    list_filter = ['location', 'expiration_date']
    search_fields = ['medication__name', 'medication__generic_name__name']
    readonly_fields = ['last_updated']
    
    def is_low_stock(self, obj):
        return obj.is_low_stock
    is_low_stock.boolean = True
    is_low_stock.short_description = 'Low Stock'

@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ['inventory', 'transaction_type', 'quantity_change', 'performed_by', 'timestamp']
    list_filter = ['transaction_type', 'timestamp']
    search_fields = ['inventory__medication__name']
    readonly_fields = ['timestamp']

@admin.register(MedicationPrescription)
class MedicationPrescriptionAdmin(admin.ModelAdmin):
    list_display = ['pdl_profile', 'medication', 'quantity_prescribed', 'quantity_dispensed', 'status', 'prescribed_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['pdl_profile__username__last_name', 'medication__name']
    readonly_fields = ['created_at']
