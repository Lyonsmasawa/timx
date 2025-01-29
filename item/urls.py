from django.urls import path
from . import views

app_name = 'item'  # This is the namespace

urlpatterns = [
    path("", views.item_list, name="item_list"),
    path("create/<int:pk>/", views.item_create, name="item_create"),
    path("<int:pk>/", views.item_detail, name="item_detail"),
    path("<int:pk>/update/", views.item_update, name="item_update"),
    path("<int:pk>/delete/", views.item_delete, name="item_delete"),
    path('update-quantity/', views.update_item_quantity, name='update_quantity'),
    path('update_mapped_item_quantity/', views.update_mapped_item_quantity,
         name='update_mapped_item_quantity'),
    path('create_items_from_purchase/<int:pk>/', views.create_items_from_purchase,
         name='create_items_from_purchase'),
    path("save-item-composition/", views.save_item_composition,
         name="save_item_composition"),
    path('ajax/filter/<str:field_name>/',
         views.ajax_filter, name='ajax_filter'),
]
