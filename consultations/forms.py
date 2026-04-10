from django import forms
from .models import Consultation
from pdl.models import PDLProfile
from consultations.models import Physician, ConsultationLocation, ConsultationReason

class ScheduleConsultationForm(forms.ModelForm):
    # Explicitly define ForeignKey fields to ensure dropdown options are populated
    pdl_profile = forms.ModelChoiceField(
        queryset=PDLProfile.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'pdlSelect'}),
        label="PDL Profile",
        required=True
    )
    physician = forms.ModelChoiceField(
        queryset=Physician.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'physicianSelect'}),
        label="Physician",
        required=True
    )
    reason = forms.ModelChoiceField(
        queryset=ConsultationReason.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'reasonSelect'}),
        label="Reason",
        required=True
    )
    
    class Meta:
        model = Consultation
        fields = [
            # Details
            'pdl_profile','physician','reason',
            'consultation_date_date_only','consultation_time_block',
            'is_an_emergency','notes',
            # PMH
            'pmh_pediatric_history','pmh_major_adult_illnesses','pmh_major_surgeries',
            'pmh_serious_injuries','pmh_limitations','pmh_medication_history',
            'pmh_transfusions_reactions','pmh_mental_emotional','pmh_blood_type','pmh_allergies',
            'pmh_family_history','pmh_psychiatric_history','pmh_psychiatric_when',
            'pmh_psychiatric_facility','pmh_arv_treatment','pmh_arv_details',
            'pmh_vaccines','pmh_alcohol_drinker','pmh_smoking','pmh_illicit_drugs','pmh_poly_drug_use',
            # PEA
            'pea_temperature','pea_blood_pressure','pea_heart_rate','pea_rr',
            'pea_height','pea_weight','pea_bmi',
            'pea_general_appearance','pea_head_eyes_ears_nose_throat','pea_neck','pea_chest_lungs',
            'pea_heart','pea_abdomen','pea_genito_urinary','pea_musculoskeletal','pea_extremities',
            'pea_other_findings',
            # TB
            'tb_unexplained_cough','tb_bmi_less_18_5','tb_blood_streaked_sputum',
            'tb_cxr_suggestive','tb_previous_treatment','tb_exposure','tb_remarks',
            # Final Remarks
            'fr_conclusion','fr_other_impressions','fr_recommendation',
        ]
        widgets = {
            'consultation_date_date_only': forms.DateInput(attrs={'class':'form-control','type':'date','id':'consultationDate'}),
            'consultation_time_block': forms.Select(attrs={'class':'form-select','id':'timeSelect'}),
            'is_an_emergency': forms.CheckboxInput(attrs={'class':'form-check-input','id':'isEmergency'}),
            'notes': forms.Textarea(attrs={'class':'form-control','rows':3,'id':'notesField'}),
            # PMH
            'pmh_pediatric_history': forms.Textarea(attrs={'class':'form-control','rows':2}),
            'pmh_major_adult_illnesses': forms.Textarea(attrs={'class':'form-control','rows':2}),
            'pmh_major_surgeries': forms.Textarea(attrs={'class':'form-control','rows':2}),
            'pmh_serious_injuries': forms.Textarea(attrs={'class':'form-control','rows':2}),
            'pmh_limitations': forms.Textarea(attrs={'class':'form-control','rows':2}),
            'pmh_medication_history': forms.Textarea(attrs={'class':'form-control','rows':2}),
            'pmh_transfusions_reactions': forms.Textarea(attrs={'class':'form-control','rows':2}),
            'pmh_mental_emotional': forms.Textarea(attrs={'class':'form-control','rows':2}),
            'pmh_blood_type': forms.Select(attrs={'class':'form-select'}),
            'pmh_allergies': forms.Textarea(attrs={'class':'form-control','rows':2}),
            'pmh_family_history': forms.Select(attrs={'class':'form-select'}),
            'pmh_psychiatric_history': forms.CheckboxInput(attrs={'class':'form-check-input','id':'pmh_psych'}),
            'pmh_psychiatric_when': forms.TextInput(attrs={'class':'form-control','id':'pmh_psychiatric_when'}),
            'pmh_psychiatric_facility': forms.CheckboxInput(attrs={'class':'form-check-input','id':'pmh_psych_fac'}),
            'pmh_arv_treatment': forms.CheckboxInput(attrs={'class':'form-check-input','id':'pmh_arv_treatment'}),
            'pmh_arv_details': forms.Textarea(attrs={'class':'form-control','rows':2}),
            'pmh_vaccines': forms.Textarea(attrs={'class':'form-control','rows':2}),
            'pmh_alcohol_drinker': forms.CheckboxInput(attrs={'class':'form-check-input','id':'pmh_alcohol'}),
            'pmh_smoking': forms.Select(attrs={'class':'form-select','id':'pmh_smoking'}),
            'pmh_illicit_drugs': forms.CheckboxInput(attrs={'class':'form-check-input','id':'pmh_illicit'}),
            'pmh_poly_drug_use': forms.CheckboxInput(attrs={'class':'form-check-input','id':'pmh_poly'}),
            # PEA vitals
            'pea_temperature': forms.NumberInput(attrs={'class':'form-control','step':'0.1'}),
            'pea_blood_pressure': forms.TextInput(attrs={'class':'form-control','placeholder':'e.g., 120/80'}),
            'pea_heart_rate': forms.NumberInput(attrs={'class':'form-control','step':'1','min':'0'}),
            'pea_rr': forms.NumberInput(attrs={'class':'form-control','step':'1','min':'0'}),
            'pea_height': forms.NumberInput(attrs={'class':'form-control','step':'0.1','min':'0'}),
            'pea_weight': forms.NumberInput(attrs={'class':'form-control','step':'0.1','min':'0'}),
            'pea_bmi': forms.NumberInput(attrs={'class':'form-control','step':'0.1','min':'0'}),
            # PEA booleans
            'pea_general_appearance': forms.CheckboxInput(attrs={'class':'form-check-input','id':'pea_ga'}),
            'pea_head_eyes_ears_nose_throat': forms.CheckboxInput(attrs={'class':'form-check-input','id':'pea_heent'}),
            'pea_neck': forms.CheckboxInput(attrs={'class':'form-check-input','id':'pea_neck'}),
            'pea_chest_lungs': forms.CheckboxInput(attrs={'class':'form-check-input','id':'pea_chest'}),
            'pea_heart': forms.CheckboxInput(attrs={'class':'form-check-input','id':'pea_heart'}),
            'pea_abdomen': forms.CheckboxInput(attrs={'class':'form-check-input','id':'pea_abdomen'}),
            'pea_genito_urinary': forms.CheckboxInput(attrs={'class':'form-check-input','id':'pea_gu'}),
            'pea_musculoskeletal': forms.CheckboxInput(attrs={'class':'form-check-input','id':'pea_msk'}),
            'pea_extremities': forms.CheckboxInput(attrs={'class':'form-check-input','id':'pea_ext'}),
            'pea_other_findings': forms.Textarea(attrs={'class':'form-control','rows':2}),
            # TB
            'tb_unexplained_cough': forms.CheckboxInput(attrs={'class':'form-check-input','id':'tb_cough'}),
            'tb_bmi_less_18_5': forms.CheckboxInput(attrs={'class':'form-check-input','id':'tb_bmi'}),
            'tb_blood_streaked_sputum': forms.CheckboxInput(attrs={'class':'form-check-input','id':'tb_sputum'}),
            'tb_cxr_suggestive': forms.CheckboxInput(attrs={'class':'form-check-input','id':'tb_cxr'}),
            'tb_previous_treatment': forms.CheckboxInput(attrs={'class':'form-check-input','id':'tb_prev'}),
            'tb_exposure': forms.CheckboxInput(attrs={'class':'form-check-input','id':'tb_exposure'}),
            'tb_remarks': forms.Select(attrs={'class':'form-select','id':'tb_remarks'}),
            # Final remarks
            'fr_conclusion': forms.Select(attrs={'class':'form-select','id':'fr_conclusion'}),
            'fr_other_impressions': forms.Textarea(attrs={'class':'form-control','rows':2}),
            'fr_recommendation': forms.Select(attrs={'class':'form-select','id':'fr_recommendation'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional: nicer labels / helptexts (keeps template simple)
        self.fields['consultation_date_date_only'].label = "Date"
        self.fields['consultation_time_block'].label = "Time"
        self.fields['is_an_emergency'].label = "Emergency case"
        self.fields['notes'].widget.attrs.update({'placeholder': 'Additional notes...'})

