from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, login_api, register_api, logout_api

app_name = 'accounts'

router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    # Custom registration view
    path("register/", views.register, name="register"),
    path('login/', views.loginPage, name="login"),
    path('', views.loginPage, name="login"),

    # Django's built-in authentication views
    path("login/", auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/accounts/login/"), name="logout"),
    path('password-change/', views.ChangePasswordView.as_view(),
         name='password_change'),
    path('password-reset/', views.ResetPasswordView.as_view(), name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html'),
         name='password_reset_confirm'),
    
    
    path('api/', include(router.urls)),
    path('api/login/', login_api, name='api-login'),
    path('api/register/', register_api, name='api-register'),
    path('api/logout/', logout_api, name='api-logout'),

]
