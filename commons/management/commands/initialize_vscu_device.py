from django.core.management.base import BaseCommand
from api_tracker.tasks import async_initialize_vscu_device

class Command(BaseCommand):
    help = "Initializes the VSCU device asynchronously"

    def handle(self, *args, **kwargs):
        async_initialize_vscu_device.delay()
        self.stdout.write(self.style.SUCCESS("✅ VSCU Device initialization started."))