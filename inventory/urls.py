from django.urls import path
from . import views

app_name = 'inventory'  # This is the namespace

urlpatterns = [
    path("", views.inventory_list, name="inventory_list"),
    path("create/", views.inventory_create, name="inventory_create"),
    path("<int:pk>/", views.inventory_detail, name="inventory_detail"),
    path("<int:pk>/update/", views.inventory_update, name="inventory_update"),
    path("<int:pk>/delete/", views.inventory_delete, name="inventory_delete"),
]
