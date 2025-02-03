from collections import defaultdict
from datetime import datetime
from decimal import Decimal
import json
from django.http import HttpResponse
import os
from weasyprint import HTML
from django.template.loader import render_to_string
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.mail import send_mail
from api_tracker.models import APIRequestLog
from api_tracker.tasks import send_api_request
from commons.constants import TAX_RATES
from commons.utils import generate_qr_code, generate_qr_code_base64, generate_qr_link, intcomma
from item_movement.models import ItemMovement
from organization.models import Organization
from transaction.models import Transaction
from .models import SalesItems
from transaction.forms import TransactionForm
from .forms import SalesItemsForm
from customer.models import Customer
from item.models import Item
from django.conf import settings
from django.contrib import messages
from django.db import transaction as transaction_mode
from dal import autocomplete
from celery.exceptions import OperationalError
# List Sales Items


def sales_items_list(request):
    try:
        sales_items = SalesItems.objects.select_related(
            'transaction', 'item').all()
        return render(request, "sales_items_list.html", {"sales_items": sales_items})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# Create Sales Item


def sales_items_create(request, pk):
    organization = get_object_or_404(Organization, pk=pk)

    if request.method == 'POST':
        try:
            invoice_data = json.loads(request.body.decode('utf-8'))
            print(invoice_data)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)

        # Get customer
        try:
            customer = Customer.objects.get(
                pk=invoice_data['customerId'], customer_pin=invoice_data['customerPin'], organization=organization)
        except Customer.DoesNotExist:
            return JsonResponse({"error": "Customer not found"}, status=404)

        try:
            with transaction_mode.atomic():
                # Create Transaction
                transaction = Transaction.objects.create(
                    organization=organization,
                    customer=customer,
                    receipt_number=invoice_data['invoiceNumber'],
                    original_receipt_number=invoice_data['invoiceNumber'],
                    document_type="invoice",
                    created_by=request.user
                )

                sales_items_list = []
                # Track totals per tax type
                tax_totals = defaultdict(
                    lambda: {"taxable_amount": 0, "tax_amount": 0})
                total_line_items_amount = 0

                # Create SalesItems
                for item in invoice_data['items']:
                    try:
                        item_obj = Item.objects.get(pk=item['itemId'])
                    except Item.DoesNotExist:
                        return JsonResponse({"error": f"Item with ID {item['itemId']} not found"}, status=404)

                    if item['quantity'] <= 0 or item['rate'] <= 0 or item['lineTotal'] < 0:
                        return JsonResponse({"error": "Invalid item details"}, status=400)

                    # Normalize tax code (A, B, C, D, E)
                    tax_code = item['taxCode'].upper()

                    taxable_amount = round(
                        (float(item["quantity"]) * float(item["rate"])) - float(item['discount']), 2)
                    tax_rate = TAX_RATES.get(tax_code, 0)
                    tax_amount = (taxable_amount * tax_rate) / \
                        100  # Calculate tax

                    total_line_items_amount += round(
                        float(item["lineTotal"]), 2)

                    # Store taxable amount & tax amount based on tax code
                    tax_totals[tax_code]["taxable_amount"] += taxable_amount
                    tax_totals[tax_code]["tax_amount"] += tax_amount

                    # Create Sales Item
                    sales_item = SalesItems.objects.create(
                        transaction=transaction,
                        created_by=request.user,
                        item=item_obj,
                        item_description=item['description'],
                        qty=item['quantity'],
                        rate=item['rate'],
                        discount_rate=item['discount'],
                        discount_amount=item['discount'],
                        tax_code=item['taxCode'],
                        line_total=item['lineTotal'],
                    )

                    # Update Item Movement
                    ItemMovement.objects.create(
                        item=item_obj,
                        movement_type='REMOVE',
                        movement_reason='Sale',
                        item_unit=item['quantity'],
                    )

                    # Update Item's current balance by subtracting the quantity sold
                    if item_obj.item_current_balance < item['quantity']:
                        messages.error(
                            request, f"Insufficient stock for item {item['itemId']}")
                        return JsonResponse({"error": f"Insufficient stock for item {item['itemId']}"}, status=400)

                    item_obj.item_current_balance -= item['quantity']
                    item_obj.save()  # Save the updated balance

                    sales_items_list.append(sales_item)

                print(sales_items_list)
                # Compute final totals
                total_taxable_amount = sum(
                    tax["taxable_amount"] for tax in tax_totals.values())
                total_tax_amount = sum(tax["tax_amount"]
                                       for tax in tax_totals.values())

                # Step 3: Generate the API Request Payload
                request_payload = {
                    "invcNo": str(transaction.receipt_number),
                    "orgInvcNo": str(transaction.original_receipt_number) if transaction.original_receipt_number else str(transaction.receipt_number),
                    "custTin": transaction.customer.customer_pin,
                    "custNm": transaction.customer.customer_name,
                    "salesTyCd": "N",
                    "rcptTyCd": "S",
                    "pmtTyCd": "01",
                    "salesSttsCd": "02",
                    "cfmDt": transaction.created_at.strftime("%Y%m%d%H%M%S"),
                    "salesDt": transaction.created_at.strftime("%Y%m%d"),
                    "stockRlsDt": transaction.created_at.strftime("%Y%m%d%H%M%S"),
                    "totItemCnt": len(sales_items_list),
                    "taxblAmtA": tax_totals["A"]["taxable_amount"],
                    "taxblAmtB": tax_totals["B"]["taxable_amount"],
                    "taxblAmtC": tax_totals["C"]["taxable_amount"],
                    "taxblAmtD": tax_totals["D"]["taxable_amount"],
                    "taxblAmtE": tax_totals["E"]["taxable_amount"],
                    "taxRtA": TAX_RATES["A"],
                    "taxRtB": TAX_RATES["B"],
                    "taxRtC": TAX_RATES["C"],
                    "taxRtD": TAX_RATES["D"],
                    "taxRtE": TAX_RATES["E"],
                    "taxAmtA": tax_totals["A"]["tax_amount"],
                    "taxAmtB": tax_totals["B"]["tax_amount"],
                    "taxAmtC": tax_totals["C"]["tax_amount"],
                    "taxAmtD": tax_totals["D"]["tax_amount"],
                    "taxAmtE": tax_totals["E"]["tax_amount"],
                    "totTaxblAmt": total_taxable_amount,
                    "totTaxAmt": total_tax_amount,
                    "totAmt": total_line_items_amount,
                    "totItemCnt": len(sales_items_list),
                    "prchrAcptcYn": "N",
                    "remark": None,
                    "regrId": "Admin",
                    "regrNm": "Admin",
                    "modrId": "Admin",
                    "modrNm": "Admin",
                    "receipt": {
                        "custTin": transaction.customer.customer_pin,
                        "custMblNo": transaction.customer.customer_phone,
                        "rptNo": str(transaction.receipt_number),
                        "rcptPbctDt": transaction.created_at.strftime("%Y%m%d%H%M%S"),
                        "topMsg": "Shopwithus",
                        "btmMsg": "Welcome",
                        "prchrAcptcYn": "N"
                    },
                    "itemList": [
                        {
                            "itemSeq": index + 1,
                            "itemCd": sale_item.item.itemCd,
                            "itemClsCd": sale_item.item.item_class_code,
                            "itemNm": sale_item.item.item_name,
                            "bcd": None,
                            "pkgUnitCd": sale_item.item.package_unit_code,
                            "pkg": 1,
                            "qtyUnitCd": sale_item.item.quantity_unit_code,
                            "qty": sale_item.qty,
                            "prc": float(sale_item.rate),
                            "splyAmt": round(float(sale_item.line_total) - ((TAX_RATES.get(sale_item.tax_code, 0) / 100) * float(sale_item.line_total)), 2),
                            "dcRt": round(float(sale_item.discount_rate) if sale_item.discount_rate else 0.0, 2),
                            "dcAmt": round(float(sale_item.discount_amount) if sale_item.discount_amount else 0.0, 2),
                            "isrccCd": None,
                            "isrccNm": None,
                            "isrcRt": None,
                            "isrcAmt": None,
                            "taxTyCd": sale_item.tax_code,
                            "taxblAmt": round(float(sale_item.line_total) - ((TAX_RATES.get(sale_item.tax_code, 0) / 100) * float(sale_item.line_total)), 2),
                            "taxAmt": round(float(sale_item.line_total) - float(sale_item.line_total) / (1 + (TAX_RATES.get(sale_item.tax_code, 0) / 100)), 2),
                            "totAmt": round(float(sale_item.line_total), 2),
                        }
                        for index, sale_item in enumerate(sales_items_list)
                    ]
                }

                print(request_payload)

                # ✅ Save API Request Log
                request_log = APIRequestLog.objects.create(
                    request_type="saveSalesTransaction",
                    request_payload=request_payload,
                    transaction=transaction,
                    user=request.user,
                    organization=transaction.organization,
                )

                # ✅ Send request asynchronously using Celery
                try:
                    send_api_request.apply_async(args=[request_log.id])
                    return JsonResponse({'success': True, 'data': "Processing request"})
                except OperationalError as e:
                    print(f"Celery is mot reachable: {e}")
                    return JsonResponse({'success': True, 'data': "Processing request"})

                # # Step 3: Generate the PDF Invoice and get the file path
                # pdf_path = generate_transaction_pdf(
                #     organization, transaction, customer, sales_items_list, invoice_data, "invoice")

                # # Open and send the PDF as a response to auto-download
                # with open(pdf_path, "rb") as pdf_file:
                #     response = HttpResponse(
                #         pdf_file.read(), content_type='application/pdf')
                #     response['Content-Disposition'] = f'attachment; filename="invoice_{transaction.receipt_number}.pdf"'
                #     return response

        except Exception as e:
            # messages.error(request, f"An error occurred: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

    else:  # GET method
        items = Item.objects.filter(organization=organization)
        customers = Customer.objects.filter(organization=organization)
        transaction_form = TransactionForm()
        sales_items_form = SalesItemsForm()

        # Calculate the invoice number based on transactions count
        invoice_number = Transaction.objects.filter(
            organization=organization
        ).count() + 1

        # Format the invoice number as 4 digits
        formatted_invoice_number = str(invoice_number).zfill(4)

        print(formatted_invoice_number)

        return render(request, 'sales_items/sales_items_form.html', {
            'organization': organization,
            'transaction_form': transaction_form,
            'sales_items_form': sales_items_form,
            'customers': customers,
            'items': items,
            'invoice_number': formatted_invoice_number,
        })

# Sales Item Detail


def sales_items_create_note(request, organization_id, transaction_id):
    organization = get_object_or_404(Organization, pk=organization_id)

    if request.method == 'POST':
        try:
            credit_note_data = json.loads(request.body.decode('utf-8'))
        except json.JSONDecodeError:
            return JsonResponse({'success': False, "errors": {"general": ["Invalid JSON data"]}})

        try:
            transaction_ = Transaction.objects.get(
                id=transaction_id, organization=organization)
        except Transaction.DoesNotExist:
            return JsonResponse({'success': False, "errors":  {"general": ["Transaction not found"]}})

        errors = {
            "success": False,
            "errors": {}
        }

        try:
            with transaction_mode.atomic():
                credit_note_items = []
                total_taxable_amount = 0
                total_tax_amount = 0

                # Process each credit note item
                for item in credit_note_data['items']:
                    try:
                        sales_item = transaction_.sales_items.get(
                            id=item['salesItemId'])

                        # Validate the quantity
                        credit_note_quantity = float(
                            item['creditNoteQuantity'])
                        if credit_note_quantity <= 0:
                            errors["errors"][item['salesItemId']] = (
                                [f"{sales_item.item.item_name} Quantity must be greater than zero."]
                            )
                        elif credit_note_quantity > float(sales_item.qty):
                            errors["errors"][item['salesItemId']] = (
                                [f"{sales_item.item.item_name} Quantity cannot exceed available quantity ({sales_item.qty})."]
                            )
                    except SalesItems.DoesNotExist:
                        errors["errors"][item['salesItemId']] = (
                            [f"Sales item with ID {item['salesItemId']} not found."]
                        )

                # If there are errors, return them
                if errors["errors"]:
                    return JsonResponse({"success": errors["success"], "errors": errors["errors"]})

                # Generate Credit Note Invoice Number
                credit_note_number = Transaction.objects.filter(
                    organization=organization).count() + 1
                formatted_credit_note_number = f"{str(credit_note_number).zfill(4)}"

                # Create a new Credit Note transaction
                credit_note_transaction = Transaction.objects.create(
                    organization=organization,
                    customer=transaction_.customer,
                    receipt_number=formatted_credit_note_number,
                    original_receipt_number=transaction_.receipt_number,
                    document_type="credit_note",
                    created_by=request.user,
                    reason=item.get('creditNoteReason', 'Other')
                )

                # Process each credit note item
                for item in credit_note_data['items']:
                    sales_item = transaction_.sales_items.get(
                        id=item['salesItemId'])

                    credit_note_reason = item.get('creditNoteReason', 'Other')
                    credit_note_quantity = float(item['creditNoteQuantity'])
                    item_obj = sales_item.item

                    # # Tax calculations
                    tax_code = sales_item.tax_code
                    tax_rate = TAX_RATES.get(tax_code, 0)
                    taxable_amount = round(
                        float(credit_note_quantity) * float(sales_item.rate), 2)
                    tax_amount = round(
                        (float(taxable_amount) * float(tax_rate)) / 100, 2)

                    # Collect data for the Credit Note PDF
                    credit_note_items.append({
                        "transaction": transaction_,
                        "item": sales_item.item,
                        "item_description": sales_item.item_description,
                        "qty": credit_note_quantity,
                        "rate": sales_item.rate,
                        "discount_rate": sales_item.discount_rate,
                        "discount_amount": sales_item.discount_amount,
                        "tax_code": sales_item.tax_code,
                        "line_total": float(credit_note_quantity) * float(sales_item.rate),
                        "reason": credit_note_reason
                    })

                    if credit_note_reason == "refund":
                        ItemMovement.objects.create(
                            item=item_obj,
                            movement_type='ADD',
                            movement_reason='Return',
                            item_unit=credit_note_quantity,
                        )

                        # Update Item's stock balance
                        item_obj.item_current_balance += Decimal(
                            credit_note_quantity)
                        item_obj.save()

                        total_taxable_amount += float(taxable_amount)
                        total_tax_amount += float(tax_amount)

                # Ensure all tax categories are accounted for in tax_totals
                tax_totals = {tax_code: {"taxable_amount": 0.00,
                                         "tax_amount": 0.00} for tax_code in TAX_RATES.keys()}

                # Calculate taxable amounts per tax category
                for credit_note_item in credit_note_items:
                    tax_code = credit_note_item["tax_code"]
                    taxable_amount = float(
                        credit_note_item["rate"]) * float(credit_note_item["qty"])
                    tax_amount = taxable_amount * \
                        (TAX_RATES.get(tax_code, 0) / 100)

                    tax_totals[tax_code]["taxable_amount"] += taxable_amount
                    tax_totals[tax_code]["tax_amount"] += tax_amount

                # Step 3: Generate the API Request Payload
                request_payload = {
                    "invcNo": str(credit_note_transaction.receipt_number),
                    "orgInvcNo": str(credit_note_transaction.original_receipt_number) if credit_note_transaction.original_receipt_number else str(credit_note_transaction.receipt_number),
                    "custTin": credit_note_transaction.customer.customer_pin,
                    "custNm": credit_note_transaction.customer.customer_name,
                    "salesTyCd": "R",
                    "rcptTyCd": "R",
                    "pmtTyCd": "01",
                    "salesSttsCd": "02",
                    "cfmDt": credit_note_transaction.created_at.strftime("%Y%m%d%H%M%S"),
                    "salesDt": credit_note_transaction.created_at.strftime("%Y%m%d"),
                    "stockRlsDt": credit_note_transaction.created_at.strftime("%Y%m%d%H%M%S"),
                    "totItemCnt": len(credit_note_items),
                    # Ensure all tax fields exist (Set default values if missing)
                    "taxblAmtA": round(tax_totals.get("A", {"taxable_amount": 0.00})["taxable_amount"], 2),
                    "taxblAmtB": round(tax_totals.get("B", {"taxable_amount": 0.00})["taxable_amount"], 2),
                    "taxblAmtC": round(tax_totals.get("C", {"taxable_amount": 0.00})["taxable_amount"], 2),
                    "taxblAmtD": round(tax_totals.get("D", {"taxable_amount": 0.00})["taxable_amount"], 2),
                    "taxblAmtE": round(tax_totals.get("E", {"taxable_amount": 0.00})["taxable_amount"], 2),
                    "taxRtA": TAX_RATES["A"],
                    "taxRtB": TAX_RATES["B"],
                    "taxRtC": TAX_RATES["C"],
                    "taxRtD": TAX_RATES["D"],
                    "taxRtE": TAX_RATES["E"],
                    "taxAmtA": round(tax_totals.get("A", {"tax_amount": 0.00})["tax_amount"], 2),
                    "taxAmtB": round(tax_totals.get("B", {"tax_amount": 0.00})["tax_amount"], 2),
                    "taxAmtC": round(tax_totals.get("C", {"tax_amount": 0.00})["tax_amount"], 2),
                    "taxAmtD": round(tax_totals.get("D", {"tax_amount": 0.00})["tax_amount"], 2),
                    "taxAmtE": round(tax_totals.get("E", {"tax_amount": 0.00})["tax_amount"], 2),
                    "totTaxblAmt": total_taxable_amount,
                    "totTaxAmt": total_tax_amount,
                    "totAmt": total_taxable_amount + total_tax_amount,
                    "prchrAcptcYn": "N",
                    "remark": None,
                    "regrId": "Admin",
                    "regrNm": "Admin",
                    "modrId": "Admin",
                    "modrNm": "Admin",
                    "receipt": {
                        "custTin": credit_note_transaction.customer.customer_pin,
                        "custMblNo": credit_note_transaction.customer.customer_phone,
                        "rptNo": str(credit_note_transaction.receipt_number),
                        "rcptPbctDt": credit_note_transaction.created_at.strftime("%Y%m%d%H%M%S"),
                        "topMsg": "Shopwithus",
                        "btmMsg": "Welcome",
                        "prchrAcptcYn": "N"
                    },
                    "itemList": [
                        {
                            "itemSeq": index + 1,
                            "itemCd": credit_note_item["item"].itemCd,
                            "itemClsCd": credit_note_item["item"].item_class_code,
                            "itemNm": credit_note_item["item"].item_name,
                            "bcd": None,
                            "pkgUnitCd": credit_note_item["item"].package_unit_code,
                            "pkg": 1,
                            "qtyUnitCd": credit_note_item["item"].quantity_unit_code,
                            "qty": credit_note_item["qty"],
                            "prc": float(credit_note_item["rate"]),
                            "splyAmt": round(float(credit_note_item["rate"]) * credit_note_item["qty"], 2),
                            "dcRt": round(float(credit_note_item.get("discount_rate", 0.0)), 2),
                            "dcAmt": round(float(credit_note_item.get("discount_amount", 0.0)), 2),
                            "isrccCd": None,
                            "isrccNm": None,
                            "isrcRt": None,
                            "isrcAmt": None,
                            "taxTyCd": credit_note_item["tax_code"],
                            "taxblAmt": round(float(credit_note_item["rate"]) * credit_note_item["qty"], 2),
                            "taxAmt": round(
                                float(credit_note_item["rate"]) * credit_note_item["qty"] *
                                (TAX_RATES.get(
                                    credit_note_item["tax_code"], 0) / 100), 2
                            ),
                            "totAmt": round(float(credit_note_item["rate"]) * credit_note_item["qty"], 2) + round(
                                float(credit_note_item["rate"]) * credit_note_item["qty"] *
                                (TAX_RATES.get(
                                    credit_note_item["tax_code"], 0) / 100), 2
                            ),
                        }
                        for index, credit_note_item in enumerate(credit_note_items)
                    ]

                }

                # Log API Request
                request_log = APIRequestLog.objects.create(
                    request_type="saveCreditNote",
                    request_payload=request_payload,
                    transaction=credit_note_transaction,
                    user=request.user,
                    organization=credit_note_transaction.organization,
                )

                # Send Request via Celery
                try:
                    send_api_request.apply_async(args=[request_log.id])
                    return JsonResponse({'success': True, 'data': "Processing request"})
                except OperationalError as e:
                    print(f"Celery is mot reachable: {e}")
                    return JsonResponse({'success': True, 'data': "Processing request"})

                # # Generate PDF for Credit Note
                # pdf_path = generate_transaction_pdf(
                #     organization, credit_note_transaction, transaction_.customer, credit_note_items, credit_note_data, "credit_note")

                # # Open and send the PDF as a response to auto-download
                # with open(pdf_path, "rb") as pdf_file:
                #     response = HttpResponse(
                #         pdf_file.read(), content_type='application/pdf'
                #     )
                #     response[
                #         'Content-Disposition'] = f'attachment; filename="credit_note_{formatted_credit_note_number}.pdf"'
                #     return response

        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)

    return JsonResponse({"error": "GET method not allowed for this endpoint."}, status=405)


def sales_items_detail(request, pk):
    try:
        sales_item = SalesItems.objects.select_related(
            'transaction', 'item').get(pk=pk)
        return JsonResponse({
            "status": "success",
            "data": {
                "id": sales_item.id,
                "item_description": sales_item.item_description,
                "qty": sales_item.qty,
                "rate": sales_item.rate,
                "discount_rate": sales_item.discount_rate,
                "discount_amount": sales_item.discount_amount,
                "tax_code": sales_item.tax_code,
                "line_total": sales_item.line_total,
            }
        }, status=200)
    except SalesItems.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Sales Item not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# Update Sales Item


def sales_items_update(request, pk):
    sales_item = get_object_or_404(SalesItems, pk=pk)
    if request.method == "POST":
        form = SalesItemsForm(request.POST, instance=sales_item)
        if form.is_valid():
            try:
                form.save()
                return redirect("sales_items_list")
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)
        else:
            return JsonResponse({
                "status": "error",
                "message": "Invalid data submitted",
                "errors": form.errors
            }, status=400)
    else:
        form = SalesItemsForm(instance=sales_item)
        return render(request, "sales_items_form.html", {"form": form})

# Delete Sales Item


def sales_items_delete(request, pk):
    try:
        sales_item = get_object_or_404(SalesItems, pk=pk)
        sales_item.delete()
        return redirect("sales_items_list")
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def generate_invoice_pdf(request, request_log_id, transaction_id,):
    """
    Generate and return the invoice PDF dynamically from stored API request and response.
    """
    transaction = get_object_or_404(Transaction, id=transaction_id)
    print(transaction)

    # Retrieve the latest successful API request for this transaction
    try:
        request_log = APIRequestLog.objects.get(
            id=request_log_id, transaction=transaction, request_type="saveSalesTransaction", status="success")
    except APIRequestLog.DoesNotExist:
        return HttpResponse("Invoice not available yet. Please retry later.", status=404)

    # Get the API response details
    response_data = request_log.response_data
    request_data = request_log.request_payload

    if not response_data or "data" not in response_data:
        return HttpResponse("API response not found. Try again later.", status=404)

    # Extract relevant data from the API response
    receipt_number = response_data["data"]["curRcptNo"]
    total_receipts = response_data["data"]["totRcptNo"]
    internal_data = response_data["data"]["intrlData"]
    receipt_signature = response_data["data"]["rcptSign"]
    issued_date = response_data["data"]["sdcDateTime"]

    document_type = "invoice"

    # ✅ Generate the PDF dynamically using API data
    pdf_path = generate_transaction_pdf(
        transaction.organization,
        transaction,
        transaction.customer,
        request_data,
        response_data,
        document_type,
        receipt_number,
        total_receipts,
        internal_data,
        receipt_signature,
        issued_date
    )

    # Open and send the PDF as a response to auto-download
    with open(pdf_path, "rb") as pdf_file:
        response = HttpResponse(
            pdf_file.read(), content_type="application/pdf")
        response['Content-Disposition'] = f'attachment; filename="invoice_{transaction.receipt_number}.pdf"'
    return response


def generate_credit_note_pdf(request, request_log_id, transaction_id,):
    """
    Generate and return the credit note PDF dynamically from stored API request and response.
    """
    transaction = get_object_or_404(Transaction, id=transaction_id)
    print(transaction)

    # Retrieve the latest successful API request for this transaction
    try:
        request_log = APIRequestLog.objects.get(
            id=request_log_id, transaction=transaction, request_type="saveCreditNote", status="success")
    except APIRequestLog.DoesNotExist:
        return HttpResponse("Credit note not available yet. Please retry later.", status=404)

    # Get the API response details
    response_data = request_log.response_data
    request_data = request_log.request_payload

    if not response_data or "data" not in response_data:
        return HttpResponse("API response not found. Try again later.", status=404)

    # Extract relevant data from the API response
    receipt_number = response_data["data"]["curRcptNo"]
    total_receipts = response_data["data"]["totRcptNo"]
    internal_data = response_data["data"]["intrlData"]
    receipt_signature = response_data["data"]["rcptSign"]
    issued_date = response_data["data"]["sdcDateTime"]

    document_type = "credit note"

    # ✅ Generate the PDF dynamically using API data
    pdf_path = generate_transaction_pdf(
        transaction.organization,
        transaction,
        transaction.customer,
        request_data,
        response_data,
        document_type,
        receipt_number,
        total_receipts,
        internal_data,
        receipt_signature,
        issued_date
    )

    # Open and send the PDF as a response to auto-download
    with open(pdf_path, "rb") as pdf_file:
        response = HttpResponse(
            pdf_file.read(), content_type="application/pdf")
        response['Content-Disposition'] = f'attachment; filename="invoice_{transaction.receipt_number}.pdf"'
    return response


def generate_transaction_pdf(
    organization,
    transaction,
    customer,
    request_data,
    response_data,
    document_type,
    receipt_number,
    total_receipts,
    internal_data,
    receipt_signature,
    issued_date
):
    """
    Generates a PDF for both Invoices and Credit Notes dynamically using API response.
    """
    document_label = "Invoice" if document_type == "invoice" else "Credit Note"

    # Extract SCU response details
    scu_info = response_data.get("data", {})
    qr_link = generate_qr_link(scu_info)  # Generate SCU verification link
    qr_code_path = generate_qr_code_base64(
        qr_link)

    # ✅ Extract tax rates
    TAX_RATES = {
        "A": 0,   # Exempt
        "B": 16,  # VAT 16%
        "C": 0,   # Zero-rated
        "D": 0,   # Non-VAT
        "E": 8    # VAT 8%
    }

    # ✅ Initialize tax summary
    tax_summary = {code: {"taxable_amount": 0,
                          "tax_rate": TAX_RATES[code], "tax_amount": 0} for code in TAX_RATES.keys()}

    # ✅ Extract tax details from API response
    tax_summary["A"]["taxable_amount"] = request_data.get("taxblAmtA", 0)
    tax_summary["B"]["taxable_amount"] = request_data.get("taxblAmtB", 0)
    tax_summary["C"]["taxable_amount"] = request_data.get("taxblAmtC", 0)
    tax_summary["D"]["taxable_amount"] = request_data.get("taxblAmtD", 0)
    tax_summary["E"]["taxable_amount"] = request_data.get("taxblAmtE", 0)

    tax_summary["A"]["tax_amount"] = request_data.get("taxAmtA", 0)
    tax_summary["B"]["tax_amount"] = request_data.get("taxAmtB", 0)
    tax_summary["C"]["tax_amount"] = request_data.get("taxAmtC", 0)
    tax_summary["D"]["tax_amount"] = request_data.get("taxAmtD", 0)
    tax_summary["E"]["tax_amount"] = request_data.get("taxAmtE", 0)

    # ✅ Extract items from API request data
    items_data = []
    total_due = request_data.get("totAmt", 0)

    for item in request_data["itemList"]:
        items_data.append({
            "description": item["itemNm"],
            "name": item["itemNm"],
            "quantity": intcomma(float(item["qty"])),
            "rate": intcomma(float(item["prc"])),
            "discount": intcomma(float(item["dcAmt"])),
            "tax_code": item["taxTyCd"],
            "line_total": intcomma(float(item["totAmt"])),
        })

    # Separate `internal_data` and `receipt_signature` by dashes
    internal_data_formatted = "-".join([internal_data[i:i+4]
                                       for i in range(0, len(internal_data), 4)])
    receipt_signature_formatted = "-".join([receipt_signature[i:i+4]
                                           for i in range(0, len(receipt_signature), 4)])

    # Parse the string into a datetime object
    issued_date = datetime.strptime(issued_date, "%Y%m%d%H%M%S")

    response_date = scu_info.get('sdcDateTime', '')

    response_date = datetime.strptime(response_date, "%Y%m%d%H%M%S")

    # Format tax_summary values
    formatted_tax_summary = {
        key: {
            "taxable_amount": intcomma(value["taxable_amount"]),
            "tax_rate": intcomma(value["tax_rate"]),
            "tax_amount": intcomma(value["tax_amount"]),
        }
        for key, value in tax_summary.items()
    }

    # ✅ Generate PDF Content
    context = {
        "organization": organization,
        "document_number": transaction.receipt_number,
        "document_date": issued_date,
        "customer_name": customer.customer_name,
        "customer_email": customer.customer_email,
        "customer_pin": customer.customer_pin,
        "items": items_data,
        "total_due": intcomma(total_due),
        "document_type": document_label,
        "tax_summary": formatted_tax_summary,
        "receipt_number": receipt_number,
        "total_receipts": total_receipts,
        "internal_data": internal_data_formatted,
        "receipt_signature": receipt_signature_formatted,
        "res_date": response_date,
        'scu_info': scu_info,
        'qr_code_path': qr_code_path,
    }

    html_content = render_to_string(
        "../templates/invoice_template.html", context)

    # Convert the HTML to PDF
    pdf = HTML(string=html_content).write_pdf()

    # Save the PDF to the server
    pdf_filename = f"transaction_{transaction.receipt_number}.pdf"
    pdf_path = os.path.join(settings.MEDIA_ROOT,
                            "transaction_documents", pdf_filename)

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

    with open(pdf_path, "wb") as f:
        f.write(pdf)

    # Update transaction document_path field
    transaction.document_path = f"transaction_documents/{pdf_filename}"
    transaction.save()

    return pdf_path


def gxeenerate_transaction_pdf(organization, transaction, customer, sales_items_list, transaction_data, document_type):
    """
    Generates a PDF for both Invoices and Credit Notes dynamically using the same template.
    """
    document_label = "Invoice" if document_type == "invoice" else "Credit Note"

    print(sales_items_list, transaction_data)

    # Define tax rates
    TAX_RATES = {
        "A": 0,   # Exempt
        "B": 16,  # VAT 16%
        "C": 0,   # Zero-rated
        "D": 0,   # Non-VAT
        "E": 8    # VAT 8%
    }

    # Initialize tax summary
    tax_summary = {code: {"taxable_amount": 0,
                          "tax_rate": TAX_RATES[code], "tax_amount": 0} for code in TAX_RATES.keys()}

    # Process items (Unifies invoice & credit note logic)
    items_data = []
    total_due = 0

    for item in sales_items_list:
        # Handle both object-based and dictionary-based data
        item_description = item.get("item_description", "Item") if isinstance(
            item, dict) else item.item_description
        item_name = item.get("item").item_name if isinstance(
            item, dict) else item.item.item_name
        quantity = float(item.get("qty", 0)) if isinstance(
            item, dict) else float(item.qty)
        rate = float(item.get("rate", 0)) if isinstance(
            item, dict) else float(item.rate)
        discount = float(item.get("discount_amount", 0)) if isinstance(
            item, dict) else float(item.discount_amount)
        tax_code = item.get("tax_code", None) if isinstance(
            item, dict) else item.tax_code
        line_total = float(item.get("line_total", 0)) if isinstance(
            item, dict) else float(item.line_total)

        # Ensure tax code is valid
        if tax_code and tax_code in TAX_RATES:
            taxable_amount = line_total  # Tax is applied on the line total
            tax_amount = (taxable_amount * TAX_RATES[tax_code]) / 100

            # Update tax summary
            tax_summary[tax_code]["taxable_amount"] += taxable_amount
            tax_summary[tax_code]["tax_amount"] += tax_amount

        # Append to items_data for rendering in template
        items_data.append({
            "description": item_description,
            "name": item_name,
            "quantity": quantity,
            "rate": rate,
            "discount": discount,
            "tax_code": tax_code,
            "line_total": line_total
        })

        total_due += line_total

    # Context data (Unified for both invoices and credit notes)
    context = {
        'organization': organization,
        'document_number': transaction.receipt_number,
        'document_date': transaction_data.get('invoiceDate', timezone.now().strftime('%Y-%m-%d')),
        'customer_name': customer.customer_name,
        'customer_email': customer.customer_email,
        'customer_pin': customer.customer_pin,
        'items': items_data,
        'total_due': transaction_data.get('balanceDue', total_due),
        'document_type': document_label,  # Displays "Invoice" or "Credit Note"
        'tax_summary': tax_summary  # ✅ Pass the tax summary to the template
    }

    html_content = render_to_string(
        "../templates/invoice_tempate.html", context)

    # Convert the HTML to PDF
    pdf = HTML(string=html_content).write_pdf()

    # Save the PDF to the server
    pdf_filename = f"transaction_{transaction.receipt_number}.pdf"
    pdf_path = os.path.join(settings.MEDIA_ROOT,
                            "transaction_documents", pdf_filename)

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

    with open(pdf_path, "wb") as f:
        f.write(pdf)

    # Update transaction document_path field
    transaction.document_path = f"transaction_documents/{pdf_filename}"
    transaction.save()

    return pdf_path
