from django.urls import path
from .views import *

app_name = "device"

urlpatterns = [
    path("status/<int:org_id>/", get_device_status, name="get_device_status"),
    path("set-live/<int:org_id>/", set_live_mode, name="set_live_mode"),
    path("go-live/<int:org_id>/", initialize_device, name="go_live_mode"),
    path("import-keys/<int:org_id>/", import_device_keys, name="import_device_keys"),
    path("list/<int:org_id>/", get_available_devices, name="get_available_devices"),
    path("set-active/<int:org_id>/<int:device_id>/", set_active_device, name="set_active_device"),
    path("switch-to-demo/<int:org_id>/", switch_to_demo_mode, name="switch_to_demo_mode"),
]
