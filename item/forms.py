from django import forms
from .models import Item

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
            "organization",
            "item_name",
            "origin_nation_code",
            "item_type_code",
            "quantity_unit_code",
            "package_unit_code",
            "item_class_code",
            "item_tax_code",
            "item_opening_balance",
            "item_current_balance",
            "item_system_id",
            "item_system_name",
        ]
