from django.urls import path
from . import views

app_name = 'sales_items'  # This is the namespace

urlpatterns = [
    path("", views.sales_items_list, name="sales_items_list"),
    path("create/<int:pk>/", views.sales_items_create, name="sales_items_create"),
    path("create_note/<int:organization_id>/<int:transaction_id>/",
         views.sales_items_create_note, name="sales_items_create_note"),
    path("<int:pk>/", views.sales_items_detail, name="sales_items_detail"),
    path("<int:pk>/update/", views.sales_items_update, name="sales_items_update"),
    path("<int:pk>/delete/", views.sales_items_delete, name="sales_items_delete"),
    path("generate-invoice/<int:request_log_id>/<int:transaction_id>/",
         views.generate_invoice_pdf, name="generate_invoice_pdf"),
    path("generate_credit_note_pdf/<int:request_log_id>/<int:transaction_id>/",
         views.generate_credit_note_pdf, name="generate_credit_note_pdf"),
    path('items-autocomplete/', views.ItemAutocomplete.as_view(),
         name='items-autocomplete'),
]
