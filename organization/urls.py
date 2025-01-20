from django.urls import path
from . import views

app_name = 'organization'  # This is the namespace

urlpatterns = [
    path("", views.organization_list, name="organization_list"),
    path("create/", views.organization_create, name="organization_create"),
    path("<int:pk>/", views.organization_detail, name="organization_detail"),
    path("<int:pk>/update/", views.organization_update,
         name="organization_update"),
    path("<int:pk>/delete/", views.organization_delete,
         name="organization_delete"),
    path('download-invoice/<int:pk>/',
         views.download_invoice, name='download_invoice'),
    path("retry/<str:request_type>/<int:request_id>/",
         views.retry_failed_request, name="retry_failed_request"),
    path("update_purchases_view/<int:org_id>/",
         views.update_purchases_view, name="update_purchases_view"),
    path("verify/<str:request_type>/<str:inv_no>/<int:purchase_id>",
         views.verify_purchase, name="verify_purchase"),
]