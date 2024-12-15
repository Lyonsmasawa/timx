from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Item
from .forms import ItemForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages

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
def item_create(request):
    organization = request.user.organizations.first()

    if request.method == "POST":
        form = ItemForm(request.POST)
        if form.is_valid():
            try:
                item = form.save(commit=False)
                item.organization = organization
                item.save()

                messages.success(request, "Item created successfully!")
                return redirect('organization:organization_detail', pk=item.organization.id)
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
        else:
            print(organization.id)
            messages.error(
                request, "There was an error with the form. Please check your input.")

    else:
        form = ItemForm()

    return render(request, "item/item_form.html", {"form": form, "organization": organization})


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
    # Get the organization of the current user
    organization = request.user.organizations.first()

    try:
        # Try to retrieve the item that belongs to the organization
        item = Item.objects.get(pk=pk, organization=organization)
    except Item.DoesNotExist:
        messages.error(
            request, "Item not found or you don't have permission to edit it.")
        return redirect('organization:organization_detail', pk=organization.id)

    if request.method == "POST":
        # Pass the existing item to the form for updating
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            try:
                updated_item = form.save(commit=False)
                updated_item.organization = organization  # Ensure organization is set
                updated_item.save()

                messages.success(request, "Item updated successfully!")
                return redirect('organization:organization_detail', pk=updated_item.organization.id)
            except Exception as e:
                messages.error(request, f"An error occurred: {str(e)}")
        else:
            messages.error(
                request, "There was an error with the form. Please check your input.")
    else:
        # Pre-populate the form with the current item data
        form = ItemForm(instance=item)

    return render(request, "item/item_form.html", {"form": form, "organization": organization, "item": item})


# Delete Item


@login_required
def item_delete(request, pk):
    try:
        item = get_object_or_404(Item, pk=pk)
        item.delete()
        return redirect("item:item_list")
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
