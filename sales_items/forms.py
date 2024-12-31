from django import forms
from .models import SalesItems

class SalesItemsForm(forms.ModelForm):
    class Meta:
        model = SalesItems
        fields = [
            'item',
            'item_description',
            'qty',
            'rate',
            'discount_rate',
            'discount_amount',
            'tax_code',
            'line_total',
        ]
