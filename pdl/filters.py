import django_filters
from .models import DetentionInstance, DetentionStatus, DetentionReason, HealthCondition


class PDLFilter(django_filters.FilterSet):

    pdl_profile = django_filters.CharFilter(
        field_name='pdl_profile__username__username',
        lookup_expr='icontains',
        label="Name"
    )

    detention_status = django_filters.ModelChoiceFilter(
        queryset=DetentionStatus.objects.all(),
        label="Status"
    )

    detention_reason = django_filters.ModelChoiceFilter(
        queryset=DetentionReason.objects.all(),
        label="Reason"
    )

    illness_type = django_filters.ChoiceFilter(
        choices=HealthCondition.CONDITION_CHOICES,
        label="Patients by Illness Type",
        method='filter_active_illness'
    )

    class Meta:
        model = DetentionInstance
        fields = [
            'pdl_profile',
            'detention_status',
            'detention_reason',
            'illness_type'
        ]

    def filter_active_illness(self, queryset, name, value):
        return queryset.filter(
            pdl_profile__health_conditions__condition=value,
            pdl_profile__health_conditions__is_active=True
        ).distinct()