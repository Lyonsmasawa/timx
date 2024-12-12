from django.urls import path
from . import views

app_name = 'transaction'  # This is the namespace

urlpatterns = [
    path("", views.transaction_list, name="transaction_list"),
    path("create/", views.transaction_create, name="transaction_create"),
    path("<int:pk>/", views.transaction_detail, name="transaction_detail"),
    path("<int:pk>/update/", views.transaction_update, name="transaction_update"),
    path("<int:pk>/delete/", views.transaction_delete, name="transaction_delete"),
]