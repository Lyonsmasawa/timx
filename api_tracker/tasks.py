import requests
import json
from celery import shared_task
from api_tracker.models import APIRequestLog
from django.conf import settings
from commons.constants import API_ENDPOINTS

HEADERS = {
    "Content-Type": "application/json",
    "tin": settings.TAXPAYER_TIN,
    "bhfid": settings.BRANCH_ID,
    "cmcKey": settings.API_KEY,
}

@shared_task(bind=True, max_retries=3)
def send_api_request(self, request_id):
    """
    Celery task to send API requests asynchronously.
    Automatically retries up to 3 times if it fails.
    """
    request_log = APIRequestLog.objects.get(id=request_id)
    url = API_ENDPOINTS.get(request_log.request_type)

    if not url:
        request_log.mark_failed({"error": f"Unknown API endpoint {request_log.request_type}"})
        return

    try:
        response = requests.post(url, headers=HEADERS, data=json.dumps(request_log.request_payload))
        response_data = response.json()

        if response.status_code == 200:
            request_log.mark_success(response_data)
        else:
            request_log.mark_failed(response_data)

    except requests.exceptions.RequestException as exc:
        request_log.mark_retrying()
        raise self.retry(exc=exc, countdown=5)  # Retry after 5 seconds
