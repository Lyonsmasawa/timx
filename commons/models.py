from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    key = models.CharField(max_length=7, unique=True, editable=False)

    class Meta:
        abstract = True

    def generate_unique_key(self, queryset):
        """
        Generate a unique key based on the sequence of existing keys.
        Subclasses can pass the relevant queryset for context-specific uniqueness.
        """
        last_key = queryset.order_by(
            "-key").values_list("key", flat=True).first()
        next_key = int(last_key) + 1 if last_key else 1
        return f"{next_key:07d}"

    def save(self, *args, **kwargs):
        # Make sure the key is generated before saving
        if not self.key:
            raise NotImplementedError(
                "Subclasses must implement their own unique key generation logic."
            )
        super().save(*args, **kwargs)
