from django.db import models
from commons.models import BaseModel
from item.models import Item
from commons.constants import MOVEMENT_TYPE_CHOICES


class ItemMovement(BaseModel):
    item = models.ForeignKey(
        Item, on_delete=models.DO_NOTHING, related_name='item_movements')
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPE_CHOICES)
    movement_reason = models.CharField(max_length=10, blank=True, null=True)
    item_unit = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.movement_type} - {self.item.item_name} - {self.movement_reason} ({self.item_unit})"
