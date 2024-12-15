from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class CustomUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email or username already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username').lower()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("A user with this email or username already exists.")
        return username
