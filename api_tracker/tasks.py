import os
import requests
import json
import time
import logging
from celery import shared_task
from api_tracker.models import APIRequestLog
from django.conf import settings
from commons.constants import API_ENDPOINTS
from commons.utils import process_purchase_data, send_vscu_request, update_constants_file
from celery.exceptions import OperationalError

logger = logging.getLogger("vscu_api")


@shared_task(bind=True, max_retries=3)
def async_initialize_vscu_device(self):
    """
    Celery task to initialize the VSCU device asynchronously.
    Uses a delayed import to avoid circular dependency issues.
    """
    try:
        from api_tracker.models import APIRequestLog
        from commons.vscu import initialize_vscu_device

        # Start request log
        request_log = APIRequestLog.objects.create(
            request_type="initializeDevice",
            request_payload={"message": "Initializing VSCU device"}
        )

        # Initialize device
        result = initialize_vscu_device()

        # If initialization failed, raise an exception for retry
        if not result:
            request_log.mark_failed({"error": "VSCU Initialization Failed"})
            raise Exception("VSCU Initialization Failed")

        # Mark success in log
        request_log.mark_success({"message": "VSCU initialized successfully"})
        return result

    except Exception as exc:
        # Mark log as retrying
        request_log.mark_retrying()
        logger.error(f"❌ VSCU Initialization Error: {str(exc)}")

        # Retry the task with exponential backoff
        # Increases delay with each retry
        raise self.retry(exc=exc, countdown=5 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=3)
def fetch_and_update_item_classification(self):
    """
    Celery task to fetch item classifications from the VSCU API and update constants dynamically.
    """
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

        return {"status": "success", "updated_classes": len(item_class_choices)}

    except Exception as exc:
        # ✅ Save full response data in tracker model
        request_log.mark_retrying()

        raise self.retry(exc=exc, countdown=60)  # Retry after 1 min


@shared_task(bind=True, max_retries=3)
def send_api_request(self, request_id):
    """
    Celery task to send API requests asynchronously.
    Automatically retries up to 3 times with exponential backoff.
    """
    request_log = APIRequestLog.objects.get(id=request_id)
    url = API_ENDPOINTS.get(request_log.request_type)

    if not url:
        request_log.mark_failed(
            {"error": f"Unknown API endpoint {request_log.request_type}"})
        return

    try:
        print(f"🔍 Sending request to: {url}")
        print(
            f"📤 Payload: {json.dumps(request_log.request_payload, indent=2)}")

        response = send_vscu_request(
            endpoint=url, method="POST", data=request_log.request_payload)

        print(f"📥 Response Status Code: {response.status_code}")
        print(f"📥 Response Content: {response.text}")

        # Handle empty response body
        try:
            response_data = response.json() if response.text else {
                "message": "No response body"}
        except json.JSONDecodeError:
            response_data = {"error": "Invalid JSON response from API"}

        # Check API success response
        result_code = response_data.get("resultCd")
        result_msg = response_data.get("resultMsg")

        if response.status_code == 200 and result_code == "000" and result_msg == "Successful":
            if request_log.request_type == "updatePurchases":
                # Ensure response is in JSON format
                try:
                    response_data = response.json()
                except ValueError:
                    request_log.mark_failed({"error": "Invalid JSON response"})
                    raise Exception("Invalid JSON response received")

                logger.info(
                    f"📥 Response Content: {json.dumps(response_data, indent=2)}")

                # ✅ Log response before accessing `sales list`
                data_content = response_data.get("data")
                if not isinstance(data_content, dict):
                    logger.error(
                        f"⚠️ Unexpected response format: {json.dumps(response_data, indent=2)}")
                    request_log.mark_failed(
                        {"error": "Invalid response format"})
                    raise Exception("Invalid response format")

                sales_list = data_content.get("saleList", [])
                # ✅ Ensure it's a list, not a tuple or None
                if not isinstance(sales_list, list):
                    logger.error(
                        f"⚠️ Invalid purchase structure: {json.dumps(data_content, indent=2)}")
                    request_log.mark_failed(
                        {"error": "Invalid purchase structure"})
                    raise Exception("Invalid purchase structure")

                if not sales_list:
                    logger.warning(
                        f"⚠️ No purchase data found in response: {json.dumps(response_data, indent=2)}")
                    request_log.mark_failed({
                        "error": "No purchase data found",
                        "response": response_data
                    })
                    raise Exception("No purchase data received")

                # ✅ Update `purchases db`
                created_purchases = process_purchase_data(
                    sales_list, request_log.organization.id)

                # ✅ Mark the request as successful
                request_log.mark_success({
                    "message": "purchases updated successfully",
                    "response": created_purchases
                })

            elif request_log.request_type == "verifyPurchase":
                try:
                    # Mark the purchase as verified
                    request_log.purchase.verified = True
                    request_log.purchase.save()
                    request_log.mark_success(response_data)
                    logger.info(f"✅ Request successful: {response_data}")
                except Exception as e:
                    request_log.mark_failed({"error": str(e)})
                    raise requests.exceptions.RequestException(
                        f"API returned resultCd: {request_log.purchase}, msg: {e}, response: {response_data}")
            else:
                request_log.mark_success(response_data)
                print(f"✅ Request successful: {response_data}")
        else:
            # Mark as failed if response code is not 000
            error_msg = response_data.get("resultMsg", "Unknown error")
            request_log.mark_failed(
                {"error": f"API returned resultCd: {result_code}, msg: {error_msg}, response: {response}"})
            raise requests.exceptions.RequestException(
                f"API returned resultCd: {result_code}, msg: {error_msg}, response: {response}")

    except requests.exceptions.RequestException as exc:
        retry_attempts = self.request.retries + 1
        wait_time = 5 * retry_attempts  # Exponential backoff

        print(
            f"⚠️ Retry {retry_attempts}/3 in {wait_time}s due to error: {exc}")

        if retry_attempts >= 3:
            request_log.mark_failed({"error": str(exc)})
            print(
                f"❌ API request failed after {retry_attempts} retries. No more attempts.")
        else:
            request_log.mark_retrying()
            # Retry with exponential backoff
            raise self.retry(exc=exc, countdown=wait_time)


@shared_task
def retry_failed_requests():
    """
    Retries all pending or failed API requests that have not exceeded the retry limit.
    """
    failed_requests = APIRequestLog.objects.filter(
        status__in=["pending", "failed"], retries__lt=4)

    for request_log in failed_requests:
        wait_time = 5 * (request_log.retries + 1)  # Exponential backoff

        print(
            f"♻️ Retrying request {request_log.id} (Attempt {request_log.retries + 1}/4) in {wait_time}s")

        try:
            send_api_request.apply_async(args=[request_log.id])
        except OperationalError as e:
            print(f"Celery is mot reachable: {e}")  # Retry with delay


@shared_task(bind=True, max_retries=3)
def fetch_and_update_purchases(self, organization):
    """
    Celery task to fetch purchases from the VSCU API and update db dynamically.
    """
    try:
        # Define request payload
        request_payload = {"lastReqDt": "20231010000000"}

        # Log API request in the tracker
        request_log = APIRequestLog.objects.create(
            request_type="updatePurchases",
            request_payload=request_payload,
            organization=organization,
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
            f"📤 Fetch update with payload: {json.dumps(request_payload, indent=2)}")

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

        # ✅ Log response before accessing `sales list`
        data_content = response_data.get("data")
        if not isinstance(data_content, dict):
            logger.error(
                f"⚠️ Unexpected response format: {json.dumps(response_data, indent=2)}")
            request_log.mark_failed({"error": "Invalid response format"})
            raise Exception("Invalid response format")

        sales_list = data_content.get("saleList", [])
        # ✅ Ensure it's a list, not a tuple or None
        if not isinstance(sales_list, list):
            logger.error(
                f"⚠️ Invalid purchase structure: {json.dumps(data_content, indent=2)}")
            request_log.mark_failed(
                {"error": "Invalid purchase structure"})
            raise Exception("Invalid purchase structure")

        if not sales_list:
            logger.warning(
                f"⚠️ No purchase data found in response: {json.dumps(response_data, indent=2)}")
            request_log.mark_failed({
                "error": "No purchase data found",
                "response": response_data
            })
            raise Exception("No purchase data received")

        # ✅ Update `purchases db`
        created_purchases = process_purchase_data(sales_list, organization.id)

        # ✅ Mark the request as successful
        request_log.mark_success({
            "message": "purchases updated successfully",
            "response": created_purchases
        })

        return {"status": "success", "updated_classes": len(created_purchases)}

    except Exception as exc:
        # ✅ Save full response data in tracker model
        request_log.mark_retrying()

        raise self.retry(exc=exc, countdown=60)  # Retry after 1 min
