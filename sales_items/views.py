from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import SalesItems
from .forms import SalesItemsForm

# List Sales Items
def sales_items_list(request):
    try:
        sales_items = SalesItems.objects.select_related('transaction', 'item').all()
        return render(request, "sales_items_list.html", {"sales_items": sales_items})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# Create Sales Item
def sales_items_create(request):
    if request.method == "POST":
        form = SalesItemsForm(request.POST)
        if form.is_valid():
            try:
                sales_item = form.save()
                return JsonResponse({
                    "status": "success",
                    "message": "Sales Item created successfully!",
                    "data": {
                        "id": sales_item.id,
                        "item_description": sales_item.item_description,
                        "qty": sales_item.qty,
                        "line_total": sales_item.line_total,
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
        form = SalesItemsForm()
        return render(request, "sales_items_form.html", {"form": form})

# Sales Item Detail
def sales_items_detail(request, pk):
    try:
        sales_item = SalesItems.objects.select_related('transaction', 'item').get(pk=pk)
        return JsonResponse({
            "status": "success",
            "data": {
                "id": sales_item.id,
                "item_description": sales_item.item_description,
                "qty": sales_item.qty,
                "rate": sales_item.rate,
                "discount_rate": sales_item.discount_rate,
                "discount_amount": sales_item.discount_amount,
                "tax_code": sales_item.tax_code,
                "line_total": sales_item.line_total,
            }
        }, status=200)
    except SalesItems.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Sales Item not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# Update Sales Item
def sales_items_update(request, pk):
    sales_item = get_object_or_404(SalesItems, pk=pk)
    if request.method == "POST":
        form = SalesItemsForm(request.POST, instance=sales_item)
        if form.is_valid():
            try:
                form.save()
                return redirect("sales_items_list")
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)
        else:
            return JsonResponse({
                "status": "error",
                "message": "Invalid data submitted",
                "errors": form.errors
            }, status=400)
    else:
        form = SalesItemsForm(instance=sales_item)
        return render(request, "sales_items_form.html", {"form": form})

# Delete Sales Item
def sales_items_delete(request, pk):
    try:
        sales_item = get_object_or_404(SalesItems, pk=pk)
        sales_item.delete()
        return redirect("sales_items_list")
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
