import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "etimsx.settings")

# Create Celery instance
app = Celery("etimsx")

# Load task modules from all registered Django app configs.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in installed apps
app.autodiscover_tasks()

# "update_item_classification_daily": {
#     "task": "api_tracker.tasks.fetch_and_update_item_classification",
#     "schedule": 50,
# },
app.conf.beat_schedule = {
    "retry_failed_requests": {
        "task": "api_tracker.tasks.retry_failed_requests",
        "schedule": 300.0,  # Every 5 minutes
    },
}

app.conf.timezone = "Africa/Nairobi"
# crontab(hour=0, minute=0)


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
