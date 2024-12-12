from django.db import models
from common.models import BaseModel
from organization.models import Organization
from django.contrib.auth.models import User

class Item(BaseModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField(max_length=200)
    origin_nation_code = models.CharField(max_length=3)
    item_type_code = models.CharField(max_length=5)
    quantity_unit_code = models.CharField(max_length=5)
    package_unit_code = models.CharField(max_length=5)
    item_class_code = models.CharField(max_length=200)
    item_tax_code = models.CharField(max_length=200)
    item_opening_balance = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    item_current_balance = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    item_system_id = models.CharField(max_length=200)
    item_system_name = models.CharField(max_length=200)

    def __str__(self):
        return self.item_name
