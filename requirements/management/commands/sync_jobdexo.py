from django.core.management.base import BaseCommand
from django.utils import timezone
from requirements.jobdexo_service import auto_import_from_jobdexo, resolve_all_jobdexo_apply_urls


class Command(BaseCommand):
    help = 'Automatically fetch and sync fresh verified job opportunities from Jobdexo into Kashii Updatez.'

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=5, help='Number of latest jobs to fetch from Jobdexo (default: 5)')
        parser.add_argument('--group-name', type=str, default='', help='Optional custom name for the created requirement group')
        parser.add_argument('--urls', nargs='+', type=str, default=[], help='Specific Jobdexo URLs to import')

    def handle(self, *args, **options):
        count = options['count']
        custom_name = options['group_name']
        urls = options['urls']

        self.stdout.write(self.style.NOTICE("🔍 Resolving any legacy Jobdexo apply URLs to direct career ATS links..."))
        resolved = resolve_all_jobdexo_apply_urls()
        self.stdout.write(self.style.SUCCESS(f"✅ Resolved {resolved['updated']} legacy links!"))

        self.stdout.write(self.style.NOTICE(f"🚀 Starting Jobdexo Sync (fetching up to {count} latest jobs)..."))

        result = auto_import_from_jobdexo(
            urls=urls if urls else None,
            limit=count,
            group_name=custom_name if custom_name else None
        )

        imported = result['imported_count']
        total = result['total_in_group']
        group_name = result['group_name']
        group_url = result['group_url']

        if imported > 0:
            self.stdout.write(self.style.SUCCESS(
                f"✅ Successfully imported {imported} new opportunities! Group '{group_name}' active for 7 days at {group_url}"
            ))
        else:
            self.stdout.write(self.style.WARNING(
                f"ℹ️ No new jobs found (all {total} jobs are already in database)."
            ))
