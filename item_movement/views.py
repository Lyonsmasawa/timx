from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import ItemMovement
from .forms import ItemMovementForm

# List item_movement Records


def item_movement_list(request):
    try:
        inventories = ItemMovementForm.objects.select_related('item').all()
        return render(request, "item_movement_list.html", {"inventories": inventories})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# Create item_movement Record


def item_movement_create(request):
    if request.method == "POST":
        form = ItemMovementForm(request.POST)
        if form.is_valid():
            try:
                item_movement = form.save()
                return JsonResponse({
                    "status": "success",
                    "message": "item_movement record created successfully!",
                    "data": {
                        "id": item_movement.id,
                        "item": item_movement.item.item_name,
                        "movement_type": item_movement.get_movement_type_display(),
                        "quantity": item_movement.quantity
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
        form = ItemMovementForm()
        return render(request, "item_movement_form.html", {"form": form})

# item_movement Detail


def item_movement_detail(request, pk):
    try:
        item_movement = item_movement.objects.select_related('item').get(pk=pk)
        return JsonResponse({
            "status": "success",
            "data": {
                "id": item_movement.id,
                "item": item_movement.item.item_name,
                "movement_type": item_movement.get_movement_type_display(),
                "quantity": item_movement.quantity,
                "description": item_movement.description,
            }
        }, status=200)
    except item_movement.DoesNotExist:
        return JsonResponse({"status": "error", "message": "item_movement record not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# Update item_movement Record


def item_movement_update(request, pk):
    item_movement = get_object_or_404(item_movement, pk=pk)
    if request.method == "POST":
        form = ItemMovementForm(request.POST, instance=item_movement)
        if form.is_valid():
            try:
                form.save()
                return redirect("item_movement_list")
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)
        else:
            return JsonResponse({
                "status": "error",
                "message": "Invalid data submitted",
                "errors": form.errors
            }, status=400)
    else:
        form = ItemMovement(instance=item_movement)
        return render(request, "item_movement_form.html", {"form": form})

# Delete item_movement Record


def item_movement_delete(request, pk):
    try:
        item_movement = get_object_or_404(ItemMovement, pk=pk)
        item_movement.delete()
        return redirect("item_movement_list")
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
