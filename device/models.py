from django.db import models
from organization.models import Organization
from commons.utils import encrypt_value, decrypt_value


class Device(models.Model):
    MODE_CHOICES = [
        ('live', 'Live'),
        ('demo', 'Demo'),
        ('imported', 'Imported Keys')
    ]

    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="devices")
    tin = models.CharField(max_length=15, unique=True)
    branch_id = models.CharField(max_length=5)
    device_serial_number = models.CharField(max_length=50)
    initialized = models.BooleanField(default=False)
    mode = models.CharField(
        max_length=10, choices=MODE_CHOICES, default='demo')

    # Encrypted Fields
    control_unit_id = models.CharField(max_length=255, null=True, blank=True)
    internal_key = models.CharField(max_length=255, null=True, blank=True)
    sign_key = models.CharField(max_length=255, null=True, blank=True)
    communication_key = models.CharField(max_length=255, null=True, blank=True)

    initialized = models.BooleanField(default=False)
    active = models.BooleanField(default=False)

    def __str__(self):
        return f"Device {self.device_serial_number} ({self.mode} - TIN: {self.tin})"
    
    def set_active(self):
        """Deactivate all other devices and activate this one."""
        Device.objects.filter(organization=self.organization).update(active=False)
        self.active = True
        self.save()

    def is_initialized(self):
        """Check if the device has been initialized (all keys exist)."""
        return all([self.device_id, self.control_unit_id, self.internal_key, self.sign_key, self.communication_key])

    def save(self, *args, **kwargs):
        """Encrypt sensitive fields before saving."""
        if self.control_unit_id:
            self.control_unit_id = encrypt_value(self.control_unit_id)
        if self.internal_key:
            self.internal_key = encrypt_value(self.internal_key)
        if self.sign_key:
            self.sign_key = encrypt_value(self.sign_key)
        if self.communication_key:
            self.communication_key = encrypt_value(self.communication_key)

        super().save(*args, **kwargs)

    def get_decrypted_keys(self):
        """Retrieve decrypted device keys."""
        return {
            "control_unit_id": decrypt_value(self.control_unit_id),
            "internal_key": decrypt_value(self.internal_key),
            "sign_key": decrypt_value(self.sign_key),
            "communication_key": decrypt_value(self.communication_key),
        }

    def set_live(self, tin, bhf_id, dvc_srl_no):
        """
        Updates device to Live Mode and triggers API initialization.
        """
        self.tin = tin
        self.branch_id = bhf_id
        self.device_serial_number = dvc_srl_no
        self.mode = "live"
        self.save()

    def import_keys(self, tin, bhf_id, cmc_key):
        """Imports manually entered keys and encrypts them."""
        self.tin = tin
        self.branch_id = bhf_id
        self.communication_key = encrypt_value(cmc_key)
        self.mode = "imported"
        self.initialized = True
        self.save()

    def __str__(self):
        return f"Device {self.device_serial_number} ({self.mode})"
