from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Transaction
from .forms import TransactionForm

# List Transactions
def transaction_list(request):
    try:
        transactions = Transaction.objects.select_related('organization', 'customer').all()
        return render(request, "transaction_list.html", {"transactions": transactions})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# Create Transaction
def transaction_create(request):
    if request.method == "POST":
        form = TransactionForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                transaction = form.save()
                return JsonResponse({
                    "status": "success",
                    "message": "Transaction created successfully!",
                    "data": {
                        "id": transaction.id,
                        "trader_invoice_number": transaction.trader_invoice_number,
                        "document_type": transaction.document_type,
                        "receipt_number": transaction.receipt_number,
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
        form = TransactionForm()
        return render(request, "transaction_form.html", {"form": form})

# Transaction Detail
def transaction_detail(request, pk):
    try:
        transaction = Transaction.objects.select_related('organization', 'customer').get(pk=pk)
        return JsonResponse({
            "status": "success",
            "data": {
                "id": transaction.id,
                "trader_invoice_number": transaction.trader_invoice_number,
                "document_type": transaction.document_type,
                "receipt_number": transaction.receipt_number,
                "document_path": transaction.document_path.url if transaction.document_path else None,
            }
        }, status=200)
    except Transaction.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Transaction not found"}, status=404)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

# Update Transaction
def transaction_update(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk)
    if request.method == "POST":
        form = TransactionForm(request.POST, request.FILES, instance=transaction)
        if form.is_valid():
            try:
                form.save()
                return redirect("transaction_list")
            except Exception as e:
                return JsonResponse({"status": "error", "message": str(e)}, status=500)
        else:
            return JsonResponse({
                "status": "error",
                "message": "Invalid data submitted",
                "errors": form.errors
            }, status=400)
    else:
        form = TransactionForm(instance=transaction)
        return render(request, "transaction_form.html", {"form": form})

# Delete Transaction
def transaction_delete(request, pk):
    try:
        transaction = get_object_or_404(Transaction, pk=pk)
        transaction.delete()
        return redirect("transaction_list")
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
