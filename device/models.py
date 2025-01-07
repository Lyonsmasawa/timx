from django.db import models

class Device(models.Model):
    tin = models.CharField(max_length=15, unique=True)
    branch_id = models.CharField(max_length=5)
    device_serial_number = models.CharField(max_length=50, unique=True)
    initialized = models.BooleanField(default=False)

    # Fields populated after successful initialization
    device_id = models.CharField(max_length=50, null=True, blank=True)
    control_unit_id = models.CharField(max_length=50, null=True, blank=True)
    internal_key = models.CharField(max_length=255, null=True, blank=True)
    sign_key = models.CharField(max_length=255, null=True, blank=True)
    communication_key = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Device {self.device_serial_number} (TIN: {self.tin})"
