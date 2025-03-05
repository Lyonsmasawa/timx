from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from device.models import Device
from organization.models import Organization


@receiver(post_save, sender=Organization)
def create_demo_device(sender, instance, created, **kwargs):
    """
    Automatically creates a demo device when a new organization is created.
    """
    if created:
        Device.objects.create(
            organization=instance,
            mode="demo",
            tin=settings.VSCU_TIN,
            branch_id=settings.VSCU_BRANCH_ID,
            device_serial_number=settings.VSCU_DEVICE_SERIAL,
            communication_key=settings.VSCU_CMC_KEY,
            active=True
        )
