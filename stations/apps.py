from django.apps import AppConfig


class StationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stations'

    def ready(self):
        from django.conf import settings
        print("[StationsConfig] ready() called!")

        if getattr(settings, "SCHEDULER_AUTOSTART", True):
            print("[StationsConfig] Starting scheduler...")
            from .scheduler import start_scheduler
            start_scheduler()
