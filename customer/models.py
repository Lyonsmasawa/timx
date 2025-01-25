from django.db import models
from commons.models import BaseModel
from django.core.validators import MinLengthValidator
from commons.utils import generate_customer_pin
from organization.models import Organization
from django.contrib.auth.models import User


class Customer(BaseModel):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name='customers')
    customer_name = models.CharField(max_length=200)
    customer_pin = models.CharField(
        max_length=200, unique=True,  validators=[MinLengthValidator(9)],)
    customer_address = models.CharField(max_length=200, blank=True, null=True)
    customer_phone = models.CharField(max_length=200, blank=False, null=False)
    customer_email = models.EmailField(max_length=200, blank=True, null=True)

    class Meta:
        # Ensure that customer details are unique within each organization
        unique_together = (('organization', 'customer_phone'),
                           ('organization', 'customer_email'))

    def __str__(self):
        return self.customer_name
