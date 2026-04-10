from django import forms
from django.utils import timezone
from datetime import date
from .models import Medication, MedicationInventory, InventoryTransaction, MedicationPrescription

class MedicationForm(forms.ModelForm):
    class Meta:
        model = Medication
        fields = ['name', 'generic_name', 'dosage_form', 'strength', 'route_of_administration', 'manufacturer']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brand Name'}),
            'generic_name': forms.Select(attrs={'class': 'form-select'}),
            'dosage_form': forms.Select(attrs={'class': 'form-select'}),
            'strength': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 500mg'}),
            'route_of_administration': forms.Select(attrs={'class': 'form-select'}),
            'manufacturer': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Manufacturer Name'}),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 2:
                raise forms.ValidationError("Brand name must be at least 2 characters.")
        return name
    
    def clean_strength(self):
        strength = self.cleaned_data.get('strength')
        if strength:
            strength = strength.strip()
        return strength

class MedicationInventoryForm(forms.ModelForm):
    class Meta:
        model = MedicationInventory
        fields = ['quantity', 'reorder_level', 'expiration_date', 'location']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'value': '10'}),
            'expiration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Storage Location'}),
        }
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise forms.ValidationError("Quantity cannot be negative.")
        return quantity
    
    def clean_reorder_level(self):
        reorder_level = self.cleaned_data.get('reorder_level')
        if reorder_level is not None and reorder_level < 0:
            raise forms.ValidationError("Reorder level cannot be negative.")
        return reorder_level
    
    def clean_expiration_date(self):
        expiration_date = self.cleaned_data.get('expiration_date')
        if expiration_date and expiration_date < date.today():
            # Allow setting expired date (for existing inventory tracking)
            pass
        return expiration_date

class InventoryUpdateForm(forms.ModelForm):
    class Meta:
        model = MedicationInventory
        fields = ['quantity', 'reorder_level', 'expiration_date', 'location']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'reorder_level': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'expiration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity < 0:
            raise forms.ValidationError("Quantity cannot be negative.")
        return quantity

class InventoryTransactionForm(forms.ModelForm):
    class Meta:
        model = InventoryTransaction
        fields = ['transaction_type', 'quantity_change', 'notes']
        widgets = {
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity_change': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class MedicationPrescriptionForm(forms.ModelForm):
    class Meta:
        model = MedicationPrescription
        # Inalis ang 'status' dito para maging automatic ang calculation
        fields = [
            'pdl_profile',
            'medication',
            'dosage',
            'frequency',
            'duration',
            'quantity_prescribed',
            'quantity_dispensed',
        ]
        widgets = {
            'pdl_profile': forms.Select(attrs={'class': 'form-select'}),
            'medication': forms.Select(attrs={'class': 'form-select'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 500mg'}),
            'frequency': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 3 times a day'}),
            'duration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 7 days'}),
            'quantity_prescribed': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'quantity_dispensed': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'value': '0'}),
        }
    
    def clean_quantity_prescribed(self):
        quantity = self.cleaned_data.get('quantity_prescribed')
        if quantity is not None and quantity < 1:
            raise forms.ValidationError("Quantity prescribed must be at least 1.")
        return quantity
    
    def clean_quantity_dispensed(self):
        quantity = self.cleaned_data.get('quantity_dispensed')
        if quantity is not None and quantity < 0:
            raise forms.ValidationError("Quantity dispensed cannot be negative.")
        return quantity
    
    def clean(self):
        cleaned_data = super().clean()
        qty_prescribed = cleaned_data.get('quantity_prescribed')
        qty_dispensed = cleaned_data.get('quantity_dispensed')
        
        if qty_prescribed and qty_dispensed:
            if qty_dispensed > qty_prescribed:
                raise forms.ValidationError(
                    "Quantity dispensed cannot exceed quantity prescribed."
                )
        
        return cleaned_data