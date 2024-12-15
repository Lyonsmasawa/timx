from django.db import models
from commons.models import BaseModel
from item.models import Item

class Inventory(BaseModel):
    MOVEMENT_TYPE_CHOICES = [
        ('ADD', 'Addition'),
        ('REMOVE', 'Removal'),
        ('TRANSFER', 'Transfer'),
    ]

    item = models.ForeignKey(Item, on_delete=models.DO_NOTHING, related_name='inventories')
    movement_type = models.CharField(max_length=10, choices=MOVEMENT_TYPE_CHOICES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.movement_type} - {self.item.item_name} ({self.quantity})"