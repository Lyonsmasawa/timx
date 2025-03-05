import base64
from datetime import datetime
from io import BytesIO
import json
import os
import qrcode
from django.db.models import QuerySet
from django.db import transaction
import requests
import httpx
import logging
from django.conf import settings
from cryptography.fernet import Fernet
import base64
import os
from commons.constants import API_ENDPOINTS
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
        last_items = (
            Item.objects.filter(organization=self.organization)
            # Ignore invalid numeric suffix
            .exclude(itemCd__regex=r"\D{0,}[^0-9]{7}$")
            .order_by('-itemCd')
        )
        # print(last_item)

        # Extract the last 7 digits from all item codes
        existing_numbers = set()
        for item in last_items:
            # Ensure the last 7 digits are numeric
            if item.itemCd[-7:].isdigit():
                existing_numbers.add(int(item.itemCd[-7:]))

        # Find the next available number (starting from 1)
        next_number = 1
        while next_number in existing_numbers:
            next_number += 1

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
            timeout=50  # Prevent indefinite hanging
        )
        
        # with httpx.Client(timeout=50) as client:  # Uses connection pooling
        #     response = client.request(
        #         method=method,
        #         url=url,
        #         headers=default_headers,
        #         json=data
        #     )

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
        purchase_item = response.json()

        if purchase_item.get("resultCd") == "000":
            request_log.mark_success(purchase_item)
            return purchase_item
        else:
            request_log.mark_failed(purchase_item)
            return None
    except Exception as e:
        request_log.mark_failed({"error": str(e)})
        return None


def fetch_and_update_item_classification():
    """
    Celery task to fetch item classifications from the VSCU API and update constants dynamically.
    """
    from api_tracker.models import APIRequestLog

    try:
        # Define request payload
        request_payload = {"lastReqDt": "20221011150845"}

        # Log API request in the tracker
        request_log = APIRequestLog.objects.create(
            request_type="fetchItemClassification",
            request_payload=request_payload
        )

        url = API_ENDPOINTS.get(request_log.request_type)

        # API Call
        response = send_vscu_request(
            endpoint=url,
            method="POST",
            data=request_payload,
        )

        # Log API Request
        logger.info(
            f"📤 Requesting item classifications with payload: {json.dumps(request_payload, indent=2)}")

        # Validate response
        if not response or response.status_code != 200:
            error_msg = f"API Error: {response.text if response else 'No response'}"
            request_log.mark_failed({"error": error_msg})
            raise Exception(error_msg)

        logger.info(f"📥 Response Status Code: {response.status_code}")

        # Ensure response is in JSON format
        try:
            response_data = response.json()
        except ValueError:
            request_log.mark_failed({"error": "Invalid JSON response"})
            raise Exception("Invalid JSON response received")

        logger.info(
            f"📥 Response Content: {json.dumps(response_data, indent=2)}")

        print(f"📥 Response Content: {json.dumps(response_data, indent=2)}")

        # ✅ Log response before accessing `itemClsList`
        data_content = response_data.get("data")
        if not isinstance(data_content, dict):
            logger.error(
                f"⚠️ Unexpected response format: {json.dumps(response_data, indent=2)}")
            request_log.mark_failed({"error": "Invalid response format"})
            raise Exception("Invalid response format")

        item_classifications = data_content.get("itemClsList", [])
        # ✅ Ensure it's a list, not a tuple or None
        if not isinstance(item_classifications, list):
            logger.error(
                f"⚠️ Invalid item classification structure: {json.dumps(data_content, indent=2)}")
            request_log.mark_failed(
                {"error": "Invalid item classification structure"})
            raise Exception("Invalid item classification structure")

        if not item_classifications:
            logger.warning(
                f"⚠️ No item classification data found in response: {json.dumps(response_data, indent=2)}")
            request_log.mark_failed({
                "error": "No item classification data found",
                "response": response_data
            })
            raise Exception("No item classification data received")

        # ✅ Extract & format for constants update
        item_class_choices = [
            {"itemClsCd": item["itemClsCd"],
                "itemClsNm": item["itemClsNm"], "useYn": item["useYn"]}
            for item in item_classifications
        ]

        # ✅ Update `commons/constants.py`
        update_constants_file(item_class_choices)

        # ✅ Mark the request as successful
        request_log.mark_success({
            "message": "Item classification updated successfully",
            "updated_classes": len(item_class_choices),
            "response": item_class_choices
        })

        # return None
        return {"status": "success", "updated_classes": len(item_class_choices)}

    except Exception as exc:
        # ✅ Save full response data in tracker model
        request_log.mark_retrying()
        return None

        # raise retry(exc=exc, countdown=60)  # Retry after 1 min


def fetch_and_imports():
    from api_tracker.models import APIRequestLog

    # Define request payload
    request_payload = {"lastReqDt": "20221011150845"}

    # Log API request in the tracker
    request_log = APIRequestLog.objects.create(
        request_type="fetchImports",
        request_payload=request_payload
    )

    url = API_ENDPOINTS.get(request_log.request_type)

    # API Call
    response = send_vscu_request(
        endpoint=url,
        method="POST",
        data=request_payload,
    )

    try:
        res_item = response.json()

        if res_item.get("resultCd") == "000":
            request_log.mark_success(res_item)
            return res_item
        else:
            request_log.mark_failed(res_item)
            return None

    except Exception as e:
        request_log.mark_failed({"error": str(e)})
        return None


def generate_qr_link(scu_data):
    """Generates a URL link for the SCU receipt verification."""
    rcpt_sign = scu_data.get('rcptSign', '')
    receipt_number = scu_data.get('curRcptNo', '')

    if rcpt_sign and receipt_number:

        # {"resultCd": "000", "resultMsg": "Successful", "resultDt": "20250111211615", "data": {"curRcptNo": 37, "totRcptNo": 37,
        #     "intrlData": "GLNQYR4HJKVXOTVTM5BNKQHHLE", "rcptSign": "TYP7XCALGGWXM44R", "sdcDateTime": "20250111211615"}}
        return f"https://etims.kra.go.ke/common/link/etims/receipt/indexEtimsReceptData?{rcpt_sign}"

    # {KRA-PIN+BHF-ID+RcpSignture)"
    return None


def generate_qr_code(link, transaction_id):
    """
    Generates a QR code from a given link and saves it.
    """
    if not link:
        return None

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(link)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')

    # Save QR Code
    qr_filename = f"qr_{transaction_id}.png"
    qr_path = os.path.join(settings.MEDIA_ROOT,
                           "transaction_qr_codes", qr_filename)

    os.makedirs(os.path.dirname(qr_path), exist_ok=True)
    img.save(qr_path)

    return f"transaction_qr_codes/{qr_filename}"


def generate_qr_code_base64(data):
    """
    Generate a QR code as a base64 string.
    """
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)

    # Save QR code to a BytesIO stream
    img = qr.make_image(fill="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # Encode as base64 string
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    buffer.close()

    return f"data:image/png;base64,{img_base64}"


def intcomma(number):
    """Format numbers with commas and retain two decimal places."""
    try:
        # Convert to float to handle decimals
        number = float(number)
        # Format with commas and two decimal places
        return f"{number:,.2f}"
    except (ValueError, TypeError):
        # Return the number as is if it's invalid
        return number


def process_purchases(purchases_queryset):
    """
    Enrich the purchases queryset with tax summaries and return them as a list of dictionaries.
    """
    enriched_purchases = []
    for purchase in purchases_queryset:
        # print(purchase.payload)
        # Deserialize payload
        payload = purchase.payload

        # Compute tax summary
        tax_summary = compute_tax_summary(payload)

        # Add tax summary to the purchase dict
        purchase_data = {
            "id": purchase.id,
            "verified": purchase.verified,
            "supplier_name": purchase.supplier_name,
            "supplier_tin": purchase.supplier_tin,
            "invoice_number": purchase.invoice_number,
            "confirmation_date": purchase.confirmation_date,
            "total_item_count": purchase.total_item_count,
            "total_taxable_amount": purchase.total_taxable_amount,
            "total_tax_amount": purchase.total_tax_amount,
            "total_amount": purchase.total_amount,
            "items": payload.get("itemList", []),
            "tax_summary": tax_summary,
        }

        enriched_purchases.append(purchase_data)

    return enriched_purchases


def compute_tax_summary(purchase_payload):
    """
    Given a single purchase dict, accumulate taxable amount and tax amount
    by tax type (A, B, C, D, E). 
    """
    # Initialize a structure for each tax type
    # Rates can be adjusted if they differ from your scenario
    tax_summary = {
        'A': {'taxable_amount': 0, 'tax_rate': 0,  'tax_amount': 0},   # Exempt
        # VAT 16%
        'B': {'taxable_amount': 0, 'tax_rate': 16, 'tax_amount': 0},
        'C': {'taxable_amount': 0, 'tax_rate': 0,  'tax_amount': 0},   # Zero Rated
        'D': {'taxable_amount': 0, 'tax_rate': 0,  'tax_amount': 0},   # Non VAT
        'E': {'taxable_amount': 0, 'tax_rate': 8,  'tax_amount': 0},   # VAT 8%
    }

    items = purchase_payload.get('itemList', [])
    for item in items:
        code = item.get('taxTyCd')  # e.g. 'B'
        if code in tax_summary:
            tax_summary[code]['taxable_amount'] += item.get('taxblAmt', 0) or 0
            tax_summary[code]['tax_amount'] += item.get('taxAmt', 0) or 0

    return tax_summary


def process_purchase_data(sales_list, organization_id):
    """
    Process and store purchase data from the API.
    """
    from purchases.models import Purchase
    from django.db import transaction
    from django.utils.dateparse import parse_datetime

    created_purchases = []
    with transaction.atomic():
        for purchase_data in sales_list:
            invoice_number = purchase_data.get("spplrInvcNo")

            # Skip existing invoices
            if Purchase.objects.filter(invoice_number=invoice_number, organization_id=organization_id).exists():
                continue

            # Parse confirmation date
            confirmation_date = parse_datetime(purchase_data.get("cfmDt"))
            if not confirmation_date:
                confirmation_date = purchase_data.get("cfmDt")

            # Create purchase record
            purchase = Purchase.objects.create(
                organization_id=organization_id,
                supplier_name=purchase_data.get("spplrNm", "Unknown Supplier"),
                supplier_tin=purchase_data.get("spplrTin", "N/A"),
                invoice_number=invoice_number,
                confirmation_date=confirmation_date,
                total_item_count=purchase_data.get("totItemCnt", 0),
                total_taxable_amount=purchase_data.get("totTaxblAmt", 0),
                total_tax_amount=purchase_data.get("totTaxAmt", 0),
                total_amount=purchase_data.get("totAmt", 0),
                payload=purchase_data,
            )
            created_purchases.append(purchase)

    return created_purchases


def parse_date(date_str):
    """Convert date from DDMMYYYY format to YYYY-MM-DD."""
    try:
        return datetime.strptime(date_str, "%d%m%Y").strftime("%Y-%m-%d")
    except ValueError:
        return None


def process_import_data(import_list, organization_id):
    """
    Process and store purchase data from the API.
    """
    from imports.models import Import
    from django.db import transaction
    from django.utils.dateparse import parse_datetime

    created_imports = []
    with transaction.atomic():
        for import_data in import_list:
            declaration_number = import_data.get("dclNo")

            # Skip existing invoices
            if Import.objects.filter(declaration_number=declaration_number, organization_id=organization_id).exists():
                continue

            # Parse confirmation date
            confirmation_date = parse_date(import_data.get(
                "dclDe")) or import_data.get("taskCd")

            # Create import record
            import_ = Import.objects.create(
                declaration_date=confirmation_date,
                declaration_number=import_data["dclNo"],
                hs_code=import_data["hsCd"],
                item_name=import_data["itemNm"],
                import_status_code=import_data["imptItemsttsCd"],
                origin_country=import_data["orgnNatCd"],
                export_country=import_data["exptNatCd"],
                package_count=import_data["pkg"],
                package_unit_code=import_data["pkgUnitCd"],
                quantity=import_data["qty"],
                quantity_unit_code=import_data["qtyUnitCd"],
                total_weight=import_data["totWt"],
                net_weight=import_data["netWt"],
                supplier_name=import_data["spplrNm"],
                agent_name=import_data["agntNm"],
                invoice_amount=import_data["invcFcurAmt"],
                invoice_currency=import_data["invcFcurCd"],
                invoice_exchange_rate=import_data["invcFcurExcrt"],
                verified=False,
                payload=import_data,  # Store raw data
            )
            created_imports.append(import_)

    return created_imports


# Generate a secret key if it does not exist (You should securely store this key)
def generate_secret_key():
    return base64.urlsafe_b64encode(os.urandom(32))


# Store the secret key securely (Ideally, in environment variables)
# Use Django's secret key as a base key
SECRET_KEY = settings.ENCRYPTION_SECRET_KEY.encode()
FERNET_KEY = base64.urlsafe_b64encode(SECRET_KEY[:32])  # Ensure 32-byte key

cipher_suite = Fernet(FERNET_KEY)


def encrypt_value(value):
    """Encrypts a string value."""
    if value is None:
        return None
    return cipher_suite.encrypt(value.encode()).decode()


def decrypt_value(value):
    """Decrypts an encrypted string value."""
    if value is None:
        return None
    return cipher_suite.decrypt(value.encode()).decode()
