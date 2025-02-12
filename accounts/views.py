from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.models import User
from .forms import CustomUserForm
from django.contrib import messages
from .emails import send_welcome_resident, send_welcome_email
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView, PasswordResetView
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404, HttpResponse
from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .serializers import UserSerializer, LoginSerializer, RegisterSerializer
from organization.views import *



@login_required(login_url='login')
def home(request):
    user = request.user

    # Check if user is authenticated
    if user.is_authenticated:
        return redirect('organization:organization_list')  # Redirect to organization_list if user is logged in
    else:
        raise Http404("User not found")  # Raise a 404 error for unauthorized access


def loginPage(request):
    page = 'login'

    if request.user.is_authenticated:
        return redirect('organization:organization_list')

    if request.method == 'POST':
        username = request.POST.get("username").lower()
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('organization:organization_list')
        else:
            messages.error(request, 'Invalid username or Password')

    context = {'page': page}
    return render(request, 'accounts/register.html', context)


@login_required(login_url='login')
def logoutUser(request):
    logout(request)
    return redirect(loginPage)

# END USER || ADMIN

# ADMIN SECTION


def register(request):
    if request.user.is_authenticated:
        logout(request)

    if request.method == 'POST':
        form = CustomUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.email = user.email.lower()
            user.first_name = user.first_name.lower()
            user.last_name = user.last_name.lower()
            user.save()

            # User.objects.create(user=user)

            try:
                email = user.email
                name = user.username
                send_welcome_email(name, email)
                login(request, user)
                return redirect('organization:organization_list')
            except:
                login(request, user)
                return redirect('organization:organization_list')
        else:
            messages.error(request, 'please try again')
    else:
        form = CustomUserForm()

    context = {'form': form}
    return render(request, 'accounts/register.html', context)


class ChangePasswordView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'accounts/change_password.html'
    success_message = "Successfully Changed Your Password"
    # success_url = reverse_lazy(residentDashboard)


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    success_message = "We've emailed you instructions for setting your password, " \
                      "if an account exists with the email you entered. You should receive them shortly." \
                      " If you don't receive an email, " \
                      "please make sure you've entered the address you registered with, and check your spam folder."
    success_url = reverse_lazy('accounts:login')
    

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_api(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)  # Ensure Token is imported
            return Response({"token": token.key, "user": UserSerializer(user).data})
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_api(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": UserSerializer(user).data}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_api(request):
    request.user.auth_token.delete()
    logout(request)
    return Response({"message": "Logged out successfully"}, status=status.HTTP_200_OK)