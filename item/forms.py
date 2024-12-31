from django import forms
from dal import autocomplete
from .models import Item

# In the form definition


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = [
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

        # widgets = {
        #     'origin_nation_code': autocomplete.Select2(
        #         url='item:country-code-autocomplete'
        #     ),
        #     'item_type_code': autocomplete.Select2(
        #         url='item:item-type-code-autocomplete'
        #     ),
        #     'quantity_unit_code': autocomplete.Select2(
        #         url='item:quantity-unit-code-autocomplete'
        #     ),
        #     'package_unit_code': autocomplete.Select2(
        #         url='item:package-unit-code-autocomplete'
        #     ),
        #     'item_class_code': autocomplete.Select2(
        #         url='item:item-class-code-autocomplete'
        #     ),
        #     'item_tax_code': autocomplete.Select2(
        #         url='item:item-tax-code-autocomplete'
        #     ),
        # }
