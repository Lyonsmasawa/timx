# from django import forms
# from .models import Customer

# class CustomerForm(forms.ModelForm):
#     class Meta:
#         model = Customer
#         fields = ['customer_name', 'customer_email', 'customer_phone', 'customer_address']
#         widgets = {
#             'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
#             'customer_email': forms.EmailInput(attrs={'class': 'form-control'}),
#             'customer_phone': forms.TextInput(attrs={'class': 'form-control'}),
#             'customer_address': forms.Textarea(attrs={'class': 'form-control'}),
#         }

from django import forms
from .models import Customer

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            "organization",
            "customer_name",
            "customer_pin",
            "customer_address",
            "customer_phone",
            "customer_email",
        ]
