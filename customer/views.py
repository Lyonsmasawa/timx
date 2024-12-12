from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Customer
from .forms import CustomerForm

# List Customers
def customer_list(request):
    try:
        customers = Customer.objects.all()
        return render(request, "customer/customer_list.html", {"customers": customers})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# Create Customer
def customer_create(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            try:
                customer = form.save()
                redirect("organization:organization_list")
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)
        else:
            return JsonResponse({
                "status": "error",
                "message": "Invalid data submitted",
                "errors": form.errors
            }, status=400)
    else:
        form = CustomerForm()
        return render(request, "customer/customer_form.html", {"form": form})

# Detail View
def customer_detail(request, pk):
    try:
        customer = Customer.objects.get(pk=pk)
        return JsonResponse({
            "status": "success",
            "data": {
                "id": customer.id,
                "name": customer.customer_name,
                "email": customer.customer_email,
                "phone": customer.customer_phone,
                "address": customer.customer_address,
                "organization": customer.organization.organization_name,
            }
        }, status=200)
    except Customer.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Customer not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# Update Customer
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            try:
                form.save()
                return redirect("customer:customer_list")
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)
        else:
            return JsonResponse({
                "status": "error",
                "message": "Invalid data",
                "errors": form.errors
            }, status=400)
    else:
        form = CustomerForm(instance=customer)
    return render(request, "customer/customer_form.html", {"form": form})

# Delete Customer
def customer_delete(request, pk):
    try:
        customer = get_object_or_404(Customer, pk=pk)
        customer.delete()
        return redirect("customer:customer_list")
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)