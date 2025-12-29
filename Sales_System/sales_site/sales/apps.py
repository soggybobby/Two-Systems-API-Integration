from django.apps import AppConfig
import os

class SalesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sales"

    def ready(self):
        if os.environ.get("RUN_MAIN") != "true":
            return
        from .ws_products_listener import start_in_background
        start_in_background()
