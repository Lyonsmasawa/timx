from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Inventory
from .forms import InventoryForm

# List Inventory Records
def inventory_list(request):
    try:
        inventories = Inventory.objects.select_related('item').all()
        return render(request, "inventory_list.html", {"inventories": inventories})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# Create Inventory Record
def inventory_create(request):
    if request.method == "POST":
        form = InventoryForm(request.POST)
        if form.is_valid():
            try:
                inventory = form.save()
                return JsonResponse({
                    "status": "success",
                    "message": "Inventory record created successfully!",
                    "data": {
                        "id": inventory.id,
                        "item": inventory.item.item_name,
                        "movement_type": inventory.get_movement_type_display(),
                        "quantity": inventory.quantity
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
        form = InventoryForm()
        return render(request, "inventory_form.html", {"form": form})

# Inventory Detail
def inventory_detail(request, pk):
    try:
        inventory = Inventory.objects.select_related('item').get(pk=pk)
        return JsonResponse({
            "status": "success",
            "data": {
                "id": inventory.id,
                "item": inventory.item.item_name,
                "movement_type": inventory.get_movement_type_display(),
                "quantity": inventory.quantity,
                "description": inventory.description,
            }
        }, status=200)
    except Inventory.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Inventory record not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# Update Inventory Record
def inventory_update(request, pk):
    inventory = get_object_or_404(Inventory, pk=pk)
    if request.method == "POST":
        form = InventoryForm(request.POST, instance=inventory)
        if form.is_valid():
            try:
                form.save()
                return redirect("inventory_list")
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)
        else:
            return JsonResponse({
                "status": "error",
                "message": "Invalid data submitted",
                "errors": form.errors
            }, status=400)
    else:
        form = InventoryForm(instance=inventory)
        return render(request, "inventory_form.html", {"form": form})

# Delete Inventory Record
def inventory_delete(request, pk):
    try:
        inventory = get_object_or_404(Inventory, pk=pk)
        inventory.delete()
        return redirect("inventory_list")
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
