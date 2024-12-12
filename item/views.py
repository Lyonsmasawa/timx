from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Item
from .forms import ItemForm

# List Items
def item_list(request):
    try:
        items = Item.objects.select_related('organization').all()
        return render(request, "item/item_list.html", {"items": items})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# Create Item
def item_create(request):
    if request.method == "POST":
        form = ItemForm(request.POST)
        if form.is_valid():
            try:
                item = form.save()
                return JsonResponse({
                    "status": "success",
                    "message": "Item created successfully!",
                    "data": {
                        "id": item.id,
                        "item_name": item.item_name,
                        "organization": item.organization.organization_name,
                    }
                }, status=201)
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)
        else:
            return JsonResponse({
                "status": "error",
                "message": "Invalid data submitted",
                "errors": form.errors
            }, status=400)
    else:
        form = ItemForm()
        return render(request, "item/item_form.html", {"form": form})

# Item Detail
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
def item_update(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if request.method == "POST":
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            try:
                form.save()
                return redirect("item:item_list")
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)
        else:
            return JsonResponse({
                "status": "error",
                "message": "Invalid data submitted",
                "errors": form.errors
            }, status=400)
    else:
        form = ItemForm(instance=item)
        return render(request, "item/item_form.html", {"form": form})

# Delete Item
def item_delete(request, pk):
    try:
        item = get_object_or_404(Item, pk=pk)
        item.delete()
        return redirect("item:item_list")
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
