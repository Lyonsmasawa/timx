import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db import IntegrityError, OperationalError, transaction
from django.urls import reverse
from api_tracker.models import APIRequestLog
from api_tracker.tasks import send_api_request
from commons.item_classification_constants import ITEM_CLASS_CHOICES
from item_movement.models import ItemMovement
from organization.models import Organization
from .models import Item
from .forms import ItemForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from dal import autocomplete
from commons.constants import (
    COUNTRY_CHOICES, PRODUCT_TYPE_CHOICES, UNIT_CHOICES, PACKAGE_CHOICES, TAX_TYPE_CHOICES, TAXPAYER_STATUS_CHOICES
)
from commons.utils import get_choices_as_autocomplete, get_item_class_choices
# List Items


@login_required
def item_list(request):
    try:
        items = Item.objects.select_related('organization').all()
        return render(request, "item/item_list.html", {"items": items})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# Create Item


@login_required
def item_create(request, pk):
    organization = get_object_or_404(Organization, pk=pk)

    try:
        if request.method == "POST":
            item_form = ItemForm(request.POST)

            if item_form.is_valid():
                try:
                    item = item_form.save(commit=False)
                    item.organization = organization
                    item.save()

                except IntegrityError as e:
                    error_msg = str(e)

                    unique_fields = {
                        'item_name': 'The Item name must be unique.'
                    }

                    for field, message in unique_fields.items():
                        if field in error_msg:
                            return JsonResponse({
                                'success': False,
                                'errors': {field: [message]}
                            })

                    return JsonResponse({
                        'success': False,
                        'errors': {'general': [f'An error occurred. Please try again. {error_msg}']}
                    })

                except Exception as e:
                    # Catch any other errors
                    return JsonResponse({
                        'success': False,
                        'errors': {'general': [f'An error occurred: {str(e)}']}
                    })

                return JsonResponse({
                    'success': True,
                    'item_id': item.id,
                    'item_name': item.item_name,
                    'item_code': item.itemCd,
                    'item_type_code': item.item_type_code,
                    'item_tax_code': item.item_tax_code,
                    'item_class_code': item.item_class_code,
                    'item_current_balance': item.item_current_balance,
                    'item_detail_url': reverse('item:item_update', args=[item.id]),
                    'item_delete_url': reverse('item:item_delete', args=[item.id]),
                })

            return JsonResponse({'success': False, 'errors': item_form.errors})

    except Exception as e:
        print({str(e)})
        return JsonResponse({'success': False, 'error': {'general': ['Invalid action.']}})


@login_required
def update_item_quantity(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        quantity = request.POST.get('item_quantity')
        movement_type = request.POST.get('movement_type')
        movement_reason = request.POST.get('movement_reason')

        try:
            # Convert quantity to an integer
            quantity = int(quantity)

            if quantity <= 0:
                return JsonResponse({"error": "Quantity must be a positive number."}, status=400)

            if movement_type not in ['ADD', 'REMOVE']:
                return JsonResponse({"error": "Invalid movement type."}, status=400)

            # Default movement_reason for both ADD and REMOVE if None
            if not movement_reason:
                movement_reason = "Stock Movement"

            # Use a transaction block
            with transaction.atomic():
                # Get the item
                item = get_object_or_404(Item, id=item_id)

                # Update item quantity based on movement type
                if movement_type == 'ADD':
                    item.item_current_balance += quantity
                elif movement_type == 'REMOVE':
                    if item.item_current_balance < quantity:
                        return JsonResponse({"error": "Cannot remove more than the current balance."}, status=400)
                    item.item_current_balance -= quantity

                item.save()

                # Create an item movement entry
                ItemMovement.objects.create(
                    item=item,
                    movement_type=movement_type,
                    movement_reason=movement_reason,
                    item_unit=quantity,
                )

            # If everything succeeds
            return JsonResponse({'success': True, "message": "Quantity updated successfully"}, status=200)

        except ValueError:
            return JsonResponse({'success': False, "error": "Invalid quantity value."}, status=400)

        except Exception as e:
            return JsonResponse({'success': False, "error": str(e)}, status=400)


@login_required
def update_mapped_item_quantity(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            mapped_items = data.get("mapped_items", [])

            if not mapped_items:
                return JsonResponse({"error": "No mapped items provided."}, status=400)

            with transaction.atomic():
                for mapped_item in mapped_items:
                    item_id = mapped_item.get("mapped_item_id")
                    quantity = mapped_item.get("quantity")

                    if not item_id or quantity is None:
                        continue

                    # Get the item and update its stock
                    item = Item.objects.get(id=item_id)
                    item.item_current_balance += int(quantity)
                    item.save()

                    # Log the movement
                    ItemMovement.objects.create(
                        item=item,
                        movement_type="ADD",
                        movement_reason="Stock Movement",
                        item_unit=quantity,
                    )

            return JsonResponse({"success": True, "message": "Stock updated successfully."}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method."}, status=405)


@login_required
def create_items_from_purchase(request, pk):
    """
    Create multiple items from a purchase payload.
    """
    if request.method == 'POST':
        try:
            organization = Organization.objects.get(id=pk, user=request.user)
        except Organization.DoesNotExist:
            return JsonResponse({"error": "Organization not found."}, status=404)

        try:
            # Parse the JSON payload
            data = json.loads(request.body.decode('utf-8'))
            items_data = data.get('items', [])

            if not items_data:
                return JsonResponse({"error": "No items found in the payload."}, status=400)

            created_items = []
            with transaction.atomic():
                for item_data in items_data:
                    # Parse the string representation of the item into a dictionary
                    try:
                        # Caution: Use safer alternatives like `json.loads` if applicable
                        item = eval(item_data.get('item'))
                    except Exception as e:
                        print(f"Error parsing item data: {str(e)}")
                        continue

                    print(item)  # Debugging: Ensure it's parsed correctly
                    try:
                        # Extract data from the parsed dictionary
                        item_name = item.get('itemNm')
                        itemCd = item.get('itemCd')
                        item_class_code = item.get('itemClsCd')
                        quantity_unit_code = item.get('qtyUnitCd')
                        package_unit_code = item.get('pkgUnitCd')
                        item_tax_code = item.get('taxTyCd')
                        origin_nation_code = item.get(
                            'originNationCd', 'KE')  # Default to 'KE'
                        price = item.get('prc', 0)
                        opening_balance = item.get('qty', 0)

                        # Check if the item already exists in the organization
                        if Item.objects.filter(organization=organization, item_name=item_name).exists():
                            print(
                                f"Item '{item_name}' already exists. Skipping.")
                            continue

                        # Create the new item
                        item_obj = Item.objects.create(
                            organization=organization,
                            item_name=item_name,
                            origin_nation_code=origin_nation_code,
                            item_type_code='2',
                            quantity_unit_code=quantity_unit_code,
                            package_unit_code=package_unit_code,
                            item_class_code=item_class_code,
                            item_tax_code=item_tax_code,
                            item_opening_balance=opening_balance,
                            item_current_balance=opening_balance,
                            item_system_name=item_name,  # Optional field
                            itemCd=itemCd,
                        )
                        created_items.append(item_obj.item_name)
                    except Exception as e:
                        # Log or handle errors for individual items
                        print(f"Error creating item: {str(e)}")
                        continue
            return JsonResponse({
                "success": True,
                "message": f"Successfully created {len(created_items)} item(s).",
                "created_items": created_items,
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data."}, status=400)

        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)


# Item Detail
@login_required
def item_detail(request, pk):
    try:
        item = Item.objects.select_related('organization').get(pk=pk)
        return JsonResponse({
            "status": "success",
            "data": {
                "id": item.id,
                "item_name": item.item_name,
                "organization": item.organization.organization_name,
                "origin_nation_code": item.origin_nation_code,
                "item_type_code": item.item_type_code,
                "quantity_unit_code": item.quantity_unit_code,
                "package_unit_code": item.package_unit_code,
                "item_class_code": item.item_class_code,
                "item_tax_code": item.item_tax_code,
                "item_opening_balance": float(item.item_opening_balance or 0),
                "item_current_balance": float(item.item_current_balance or 0),
                "item_system_id": item.item_system_id,
                "item_system_name": item.item_system_name,
            }
        }, status=200)
    except Item.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Item not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# Update Item


@login_required
def item_update(request, pk):
    print(1111)
    try:
        item = Item.objects.get(pk=pk)
    except Item.DoesNotExist:
        return JsonResponse({'success': False, 'errors': {'general': [f"An error occurred: {str(e)}"]}})

    if request.method == "POST":
        # Create a dictionary to track updates
        updates = {}

        # Iterate through the submitted data and update only changed fields
        for field, value in request.POST.items():
            if field in ['csrfmiddlewaretoken']:
                continue  # Skip CSRF token field

            # Check if the submitted value is different from the current value
            current_value = getattr(item, field, None)
            if current_value != value and value.strip() != "":
                updates[field] = value

        if updates:
            try:
                # Update the organization with the modified fields
                for field, value in updates.items():
                    setattr(item, field, value)
                item.save()
                return JsonResponse({'success': True, 'message': "Item updated successfully."})
            except Exception as e:
                return JsonResponse({'success': False, 'errors': {'general': [f"An error occurred: {str(e)}"]}})
        else:
            return JsonResponse({'success': True, 'message': "No changes detected."})

    return JsonResponse({'success': False, 'errors': {'general': ["Invalid request method."]}})

# Delete Item


@login_required
def item_delete(request, pk):
    try:
        item = get_object_or_404(Item, pk=pk)
        item.delete()
        return JsonResponse({'success': True, 'message': "Item deleted successfully."})

    except Exception as e:
        return JsonResponse({'success': False, 'errors': {'general': ["Invalid request, Please try again!"]}})


@login_required
def save_item_composition(request):
    if request.method == "POST":
        try:
            item_cd = request.POST.get("itemCd")
            cpst_item_cd = request.POST.get("cpstItemCd")
            cpst_qty = request.POST.get("cpstQty")

            if not all([item_cd, cpst_item_cd, cpst_qty]):
                return JsonResponse({"error": "Missing required fields."}, status=400)

            # Validate item codes
            try:
                item = Item.objects.get(itemCd=item_cd)
                cpst_item = Item.objects.get(itemCd=cpst_item_cd)
            except Item.DoesNotExist:
                return JsonResponse({"error": "Invalid item code(s)."}, status=400)

            # Prepare the API payload
            payload = {
                "itemCd": item_cd,
                "cpstItemCd": cpst_item_cd,
                "cpstQty": int(cpst_qty),
                "regrId": getattr(request.user, "username", "admin"),
                "regrNm": request.user.get_full_name() if hasattr(request.user, "get_full_name") and request.user.get_full_name() else "admin",
            }

            # Log the API request
            request_log = APIRequestLog.objects.create(
                request_type="saveItemComposition",
                request_payload=payload,
                user=request.user,
                organization=item.organization,
                item=item,
            )

            # Send the request asynchronously
            try:
                send_api_request.apply_async(args=[request_log.id])
                return JsonResponse({"success": "Item composition saved and queued for API request."}, status=200)
            except OperationalError as e:
                print(f"Celery is mot reachable: {e}")
                return JsonResponse({'success': True, 'data': "Processing request"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method."}, status=405)


# def ajax_filter(request):
#     term = request.GET.get('q', '')  # Get the search term
#     if term:
#         filtered_units = [unit for unit in UNIT_CHOICES if term.lower() in unit[1].lower()]  # Filter based on the term
#     else:
#         filtered_units = UNIT_CHOICES  # Return the full list if no search term is provided

#     results = [{'id': unit[0], 'text': unit[1]} for unit in filtered_units]  # Prepare response data
#     return JsonResponse({'results': results})

def ajax_filter(request, field_name):
    term = request.GET.get('q', '')  # Get the search term

    # Determine which field is being filtered
    if field_name == 'quantity_unit_code':
        choices = UNIT_CHOICES
    elif field_name == 'origin_nation_code':
        choices = COUNTRY_CHOICES
    elif field_name == 'item_type_code':
        choices = PRODUCT_TYPE_CHOICES
    elif field_name == 'package_unit_code':
        choices = PACKAGE_CHOICES
    elif field_name == 'item_class_code':
        choices = get_item_class_choices()
    elif field_name == 'item_tax_code':
        choices = TAX_TYPE_CHOICES
    else:
        choices = []

    # Filter the list based on the search term
    filtered_choices = [unit for unit in choices if term.lower(
    ) in unit[1].lower()] if term else choices

    # Prepare the response data
    results = [{'id': unit[0], 'text': unit[1]} for unit in filtered_choices]
    return JsonResponse({'results': results})
