"""Crops – Django Admin"""

from django.contrib import admin
from .models import Crop, Disease, AgronomyTip


@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display  = ['icon', 'name_en', 'name_ny', 'slug', 'is_active']
    list_filter   = ['is_active']
    search_fields = ['name_en', 'name_ny', 'slug']
    prepopulated_fields = {'slug': ('name_en',)}


class DiseaseInline(admin.TabularInline):
    model  = Disease
    extra  = 1
    fields = ['menu_number', 'name_en', 'name_ny', 'category', 'severity', 'is_active']


@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display  = ['crop', 'menu_number', 'name_en', 'category', 'severity', 'is_active', 'updated_at']
    list_filter   = ['crop', 'category', 'severity', 'is_active']
    search_fields = ['name_en', 'name_ny']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = [
        ('Basic Info', {'fields': ['crop', 'menu_number', 'name_en', 'name_ny', 'category', 'severity', 'is_active']}),
        ('Symptoms',   {'fields': ['symptoms_en', 'symptoms_ny']}),
        ('Treatment',  {'fields': ['treatment_en', 'treatment_ny', 'recommended_product']}),
        ('Prevention', {'fields': ['prevention_en', 'prevention_ny']}),
        ('Meta',       {'fields': ['created_at', 'updated_at', 'updated_by'], 'classes': ['collapse']}),
    ]

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AgronomyTip)
class AgronomyTipAdmin(admin.ModelAdmin):
    list_display = ['title_en', 'crop', 'season', 'is_active', 'created_at']
    list_filter  = ['season', 'is_active', 'crop']
