from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from common.models import BaseModel

class Organization(BaseModel):
    organization_name = models.CharField(max_length=50, blank=True)
    organization_pin = models.CharField(max_length=50, blank=True)
    organization_email = models.EmailField(max_length=50, blank=True)
    organization_physical_address = models.CharField(max_length=100, blank=True)
    organization_phone = models.CharField(max_length=15, blank=True)
    organization_key = models.CharField(max_length=7, unique=True, editable=False)

    def __str__(self):
        return self.organization_name

# Signal to auto-generate the unique key
@receiver(pre_save, sender=Organization)
def generate_organization_key(sender, instance, **kwargs):
    if not instance.organization_key:
        last_key = (
            sender.objects.order_by("-id")
            .values_list("organization_key", flat=True)
            .first()
        )
        next_key = int(last_key) + 1 if last_key else 1
        instance.organization_key = f"{next_key:07d}"
