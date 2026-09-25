import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.sessions.models import Session
from requirements.models import SiteVisit

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Database maintenance (cleans expired sessions without deleting traffic or visit data)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🔍 Running Database Maintenance..."))

        # Purge expired Django sessions only (standard maintenance)
        expired_sessions, _ = Session.objects.filter(expire_date__lt=timezone.now()).delete()
        self.stdout.write(f"  - Purged {expired_sessions} expired Django sessions.")

        total_visits = SiteVisit.objects.count()
        self.stdout.write(self.style.SUCCESS(f"✅ Maintenance complete. All {total_visits} traffic visits preserved."))

