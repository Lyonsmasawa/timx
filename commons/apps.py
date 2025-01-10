from django.apps import AppConfig


class CommonsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "commons"

    def ready(self):
        """
        Runs when Django starts.
        Triggers VSCU device initialization in Celery.
        Uses a delayed import to avoid circular dependency.
        """
        from commons.utils import initialize_vscu_device
        # initialize_vscu_device()
