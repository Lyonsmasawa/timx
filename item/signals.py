from django.db.models.signals import post_save
from django.dispatch import receiver
from api_tracker.models import APIRequestLog
from api_tracker.tasks import send_api_request
from item.models import Item
from celery.exceptions import OperationalError

@receiver(post_save, sender=Item)
def track_item_creation(sender, instance, created, **kwargs):
    """
    When a new Item is created, automatically send it to VSCU API.
    """
    if created:
        request_log = APIRequestLog.objects.create(
            request_type="saveItem",
            request_payload={
                "itemCd": instance.itemCd,
                "itemClsCd": instance.item_class_code,
                "itemTyCd": instance.item_type_code,
                "itemNm": instance.item_name,
                "itemStdNm": instance.item_name,
                "orgnNatCd": instance.origin_nation_code,
                "pkgUnitCd": instance.package_unit_code,
                "qtyUnitCd": instance.quantity_unit_code,
                "taxTyCd": instance.item_tax_code,
                "btchNo": None,
                "bcd": None,
                "dftPrc": float(instance.item_opening_balance),
                "grpPrcL1": 0,
                "grpPrcL2": 0,
                "grpPrcL3": 0,
                "grpPrcL4": 0,
                "grpPrcL5": None,
                "addInfo": None,
                "sftyQty": float(instance.item_current_balance),
                "isrcAplcbYn": "N",
                "useYn": "Y",
                "regrNm": "Admin",
                "regrId": "Admin",
                "modrNm": "Admin",
                "modrId": "Admin"
            },
            item=instance,
            user=instance.created_by if hasattr(
                instance, "created_by") else None,
            organization=instance.organization if hasattr(
                instance, "organization") else None,
        )

        try:
            send_api_request.apply_async(args=[request_log.id])
        except OperationalError as e:
            print(f"Celery is mot reachable: {e}")