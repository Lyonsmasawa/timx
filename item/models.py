from django.db import models
from commons.models import BaseModel
from organization.models import Organization
from django.contrib.auth.models import User
from commons.constants import COUNTRY_CHOICES, TAX_TYPE_CHOICES, PRODUCT_TYPE_CHOICES, UNIT_CHOICES, PACKAGE_CHOICES, TAXPAYER_STATUS_CHOICES
from commons.utils import generate_item_cd
from django.db.models.signals import post_save
from django.dispatch import receiver
from api_tracker.models import APIRequestLog
from api_tracker.tasks import send_api_request

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


@receiver(post_save, sender=Item)
def track_item_creation(sender, instance, created, **kwargs):
    """
    When a new Item is created, this function is triggered automatically.
    It logs the request and adds it to the Celery queue for processing.
    """
    if created: 
        request_log = APIRequestLog.objects.create(
            request_type="saveItem",
            request_payload={
                "itemCd": instance.item_code,
                "itemNm": instance.item_name,
                "taxTyCd": instance.tax_type,
                "dftPrc": float(instance.price),
            }
        )
        
        print(request_log)

        send_api_request.delay(request_log.id)
