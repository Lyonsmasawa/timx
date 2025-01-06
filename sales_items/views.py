import json
from django.http import HttpResponse
import os
from weasyprint import HTML
from django.template.loader import render_to_string
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.core.mail import send_mail
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
                    document_type="invoice",
                    created_by=request.user
                )

                sales_items_list = []

                # Create SalesItems
                for item in invoice_data['items']:
                    try:
                        item_obj = Item.objects.get(pk=item['itemId'])
                    except Item.DoesNotExist:
                        return JsonResponse({"error": f"Item with ID {item['itemId']} not found"}, status=404)

                    if item['quantity'] <= 0 or item['rate'] <= 0 or item['lineTotal'] < 0:
                        return JsonResponse({"error": "Invalid item details"}, status=400)

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

                # Step 3: Generate the PDF Invoice and get the file path
                pdf_path = generate_transaction_pdf(
                    organization, transaction, customer, sales_items_list, invoice_data, "invoice")

                # Open and send the PDF as a response to auto-download
                with open(pdf_path, "rb") as pdf_file:
                    response = HttpResponse(
                        pdf_file.read(), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="invoice_{transaction.receipt_number}.pdf"'
                    return response

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

        print(credit_note_data)

        errors = {
            "success": False,
            "errors": {}
        }

        try:
            with transaction_mode.atomic():
                credit_note_items = []
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

                # Generate PDF for Credit Note
                pdf_path = generate_transaction_pdf(
                    organization, credit_note_transaction, transaction_.customer, credit_note_items, credit_note_data, "credit_note")

                # Open and send the PDF as a response to auto-download
                with open(pdf_path, "rb") as pdf_file:
                    response = HttpResponse(
                        pdf_file.read(), content_type='application/pdf'
                    )
                    response[
                        'Content-Disposition'] = f'attachment; filename="credit_note_{formatted_credit_note_number}.pdf"'
                    return response

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


def generate_transaction_pdf(organization, transaction, customer, sales_items_list, transaction_data, document_type):
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
    tax_summary = {code: {"taxable_amount": 0, "tax_rate": TAX_RATES[code], "tax_amount": 0} for code in TAX_RATES.keys()}

    # Process items (Unifies invoice & credit note logic)
    items_data = []
    total_due = 0

    for item in sales_items_list:
        # Handle both object-based and dictionary-based data
        item_description = item.get("item_description", "Item") if isinstance(item, dict) else item.item_description
        item_name = item.get("item").item_name if isinstance(item, dict) else item.item.item_name
        quantity = float(item.get("qty", 0)) if isinstance(item, dict) else float(item.qty)
        rate = float(item.get("rate", 0)) if isinstance(item, dict) else float(item.rate)
        discount = float(item.get("discount_amount", 0)) if isinstance(item, dict) else float(item.discount_amount)
        tax_code = item.get("tax_code", None) if isinstance(item, dict) else item.tax_code
        line_total = float(item.get("line_total", 0)) if isinstance(item, dict) else float(item.line_total)

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
