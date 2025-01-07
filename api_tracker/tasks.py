import requests
import json
import time
from celery import shared_task
from api_tracker.models import APIRequestLog
from commons.vscu import initialize_vscu_device
from django.conf import settings
from commons.constants import API_ENDPOINTS

HEADERS = {
    "Content-Type": "application/json",
    "tin": settings.VSCU_TIN,
    "bhfid": settings.VSCU_BRANCH_ID,
    # "cmcKey": settings.API_KEY,
}

@shared_task(bind=True, max_retries=3)
def async_initialize_vscu_device(self):
    """
    Celery task to initialize the VSCU device asynchronously.
    """
    try:
        request_log = APIRequestLog.objects.create(
            request_type="initializeDevice",
            request_payload={"message": "Initializing VSCU device"}
        )

        result = initialize_vscu_device()
        if not result:
            raise Exception("VSCU Initialization Failed")

        request_log.mark_success({"message": "VSCU initialized successfully"})
        return result

    except Exception as exc:
        request_log.mark_retrying()
        raise self.retry(exc=exc, countdown=5)  # Retry after 5 seconds


@shared_task(bind=True, max_retries=3)
def send_api_request(self, request_id):
    """
    Celery task to send API requests asynchronously.
    Automatically retries up to 3 times with exponential backoff.
    """
    request_log = APIRequestLog.objects.get(id=request_id)
    url = API_ENDPOINTS.get(request_log.request_type)

    if not url:
        request_log.mark_failed({"error": f"Unknown API endpoint {request_log.request_type}"})
        return

    try:
        print(f"🔍 Sending request to: {url}")
        print(f"📤 Payload: {json.dumps(request_log.request_payload, indent=2)}")

        response = requests.post(url, headers=HEADERS, data=json.dumps(request_log.request_payload))
        print(f"📥 Response Status Code: {response.status_code}")
        print(f"📥 Response Content: {response.text}")

        # Handle empty response body
        try:
            response_data = response.json() if response.text else {"message": "No response body"}
        except json.JSONDecodeError:
            response_data = {"error": "Invalid JSON response from API"}

        if response.status_code == 200:
            request_log.mark_success(response_data)
        else:
            raise requests.exceptions.RequestException(f"API returned status {response.status_code}")

    except requests.exceptions.RequestException as exc:
        retry_attempts = self.request.retries + 1
        wait_time = 5 * retry_attempts  # Exponential backoff

        print(f"⚠️Retry {retry_attempts}/3 in {wait_time}s due to error: {exc}")

        if retry_attempts >= 3:
            request_log.mark_failed({"error": str(exc)})
            print(f"❌ API request failed after {retry_attempts} retries. No more attempts.")

        else:
            request_log.mark_retrying()
            raise self.retry(exc=exc, countdown=wait_time)  # Retry with exponential backoff
