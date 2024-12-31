"""
URL configuration for etimsx project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path("accounts/", include("accounts.urls")),  # Add this line
    path("", include("accounts.urls")),  # Add this line

    # Include each app's URLs under its own unique prefix
    path('api/organization/', include('organization.urls')),  # organization URLs
    path('api/item/', include('item.urls')),                  # item URLs
    path('api/customer/', include('customer.urls')),          # customer URLs
    path('api/transaction/', include('transaction.urls')),    # transaction URLs
    path('api/item_movement/', include('item_movement.urls')),        # inventory URLs
    path('api/sales_items/', include('sales_items.urls')),    # sales_items URLs
]



urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)