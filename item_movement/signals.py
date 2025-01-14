from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from api_tracker.models import APIRequestLog
from api_tracker.tasks import send_api_request
from commons.constants import SAR_TYPE_CODES
from item_movement.models import ItemMovement
from django.utils.timezone import now


@receiver(post_save, sender=ItemMovement)
def track_stock_movement(sender, instance, created, **kwargs):
    """
    When a stock movement occurs, automatically send it to VSCU API.
    """
    if created:
        # Determine the correct sarTyCd based on movement type
        sar_type_code = SAR_TYPE_CODES.get(
            instance.movement_type, {}).get(instance.movement_reason)

        # 🔍 **Log API request to send stock update to VSCU API**
        request_log = APIRequestLog.objects.create(
            request_type="saveStockMovement",
            request_payload={
                "tin": settings.VSCU_TIN,
                "bhfId": settings.VSCU_BRANCH_ID,
                "sarNo": instance.id,
                "orgSarNo":  instance.id,
                "regTyCd": "M",  # Modify based on type
                "custTin": None,
                "custNm": None,
                "custBhfId": settings.VSCU_BRANCH_ID,
                "sarTyCd": sar_type_code,
                "ocrnDt": now().strftime("%Y%m%d"),
                "totItemCnt": 1,
                "totTaxblAmt": 0,  # Modify based on calculations
                "totTaxAmt": 0,
                "totAmt": 0,  # Modify based on calculations
                "remark": f"{instance.movement_reason} for {instance.item.item_name}",
                "regrNm": "Admin",
                "regrId": "Admin",
                "modrNm": "Admin",
                "modrId": "Admin",
                "itemList": [{
                    "itemSeq": 1,
                    "itemCd": instance.item.itemCd,
                    "itemClsCd": instance.item.item_class_code,
                    "itemNm": instance.item.item_name,
                    "bcd": None,
                    "pkgUnitCd": instance.item.package_unit_code,
                    "pkg": 0,
                    "qtyUnitCd": instance.item.quantity_unit_code,
                    "qty": instance.item_unit,
                    "itemExprDt": None,
                    "prc": 0,
                    "splyAmt": 0,
                    "totDcAmt": 0,
                    "taxblAmt": 0,
                    "taxTyCd": instance.item.item_tax_code,
                    "taxAmt": 0,
                    "totAmt": 0,
                }]
            },
            item=instance.item,
            user=instance.created_by if hasattr(
                instance, "created_by") else None,
            organization=instance.item.organization if hasattr(
                instance.item, "organization") else None,
        )

        # Send request asynchronously using Celery
        send_api_request.apply_async(args=[request_log.id])
