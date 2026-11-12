"""
WSGI config for reqpulse project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reqpulse.settings')

application = get_wsgi_application()

# Boot-time SQLite integrity check and self-healing
try:
    from requirements.db_recovery import check_database_health, auto_repair_database
    healthy, reason = check_database_health()
    if not healthy:
        print(f"==> [WSGI Boot] Database unhealthy on startup ({reason}). Auto-repairing...")
        auto_repair_database()
    else:
        print("==> [WSGI Boot] Database verified healthy.")
except Exception as e:
    print(f"==> [WSGI Boot] Integrity check notice: {e}")
