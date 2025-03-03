from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Device
from organization.models import Organization
from api_tracker.models import APIRequestLog
from api_tracker.tasks import send_api_request
from commons.utils import encrypt_value


@csrf_exempt
def initialize_device(request, organization_id):
    """Initialize the device for an organization in Live Mode."""
    try:
        organization = Organization.objects.get(id=organization_id)

        # Check if a device exists
        device, created = Device.objects.get_or_create(
            organization=organization,
            defaults={"mode": "live"}
        )

        if device.is_initialized():
            return JsonResponse({"success": False, "message": "Device already initialized."}, status=400)

        # Prepare API Request for Device Initialization
        payload = {
            "tin": device.tin,
            "branch_id": device.branch_id,
            "device_serial_number": device.device_serial_number
        }

        # Log API Request
        request_log = APIRequestLog.objects.create(
            request_type="initializeDevice",
            request_payload=payload,
            organization=organization
        )

        # Trigger API Call Asynchronously
        send_api_request.apply_async(args=[request_log.id])

        return JsonResponse({"success": True, "message": "Device initialization started."})

    except Organization.DoesNotExist:
        return JsonResponse({"error": "Organization not found."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def import_device_keys(request, organization_id):
    """Manually import device keys for an organization."""
    try:
        organization = Organization.objects.get(id=organization_id)
        data = json.loads(request.body)

        required_fields = ["device_id", "control_unit_id",
                           "internal_key", "sign_key", "communication_key"]
        if not all(field in data for field in required_fields):
            return JsonResponse({"error": "Missing required fields."}, status=400)

        device, created = Device.objects.get_or_create(
            organization=organization,
            defaults={"mode": "imported"}
        )

        # Store encrypted keys
        device.device_id = encrypt_value(data["device_id"])
        device.control_unit_id = encrypt_value(data["control_unit_id"])
        device.internal_key = encrypt_value(data["internal_key"])
        device.sign_key = encrypt_value(data["sign_key"])
        device.communication_key = encrypt_value(data["communication_key"])
        device.mode = "imported"
        device.initialized = True
        device.save()

        return JsonResponse({"success": True, "message": "Device keys imported securely."})

    except Organization.DoesNotExist:
        return JsonResponse({"error": "Organization not found."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_device_configuration(organization):
    """Returns the appropriate device configuration based on mode."""
    try:
        device = Device.objects.get(organization=organization)

        if device.mode == "live" and device.is_initialized():
            return device.get_decrypted_keys()
        elif device.mode == "imported" and device.is_initialized():
            return device.get_decrypted_keys()
        else:
            return settings.DEFAULT_DEMO_CONFIG  

    except Device.DoesNotExist:
        return settings.DEFAULT_DEMO_CONFIG
