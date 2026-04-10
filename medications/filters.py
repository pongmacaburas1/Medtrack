import django_filters
from .models import Medication

class MedicationFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains', label="Medication Name")
    generic_name = django_filters.CharFilter(field_name='generic_name__name', lookup_expr='icontains', label="Generic Name")
    dosage_form = django_filters.ChoiceFilter(choices=Medication.DOSAGE_FORM_CHOICES, label="Dosage Form")
    route_of_administration = django_filters.ChoiceFilter(choices=Medication.ROUTE_OF_ADMINISTRATION_CHOICES, label="Route of Administration")

    class Meta:
        model = Medication
        fields = ['name', 'generic_name', 'dosage_form', 'route_of_administration']