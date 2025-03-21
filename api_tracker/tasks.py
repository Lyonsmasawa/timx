import os
import requests
import json
import time
import logging
from celery import shared_task
from api_tracker.models import APIRequestLog
from django.conf import settings
from commons.constants import API_ENDPOINTS
from commons.utils import process_import_data, process_purchase_data, replace_nulls, send_vscu_request, update_branches_file, update_constants_file, update_notices_file, update_tax_code_constants_file
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
    from device.models import Device

    request_log = APIRequestLog.objects.get(id=request_id)
    url = API_ENDPOINTS.get(request_log.request_type)

    if not url:
        request_log.mark_failed(
            {"error": f"Unknown API endpoint {request_log.request_type}"})
        return

    # ✅ Retrieve Organization's Active Device
    active_device = Device.objects.filter(
        organization=request_log.organization, active=True
    ).first()

    # ✅ If no active device, fallback to Demo Mode for this Organization
    if not active_device:
        active_device = Device.objects.filter(mode="demo").first()

    try:
        print(f"🔍 Sending request to: {url}")
        print(
            f"📤 Payload: {json.dumps(request_log.request_payload, indent=2)}")
        print(
            f"🖥️ Active Device Details: {vars(active_device) if active_device else 'No active device found'}")

        response = send_vscu_request(
            endpoint=url, method="POST", data=request_log.request_payload,  active_device=active_device)

        # Handle case where response is None
        if response is None:
            error_message = "API request failed, no response received."
            print(f"❌ {error_message}")
            request_log.mark_failed({"error": error_message})
            return

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

            elif request_log.request_type == "updateImports":
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

                import_list = data_content.get("itemList", [])
                # ✅ Ensure it's a list, not a tuple or None
                if not isinstance(import_list, list):
                    logger.error(
                        f"⚠️ Invalid import structure: {json.dumps(data_content, indent=2)}")
                    request_log.mark_failed(
                        {"error": "Invalid import structure"})
                    raise Exception("Invalid import structure")

                if not import_list:
                    logger.warning(
                        f"⚠️ No import data found in response: {json.dumps(response_data, indent=2)}")
                    request_log.mark_failed({
                        "error": "No import data found",
                        "response": response_data
                    })
                    raise Exception("No import data received")

                # ✅ Update `purchases db`
                created_imports = process_import_data(
                    import_list, request_log.organization.id)

                # ✅ Mark the request as successful
                request_log.mark_success({
                    "message": "Imports updated successfully",
                    "response": created_imports
                })
            elif request_log.request_type == "initializeDevice":
                try:
                    data = response_data.get("data", {})
                    Device.objects.filter(tin=request_log.request_payload["tin"]).update(
                        initialized=True,
                        device_id=data.get("deviceId"),
                        control_unit_id=data.get("controlUnitId"),
                        internal_key=data.get("internalKey"),
                        sign_key=data.get("signKey"),
                        communication_key=data.get("communicationKey"),
                        active=True
                    )
                    # Mark the purchase as verified
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
        status__in=["pending", "failed", "retrying"], retries__lt=4)

    for request_log in failed_requests:
        # Increment retry count before re-queuing the request
        request_log.retries += 1
        request_log.status = "retrying"
        request_log.save()  # ✅ Ensure the retry count is updated in the DB
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


@shared_task(bind=True, max_retries=3)
def fetch_and_update_branches(self):
    """
    Celery task to fetch branch lists from the VSCU API and update constants dynamically.
    """
    try:
        # Define request payload
        request_payload = {
            "lastReqDt": "20230118000000"
        }

        # Log API request in the tracker
        request_log = APIRequestLog.objects.create(
            request_type="fetchBranches",
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
            f"📤 Requesting branches with payload: {json.dumps(request_payload, indent=2)}")

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

        branches = data_content.get("bhfList", [])
        # ✅ Ensure it's a list, not a tuple or None
        if not isinstance(branches, list):
            logger.error(
                f"⚠️ Invalid branches structure: {json.dumps(data_content, indent=2)}")
            request_log.mark_failed(
                {"error": "Invalid branches structure"})
            raise Exception("Invalid branches structure")

        if not branches:
            logger.warning(
                f"⚠️ No branches data found in response: {json.dumps(response_data, indent=2)}")
            request_log.mark_failed({
                "error": "No branches data found",
                "response": response_data
            })
            raise Exception("No branches data received")

        # ✅ Extract & format for constants update
        branches_list = [
            replace_nulls({
                "tin": item["tin"],
                # Default to empty if not present
                "bhfId": item.get("bhfId", ""),
                "bhfNm": item["bhfNm"],
                "bhfSttsCd": item.get("bhfSttsCd", ""),
                "prvncNm": item.get("prvncNm", ""),
                "dstrtNm": item.get("dstrtNm", ""),
                "sctrNm": item.get("sctrNm", ""),
                "locDesc": item.get("locDesc", None),
                "mgrNm": item.get("mgrNm", ""),
                "mgrTelNo": item.get("mgrTelNo", ""),
                "mgrEmail": item.get("mgrEmail", ""),
                "hqYn": item["hqYn"]
            })
            for item in branches
        ]

        # ✅ Update `commons/constants.py`
        update_branches_file(branches_list)

        # ✅ Mark the request as successful
        request_log.mark_success({
            "message": "Branches updated successfully",
            "updated_branches": len(branches_list),
            "response": branches_list
        })

        return {"status": "success", "updated_branches": len(branches_list)}

    except Exception as exc:
        # ✅ Save full response data in tracker model
        request_log.mark_retrying()

        raise self.retry(exc=exc, countdown=60)  # Retry after 1 min


@shared_task(bind=True, max_retries=3)
def fetch_and_update_notices(self):
    """
    Celery task to fetch notices from the VSCU API and update constants dynamically.
    """
    try:
        # Define request payload
        request_payload = {
            "lastReqDt": "20231101000000"
        }

        # Log API request in the tracker
        request_log = APIRequestLog.objects.create(
            request_type="fetchNotices",
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
            f"📤 Requesting notices with payload: {json.dumps(request_payload, indent=2)}")

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

        notices = data_content.get("noticeList", [])
        # ✅ Ensure it's a list, not a tuple or None
        if not isinstance(notices, list):
            logger.error(
                f"⚠️ Invalid notices structure: {json.dumps(data_content, indent=2)}")
            request_log.mark_failed(
                {"error": "Invalid notices structure"})
            raise Exception("Invalid notices structure")

        if not notices:
            logger.warning(
                f"⚠️ No notices data found in response: {json.dumps(response_data, indent=2)}")
            request_log.mark_failed({
                "error": "No notices data found",
                "response": response_data
            })
            raise Exception("No notices data received")

        # ✅ Extract & format for constants update
        notices_list = [
            replace_nulls({
                "noticeNo": item["noticeNo"],
                "title": item["title"],
                "content": item["cont"],
                "detailUrl": item["dtlUrl"],
                "registrarName": item["regrNm"],
                "registrationDate": item["regDt"]
            })
            for item in notices
        ]

        # ✅ Update `commons/constants.py`
        update_notices_file(notices_list)

        # ✅ Mark the request as successful
        request_log.mark_success({
            "message": "Branches updated successfully",
            "updated_notices": len(notices_list),
            "response": notices_list
        })

        return {"status": "success", "updated_branches": len(notices_list)}

    except Exception as exc:
        # ✅ Save full response data in tracker model
        request_log.mark_retrying()

        raise self.retry(exc=exc, countdown=60)  # Retry after 1 min


@shared_task(bind=True, max_retries=3)
def fetch_and_update_tax_code(self):
    """
    Celery task to fetch item codes from the VSCU API and update constants dynamically.
    """
    try:
        # Define request payload
        request_payload = {
            "lastReqDt": "20211101000000"
        }
        # Log API request in the tracker
        request_log = APIRequestLog.objects.create(
            request_type="fetchTaxCode",
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
            f"📤 Requesting item codes with payload: {json.dumps(request_payload, indent=2)}")

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

        # ✅ Log response before accessing `itemCodeList`
        data_content = response_data.get("data")
        if not isinstance(data_content, dict):
            logger.error(
                f"⚠️ Unexpected response format: {json.dumps(response_data, indent=2)}")
            request_log.mark_failed({"error": "Invalid response format"})
            raise Exception("Invalid response format")

        item_tax_codes = data_content.get("clsList", [])
        # ✅ Ensure it's a list, not a tuple or None
        if not isinstance(item_tax_codes, list):
            logger.error(
                f"⚠️ Invalid item code structure: {json.dumps(data_content, indent=2)}")
            request_log.mark_failed(
                {"error": "Invalid item code structure"})
            raise Exception("Invalid item code structure")

        if not item_tax_codes:
            logger.warning(
                f"⚠️ No item code data found in response: {json.dumps(response_data, indent=2)}")
            request_log.mark_failed({
                "error": "No item code data found",
                "response": response_data
            })
            raise Exception("No item code data received")

        # ✅ Extract & format for constants update
        item_tax_code_choices = [
            replace_nulls({
                "cdCls": cls["cdCls"],
                "cdClsNm": cls["cdClsNm"],
                "cdClsDesc": cls.get("cdClsDesc", ""),
                "useYn": cls["useYn"],
                "userDfnNm1": cls.get("userDfnNm1", ""),
                "userDfnNm2": cls.get("userDfnNm2", ""),
                "userDfnNm3": cls.get("userDfnNm3", ""),
                "dtlList": [
                    replace_nulls({
                        "cd": dtl["cd"],
                        "cdNm": dtl["cdNm"],
                        "cdDesc": dtl.get("cdDesc", ""),
                        "useYn": dtl["useYn"],
                        "srtOrd": dtl["srtOrd"],
                        "userDfnCd1": dtl.get("userDfnCd1", ""),
                        "userDfnCd2": dtl.get("userDfnCd2", ""),
                        "userDfnCd3": dtl.get("userDfnCd3", "")
                    })
                    for dtl in cls["dtlList"]
                ]
            })
            for cls in item_tax_codes
        ]

        # ✅ Update `commons/constants.py`
        update_tax_code_constants_file(item_tax_code_choices)

        # ✅ Mark the request as successful
        request_log.mark_success({
            "message": "Item code updated successfully",
            "updated_classes": len(item_tax_code_choices),
            "response": item_tax_code_choices
        })

        return {"status": "success", "updated_classes": len(item_tax_code_choices)}

    except Exception as exc:
        # ✅ Save full response data in tracker model
        request_log.mark_retrying()

        raise self.retry(exc=exc, countdown=60)  # Retry after 1 min
