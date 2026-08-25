import os
import sys
from django.apps import AppConfig


class RequirementsConfig(AppConfig):
    name = 'requirements'

    def ready(self):
        # Only start 5-minute sync daemon during live web server execution (gunicorn / runserver)
        is_web_server = any(srv in (sys.argv[0] if sys.argv else '') for srv in ['gunicorn', 'uwsgi', 'daphne', 'asgi']) or 'runserver' in sys.argv
        if is_web_server:
            try:
                from .jobdexo_service import start_5min_sync_daemon
                start_5min_sync_daemon()
            except Exception:
                pass

