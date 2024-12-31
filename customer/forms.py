from django import forms
from .models import Customer
from django.core.exceptions import ValidationError


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            "customer_name",
            "customer_pin",
            "customer_address",
            "customer_phone",
            "customer_email",
        ]
        widgets = {
            "customer_name": forms.TextInput(attrs={"class": "form-control"}),
            "customer_pin": forms.TextInput(attrs={"class": "form-control"}),
            "customer_address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "customer_phone": forms.TextInput(attrs={"class": "form-control"}),
            "customer_email": forms.EmailInput(attrs={"class": "form-control"}),
        }
        error_messages = {
            "customer_name": {"required": "Customer name is required."},
            "customer_email": {"invalid": "Please enter a valid email address."},
        }