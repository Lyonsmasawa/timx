from django.apps import AppConfig


class ItemMovementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = 'item_movement'

    def ready(self):
        import item_movement.signals
