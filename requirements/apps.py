import os
import sys
from django.apps import AppConfig


class RequirementsConfig(AppConfig):
    name = 'requirements'

    def ready(self):
        # Exclude one-off management commands from spawning persistent background threads
        excluded_commands = {
            'migrate', 'makemigrations', 'collectstatic', 'test',
            'createsuperuser', 'check', 'shell', 'dbshell', 'inspectdb'
        }
        is_mgmt_cmd = any(cmd in sys.argv for cmd in excluded_commands)

        if not is_mgmt_cmd:
            # If running runserver locally, ensure daemon only starts in the main reloader child
            if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') != 'true':
                return

            try:
                from .jobdexo_service import start_hourly_sync_daemon
                start_hourly_sync_daemon()
            except Exception:
                pass

