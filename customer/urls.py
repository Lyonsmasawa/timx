from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

app_name = 'customer'  # This is the namespace

# router = DefaultRouter()
# router.register(r'customers', views.CustomerViewSet)

urlpatterns = [
    path("", views.customer_list, name="customer_list"),
    path("create/<int:pk>", views.customer_create, name="customer_create"),
    path("<int:pk>/", views.customer_detail, name="customer_detail"),
    path("<int:pk>/update/", views.customer_update, name="customer_update"),
    path("<int:pk>/delete/", views.customer_delete, name="customer_delete"),
    
    
    # path('api/', include(router.urls)),
    # path('api/customers/<int:pk>/update/', views.customer_update, name='api-customer-update'),
    # path('api/customers/<int:pk>/delete/', views.customer_delete, name='api-customer-delete'),
]
