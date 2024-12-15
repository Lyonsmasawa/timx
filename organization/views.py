from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from .models import Organization
from .forms import OrganizationForm
from item.models import Item
from transaction.models import Transaction
from customer.models import Customer
from django.contrib.auth.decorators import login_required

# List Organizations
@login_required
def organization_list(request):
    try:
        organizations = Organization.objects.filter(user=request.user)
        return render(request, "organization/organization_list.html", {"organizations": organizations})
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect("organization:organization_list")

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
                organization = get_object_or_404(Organization, pk=organization.id)

                # Get all items, customers, and transactions related to the organization
                items = Item.objects.filter(organization=organization)
                customers = Customer.objects.filter(organization=organization)
                transactions = Transaction.objects.filter(organization=organization)

                return render(request, "organization/organization_detail.html", {
                    "organization": organization,
                    "items": items,
                    "customers": customers,
                    "transactions": transactions,
                })
            except Exception as e:
                messages.error(request, f"An error occurred while creating the organization: {str(e)}")
                # return redirect("organization:organization_create")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = OrganizationForm()
    return render(request, "organization/organization_form.html", {"form": form})

# Detail View
@login_required
def organization_detail(request, pk):
    try:
        organization = get_object_or_404(Organization, pk=pk)
        items = Item.objects.filter(organization=organization)
        customers = Customer.objects.filter(organization=organization)
        transactions = Transaction.objects.filter(organization=organization)

        return render(request, "organization/organization_detail.html", {
            "organization": organization,
            "items": items,
            "customers": customers,
            "transactions": transactions,
        })
    except Organization.DoesNotExist:
        messages.error(request, "Organization not found.")
        return redirect("organization:organization_list")
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect("organization:organization_list")

# Update Organization
@login_required
def organization_update(request, pk):
    organization = get_object_or_404(Organization, pk=pk)
    if request.method == "POST":
        form = OrganizationForm(request.POST, instance=organization)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Organization updated successfully!")
                return redirect("organization:organization_list")
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = OrganizationForm(instance=organization)
    return render(request, "organization/organization_form.html", {"form": form})

# Delete Organization
@login_required
def organization_delete(request, pk):
    try:
        organization = get_object_or_404(Organization, pk=pk)
        organization.delete()
        messages.success(request, "Organization deleted successfully!")
        return redirect("organization:organization_list")
    except Exception as e:
        messages.error(request, f"An error occurred while deleting the organization: {str(e)}")
        return redirect("organization:organization_list")
