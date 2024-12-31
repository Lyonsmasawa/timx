from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from commons.models import BaseModel
from django.contrib.auth.models import User
from commons.utils import generate_organization_pin


class Organization(BaseModel):
    user = models.ManyToManyField(User,  related_name="organizations")
    organization_name = models.CharField(max_length=50, unique=True)
    organization_pin = models.CharField(
        max_length=50,  unique=True)
    organization_email = models.EmailField(max_length=50)
    organization_physical_address = models.CharField(max_length=100)
    organization_phone = models.CharField(max_length=13)

    def __str__(self):
        return self.organization_name

    def save(self, *args, **kwargs):
        # Prevent editing of organization_pin for existing records
        if self.pk is not None:
            original = Organization.objects.get(pk=self.pk)
            if original.organization_pin != self.organization_pin:
                raise ValueError("Organization PIN cannot be edited.")

        super().save(*args, **kwargs)  # Call the parent save method
