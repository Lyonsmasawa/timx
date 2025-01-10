from django.db.models.signals import post_save
from django.dispatch import receiver
from api_tracker.models import APIRequestLog
from api_tracker.tasks import send_api_request
from customer.models import Customer


@receiver(post_save, sender=Customer)
def track_customer_creation(sender, instance, created, **kwargs):
    """
    When a new Item is created, automatically send it to VSCU API.
    """
    if created:
        request_log = APIRequestLog.objects.create(
            request_type="saveCustomer",
            request_payload={
                "custNo": instance.customer_pin,
                "custTin": instance.customer_pin,
                "custNm": instance.customer_name,
                "adrs": instance.customer_address or "",
                "telNo": instance.customer_phone or "",
                "email": instance.customer_email or "",
                "faxNo": None,
                "useYn": "Y",
                "remark": None,
                "regrNm": "Admin",
                "regrId": "Admin",
                "modrNm": "Admin",
                "modrId": "Admin"
            },
            customer=instance,
            user=instance.created_by if hasattr(
                instance, "created_by") else None,
            organization=instance.organization if hasattr(
                instance, "organization") else None,
        )

        send_api_request.apply_async(args=[request_log.id])
