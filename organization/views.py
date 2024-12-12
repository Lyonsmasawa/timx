from django.shortcuts import render, get_object_or_404, redirect
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
        organizations = Organization.objects.all()
        return render(request, "organization/organization_list.html", {"organizations": organizations})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# Create Organization


@login_required
def organization_create(request):
    if request.method == "POST":
        form = OrganizationForm(request.POST)
        if form.is_valid():
            try:
                organization = form.save()

                # Get the organization based on the primary key
                organization = get_object_or_404(Organization, pk=organization.id)

                # Get all items related to the organization
                items = Item.objects.filter(organization=organization)

                # Get all customers related to the organization
                customers = Customer.objects.filter(organization=organization)

                # You can add additional data such as transactions, movements, etc.
                transactions = Transaction.objects.filter(organization=organization)

                return render(request, "organization/organization_detail.html", {
                    "organization": organization,
                    "items": items,
                    "customers": customers,
                    "transactions": transactions,
                })

            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)
        else:
            return JsonResponse({
                "status": "error",
                "message": "Invalid data submitted",
                "errors": form.errors
            }, status=400)
    else:
        form = OrganizationForm()
        return render(request, "organization/organization_form.html", {"form": form})

# Detail View


@login_required
def organization_detail(request, pk):
    try:
        # Get the organization based on the primary key
        organization = get_object_or_404(Organization, pk=pk)

        # Get all items related to the organization
        items = Item.objects.filter(organization=organization)

        # Get all customers related to the organization
        customers = Customer.objects.filter(organization=organization)

        # You can add additional data such as transactions, movements, etc.
        transactions = Transaction.objects.filter(organization=organization)

        return render(request, "organization/organization_detail.html", {
            "organization": organization,
            "items": items,
            "customers": customers,
            "transactions": transactions,
        })
    except Organization.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Organization not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


# Update Organization
@login_required
def organization_update(request, pk):
    organization = get_object_or_404(Organization, pk=pk)
    if request.method == "POST":
        form = OrganizationForm(request.POST, instance=organization)
        if form.is_valid():
            try:
                form.save()
                return redirect("organization:organization_list")
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)
        else:
            return JsonResponse({
                "status": "error",
                "message": "Invalid data",
                "errors": form.errors
            }, status=400)
    else:
        form = OrganizationForm(instance=organization)
    return render(request, "organization/organization_form.html", {"form": form})

# Delete Organization


@login_required
def organization_delete(request, pk):
    try:
        organization = get_object_or_404(Organization, pk=pk)
        organization.delete()
        return redirect("organization:organization_list")
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
