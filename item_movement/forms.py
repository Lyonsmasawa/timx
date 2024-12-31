from django import forms
from .models import ItemMovement

class ItemMovementForm(forms.ModelForm):
    class Meta:
        model = ItemMovement
        fields = "__all__"
