from django.urls import path
from . import views

app_name = 'sales_items'  # This is the namespace

urlpatterns = [
    path("", views.sales_items_list, name="sales_items_list"),
    path("create/", views.sales_items_create, name="sales_items_create"),
    path("<int:pk>/", views.sales_items_detail, name="sales_items_detail"),
    path("<int:pk>/update/", views.sales_items_update, name="sales_items_update"),
    path("<int:pk>/delete/", views.sales_items_delete, name="sales_items_delete"),
]
