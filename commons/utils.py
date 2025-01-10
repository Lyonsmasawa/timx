import json
import os
from django.db.models import QuerySet
from django.db import transaction
import requests
import logging
from django.conf import settings

from commons.item_classification_constants import ITEM_CLASS_CHOICES


logger = logging.getLogger("vscu_api")


def generate_organization_pin(user):
    """
    Generate a sequential organization pin starting from '0000001'
    unique per user.
    """
    from organization.models import Organization

    # Get the last PIN for the user, ordered by descending organization_pin
    last_pin = (
        Organization.objects.filter(user=user)
        .order_by("-organization_pin")
        .values_list("organization_pin", flat=True)
        .first()
    )
    next_number = int(last_pin) + 1 if last_pin else 1
    return f"{next_number:07d}"


def generate_customer_pin(organization):
    """
    Generate a sequential customer pin starting from '0000001'
    unique per organization.
    """
    from customer.models import Customer

    # Get the last customer pin for the given organization, ordered by descending customer_pin
    last_pin = (
        Customer.objects.filter(organization=organization)
        .order_by("-customer_pin")
        .values_list("customer_pin", flat=True)
        .first()
    )
    next_number = int(last_pin) + 1 if last_pin else 1
    return f"{next_number:07d}"


def generate_item_cd(self):
    """
    Generate a unique item code that includes sequential number specific to
    the country, product type, packaging, and quantity unit.
    """

    from item.models import Item
    country_code = self.origin_nation_code  # e.g., KE for Kenya
    product_type = self.item_type_code  # e.g., 2 for Finished Product
    package_unit = self.package_unit_code  # e.g., NT for NET
    quantity_unit = self.quantity_unit_code  # e.g., BA for Barrel

    # Build the prefix based on the provided fields
    prefix = f"{country_code}{product_type}{package_unit}{quantity_unit}"

    with transaction.atomic():
        # Get the last item's numeric part (last 7 digits) within the organization
        last_item = (
            Item.objects.filter(organization=self.organization)
            # Ignore invalid numeric suffix
            .exclude(itemCd__regex=r"\D{0,}[^0-9]{7}$")
            .order_by('-itemCd')  # Order by `itemCd`
            .first()
        )
        # print(last_item)

        # Extract and increment the numeric part
        if last_item and last_item.itemCd[-7:].isdigit():
            last_number = int(last_item.itemCd[-7:])
        else:
            last_number = 0

        next_number = last_number + 1
        increment = f"{next_number:07d}"  # Ensure zero-padded to 7 digits
        print(increment)
        # Generate the new item code
        return f"{prefix}{increment}"


def get_choices_as_autocomplete(choices, query):
    """Filter and format choices for autocomplete."""
    query = query.lower()
    return [
        {"id": code, "text": name}
        for code, name in choices
        if query in name.lower() or query in code.lower()
    ]


def get_item_class_choices():
    return [(item["itemClsCd"], item["itemClsNm"]) for item in ITEM_CLASS_CHOICES if "itemClsCd" in item and "itemClsNm" in item]


def send_vscu_request(endpoint, method="POST", data=None, headers=None):
    """
    Sends API requests to VSCU and logs EVERYTHING.

    :param endpoint: API endpoint (e.g., "/selectItemClsList")
    :param method: HTTP method (default: POST)
    :param data: Request payload
    :param headers: Additional headers (if needed)
    :return: Response object
    """

    base_url = os.getenv("VSCU_API_BASE_URL", settings.VSCU_API_BASE_URL)
    url = f"{base_url}{endpoint}"

    # Default headers
    default_headers = {
        "Content-Type": "application/json",
        "tin": settings.VSCU_TIN,
        "bhfid": settings.VSCU_BRANCH_ID,
        "cmcKey": os.getenv("VSCU_CMC_KEY"),
    }

    # Merge headers if provided
    if headers:
        default_headers.update(headers)

    try:
        # Log request details
        logger.debug(f"🔍 Sending {method} request to: {url}")
        logger.debug(
            f"📤 Headers: {json.dumps(default_headers, indent=2, ensure_ascii=False)}")
        logger.debug(
            f"📤 Payload: {json.dumps(data, indent=2, ensure_ascii=False)}")

        response = requests.request(
            method=method,
            url=url,
            headers=default_headers,
            json=data,
            timeout=30  # Prevent indefinite hanging
        )

        # Log response details
        logger.info(f"📥 Response Status Code: {response.status_code}")
        logger.info(
            f"📥 Response Content: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

        return response

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request failed: {str(e)}", exc_info=True)
        return None


def update_constants_file(item_classifications):
    """
    Updates `commons/item_classification_constants.py` dynamically with the latest item classification list.
    Ensures it is formatted correctly before writing.
    """
    logger.info(
        f"📝 Attempting to update constants.py with {len(item_classifications)} item classifications...")

    # 🚨 Debugging: Check if the item_classifications list is valid
    if not isinstance(item_classifications, list):
        logger.error(
            f"❌ Invalid data type for item classifications: {type(item_classifications)}")
        return

    if not item_classifications:
        logger.warning(
            "⚠️ No valid item classifications found. Skipping constants update.")
        return

    constants_path = os.path.join(
        settings.BASE_DIR, "commons", "item_classification_constants.py")

    try:
        # ✅ Debug First 5 Items Before Writing
        logger.info(
            f"🔍 First 5 Items (Before Writing to File): {json.dumps(item_classifications[:5], indent=2, ensure_ascii=False)}")

        # ✅ Format list correctly
        formatted_data = json.dumps(
            item_classifications, indent=4, ensure_ascii=False)

        # 🚀 Debug formatted JSON before writing
        # Show first 500 chars
        logger.debug(f"📄 JSON Ready to Write: {formatted_data[:500]}...")

        # ✅ Write to file
        with open(constants_path, "w", encoding="utf-8") as f:
            f.write(f"ITEM_CLASS_CHOICES = {formatted_data}\n")

        logger.info(
            f"✅ Successfully updated constants.py with {len(item_classifications)} items.")

    except Exception as e:
        logger.error(
            f"❌ Failed to update constants.py: {str(e)}", exc_info=True)


def initialize_vscu_device():
    """
    Initialize the VSCU device by calling the API.
    Runs once at system startup.
    """
    from api_tracker.models import APIRequestLog

    url = f"{os.getenv('API_BASE_URL')}/selectInitOsdcInfo"
    print(12345678910)

    headers = {
        "tin": os.getenv("VSCU_TIN"),
        "bhfid": os.getenv("VSCU_BRANCH_ID"),
        "cmcKey": os.getenv("VSCU_CMC_KEY")
    }

    payload = {
        "tin": os.getenv("VSCU_TIN"),
        "bhfId": os.getenv("VSCU_BRANCH_ID"),
        "dvcSrlNo": os.getenv("VSCU_DEVICE_SERIAL")
    }

    request_log = APIRequestLog.objects.create(
        request_type="initializeDevice",
        request_payload=payload
    )

    try:
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()

        if response_data.get("resultCd") == "000":
            request_log.mark_success(response_data)
            return response_data
        else:
            request_log.mark_failed(response_data)
            return None
    except Exception as e:
        request_log.mark_failed({"error": str(e)})
        return None
