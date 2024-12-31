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
                pdf_path = generate_invoice(
                    organization, transaction, customer, sales_items_list, invoice_data)

                # Open and send the PDF as a response to auto-download
                with open(pdf_path, "rb") as pdf_file:
                    response = HttpResponse(
                        pdf_file.read(), content_type='application/pdf')
                    response['Content-Disposition'] = f'attachment; filename="invoice_{transaction.receipt_number}.pdf"'
                    return response

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)

    else:  # GET method
        items = Item.objects.filter(organization=organization)
        customers = Customer.objects.filter(organization=organization)
        transaction_form = TransactionForm()
        sales_items_form = SalesItemsForm()
        return render(request, 'sales_items/sales_items_form.html', {
            'organization': organization,
            'transaction_form': transaction_form,
            'sales_items_form': sales_items_form,
            'customers': customers,
            'items': items
        })

# Sales Item Detail


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


def generate_invoice(organization, transaction, customer, sales_items_list, invoice_data):
    print(sales_items_list)

    # Extract relevant fields from SalesItems objects
    items_data = [
        {
            "description": item.item_description or "Item",
            "name": item.item.item_name or "Item",
            "quantity": item.qty or 0,
            "rate": item.rate or 0,
            "discount": item.discount_amount or 0,
            "tax_code": item.tax_code or None,
            "line_total": item.line_total or 0,
        }
        for item in sales_items_list
    ]

    context = {
        'organization': organization,
        'invoice_number': transaction.receipt_number,
        'invoice_date': invoice_data['invoiceDate'],
        'invoice_due_date': invoice_data['dueDate'],
        'customer_name': customer.customer_name,
        'customer_email': customer.customer_email,
        'customer_pin': customer.customer_pin,
        'items': items_data,
        'total_due': invoice_data['balanceDue']
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
