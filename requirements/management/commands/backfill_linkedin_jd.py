from django.core.management.base import BaseCommand

from requirements.job_aggregator.adapters.linkedin_adapter import backfill_linkedin_descriptions


class Command(BaseCommand):
    help = "Replace placeholder descriptions on active LinkedIn jobs with the real job description."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=25)

    def handle(self, *args, **opts):
        stats = backfill_linkedin_descriptions(limit=opts["limit"])
        self.stdout.write(self.style.SUCCESS(f"LinkedIn JD backfill: {stats}"))
