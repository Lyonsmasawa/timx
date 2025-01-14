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
    path('country-code-autocomplete/', views.CountryCodeAutocomplete.as_view(),
         name='country-code-autocomplete'),
    path('item-type-code-autocomplete/', views.ItemTypeCodeAutocomplete.as_view(),
         name='item-type-code-autocomplete'),
    path('quantity-unit-code-autocomplete/', views.QuantityUnitCodeAutocomplete.as_view(),
         name='quantity-unit-code-autocomplete'),
    path('package-unit-code-autocomplete/', views.PackageUnitCodeAutocomplete.as_view(),
         name='package-unit-code-autocomplete'),
    path('item-class-code-autocomplete/', views.ItemClassCodeAutocomplete.as_view(),
         name='item-class-code-autocomplete'),
    path('item-tax-code-autocomplete/', views.ItemTaxCodeAutocomplete.as_view(),
         name='item-tax-code-autocomplete'),
    
]
