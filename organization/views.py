import json
from django.db.models import Sum
from django.db import IntegrityError
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
import plotly.graph_objs as go
from commons.constants import COUNTRY_CHOICES, PACKAGE_CHOICES, PRODUCT_TYPE_CHOICES, TAX_TYPE_CHOICES, TAXPAYER_STATUS_CHOICES, UNIT_CHOICES
from item_movement.models import ItemMovement
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

# List Organizations


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
        items = Item.objects.filter(organization=organization)
        customers = Customer.objects.filter(organization=organization)
        transactions = Transaction.objects.filter(organization=organization)
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

        print(items)
        
        # Aggregate total sales data per organization
        sales_data = SalesItems.objects.values('transaction__organization__organization_name') \
            .annotate(total_sales=Sum('line_total')) \
            .order_by('-total_sales')

        # Prepare data for the chart
        organization_names = [entry['transaction__organization__organization_name'] for entry in sales_data]
        total_sales = [entry['total_sales'] for entry in sales_data]

        # Create a bar chart for total sales per organization
        sales_bar_chart = go.Bar(x=organization_names, y=total_sales)
        sales_overview_chart = go.Figure(data=[sales_bar_chart])
        
        # Render the page for regular requests
        return render(request, "organization/organization_detail.html", {
            "organization": organization,
            "items": items,
            "customers": customers,
            "transactions": transactions,
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
            'sales_overview_chart': sales_overview_chart.to_html(full_html=False, default_height='500px', default_width='700px'),
        })

    except Exception as e:
        # Log the error and stay on the page
        print(f"Error in organization_detail view: {str(e)}")
        messages.error(
            request, "An unexpected error occurred. Please try again later.")
        return render(request, "organization/organization_detail.html", {
            "organization": organization,
            "items": items,
            "customers": customers,
            "transactions": transactions,
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
