from django.db import models
from django.contrib.auth.models import User
from django_softdelete.models import SoftDeleteModel


class BaseModel(SoftDeleteModel, models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_%(class)s')
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_%(class)s')

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        if not self.created_by and user:
            self.created_by = user
        if user:
            self.updated_by = user
        super().save(*args, **kwargs)
