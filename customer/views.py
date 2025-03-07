from django.db import IntegrityError
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.urls import reverse
from requests import Response
from customer.serializers import CustomerSerializer
from organization.models import Organization
from .models import Customer
from .forms import CustomerForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated


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
def customer_create(request, pk):
    organization = get_object_or_404(Organization, pk=pk)

    try:
        if request.method == "POST":
            customer_form = CustomerForm(request.POST)
            if customer_form.is_valid():
                try:
                    customer = customer_form.save(commit=False)
                    customer.organization = organization
                    customer.save()
                except IntegrityError as e:
                    error_msg = str(e)

                    unique_fields = {
                        'customer_pin': 'The customer`s pin must be unique.',
                        'customer_email': 'The customer`s email must be unique.',
                        'customer_phone': 'The customer`s phone must be unique.',
                    }

                    for field, message in unique_fields.items():
                        if field in error_msg:
                            return JsonResponse({
                                'success': False,
                                'errors': {field: [message]}
                            })

                    return JsonResponse({
                        'success': False,
                        'errors': {'general': 'An error occurred. Please try again.'}
                    })

                except Exception as e:
                    # Catch any other errors
                    return JsonResponse({
                        'success': False,
                        'errors': {'general': f'An error occurred: {str(e)}'}
                    })

                return JsonResponse({
                    'success': True,
                    'customer_id': customer.id,
                    'customer_pin': customer.customer_pin,
                    'customer_name': customer.customer_name,
                    'customer_email': customer.customer_email,
                    'customer_address': customer.customer_address,
                    'customer_phone': customer.customer_phone,
                    'customer_update_url': reverse('customer:customer_update', args=[customer.id]),
                    'customer_delete_url': reverse('customer:customer_delete', args=[customer.id]),
                })

            return JsonResponse({'success': False, 'errors': customer_form.errors})

    except Exception as e:
        print({str(e)})
        return JsonResponse({'success': False, 'error': 'Invalid action.'})
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


@login_required
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == "POST":
        # Create a dictionary to track updates
        updates = {}

        # Iterate through the submitted data and update only changed fields
        for field, value in request.POST.items():
            if field in ['csrfmiddlewaretoken']:
                continue  # Skip CSRF token field

            # Check if the submitted value is different from the current value
            current_value = getattr(customer, field, None)
            if current_value != value and value.strip() != "":
                updates[field] = value

        if updates:
            try:
                # Update the organization with the modified fields
                for field, value in updates.items():
                    setattr(customer, field, value)
                customer.save()
                return JsonResponse({'success': True, 'message': "Customer updated successfully."})
            except Exception as e:
                return JsonResponse({'success': False, 'errors': {'general': [f"An error occurred: {str(e)}"]}})
        else:
            return JsonResponse({'success': True, 'message': "No changes detected."})

    return JsonResponse({'success': False, 'errors': {'general': ["Invalid request method."]}})


# Delete Customer
@login_required
def customer_delete(request, pk):
    try:
        customer = get_object_or_404(Customer, pk=pk)
        customer.delete()
        return JsonResponse({'success': True, 'message': "Customer deleted successfully."})
    except Exception as e:
        return JsonResponse({'success': False, 'errors': {'general': ["Invalid request method."]}})


# class CustomerViewSet(viewsets.ModelViewSet):
#     queryset = Customer.objects.all()
#     serializer_class = CustomerSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return self.queryset.filter(organization__user=self.request.user)

#     def perform_create(self, serializer):
#         organization = get_object_or_404(Organization, pk=self.request.data.get('organization_id'), user=self.request.user  # ✅ Ensure the user owns the org
#                                          )
#         print(organization)
#         customer = serializer.save(organization=organization)
#         return customer


# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def customer_update(request, pk):
#     customer = get_object_or_404(Customer, pk=pk)
#     serializer = CustomerSerializer(customer, data=request.data, partial=True)
#     if serializer.is_valid():
#         serializer.save()
#         return Response({"success": True, "message": "Customer updated successfully."})
#     return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['DELETE'])
# @permission_classes([IsAuthenticated])
# def customer_delete(request, pk):
#     customer = get_object_or_404(Customer, pk=pk)
    # customer.delete()
    # return Response({"success": True, "message": "Customer deleted successfully."})
