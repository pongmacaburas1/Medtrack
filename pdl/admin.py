
from django.contrib import admin
from .models import PDLProfile, DetentionInstance, DetentionStatus, DetentionReason, UserProfile, HealthCondition

@admin.register(PDLProfile)
class PDLProfileAdmin(admin.ModelAdmin):
    list_display = ['get_first_name', 'get_last_name', 'get_username', 'date_of_birth', 'sex']
    search_fields = ['username__first_name', 'username__last_name', 'username__username', 'case_number']
    list_filter = ['sex', 'civil_status', 'educational_attainment']
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


@admin.register(DetentionInstance)
class DetentionInstanceAdmin(admin.ModelAdmin):
    list_display = ['pdl_profile', 'detention_status', 'detention_start_date', 'detention_end_date', 'detention_room_number']
    search_fields = ['pdl_profile__username__first_name', 'pdl_profile__username__last_name', 'detention_room_number']
    list_filter = ['detention_status', 'detention_start_date']
    date_hierarchy = 'detention_start_date'


@admin.register(DetentionStatus)
class DetentionStatusAdmin(admin.ModelAdmin):
    list_display = ['status', 'description']
    search_fields = ['status']


@admin.register(DetentionReason)
class DetentionReasonAdmin(admin.ModelAdmin):
    list_display = ['reason', 'description']
    search_fields = ['reason']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role']
    list_filter = ['role']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']


@admin.register(HealthCondition)
class HealthConditionAdmin(admin.ModelAdmin):
    list_display = ['pdl_profile', 'condition', 'date_diagnosed', 'is_active', 'recorded_by', 'created_at']
    list_filter = ['condition', 'is_active']
    search_fields = ['pdl_profile__username__first_name', 'pdl_profile__username__last_name']
    date_hierarchy = 'created_at'
