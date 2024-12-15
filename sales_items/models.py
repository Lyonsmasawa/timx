from django.db import models
from commons.models import BaseModel
from transaction.models import Transaction
from item.models import Item

class SalesItems(BaseModel):
    transaction = models.ForeignKey(Transaction, on_delete=models.DO_NOTHING)
    item = models.ForeignKey(Item, on_delete=models.DO_NOTHING)
    item_description = models.CharField(max_length=200)
    qty = models.DecimalField(max_digits=10, decimal_places=2)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    discount_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_code = models.CharField(max_length=50)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Sales Item: {self.item_description}"
