from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from commons.models import BaseModel
from django.contrib.auth.models import User


class Organization(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="organizations")  # Link to user
    organization_name = models.CharField(max_length=50)
    organization_pin = models.CharField(
        max_length=50,  unique=True)
    organization_email = models.EmailField(max_length=50)
    organization_physical_address = models.CharField(max_length=100)
    organization_phone = models.CharField(max_length=13)

    def __str__(self):
        return self.organization_name

    def save(self, *args, **kwargs):
        if not self.key:
            # Generate the key unique to the user's organizations
            self.key = self.generate_unique_key(
                Organization.objects.filter(user=self.user)
            )
            
         # Prevent editing of organization_pin for existing records
        if self.pk is not None:
            original = Organization.objects.get(pk=self.pk)
            if original.organization_pin != self.organization_pin:
                raise ValueError("Organization PIN cannot be edited.")
            
        super().save(*args, **kwargs)
