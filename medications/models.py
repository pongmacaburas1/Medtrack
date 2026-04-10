from django.db import models
from django.contrib.auth.models import User
from pdl.models import PDLProfile
from consultations.models import Physician

# --- Basic Models ---

class Pharmacist(models.Model):
    EMPLOYEE_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
    ]
    username = models.ForeignKey(User, on_delete=models.CASCADE)
    employee_type = models.CharField(max_length=20, choices=EMPLOYEE_TYPE_CHOICES, default='full_time')
    phone_number = models.CharField(max_length=15)
    address = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.username.first_name} {self.username.last_name}"

class MedicationType(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Medication Type"
        verbose_name_plural = "Medication Types"
        ordering = ['name']

class MedicationGenericName(models.Model):
    name = models.CharField(max_length=100)
    medication_type = models.ForeignKey(MedicationType, on_delete=models.CASCADE)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name = "Medication Generic Name"
        verbose_name_plural = "Medication Generic Names"
        ordering = ['name']

class Medication(models.Model):
    DOSAGE_FORM_CHOICES = [
        ('tablet', 'Tablet'), ('capsule', 'Capsule'), ('syrup', 'Syrup'),
        ('injection', 'Injection'), ('cream', 'Cream'), ('ointment', 'Ointment'),
    ]
    ROUTE_OF_ADMINISTRATION_CHOICES = [
        ('oral', 'Oral'), ('intravenous', 'Intravenous'), ('intramuscular', 'Intramuscular'),
        ('subcutaneous', 'Subcutaneous'), ('topical', 'Topical'),
    ]
    name = models.CharField(max_length=100)
    generic_name = models.ForeignKey(MedicationGenericName, on_delete=models.CASCADE)
    dosage_form = models.CharField(max_length=20, choices=DOSAGE_FORM_CHOICES)
    strength = models.CharField(max_length=50)
    route_of_administration = models.CharField(max_length=20, choices=ROUTE_OF_ADMINISTRATION_CHOICES)
    manufacturer = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.generic_name})"
    class Meta:
        verbose_name = "Medication"
        verbose_name_plural = "Medications"
        ordering = ['name']

# --- Inventory & Prescription Logic ---

class MedicationInventory(models.Model):
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0, help_text="Current quantity in stock")
    reorder_level = models.IntegerField(default=10, help_text="Minimum quantity before reorder")
    expiration_date = models.DateField()
    location = models.CharField(max_length=100)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.medication} - {self.quantity} units"
    
    @property
    def is_low_stock(self):
        return self.quantity <= self.reorder_level
    
    @property
    def is_expired(self):
        from django.utils import timezone
        return self.expiration_date < timezone.now().date()
    
    class Meta:
        verbose_name = "Medication Inventory"
        verbose_name_plural = "Medication Inventories"
        ordering = ['medication__name']

class MedicationPrescription(models.Model):
    STATUS_CHOICES = [
        ('ongoing', 'Ongoing'),
        ('dispensed', 'Dispensed'),
    ]
    pdl_profile = models.ForeignKey(PDLProfile, on_delete=models.CASCADE)
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    prescribed_by = models.ForeignKey(Physician, on_delete=models.CASCADE)
    quantity_prescribed = models.IntegerField(default=0)
    quantity_dispensed = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ongoing')
    created_at = models.DateTimeField(auto_now_add=True)
    dispensed_by = models.ForeignKey(Pharmacist, on_delete=models.SET_NULL, null=True, blank=True)
    dispensed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # 1. Alamin ang dami ng dating naibigay na gamot (old quantity_dispensed)
        old_dispensed = 0
        if self.pk:
            try:
                # Ginagamit ang self.__class__ para maiwasan ang circular import error sa terminal
                old_instance = self.__class__.objects.get(pk=self.pk)
                old_dispensed = old_instance.quantity_dispensed
            except self.__class__.DoesNotExist:
                old_dispensed = 0

        # 2. I-update ang Status base sa QTY (P/D)
        if self.quantity_dispensed >= self.quantity_prescribed and self.quantity_prescribed > 0:
            self.status = 'dispensed'
        else:
            self.status = 'ongoing'
        
        # Save ang prescription muna
        super().save(*args, **kwargs)

        # 3. AUTOMATIC DEDUCTION (Dito nababawasan ang Inventory)
        # diff = (Bagong nilagay na Dispensed) - (Dating naibigay na)
        diff = self.quantity_dispensed - old_dispensed
        if diff != 0:
            # Hanapin ang inventory ng gamot na ito
            inv = MedicationInventory.objects.filter(medication=self.medication).first()
            if inv:
                # Ibabawas ang difference sa Stock Qty
                inv.quantity -= diff 
                inv.save()

    def __str__(self):
        return f"{self.medication} prescribed to {self.pdl_profile}"
    
    @property
    def remaining_quantity(self):
        return self.quantity_prescribed - self.quantity_dispensed
    
    class Meta:
        verbose_name = "Medication Prescription"
        verbose_name_plural = "Medication Prescriptions"
        ordering = ['-created_at']

class InventoryTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('addition', 'Stock Addition'),
        ('dispensation', 'Dispensation'),
        ('adjustment', 'Adjustment'),
        ('return', 'Return'),
        ('expired', 'Expired/Disposed'),
    ]
    inventory = models.ForeignKey(MedicationInventory, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    quantity_change = models.IntegerField()
    prescription = models.ForeignKey(MedicationPrescription, on_delete=models.SET_NULL, null=True, blank=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.inventory.medication} ({self.quantity_change})"
    
    class Meta:
        verbose_name = "Inventory Transaction"
        verbose_name_plural = "Inventory Transactions"
        ordering = ['-timestamp']