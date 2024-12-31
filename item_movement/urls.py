from django.urls import path
from . import views

app_name = 'item_movement'  # This is the namespace

urlpatterns = [
    path("", views.item_movement_list, name="item_movement_list"),
    path("create/", views.item_movement_create, name="item_movement_create"),
    path("<int:pk>/", views.item_movement_detail, name="item_movement_detail"),
    path("<int:pk>/update/", views.item_movement_update, name="item_movement_update"),
    path("<int:pk>/delete/", views.item_movement_delete, name="item_movement_delete"),
]
