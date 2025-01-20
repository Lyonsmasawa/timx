from django.db import models

from commons.models import BaseModel


class APIRequestLog(BaseModel):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
        ("retrying", "Retrying"),
    ]

    # e.g., initializeDevice, saveItem, saveCustomer
    request_type = models.CharField(max_length=50)
    request_payload = models.JSONField()
    response_data = models.JSONField(null=True, blank=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="pending")
    retries = models.PositiveIntegerField(default=0)

    # Allow easy debugging by linking requests to Users, Organizations, and Items
    user = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True)
    organization = models.ForeignKey(
        "organization.Organization", on_delete=models.SET_NULL, null=True, blank=True)
    item = models.ForeignKey(
        "item.Item", on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey(
        "customer.Customer", on_delete=models.CASCADE, null=True, blank=True)
    purchase = models.ForeignKey(
        "purchases.Purchase", on_delete=models.CASCADE, null=True, blank=True)
    transaction = models.ForeignKey(
        "transaction.Transaction", on_delete=models.CASCADE, null=True, blank=True)

    def mark_success(self, response):
        self.status = "success"
        self.response_data = response
        self.save()

    def mark_failed(self, response):
        self.status = "failed"
        self.response_data = response
        self.save()

    def mark_retrying(self):
        self.status = "retrying"
        self.retries += 1
        self.save()

    def __str__(self):
        return f"{self.request_type} - {self.status} (Retries: {self.retries})"
