from django.apps import AppConfig

class CommonsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "commons"

    # def ready(self):
    #     """
    #     Runs when Django starts.
    #     Triggers VSCU device initialization in Celery.
    #     Uses a delayed import to avoid circular dependency.
    #     """
    #     from django.core.management import call_command
    #     call_command("initialize_vscu_device")  # Runs a Django management command
