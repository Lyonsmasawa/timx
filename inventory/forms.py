from django import forms
from .models import Inventory

class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = [
            "item",
            "movement_type",
            "quantity",
            "description",
        ]
