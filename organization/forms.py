from django import forms
from .models import Organization

class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = [
            "organization_name",
            "organization_pin",
            "organization_email",
            "organization_physical_address",
            "organization_phone",
        ]
        widgets = {
            "organization_name": forms.TextInput(attrs={"class": "form-control"}),
            "organization_pin": forms.TextInput(attrs={"class": "form-control"}),
            "organization_email": forms.EmailInput(attrs={"class": "form-control"}),
            "organization_physical_address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "organization_phone": forms.TextInput(attrs={"class": "form-control"}),
        }
        error_messages = {
            "organization_name": {"required": "Organization name is required."},
            "organization_email": {"invalid": "Please enter a valid email address."},
        }
