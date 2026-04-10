from django import forms
from .models import PDLProfile, DetentionInstance, DetentionStatus, DetentionReason
from django.contrib.auth.models import User

# app/forms.py
from django import forms
from django.contrib.auth.models import User

class UserForm(forms.ModelForm):
    """
    Form for creating a new User.
    """
    class Meta:
        model = User
        # Reorder: First/Last Name first, then username/email
        fields = ['first_name', 'last_name', 'username', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),

            # Greyed out + read-only
            'username': forms.TextInput(attrs={
                'class': 'form-control bg-light text-muted',
                'readonly': 'readonly',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control bg-light text-muted',
                'readonly': 'readonly',
            }),
        }
        help_texts = {
            'username': 'Auto-generated for internal use only.',
            'email': 'Auto-generated for internal use only.',
        }


# app/forms.py
from django import forms
from .models import PDLProfile


class PDLProfileForm(forms.ModelForm):
    """
    Form for creating or editing a PDLProfile.
    """
    class Meta:
        model = PDLProfile
        fields = [
            'middle_name',
            'name_suffix',
            'profile_picture_url',
            'sex',
            'age',
            'civil_status',
            'educational_attainment',
            'date_of_birth',
            'place_of_birth_municipality',
            'place_of_birth_province',
            'place_of_birth_region',
            'place_of_birth_country',
            'date_of_commitment',
            'name_of_jail',
            'case',
            'case_number',
            'origin_lockup',
            'contact_person_name',
            'contact_person_address',
            'contact_person_phone',
            'contact_person_email',
            'contact_person_relationship',
        ]
        widgets = {
            'middle_name': forms.TextInput(attrs={'class': 'form-control'}),
            'name_suffix': forms.Select(attrs={'class': 'form-select'}),
            'sex': forms.Select(attrs={'class': 'form-select'}),
            'profile_picture_url': forms.URLInput(attrs={
                'class':'form-control',
                'placeholder':'https://…/photo.jpg',
                'inputmode':'url',
                'autocomplete':'off',
                'data-preview-target':'profilePhotoPreview',
                'pattern': r'^https?://.+',
            }),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'civil_status': forms.Select(attrs={'class': 'form-select'}),
            'educational_attainment': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'place_of_birth_municipality': forms.TextInput(attrs={'class': 'form-control'}),
            'place_of_birth_province': forms.TextInput(attrs={'class': 'form-control'}),
            'place_of_birth_region': forms.TextInput(attrs={'class': 'form-control'}),
            'place_of_birth_country': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_commitment': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'name_of_jail': forms.TextInput(attrs={'class': 'form-control'}),
            'case': forms.TextInput(attrs={'class': 'form-control'}),
            'case_number': forms.TextInput(attrs={'class': 'form-control'}),
            'origin_lockup': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'contact_person_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_person_relationship': forms.TextInput(attrs={'class': 'form-control'}),
        }


class DetentionInstanceForm(forms.ModelForm):
    """
    Form for creating a new DetentionInstance.
    """
    class Meta:
        model = DetentionInstance
        fields = ['detention_status', 'detention_reason', 'detention_term_length', 'detention_start_date', 'detention_end_date', 'detention_room_number','notes']
        widgets = {
            'detention_status': forms.Select(attrs={'class': 'form-select'}),
            'detention_reason': forms.Select(attrs={'class': 'form-select'}),
            'detention_term_length': forms.NumberInput(attrs={'class': 'form-control'}),
            'detention_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'detention_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'detention_room_number': forms.TextInput(attrs={'class': 'form-control'}),

            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }