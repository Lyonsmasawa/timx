from rest_framework import serializers
from .models import SalesItems

class SalesItemsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesItems
        fields = '__all__'
