from django.db import models
from commons.models import BaseModel
from organization.models import Organization
from django.contrib.auth.models import User


class Customer(BaseModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='customers')
    customer_name = models.CharField(max_length=200)
    customer_pin = models.CharField(max_length=200, unique=True)
    customer_address = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=200, unique=True)
    customer_email = models.EmailField(max_length=200, unique=True)

    def __str__(self):
        return self.customer_name

    def save(self, *args, **kwargs):
        # Automatically set the organization to the logged-in user's organization
        if not self.organization:
            self.organization = Organization.objects.filter(
                user=self.user).first()

        if not self.key:
            # Generate the key unique to the organization's customers
            self.key = self.generate_unique_key(
                Customer.objects.filter(organization=self.organization)
            )

        super().save(*args, **kwargs)
