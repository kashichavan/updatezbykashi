import logging
from django.core.management.base import BaseCommand
from requirements.job_link_verifier import verify_active_job_links

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Validates active job application URLs and automatically marks dead, expired, or redirected links as EXPIRED."

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maximum number of active jobs to check in this run (default: 50)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate check without marking jobs as expired in database'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        auto_expire = not options['dry_run']

        self.stdout.write(self.style.NOTICE(f"🔍 Checking active job URLs (Limit: {limit}, Auto-Expire: {auto_expire})..."))
        result = verify_active_job_links(limit=limit, auto_expire=auto_expire)

        self.stdout.write(f"Checked: {result['checked']} | Active: {result['active']} | Expired/Dead: {result['expired']}")

        for item in result['details']:
            if not item['is_active']:
                self.stdout.write(self.style.WARNING(
                    f"  ❌ Job #{item['job_id']} '{item['title']}' ({item['company']}) -> {item['reason']}"
                ))

        if result['expired'] > 0 and auto_expire:
            self.stdout.write(self.style.SUCCESS(f"✅ Soft-expired {result['expired']} dead/closed requirements from active feeds."))
        else:
            self.stdout.write(self.style.SUCCESS("✅ Link health verification complete."))
