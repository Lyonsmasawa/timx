from django.urls import path
from . import views

app_name = 'item'  # This is the namespace

urlpatterns = [
    path("", views.item_list, name="item_list"),
    path("create/", views.item_create, name="item_create"),
    path("<int:pk>/", views.item_detail, name="item_detail"),
    path("<int:pk>/update/", views.item_update, name="item_update"),
    path("<int:pk>/delete/", views.item_delete, name="item_delete"),
]
