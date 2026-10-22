from django.core.management.base import BaseCommand
from requirements.job_aggregator.orchestrator import orchestrator


class Command(BaseCommand):
    help = 'Discover and ingest fresh jobs across India with last-hour tracking and multi-tier deduplication.'

    def add_arguments(self, parser):
        parser.add_argument('--sources', nargs='+', type=str, default=[], help='Specific sources to run (e.g. jobdexo greenhouse ashby publicfeeds)')
        parser.add_argument('--limit', type=int, default=10, help='Max jobs to fetch per source (default: 10)')
        parser.add_argument('--last-hours', type=int, default=None, help='Filter by publication window (e.g. 1 for last-hour jobs)')
        parser.add_argument('--keywords', type=str, default=None, help='Filter by technology or role keyword')
        parser.add_argument('--location', type=str, default=None, help='Filter by Indian city (e.g. Bengaluru, Hyderabad, Pune, Mumbai)')
        parser.add_argument('--list-sources', action='store_true', help='List all registered sources and exit')

    def handle(self, *args, **options):
        if options.get('list_sources'):
            self.stdout.write(self.style.NOTICE("📡 Registered Job Sources:"))
            for s in orchestrator.get_registered_sources():
                status = "✅ Enabled" if s['is_enabled'] else "⏸️ Disabled"
                self.stdout.write(f"  • {s['name']:<15} {status} (rate limit delay: {s['rate_limit_delay']}s)")
            return

        sources = options.get('sources')
        limit = options.get('limit')
        last_hours = options.get('last_hours')
        keywords = options.get('keywords')
        location = options.get('location')

        self.stdout.write(self.style.NOTICE(
            f"🚀 Initiating India-Wide Ingestion Cycle "
            f"(Sources: {sources or 'All Enabled'}, Limit: {limit}, Last Hours: {last_hours or 'Any'})..."
        ))

        result = orchestrator.run_aggregation(
            sources=sources if sources else None,
            limit_per_source=limit,
            last_hours=last_hours,
            keywords=keywords,
            location=location
        )

        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 Ingestion Complete in {result['duration_seconds']}s!\n"
            f"  • Discovered: {result['total_discovered']}\n"
            f"  • Imported:   {result['total_imported']}\n"
            f"  • Duplicates: {result['total_duplicates']} (Observed & refreshed)\n"
            f"  • Batch ID:   {result['batch_id']}"
        ))

        self.stdout.write("\n📊 Per-Source Breakdown:")
        for src, data in result.get('sources', {}).items():
            if data.get('status') == 'FAILED':
                self.stdout.write(self.style.ERROR(f"  ❌ {src:<15} FAILED: {data.get('error')}"))
            else:
                self.stdout.write(
                    f"  ✅ {src:<15} Imported: {data.get('imported', 0):<3} "
                    f"Duplicates: {data.get('duplicates', 0):<3} "
                    f"Duration: {data.get('duration_s', 0)}s"
                )
