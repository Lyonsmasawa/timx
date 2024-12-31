from rest_framework import serializers
from .models import ItemMovement

class ItemMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemMovement
        fields = '__all__'
