import os
import sys
from django.apps import AppConfig


class RequirementsConfig(AppConfig):
    name = 'requirements'

    def ready(self):
        # Only start daemon during actual 'runserver' (reloader child) or explicit daemon flag
        should_start = (
            'runserver' in sys.argv and os.environ.get('RUN_MAIN') == 'true'
        ) or os.environ.get('ENABLE_AUTO_SYNC_DAEMON') == '1'

        if should_start:
            try:
                from .jobdexo_service import start_hourly_sync_daemon
                start_hourly_sync_daemon()
            except Exception:
                pass

