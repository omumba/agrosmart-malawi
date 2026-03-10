"""Crops – DRF Serializers"""
from rest_framework import serializers
from .models import Crop, Disease, AgronomyTip


class DiseaseSerializer(serializers.ModelSerializer):
    crop_name = serializers.CharField(source='crop.name_en', read_only=True)

    class Meta:
        model  = Disease
        fields = [
            'id', 'crop_name', 'menu_number', 'name_en', 'name_ny',
            'category', 'severity', 'symptoms_en', 'symptoms_ny',
            'treatment_en', 'treatment_ny', 'prevention_en',
            'recommended_product', 'is_active',
        ]


class CropSerializer(serializers.ModelSerializer):
    diseases = DiseaseSerializer(many=True, read_only=True)

    class Meta:
        model  = Crop
        fields = ['id', 'name_en', 'name_ny', 'slug', 'icon', 'description_en', 'diseases']
