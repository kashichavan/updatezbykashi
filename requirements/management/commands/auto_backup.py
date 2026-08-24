import os
import glob
from datetime import datetime, timedelta
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings

class Command(BaseCommand):
    help = "Exports database data into timestamped JSON backup files and rotates old backups."

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-days',
            type=int,
            default=30,
            help='Number of days to keep backup files before auto-pruning (default: 30 days).'
        )

    def handle(self, *args, **options):
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"kashii_backup_{timestamp}.json"
        filepath = backup_dir / filename

        self.stdout.write(self.style.NOTICE(f"Starting automatic database backup to {filepath}..."))

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                call_command(
                    'dumpdata',
                    '--natural-foreign',
                    '--natural-primary',
                    '--indent', '2',
                    exclude=['contenttypes', 'auth.Permission'],
                    stdout=f
                )

            file_size_kb = filepath.stat().st_size / 1024
            self.stdout.write(
                self.style.SUCCESS(f"✓ Backup successfully created: {filename} ({file_size_kb:.2f} KB)")
            )

            # Prune backups older than keep_days
            keep_days = options['keep_days']
            cutoff = datetime.now() - timedelta(days=keep_days)
            for old_file in backup_dir.glob("kashii_backup_*.json"):
                mtime = datetime.fromtimestamp(old_file.stat().st_mtime)
                if mtime < cutoff:
                    old_file.unlink()
                    self.stdout.write(self.style.WARNING(f"Pruned old backup: {old_file.name}"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"✕ Backup failed: {str(e)}"))
            raise e
