from django.conf import settings
from api_tracker.tasks import send_api_request
from .models import Organization
from django.http import JsonResponse
import json
from django.db.models import Sum
from django.forms import ValidationError
from django.views.decorators.csrf import csrf_exempt
from api_tracker.tasks import fetch_and_update_purchases, send_api_request
from api_tracker.models import APIRequestLog
from django.db import IntegrityError
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
import plotly.graph_objs as go
from api_tracker.models import APIRequestLog
from commons.constants import API_ENDPOINTS, COUNTRY_CHOICES, PACKAGE_CHOICES, PRODUCT_TYPE_CHOICES, TAX_TYPE_CHOICES, TAXPAYER_STATUS_CHOICES, UNIT_CHOICES
from commons.utils import compute_tax_summary, initialize_vscu_device, process_purchases, fetch_and_update_item_classification, fetch_and_imports
from device.models import Device
from imports.models import Import
from item_movement.models import ItemMovement
from purchases.models import Purchase
from .models import Organization
from .forms import OrganizationForm
from item.models import Item
from sales_items.models import SalesItems
from sales_items.forms import SalesItemsForm
from transaction.models import Transaction
from transaction.forms import TransactionForm
from customer.models import Customer
from django.contrib.auth.decorators import login_required
from item.forms import ItemForm
from customer.forms import CustomerForm
from .serializers import OrganizationSerializer
from celery.exceptions import OperationalError
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
# List Organizations


@login_required
def initialize_device_view(request):
    if request.method == "POST":
        success = initialize_vscu_device()
        if success:
            return JsonResponse({"success": True, "message": "VSCU Device initialized successfully!"})
        return JsonResponse({"success": False, "message": "VSCU Device initialization failed."})

    return JsonResponse({"error": "Invalid request method."}, status=405)


@login_required
def fetch_classifications_view(request):
    if request.method == "POST":
        success = fetch_and_update_item_classification()
        if success:
            return JsonResponse({"success": True, "message": "Item Classifications updated successfully!"})
        return JsonResponse({"success": False, "message": "Item Classifications update failed."})

    return JsonResponse({"error": "Invalid request method."}, status=405)


@login_required
def organization_settings(request, organization_id):
    """View to manage organization settings including device configuration."""
    organization = get_object_or_404(Organization, id=organization_id)

    # Fetch the associated device if available
    device = Device.objects.filter(organization=organization).first()

    return render(request, "organization/organization_settings.html", {
        "organization": organization,
        "device": device,
    })


@login_required
def fetch_imports_view(request):
    if request.method == "POST":
        success = fetch_and_imports()
        if success:
            return JsonResponse({"success": True, "message": "Imports updated successfully!"})
        return JsonResponse({"success": False, "message": "Imports update failed."})

    return JsonResponse({"error": "Invalid request method."}, status=405)


# def initialize_device(request, organization_id):
#     """API endpoint to initialize a device for an organization."""
#     if request.method == "POST":
#         organization = Organization.objects.get(id=organization_id)

#         # Simulated API request to initialize device
#         request_payload = {
#             "tin": organization.tin,
#             "branch_id": "00",
#             "device_serial_number": f"dvc{organization.id}99999"
#         }

#         # Log the request in API tracker
#         request_log = APIRequestLog.objects.create(
#             request_type="initializeDevice",
#             request_payload=request_payload,
#             organization=organization,
#         )

#         # Send request to the actual API
#         send_api_request.apply_async(args=[request_log.id])

#         # Create a new Device entry (assumes API will return this data)
#         device = Device.objects.create(
#             organization=organization,
#             tin=request_payload["tin"],
#             branch_id=request_payload["branch_id"],
#             device_serial_number=request_payload["device_serial_number"],
#             initialized=True
#         )

#         return JsonResponse({"message": "Device initialized successfully!", "device_id": device.id})

#     return JsonResponse({"error": "Invalid request method."}, status=400)

@csrf_exempt
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
            device = Device.objects.get(organization_id=org_id)
            device.set_live(tin, bhf_id, dvc_srl_no)

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

        except Device.DoesNotExist:
            return JsonResponse({"error": "Device not found for this organization"}, status=404)


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
def set_active_device(request, org_id, device_id):
    """
    Updates the active device for an organization.
    """
    try:
        organization = Organization.objects.get(id=org_id, user=request.user)
        device = Device.objects.get(id=device_id, organization=organization)

        # Set this device as the active one
        device.mode = "live"
        device.save()

        return JsonResponse({"success": True, "message": "Device activated successfully!"})

    except Organization.DoesNotExist:
        return JsonResponse({"error": "Organization not found."}, status=404)
    except Device.DoesNotExist:
        return JsonResponse({"error": "Device not found."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def organization_list(request):
    try:
        if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
            form = OrganizationForm(request.POST)
            if form.is_valid():
                try:
                    organization = form.save(user=request.user)
                except IntegrityError as e:
                    error_msg = str(e)

                    unique_fields = {
                        'organization_pin': 'The organization pin must be unique.',
                        'organization_name': 'The organization name must be unique.',
                    }

                    for field, message in unique_fields.items():
                        if field in error_msg:
                            return JsonResponse({
                                'success': False,
                                'errors': {field: [message]}
                            })

                    return JsonResponse({
                        'success': False,
                        'errors': {'general': 'An integrity error occurred. Please try again.'}
                    })

                except Exception as e:
                    # Catch any other errors
                    return JsonResponse({
                        'success': False,
                        'errors': {'general': f'An error occurred: {str(e)}'}
                    })

                return JsonResponse({
                    'success': True,
                    'organization_id': organization.id,
                    'organization_name': organization.organization_name,
                    'organization_created_at': organization.created_at,
                    'organization_pin': organization.organization_pin,
                    'organization_email': organization.organization_email,
                    'organization_physical_address': organization.organization_physical_address,
                    'organization_phone': organization.organization_phone,
                    'organization_detail_url': reverse('organization:organization_detail', args=[organization.id]),
                    'organization_update_url': reverse('organization:organization_update', args=[organization.id]),
                    'organization_delete_url': reverse('organization:organization_delete', args=[organization.id])
                })
            print(form.errors)
            return JsonResponse({"success": False, "errors": form.errors})

        # Handle GET request (list organizations)
        organizations = Organization.objects.filter(user=request.user)
        print(organizations)
        form = OrganizationForm()
        return render(
            request,
            "organization/organization_list.html",
            {"organizations": organizations, "form": form}
        )
    except Exception as e:
        # messages.error(request, f"An error occurred: {str(e)}")
        return JsonResponse({"success": False, "errors": str(e)})

# Create Organization


@login_required
def organization_create(request):
    if request.method == "POST":
        form = OrganizationForm(request.POST)
        if form.is_valid():
            try:
                organization = form.save(commit=False)
                organization.user = request.user
                organization.save()

                messages.success(request, "Organization created successfully!")

                # Get the organization based on the primary key
                organization = get_object_or_404(
                    Organization, pk=organization.id)

                # Get all items, customers, and transactions related to the organization
                items = Item.objects.filter(organization=organization)
                customers = Customer.objects.filter(organization=organization)
                transactions = Transaction.objects.filter(
                    organization=organization)

                return render(request, "organization/organization_detail.html", {
                    "organization": organization,
                    "items": items,
                    "customers": customers,
                    "transactions": transactions,
                })
            except Exception as e:
                # messages.error(request, f"An error occurred while creating the organization: {str(e)}")
                return JsonResponse({
                    'success': False,
                    'errors': {'general': f'An error occurred while creating the organization'}
                })
                # return redirect("organization:organization_create")
        else:
            return JsonResponse({"success": False, "errors": form.errors})

    else:
        form = OrganizationForm()
    return render(request, "organization/organization_form.html", {"form": form})

# Detail View


@login_required
def organization_detail(request, pk):
    try:
        organization = get_object_or_404(Organization, pk=pk)
        # Querysets for related objects
        items = Item.objects.select_related("organization").filter(
            organization=organization).order_by('-created_at')
        customers = Customer.objects.select_related("organization").filter(
            organization=organization).order_by('-created_at')

        # Separate invoices and credit notes
        invoices = Transaction.objects.select_related("organization").filter(
            organization=organization, document_type="invoice").order_by('-created_at')
        credit_notes = Transaction.objects.select_related("organization").filter(
            organization=organization, document_type="credit_note").order_by('-created_at')
        purchases_data = Purchase.objects.select_related("organization").filter(
            organization=organization).order_by('-created_at')
        purchases = process_purchases(purchases_data)
        imports = Import.objects.select_related("organization").filter(
            organization=organization).order_by('-created_at')

        imports_ = [
            {
                "id": 1,
                "task_code": "20230209023992",
                "declaration_date": "2023-02-01",
                "item_sequence": 1,
                "declaration_number": "23NBOIM401167364",
                "hs_code": "63079000",
                "item_name": "ORANGES",
                "import_status_code": "2",
                "origin_country": "DE",
                "export_country": "DE",
                "package_count": 17,
                "package_unit_code": "KGM",
                "quantity": 14,
                "quantity_unit_code": "KGM",
                "total_weight": 140,
                "net_weight": 14,
                "supplier_name": "SEITZ GMGH",
                "agent_name": "SCHENKER LIMITED",
                "invoice_amount": 11817.5,
                "invoice_currency": "EUR",
                "invoice_exchange_rate": 135.73,
                "verified": False,
                "organization_id": 1,
                "created_at": "2025-02-26T17:37:38Z"
            },
            # {
            #     "id": 2,
            #     "task_code": "20230209023991",
            #     "declaration_date": "2023-02-01",
            #     "item_sequence": 1,
            #     "declaration_number": "23NBOIM401167364",
            #     "hs_code": "63079000",
            #     "item_name": "ORANGES",
            #     "import_status_code": "2",
            #     "origin_country": "DE",
            #     "export_country": "DE",
            #     "package_count": 17,
            #     "package_unit_code": "KGM",
            #     "quantity": 14,
            #     "quantity_unit_code": "KGM",
            #     "total_weight": 140,
            #     "net_weight": 14,
            #     "supplier_name": "SEITZ GMGH",
            #     "agent_name": "SCHENKER LIMITED",
            #     "invoice_amount": 11817.5,
            #     "invoice_currency": "EUR",
            #     "invoice_exchange_rate": 135.73,
            #     "verified": False,
            #     "organization_id": 1,
            #     "created_at": "2025-02-26T17:37:38Z"
            # }
        ]

        # Fetch latest API status for each item, customer, and transaction
        item_statuses = {log.item.id: {"id": log.id, "status": log.status} for log in APIRequestLog.objects.filter(
            item__organization=organization)}

        customer_statuses = {log.customer.id: {"id": log.id, "status": log.status} for log in APIRequestLog.objects.filter(
            customer__organization=organization, request_type="saveCustomer")}

        transaction_statuses = {log.transaction.id: {"id": log.id, "status": log.status} for log in APIRequestLog.objects.filter(
            transaction__organization=organization)}

        purchases_statuses = {log.purchase.id: {"id": log.id, "status": log.status} for log in APIRequestLog.objects.filter(
            purchase__organization=organization, request_type="verifyPurchase")}

        if request.method == 'POST':
            action_name = request.POST.get('action_name')

            if not action_name:
                return JsonResponse({'success': False, 'error': 'No action specified.'})

        else:
            # Initialize forms for GET request
            item_form = ItemForm()
            customer_form = CustomerForm()
            transaction_form = TransactionForm()
            customer_form = CustomerForm()
            transaction_form = TransactionForm()
            sales_items_form = SalesItemsForm()

        # print(f" Customer, {customer_statuses}")
        # print(f" Items, {item_statuses}")
        # print(f" Transaction, {transaction_statuses}")
        # print(f"Imports {imports_}")

        # Render the page for regular requests
        return render(request, "organization/organization_detail.html", {
            "organization": organization,
            "items": items,
            "customers": customers,
            "invoices": invoices,
            "credit_notes": credit_notes,
            "imports": imports,
            "imports_s": imports_,
            "item_statuses": item_statuses,
            "customer_statuses": customer_statuses,
            "transaction_statuses": transaction_statuses,
            'purchases_statuses':  purchases_statuses,
            "item_form": item_form,
            "customer_form": customer_form,
            "transaction_form": transaction_form,
            "sales_items_form": sales_items_form,
            'COUNTRY_CHOICES': COUNTRY_CHOICES,
            'PRODUCT_TYPE_CHOICES': PRODUCT_TYPE_CHOICES,
            'UNIT_CHOICES': UNIT_CHOICES,
            'PACKAGE_CHOICES': PACKAGE_CHOICES,
            'TAXPAYER_STATUS_CHOICES': TAXPAYER_STATUS_CHOICES,
            'TAX_TYPE_CHOICES': TAX_TYPE_CHOICES,
            'purchases': purchases,
        })

    except Exception as e:
        # Log the error and stay on the page
        print(f"Error in organization_detail view: {str(e)}")
        # messages.error(request, "An unexpected error occurred. Please try again later.")
        return render(request, "organization/organization_detail.html", {
            "organization": organization,
            "items": items,
            "customers": customers,
            "invoices": [],
            "credit_notes": [],
            "item_form": ItemForm(),
            "customer_form": CustomerForm(),
            "transaction_form": TransactionForm(),
            "sales_items_form": SalesItemsForm(),
        })


# Update Organization
@login_required
def organization_update(request, pk):
    organization = get_object_or_404(Organization, pk=pk)

    if request.method == "POST":
        # Create a dictionary to track updates
        updates = {}

        # Iterate through the submitted data and update only changed fields
        for field, value in request.POST.items():
            if field in ['csrfmiddlewaretoken']:
                continue  # Skip CSRF token field

            # Check if the submitted value is different from the current value
            current_value = getattr(organization, field, None)
            if current_value != value and value.strip() != "":
                updates[field] = value

        if updates:
            try:
                # Update the organization with the modified fields
                for field, value in updates.items():
                    setattr(organization, field, value)
                organization.save()
                return JsonResponse({'success': True, 'message': "Organization updated successfully."})
            except Exception as e:
                return JsonResponse({'success': False, 'errors': {'general': [f"An error occurred: {str(e)}"]}})
        else:
            return JsonResponse({'success': True, 'message': "No changes detected."})

    return JsonResponse({'success': False, 'errors': {'general': ["Invalid request method."]}})

# Delete Organization


@login_required
def organization_delete(request, pk):
    try:
        organization = get_object_or_404(Organization, pk=pk)
        organization.delete()
        messages.success(request, "Organization deleted successfully!")
        return redirect("organization:organization_list")
    except Exception as e:
        messages.error(
            request, f"An error occurred while deleting the organization: {str(e)}")
        return redirect("organization:organization_list")


@login_required
# View to get customers for the select dropdown
def get_customers(request):
    customers = Customer.objects.all()
    customer_data = [{'id': customer.id, 'name': customer.name}
                     for customer in customers]
    return JsonResponse({'customers': customer_data})


def download_invoice(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)
    if not transaction.document_path:
        # Redirect to invoice detail view
        return redirect('invoice_detail', pk)

    with open(transaction.document_path, 'rb') as pdf_file:
        response = HttpResponse(
            pdf_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename=invoice_{pk}.pdf'
        return response


@csrf_exempt
def retry_failed_request(request, request_type, request_id):
    if request.method == "POST":
        try:
            # ✅ Parse JSON data from request body
            data = json.loads(request.body.decode("utf-8"))
            log_id = data.get("log_id")

            if not log_id:
                return JsonResponse({"error": "Missing log_id in request."}, status=400)

            # ✅ Retrieve the request log
            request_log = APIRequestLog.objects.get(pk=log_id, status="failed")

            # ✅ Retry the request using Celery
            try:
                send_api_request.apply_async(args=[request_log.id])
            except OperationalError as e:
                # Log the error and allow the application to proceed
                print(f"Celery is not reachable: {e}")

            # ✅ Update status to retrying
            request_log.retries = 0
            request_log.mark_retrying()
            request_log.save()

            return JsonResponse({"success": True, "message": f"Retry for {request_type} initiated successfully!"})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)

        except APIRequestLog.DoesNotExist:
            return JsonResponse({"error": f"{request_type.capitalize()} request not found or not failed."}, status=404)

    return JsonResponse({"error": "Invalid request method."}, status=405)


@login_required
def update_purchases_view(request, org_id):
    try:
        try:
            organization = Organization.objects.get(
                id=org_id, user=request.user)
        except Organization.DoesNotExist:
            return JsonResponse({"error": "Organization not found."}, status=404)

        # Define request payload
        request_payload = {"lastReqDt": "20231010000000"}

        # Log API request in the tracker
        request_log = APIRequestLog.objects.create(
            request_type="updatePurchases",
            request_payload=request_payload,
            organization=organization,
        )

        # ✅ Retry the request using Celery
        try:
            send_api_request.apply_async(args=[request_log.id])
        except OperationalError as e:
            # Log the error and allow the application to proceed
            print(f"Celery is not reachable: {e}")

        return JsonResponse({"success": True, "message": "Purchase update initiated"}, status=200)
    except AttributeError:
        return JsonResponse({"error": "User is not associated with an organization"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
def verify_purchase(request, request_type, inv_no, purchase_id):
    if request.method == "POST":
        try:
            # ✅ Parse JSON data from request body
            # data = json.loads(request.body.decode("utf-8"))
            # invoice_number = data.get("invoice_number")

            if not purchase_id:
                return JsonResponse({"error": "Missing id in request."}, status=400)

            # ✅ Retrieve the request log

            try:
                purchase = Purchase.objects.get(
                    pk=purchase_id, invoice_number=inv_no)
            except Purchase.DoesNotExist:
                return JsonResponse({"error": "Purchase not found."}, status=404)

            purchase.payload.update({
                "modrId": "Admin",
                "modrNm": "Admin",
                "regrId": "Admin",
                "regrNm": "Admin",
                "regTyCd": "M",
                "invcNo": purchase.payload.get("spplrInvcNo"),
                "orgInvcNo": 0,
                "rcptTyCd": "P",
                "pchsTyCd": "N",
                "pchsSttsCd": "02",
                "pchsDt": purchase.payload.get("salesDt", "")
            })

            # Swap cfmDt and stockRlsDt
            cfmDt_value = purchase.payload.get("cfmDt")
            stockRlsDt_value = purchase.payload.get("stockRlsDt")
            purchase.payload["cfmDt"] = stockRlsDt_value if stockRlsDt_value is not None else ""
            purchase.payload["stockRlsDt"] = cfmDt_value if cfmDt_value is not None else ""

            # Replace null values with empty strings
            for key, value in purchase.payload.items():
                if value is None:
                    purchase.payload[key] = ""

            # payload = json.dumps(purchase.payload)

            # ✅ Save API Request Log
            request_log = APIRequestLog.objects.create(
                request_type="verifyPurchase",
                request_payload=purchase.payload,
                user=request.user,
                purchase=purchase,
                organization=purchase.organization,
            )

            # ✅ Send request asynchronously using Celery
            try:
                send_api_request.apply_async(args=[request_log.id])
            except OperationalError as e:
                print(f"Celery is mot reachable: {e}")

            return JsonResponse({"success": True, "message": f"Retry for {request_log.request_type} initiated successfully!"})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)

        except APIRequestLog.DoesNotExist:
            return JsonResponse({"error": f"{request_type.capitalize()} request not found or not failed."}, status=404)

    return JsonResponse({"error": "Invalid request method."}, status=405)


@login_required
def update_imports_view(request, org_id):
    print(request)
    try:
        try:
            organization = Organization.objects.get(
                id=org_id, user=request.user)
        except Organization.DoesNotExist:
            return JsonResponse({"error": "Organization not found."}, status=404)

        # Define request payload
        request_payload = {"lastReqDt": "20231010000000"}
        print(request_payload)

        # Log API request in the tracker
        request_log = APIRequestLog.objects.create(
            request_type="updateImports",
            request_payload=request_payload,
            organization=organization,
        )

        # ✅ Retry the request using Celery
        try:
            send_api_request.apply_async(args=[request_log.id])
        except OperationalError as e:
            # Log the error and allow the application to proceed
            print(f"Celery is not reachable: {e}")

        return JsonResponse({"success": True, "message": "Import update initiated"}, status=200)
    except AttributeError:
        return JsonResponse({"error": "User is not associated with an organization"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# class OrganizationViewSet(viewsets.ModelViewSet):
#     queryset = Organization.objects.all()
#     serializer_class = OrganizationSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return self.queryset.filter(user=self.request.user)

#     def perform_create(self, serializer):
#         organization = serializer.save()
#         organization.user.add(self.request.user)
#         return organization

#     def perform_update(self, serializer):
#         try:
#             serializer.save()
#         except ValidationError as e:
#             print(f"Validation Error: {e}")
#             # 🔹 Ensure this raises an error
#             raise ValidationError({"error": str(e)})
#         except Exception as e:
#             print(f"Unexpected Error: {e}")
#             # 🔹 Raise ValidationError to return JSON response
#             raise ValidationError({"error": "An unexpected error occurred."})


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def retry_failed_request(request, request_type, request_id):
#     try:
#         request_log = APIRequestLog.objects.get(pk=request_id, status="failed")
#         send_api_request.apply_async(args=[request_log.id])
#         request_log.retries = 0
#         request_log.mark_retrying()
#         request_log.save()
#         return JsonResponse({"success": True, "message": f"Retry for {request_type} initiated successfully!"})
#     except APIRequestLog.DoesNotExist:
#         return JsonResponse({"error": "Request not found or not failed."}, status=404)


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def update_purchases_view_api(request, org_id):
#     try:
#         organization = get_object_or_404(
#             Organization, id=org_id, user=request.user)
#         request_payload = {"lastReqDt": "20231010000000"}
#         request_log = APIRequestLog.objects.create(
#             request_type="updatePurchases",
#             request_payload=request_payload,
#             organization=organization,
#         )
#         send_api_request.apply_async(args=[request_log.id])
#         return JsonResponse({"success": True, "message": "Purchase update initiated"}, status=200)
#     except Exception as e:
#         return JsonResponse({"success": False, "error": str(e)}, status=500)


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def verify_purchase_api(request, request_type, inv_no, purchase_id):
#     try:
#         purchase = get_object_or_404(
#             Purchase, pk=purchase_id, invoice_number=inv_no)
#         purchase.payload["modrId"] = "Admin"
#         purchase.payload["modrNm"] = "Admin"
#         purchase.payload["pchsSttsCd"] = "02"
#         request_log = APIRequestLog.objects.create(
#             request_type="verifyPurchase",
#             request_payload=purchase.payload,
#             user=request.user,
#             purchase=purchase,
#             organization=purchase.organization,
#         )
#         send_api_request.apply_async(args=[request_log.id])
#         return JsonResponse({"success": True, "message": "Verification initiated successfully!"})
#     except Purchase.DoesNotExist:
#         return JsonResponse({"error": "Purchase not found."}, status=404)
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)
