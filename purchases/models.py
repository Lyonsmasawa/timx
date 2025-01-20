from django.db import models
from django.utils.timezone import now
from commons.models import BaseModel
from organization.models import Organization

class Purchase(BaseModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="organization_purchase"
    )
    supplier_name = models.CharField(max_length=255)
    supplier_tin = models.CharField(max_length=50)
    invoice_number = models.PositiveIntegerField(unique=True)
    confirmation_date = models.DateTimeField()
    total_item_count = models.PositiveIntegerField()
    total_taxable_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_tax_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payload = models.JSONField()  # Store the entire payload as JSON
    verified = models.BooleanField(default=False)

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.supplier_name}"
