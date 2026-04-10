from django.contrib import admin

# Register your models here.
from .models import MedicalSpecialty, Physician, ConsultationLocation, ConsultationReason, Consultation

@admin.register(MedicalSpecialty)
class MedicalSpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    ordering = ('name',)
    list_filter = ('name',)
    fieldsets = (
        (None, {
            'fields': ('name', 'description')
        }),
    )

@admin.register(Physician)
class PhysicianAdmin(admin.ModelAdmin):
    list_display = ['get_first_name', 'get_last_name', 'get_username']
    search_fields = ['username__first_name', 'username__last_name', 'username__username']
    list_display_links = ['get_first_name', 'get_last_name']
    
    def get_first_name(self, obj):
        return obj.username.first_name
    get_first_name.short_description = 'First Name'
    get_first_name.admin_order_field = 'username__first_name'
    
    def get_last_name(self, obj):
        return obj.username.last_name
    get_last_name.short_description = 'Last Name'
    get_last_name.admin_order_field = 'username__last_name'
    
    def get_username(self, obj):
        return obj.username.username
    get_username.short_description = 'Username'
    get_username.admin_order_field = 'username__username'
    
    fieldsets = (
        (None, {
            'fields': ('username', 'employee_type', 'specialty')
        }),
        ('Contact Information', {
            'fields': ('phone_number',)
        }),
        ('Address Information', {
            'fields': ('address',)
        }),
    )

@admin.register(ConsultationLocation)
class ConsultationLocationAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'capacity')
    search_fields = ('room_number',)
    ordering = ('room_number',)
    list_filter = ('capacity',)
    fieldsets = (
        (None, {
            'fields': ('room_number', 'capacity')
        }),
    )

@admin.register(ConsultationReason)
class ConsultationReasonAdmin(admin.ModelAdmin):
    list_display = ('reason',)
    search_fields = ('reason',)

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = (
        'pdl_profile',
        'physician',
        'location',
        'reason',
        'status',
        'consultation_date_date_only',
        'consultation_time_block',
        'is_an_emergency',
    )
    search_fields = (
        'pdl_profile__username__first_name',
        'pdl_profile__username__last_name',
        'physician__username__first_name',
        'physician__username__last_name',
    )
    list_filter = ('status', 'is_an_emergency', 'consultation_date_date_only', 'consultation_time_block')