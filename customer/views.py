from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Customer
from .forms import CustomerForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required


# List Customers
@login_required
def customer_list(request):
    try:
        customers = Customer.objects.all()
        return render(request, "customer/customer_list.html", {"customers": customers})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# Create Customer


@login_required
def customer_create(request):
    organization = request.user.organizations.first() or None

    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            try:
                customer = form.save(commit=False)
                # Set the organization (assuming a user can have one organization)
                customer.organization = organization
                print(customer)
                # Save the customer
                customer.save()
                messages.success(request, "Customer created successfully.")
                return redirect('organization:organization_detail', pk=customer.organization.id)
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
        else:
            messages.error(
                request, "Invalid data submitted. Please fix the errors.")
    else:
        form = CustomerForm()

    # Render the form and pass the messages to the template
    return render(request, "customer/customer_form.html", {"form": form, "organization": organization})

# Detail View


@login_required
def customer_detail(request, pk):
    try:
        # Get the customer object
        customer = get_object_or_404(Customer, pk=pk)
        
        # Pass customer data to the template
        return render(request, "customer/customer_detail.html", {
            "customer": customer,
        })
    except Customer.DoesNotExist:
        # Handle customer not found
        return render(request, "error.html", {
            "message": "Customer not found"
        })
    except Exception as e:
        # Handle general errors
        return render(request, "error.html", {
            "message": f"An error occurred: {str(e)}"
        })

# Update Customer
@login_required
def customer_update(request, pk):
    organization = request.user.organizations.first() or None
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == "POST":
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            try:
                # Save the updated customer
                form.save()

                # Add success message and render the updated form
                messages.success(request, "Customer updated successfully.")
                return render(request, "customer/customer_form.html", {"form": form, "organization": organization})
            except Exception as e:
                # If any error occurs, show an error message
                messages.error(request, f"An error occurred: {str(e)}")
                return render(request, "customer/customer_form.html", {"form": form, "organization": organization})

        else:
            # If form is not valid, show the errors
            messages.error(request, "Invalid data submitted.")
            return render(request, "customer/customer_form.html", {"form": form, "organization": organization})

    else:
        # If it's a GET request, just show the form with the existing data
        form = CustomerForm(instance=customer)

    return render(request, "customer/customer_form.html", {"form": form, "organization": organization})

# Delete Customer


@login_required
def customer_delete(request, pk):
    try:
        customer = get_object_or_404(Customer, pk=pk)
        customer.delete()
        return redirect("customer:customer_list")
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
