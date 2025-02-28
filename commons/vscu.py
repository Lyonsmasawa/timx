import json
import logging
from django.conf import settings
from commons.constants import API_ENDPOINTS
from commons.utils import send_vscu_request, update_constants_file
from device.models import Device
from api_tracker.models import APIRequestLog
from item.models import Item

logger = logging.getLogger(__name__)


def initialize_vscu_device():
    """
    Initializes the VSCU device at system startup and logs the request.
    """
    tin = settings.VSCU_TIN
    branch_id = settings.VSCU_BRANCH_ID
    device_serial_number = settings.VSCU_DEVICE_SERIAL

    # Check if the device is already initialized
    if Device.objects.filter(tin=tin, branch_id=branch_id, initialized=True).exists():
        logger.info(
            f"✅ VSCU Device {device_serial_number} is already initialized. Skipping initialization.")
        return True

    logger.info("🔄 Initializing VSCU Device...")

    # Prepare payload for API request
    payload = {
        "tin": tin,
        "bhfId": branch_id,
        "dvcSrlNo": device_serial_number
    }

    # Log the API request
    request_log = APIRequestLog.objects.create(
        request_type="initializeDevice",
        request_payload=payload
    )
    

    url = API_ENDPOINTS.get(request_log.request_type)

    # Send request to VSCU API
    response = send_vscu_request(
        endpoint=url,
        method="POST",
        data=request_log.request_payload,
    )
    
    # # Send request to VSCU API
    # response = send_vscu_request(url, payload)

    if response and response.get("resultCd") == "000":
        print (response)
        device, created = Device.objects.get_or_create(
            tin=tin, branch_id=branch_id, device_serial_number=device_serial_number
        )
        device.device_id = response["data"]["info"].get("dvcId")
        device.control_unit_id = response["data"].get("sdcId")
        device.internal_key = response["data"].get("intrlKey")
        device.sign_key = response["data"].get("signKey")
        device.communication_key = response["data"].get("cmcKey")
        device.initialized = True
        device.save()

        # Update the log with the response
        request_log.mark_success(response)
        logger.info(
            f"✅ VSCU Device {device_serial_number} initialized successfully.")
        return True

    # Log failed response
    request_log.mark_failed(response)
    logger.error(f"❌ VSCU Device initialization failed: {response}")
    print (response)
    return False

def register_item_with_vscu(self, item_id):
    """
    Sends item registration data to the VSCU API and logs the request.
    """
    try:
        # Lazy import to avoid circular import
        from item.models import Item

        item = Item.objects.get(id=item_id)
        null = None

        payload = {
            "itemCd": item.itemCd,
            "itemClsCd": item.item_class_code,
            "itemTyCd": item.item_type_code,
            "itemNm": item.item_name,
            "itemStdNm": item.item_name,
            "orgnNatCd": item.origin_nation_code,
            "pkgUnitCd": item.package_unit_code,
            "qtyUnitCd": item.quantity_unit_code,
            "taxTyCd": item.item_tax_code,
            "btchNo": null,
            "bcd": null,
            "dftPrc": float(item.item_opening_balance),
            "grpPrcL1": 0,
            "grpPrcL2": 0,
            "grpPrcL3": 0,
            "grpPrcL4": 0,
            "grpPrcL5": null,
            "addInfo": null,
            "sftyQty": float(item.item_current_balance),
            "isrcAplcbYn": "N",
            "useYn": "Y",
            "regrNm": "Admin",
            "regrId": "Admin",
            "modrNm": "Admin",
            "modrId": "Admin"
        }

        # Create API request log
        request_log = APIRequestLog.objects.create(
            request_type="saveItem",
            request_payload=payload,
            item=item,
            user=item.created_by if hasattr(item, "created_by") else None,
            organization=item.organization if hasattr(
                item, "organization") else None,
        )

        # Log API request
        logger.info(
            f"🔍 Sending item registration request to VSCU API for {item.item_name}")
        logger.debug(
            f"📤 Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

        # Send request
        response = send_vscu_request(
            endpoint="/saveItem", method="POST", data=payload)

        if response and response.status_code == 200:
            request_log.mark_success(response.json())
            logger.info(
                f"✅ Item {item.item_name} registered successfully in VSCU API.")
            return {"status": "success", "message": "Item registered successfully"}
        else:
            request_log.mark_failed(response.json() if response else {
                                    "error": "No response"})
            raise Exception(
                f"API Error: {response.json() if response else 'No response'}")

    except Item.DoesNotExist:
        logger.error(f"❌ Item ID {item_id} not found. Cannot register.")
        return {"status": "error", "message": "Item not found"}

    except Exception as exc:
        logger.error(
            f"❌ Error while registering item: {str(exc)}", exc_info=True)
        request_log.mark_retrying()
        raise self.retry(exc=exc, countdown=60)  # Retry after 1 min
