"""SMS Bot – Django Admin"""
from django.contrib import admin
from .models import FarmerProfile, SMSSession, SMSLog


@admin.register(FarmerProfile)
class FarmerProfileAdmin(admin.ModelAdmin):
    list_display  = ['phone_number', 'language', 'district', 'total_queries', 'first_contact', 'last_contact', 'is_active']
    list_filter   = ['language', 'is_active']
    search_fields = ['phone_number', 'district']
    readonly_fields = ['first_contact', 'last_contact', 'total_queries']


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display  = ['created_at', 'direction', 'phone_number', 'intent', 'status', 'message_preview']
    list_filter   = ['direction', 'status', 'intent']
    search_fields = ['phone_number', 'message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'

    def message_preview(self, obj):
        return obj.message[:60] + '...' if len(obj.message) > 60 else obj.message
    message_preview.short_description = 'Message'


@admin.register(SMSSession)
class SMSSessionAdmin(admin.ModelAdmin):
    list_display = ['farmer', 'state', 'updated_at']
    list_filter  = ['state']
