from django.urls import path
from . import views

app_name = 'organization'  # This is the namespace

urlpatterns = [
    path("", views.organization_list, name="organization_list"),
    path("create/", views.organization_create, name="organization_create"),
    path("<int:pk>/", views.organization_detail, name="organization_detail"),
    path("<int:pk>/update/", views.organization_update, name="organization_update"),
    path("<int:pk>/delete/", views.organization_delete, name="organization_delete"),
]
