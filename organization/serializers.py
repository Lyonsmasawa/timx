from rest_framework import serializers
from .models import Organization

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'created_at', 'updated_at', 'organization_name', 'organization_pin', 'organization_email', 'organization_physical_address', 'organization_phone']
