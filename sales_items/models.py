from django.db import models
from django.forms import ValidationError
from commons.models import BaseModel
from transaction.models import Transaction
from item.models import Item


class SalesItems(BaseModel):
    transaction = models.ForeignKey(
        Transaction, on_delete=models.DO_NOTHING, related_name='sales_items')
    item = models.ForeignKey(Item, on_delete=models.DO_NOTHING)
    item_description = models.CharField(max_length=200)
    qty = models.DecimalField(max_digits=10, decimal_places=2)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    discount_rate = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    tax_code = models.CharField(max_length=50)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    def clean(self):
        """
        Add validation logic for `discount_amount` and `line_total`.
        """
        # Calculate the total before discount
        total_before_discount = self.qty * self.rate

        # Validate discount amount
        if self.discount_amount > total_before_discount:
            raise ValidationError({
                'discount_amount': f"Discount amount ({self.discount_amount}) cannot exceed the total before discount ({total_before_discount})."
            })

        # Calculate the expected line total after discount
        expected_line_total = total_before_discount - self.discount_amount

        # Validate line total
        if self.line_total != expected_line_total:
            raise ValidationError({
                'line_total': f"Line total ({self.line_total}) does not match the expected value ({expected_line_total}) after applying the discount."
            })

    def save(self, *args, **kwargs):
        """
        Override save to call clean() for validation.
        """
        self.full_clean()  # Triggers `clean()` for validation
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Sales Item: {self.item_description}"
