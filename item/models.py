from django.db import models
from commons.models import BaseModel
from organization.models import Organization
from django.contrib.auth.models import User
from commons.constants import COUNTRY_CHOICES, TAX_TYPE_CHOICES, PRODUCT_TYPE_CHOICES, UNIT_CHOICES, PACKAGE_CHOICES, TAXPAYER_STATUS_CHOICES
from commons.utils import generate_item_cd


class Item(BaseModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField(max_length=200)
    origin_nation_code = models.CharField(
        max_length=2, choices=COUNTRY_CHOICES)
    item_type_code = models.CharField(
        max_length=2, choices=PRODUCT_TYPE_CHOICES)
    quantity_unit_code = models.CharField(
        max_length=3,
        choices=UNIT_CHOICES,
    )
    package_unit_code = models.CharField(
        max_length=3,
        choices=PACKAGE_CHOICES,
    )
    item_class_code = models.CharField(
        max_length=2, choices=TAXPAYER_STATUS_CHOICES)
    item_tax_code = models.CharField(
        max_length=1, choices=TAX_TYPE_CHOICES)
    item_opening_balance = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, default=0)
    item_current_balance = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True, default=0)
    item_system_id = models.CharField(max_length=200, blank=True, null=True)
    item_system_name = models.CharField(max_length=200, blank=True, null=True)
    itemCd = models.CharField(
        max_length=16, null=False, blank=False)

    class Meta:
        # Ensure that itemCd is unique within each organization
        unique_together = (('organization', 'itemCd'),
                           ('organization', 'item_name'))

    def save(self, *args, **kwargs):
        if not self.itemCd:
            # Generate itemCd based on the required format
            self.itemCd = generate_item_cd(self)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.item_name
