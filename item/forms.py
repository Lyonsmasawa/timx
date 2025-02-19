# forms.py
from django import forms
from django.urls import reverse
from django_select2.forms import Select2Widget

from commons.item_classification_constants import ITEM_CLASS_CHOICES
from commons.utils import get_item_class_choices
from .models import Item
from commons.constants import COUNTRY_CHOICES, PACKAGE_CHOICES, PRODUCT_TYPE_CHOICES, TAX_TYPE_CHOICES, UNIT_CHOICES


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
            # "item_system_id",
            # "item_system_name",
        ]

    # Define all choice fields
    origin_nation_code = forms.ChoiceField(choices=COUNTRY_CHOICES)
    item_type_code = forms.ChoiceField(choices=PRODUCT_TYPE_CHOICES)
    item_class_code = forms.ChoiceField(choices=get_item_class_choices())
    quantity_unit_code = forms.ChoiceField(choices=UNIT_CHOICES)
    package_unit_code = forms.ChoiceField(choices=PACKAGE_CHOICES)
    item_tax_code = forms.ChoiceField(choices=TAX_TYPE_CHOICES)

    def __init__(self, *args, **kwargs):
        super(ItemForm, self).__init__(*args, **kwargs)

        # Apply Select2Widget to each field with choices
        for field_name in ['quantity_unit_code', 'origin_nation_code', 'item_type_code', 'item_class_code', 'package_unit_code', 'item_tax_code']:
            self.fields[field_name].widget = Select2Widget(attrs={
                'data-placeholder': 'Select or type...',
                'data-minimum-input-length': '0',
                # Dynamically pass field_name
                'data-ajax-url': reverse('item:ajax_filter', args=[field_name]),
                'data-allow-clear': 'true',
                'data-dropdown-parent': '#createItemModal .modal-content',  # Attach dropdown to modal
            })

            # Optionally set the initial value for each field
            self.fields[field_name].initial = getattr(
                self, field_name.upper() + '_CHOICES', [])
