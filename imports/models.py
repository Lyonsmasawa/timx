from django.db import models
from commons.models import BaseModel
from organization.models import Organization

class Import(BaseModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="imports"
    )
    task_code = models.CharField(max_length=20, unique=True)  # Unique task identifier
    declaration_date = models.DateField()
    declaration_number = models.CharField(max_length=50)
    hs_code = models.CharField(max_length=20)  # Harmonized System code
    item_name = models.CharField(max_length=255)
    import_status_code = models.CharField(max_length=5)
    origin_country = models.CharField(max_length=5)
    export_country = models.CharField(max_length=5)
    package_count = models.PositiveIntegerField()
    package_unit_code = models.CharField(max_length=10)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_unit_code = models.CharField(max_length=10)
    total_weight = models.DecimalField(max_digits=10, decimal_places=2)
    net_weight = models.DecimalField(max_digits=10, decimal_places=2)
    supplier_name = models.CharField(max_length=255)
    agent_name = models.CharField(max_length=255)
    invoice_amount = models.DecimalField(max_digits=12, decimal_places=2)
    invoice_currency = models.CharField(max_length=5)
    invoice_exchange_rate = models.DecimalField(max_digits=10, decimal_places=2)
    verified = models.BooleanField(default=False)
    payload = models.JSONField()  # Store raw API response for reference

    def __str__(self):
        return f"Import {self.declaration_number} - {self.item_name}"
