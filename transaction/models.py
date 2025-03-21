from django.db import models
from commons.models import BaseModel
from organization.models import Organization
from customer.models import Customer


class Transaction(BaseModel):
    organization = models.ForeignKey(Organization, on_delete=models.DO_NOTHING)
    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING)
    trader_invoice_number = models.CharField(max_length=200)
    receipt_number = models.BigIntegerField(unique=True)
    document_type = models.CharField(max_length=50, choices=[
        ('invoice', 'Invoice'),
        ('credit_note', 'Credit Note'),
        ('receipt', 'Receipt')
    ])
    original_receipt_number = models.BigIntegerField(blank=True, null=True)
    reason = models.CharField(
        max_length=200, null=True, blank=True, default="sale")
    document_path = models.FileField(
        upload_to='transaction_documents/', null=True, blank=True)

    def __str__(self):
        return f"Transaction {self.receipt_number}-{self.document_type} for {self.customer.customer_name} - {self.reason}"
