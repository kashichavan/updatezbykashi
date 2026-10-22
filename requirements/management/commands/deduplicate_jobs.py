"""
Django Management Command: Deduplicate Jobs
Performs an India-wide cross-source audit and purge of duplicate JobPosting records.

Usage:
    python manage.py deduplicate_jobs
    python manage.py deduplicate_jobs --dry-run
    python manage.py deduplicate_jobs --verbose
"""

import sys
from django.core.management.base import BaseCommand
from requirements.job_aggregator.deduplicator import purge_all_database_duplicates


class Command(BaseCommand):
    help = "Audit and purge duplicate job listings across all sources (Naukri, LinkedIn, Jobdexo, etc.)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate duplicate detection without deleting records from the database.'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Print detailed breakdown of each duplicate cluster found.'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        verbose = options.get('verbose', False)

        mode_str = "[DRY RUN] " if dry_run else ""
        self.stdout.write(self.style.NOTICE(f"🚀 {mode_str}Starting comprehensive cross-source job deduplication sweep..."))

        stats = purge_all_database_duplicates(dry_run=dry_run)

        scanned = stats['scanned_total']
        clusters = stats['duplicate_clusters']
        found = stats['duplicates_found']
        deleted = stats['duplicates_deleted']
        updated = stats['primary_records_updated']

        self.stdout.write(self.style.SUCCESS(
            f"✅ Deduplication scan finished:\n"
            f"   - Total active jobs scanned: {scanned}\n"
            f"   - Duplicate clusters found:  {clusters}\n"
            f"   - Total duplicate records:   {found}\n"
            f"   - Records deleted:           {deleted} {'(simulated)' if dry_run else ''}\n"
            f"   - Primary records upgraded:  {updated}"
        ))

        if verbose and stats.get('details'):
            self.stdout.write("\nDetailed Duplicate Clusters:")
            for item in stats['details']:
                self.stdout.write(
                    f"   • Primary #{item['primary_id']}: '{item['title']}' at '{item['company']}' "
                    f"-> Duplicate IDs: {item['duplicate_ids']}"
                )
