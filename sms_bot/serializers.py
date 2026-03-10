"""SMS Bot – DRF Serializers"""

from rest_framework import serializers
from .models import FarmerProfile, SMSLog, SMSSession


class FarmerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = FarmerProfile
        fields = [
            'id', 'phone_number', 'language', 'district',
            'first_contact', 'last_contact', 'total_queries',
        ]


class SMSLogSerializer(serializers.ModelSerializer):
    farmer_phone = serializers.CharField(source='farmer.phone_number', read_only=True, default='')

    class Meta:
        model  = SMSLog
        fields = [
            'id', 'direction', 'phone_number', 'farmer_phone',
            'message', 'response', 'status', 'intent', 'created_at',
        ]
