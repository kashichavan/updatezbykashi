import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.sessions.models import Session
from requirements.models import SiteVisit

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Enforces strict database quota limits (Neon 512MB / Compute Protection)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🔍 Running Database Quota Enforcement..."))

        # 1. Purge all Bot visits
        bot_deleted, _ = SiteVisit.objects.filter(is_bot=True).delete()
        self.stdout.write(f"  - Deleted {bot_deleted} bot visit logs.")

        # 2. Purge visits older than 14 days
        cutoff = timezone.now() - timedelta(days=14)
        old_deleted, _ = SiteVisit.objects.filter(timestamp__lt=cutoff).delete()
        self.stdout.write(f"  - Deleted {old_deleted} visit logs older than 14 days.")

        # 3. Hard ceiling: Max 5,000 analytics records
        total_visits = SiteVisit.objects.count()
        if total_visits > 5000:
            excess_ids = list(SiteVisit.objects.order_by('-timestamp').values_list('id', flat=True)[4000:])
            if excess_ids:
                capped_deleted, _ = SiteVisit.objects.filter(id__in=excess_ids).delete()
                self.stdout.write(f"  - Capped table: removed {capped_deleted} oldest visits beyond limit.")

        # 4. Purge expired Django sessions
        expired_sessions, _ = Session.objects.filter(expire_date__lt=timezone.now()).delete()
        self.stdout.write(f"  - Purged {expired_sessions} expired Django sessions.")

        remaining_visits = SiteVisit.objects.count()
        self.stdout.write(self.style.SUCCESS(f"✅ Quota Enforcement complete. Total visits retained: {remaining_visits} (under 1 MB)."))
