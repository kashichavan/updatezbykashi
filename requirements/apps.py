import os
import sys
from django.apps import AppConfig


class RequirementsConfig(AppConfig):
    name = 'requirements'

    def ready(self):
        # Don't start background daemon during manage.py migration / build commands
        is_management_cmd = any(cmd in sys.argv for cmd in ['makemigrations', 'migrate', 'check', 'test', 'collectstatic', 'createsuperuser'])
        if not is_management_cmd:
            try:
                from .jobdexo_service import start_5min_sync_daemon
                start_5min_sync_daemon()
            except Exception:
                pass

