from django.db import models
from common.models import BaseModel
from organization.models import Organization
from django.contrib.auth.models import User

class Customer(BaseModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='customers')
    customer_name = models.CharField(max_length=200)
    customer_pin = models.CharField(max_length=200, blank=True, null=True)
    customer_address = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=200)
    customer_email = models.EmailField(max_length=200)

    def __str__(self):
        return self.customer_name
