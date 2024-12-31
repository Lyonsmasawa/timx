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

    def save(self, commit=True, user=None):
        # Save the organization without committing it to the database
        organization = super().save(commit=False)

        if user:
            # Associate the organization with the user
            organization.save()
            organization.user.add(user)

        return organization

    def clean_organization_pin(self):
        # Prevent manual updates to organization_pin via the form
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:  # If updating an existing instance
            return instance.organization_pin  # Return existing value
        return self.cleaned_data.get('organization_pin', None)
