from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from api_tracker.models import APIRequestLog
from api_tracker.tasks import send_api_request
from transaction.models import Transaction

# @receiver(post_save, sender=Transaction)
# def track_sales_transaction(sender, instance, created, **kwargs):
#     """
#     When a new sales transaction (Invoice or Credit Note) is created, send it to VSCU API.
#     """
#     if created and instance.document_type in ["invoice", "credit_note"]:
#         # Determine Sale Type Code
#         sales_type_code = "S" if instance.document_type == "invoice" else "R"

#         # Compute tax details
#         taxblAmtB = sum(item.line_total for item in instance.sales_items.all())
#         totTaxAmt = sum(item.tax_amount for item in instance.sales_items.all())

#         # Construct API Request Payload
#         request_payload = {
#             "invcNo": instance.receipt_number,  # Invoice Number
#             "orgInvcNo": instance.original_receipt_number,  # Original Invoice (for Credit Notes)
#             "custTin": instance.customer.customer_pin,
#             "custNm": instance.customer.customer_name,
#             "salesTyCd": "N",  # Normal Sale
#             "rcptTyCd": sales_type_code,  # "S" for Sale, "R" for Credit Note
#             "pmtTyCd": "01",  # Payment Type (01 = Cash)
#             "salesSttsCd": "02",  # Status Code
#             "cfmDt": instance.created_at.strftime("%Y%m%d%H%M%S"),  # Confirmation Date
#             "salesDt": instance.created_at.strftime("%Y%m%d"),  # Sales Date
#             "stockRlsDt": instance.created_at.strftime("%Y%m%d%H%M%S"),  # Stock Release Date
#             "cnclReqDt": None,
#             "cnclDt": None,
#             "rfdDt": None,
#             "rfdRsnCd": None,
#             "totItemCnt": instance.sales_items.count(),
#             "taxblAmtA": 0,
#             "taxblAmtB": taxblAmtB,
#             "taxblAmtC": 0,
#             "taxblAmtD": 0,
#             "taxblAmtE": 0,
#             "taxRtA": 0,
#             "taxRtB": 16,  # Assuming 16% VAT applies
#             "taxRtC": 0,
#             "taxRtD": 0,
#             "taxRtE": 0,
#             "taxAmtA": 0,
#             "taxAmtB": totTaxAmt,
#             "taxAmtC": 0,
#             "taxAmtD": 0,
#             "taxAmtE": 0,
#             "totTaxblAmt": taxblAmtB,
#             "totTaxAmt": totTaxAmt,
#             "totAmt": taxblAmtB,
#             "prchrAcptcYn": "N",
#             "remark": None,
#             "regrId": "Admin",
#             "regrNm": "Admin",
#             "modrId": "Admin",
#             "modrNm": "Admin",
#             "receipt": {
#                 "custTin": instance.customer.customer_pin,
#                 "custMblNo": instance.customer.customer_phone,
#                 "rptNo": instance.receipt_number,
#                 "rcptPbctDt": instance.created_at.strftime("%Y%m%d%H%M%S"),
#                 "trdeNm": "",
#                 "adrs": "",
#                 "topMsg": "Shopwithus",
#                 "btmMsg": "Welcome",
#                 "prchrAcptcYn": "N"
#             },
#             "itemList": [
#                 {
#                     "itemSeq": index + 1,
#                     "itemCd": sale_item.item.itemCd,
#                     "itemClsCd": sale_item.item.item_class_code,
#                     "itemNm": sale_item.item.item_name,
#                     "bcd": None,
#                     "pkgUnitCd": sale_item.item.package_unit_code,
#                     "pkg": 1,
#                     "qtyUnitCd": sale_item.item.quantity_unit_code,
#                     "qty": sale_item.qty,
#                     "prc": sale_item.rate,
#                     "splyAmt": sale_item.line_total,
#                     "dcRt": 0,
#                     "dcAmt": 0,
#                     "isrccCd": None,
#                     "isrccNm": None,
#                     "isrcRt": None,
#                     "isrcAmt": None,
#                     "taxTyCd": sale_item.tax_code,
#                     "taxblAmt": sale_item.taxable_amount,
#                     "taxAmt": sale_item.tax_amount,
#                     "totAmt": sale_item.line_total,
#                 }
#                 for index, sale_item in enumerate(instance.sales_items.all())
#             ]
#         }

#         # Save to API Request Log
#         request_log = APIRequestLog.objects.create(
#             request_type="saveSalesTransaction",
#             request_payload=request_payload,
#             transaction=instance,
#             user=instance.created_by,
#             organization=instance.organization,
#         )

#         # Send request asynchronously using Celery
#         send_api_request.apply_async(args=[request_log.id])
