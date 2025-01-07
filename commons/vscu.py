import logging
from django.conf import settings
from commons.utils import send_vscu_request
from device.models import Device
from api_tracker.models import APIRequestLog

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
        logger.info(f"✅ VSCU Device {device_serial_number} is already initialized. Skipping initialization.")
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

    # Send request to VSCU API
    response = send_vscu_request("/initializer/selectInitInfo", payload)

    if response and response.get("resultCd") == "000":
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
        logger.info(f"✅ VSCU Device {device_serial_number} initialized successfully.")
        return True

    # Log failed response
    request_log.mark_failed(response)
    logger.error(f"❌ VSCU Device initialization failed: {response}")
    return False
