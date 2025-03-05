from django.http import JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required

from api_tracker.models import APIRequestLog
from api_tracker.tasks import send_api_request
from organization.models import Organization
from .models import Device
import json


@login_required
def get_device_status(request, org_id):
    """
    Fetches the current device configuration for the organization.
    If no device exists, it automatically creates a Demo Mode device using default values.
    """
    try:
        device, created = Device.objects.get_or_create(
            organization_id=org_id,
            defaults={
                "mode": "demo",
                "tin": settings.VSCU_TIN,
                "branch_id": settings.VSCU_BRANCH_ID,
                "device_serial_number": settings.VSCU_DEVICE_SERIAL,
                "initialized": False,
                "communication_key": settings.VSCU_CMC_KEY
            },
        )

        return JsonResponse({
            "mode": device.mode,
            "tin": device.tin,
            "branch_id": device.branch_id,
            "device_serial_number": device.device_serial_number,
            "initialized": device.initialized,
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def set_live_mode(request, org_id):
    """
    Handles switching an organization to live mode by initializing the device.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            tin = data.get("tin")
            bhf_id = data.get("bhfId")
            dvc_srl_no = data.get("dvcSrlNo")

            if not all([tin, bhf_id, dvc_srl_no]):
                return JsonResponse({"error": "All fields are required"}, status=400)

            device, _ = Device.objects.update_or_create(
                organization_id=org_id,
                defaults={
                    "mode": "live",
                    "tin": tin,
                    "branch_id": bhf_id,
                    "device_serial_number": dvc_srl_no,
                    "initialized": True,
                },
            )

            return JsonResponse({"success": True, "message": "Device successfully set to live mode", "device": {
                "tin": device.tin,
                "branch_id": device.branch_id,
                "device_serial_number": device.device_serial_number,
            }})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


@login_required
def import_device_keys(request, org_id):
    """
    Imports manually entered device keys.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            tin = data.get("tin")
            bhf_id = data.get("bhfid")
            cmc_key = data.get("cmcKey")

            if not all([tin, bhf_id, cmc_key]):
                return JsonResponse({"error": "All fields are required"}, status=400)

            device, _ = Device.objects.update_or_create(
                organization_id=org_id,
                defaults={
                    "mode": "imported",
                    "tin": tin,
                    "branch_id": bhf_id,
                    "communication_key": cmc_key,
                    "initialized": True,
                },
            )

            return JsonResponse({"success": True, "message": "Keys imported successfully", "device": {
                "tin": device.tin,
                "branch_id": device.branch_id,
                "device_serial_number": device.device_serial_number,
                "mode": device.mode,
            }})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


@login_required
def switch_to_demo_mode(request, org_id):
    """
    Switches to the existing demo device for an organization.
    If no demo device exists, it creates one.
    """
    try:
        demo_device, created = Device.objects.get_or_create(
            organization_id=org_id, mode="demo",
            defaults={
                "tin": settings.VSCU_TIN,
                "branch_id": settings.VSCU_BRANCH_ID,
                "device_serial_number": settings.VSCU_DEVICE_SERIAL,
                "communication_key": settings.VSCU_CMC_KEY,
            }
        )

        # Mark all devices inactive, then activate the demo device
        Device.objects.filter(organization_id=org_id).update(active=False)
        demo_device.active = True
        demo_device.save()

        return JsonResponse({"success": True, "message": "Switched to Demo Mode!", "device_id": demo_device.id})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def set_active_device(request, device_id):
    """Sets the selected device as active and deactivates others."""
    try:
        device = Device.objects.get(id=device_id)
        device.set_active()
        return JsonResponse({"success": True, "message": "Device activated successfully."})
    except Device.DoesNotExist:
        return JsonResponse({"error": "Device not found."}, status=404)


@login_required
def get_available_devices(request, org_id):
    """
    Returns all available device configurations for an organization.
    """
    try:
        organization = Organization.objects.get(id=org_id, user=request.user)
        devices = Device.objects.filter(organization=organization)

        device_list = [
            {
                "id": device.id,
                "tin": device.tin,
                "branch_id": device.branch_id,
                "device_serial_number": device.device_serial_number,
                "mode": device.mode,
            }
            for device in devices
        ]

        return JsonResponse({"devices": device_list}, status=200)

    except Organization.DoesNotExist:
        return JsonResponse({"error": "Organization not found."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@login_required
def initialize_device(request):
    """
    Initializes a device for an organization and switches it to live mode.
    """
    if request.method == "POST":
        data = json.loads(request.body)

        tin = data.get("tin")
        bhf_id = data.get("bhfId")
        dvc_srl_no = data.get("dvcSrlNo")
        org_id = data.get("organization_id")

        if not all([tin, bhf_id, dvc_srl_no, org_id]):
            return JsonResponse({"error": "Missing required fields"}, status=400)

        try:
            # Deactivate existing devices for the organization
            Device.objects.filter(organization_id=org_id).update(active=False)

            # Create or update the new device
            device, created = Device.objects.update_or_create(
                organization_id=org_id,
                tin=tin,
                defaults={
                    "branch_id": bhf_id,
                    "device_serial_number": dvc_srl_no,
                    "mode": "live",
                    "initialized": False,  # Set to false initially
                    "active": True
                }
            )

            # Send initialization request to API
            request_payload = {"tin": tin,
                               "bhfId": bhf_id, "dvcSrlNo": dvc_srl_no}
            request_log = APIRequestLog.objects.create(
                request_type="initializeDevice",
                request_payload=request_payload,
                organization_id=org_id,
            )

            send_api_request.apply_async(args=[request_log.id])

            return JsonResponse({"success": True, "message": "Device initialization started."})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
