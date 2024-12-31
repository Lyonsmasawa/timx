from django import forms
from .models import Transaction
from customer.models import Customer
from organization.models import Organization


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'customer',
            'trader_invoice_number',
            'receipt_number',
            'document_type',
            'document_path',
        ]

    def __init__(self, *args, **kwargs):
        super(TransactionForm, self).__init__(*args, **kwargs)
        # Optionally you can add dynamic filtering to the dropdowns based on the user's permissions
        # Make organization field read-only
        if self.instance and self.instance.pk:
            self.fields['organization'].disabled = True   
        self.fields['customer'].queryset = Customer.objects.all()
