import os
import csv
import glob
from datetime import datetime, timedelta
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from requirements.models import JobPosting, Category, JobGroup, StudentApplication, ContactInquiry

class Command(BaseCommand):
    help = "Exports core business database data into clean, compact JSON and CSV backup files."

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-days',
            type=int,
            default=30,
            help='Number of days to keep backup files before auto-pruning (default: 30 days).'
        )
        parser.add_argument(
            '--format',
            type=str,
            default='all',
            choices=['all', 'json', 'csv'],
            help='Backup format to export: json, csv, or all (default: all).'
        )
        parser.add_argument(
            '--include-logs',
            action='store_true',
            help='Include ephemeral visitor analytics logs (SiteVisit) in dump.'
        )

    def handle(self, *args, **options):
        backup_dir = Path(settings.BASE_DIR) / 'backups'
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        fmt = options['format']
        keep_days = options['keep_days']
        include_logs = options.get('include_logs', False)

        self.stdout.write(self.style.NOTICE(f"Starting optimized database backup (format: {fmt}) to {backup_dir}..."))

        # ── 1. EXPORT CLEAN FULL DATABASE JSON FIXTURE ──────────────────
        if fmt in ['all', 'json']:
            json_filename = f"kashii_backup_{timestamp}.json"
            json_filepath = backup_dir / json_filename
            
            # Exclude ephemeral logs & sessions to keep backup ultra-fast and lightweight
            excludes = ['contenttypes', 'auth.Permission', 'sessions.session', 'debugger.debugsession', 'debugger.executiontracestep']
            if not include_logs:
                excludes.append('requirements.sitevisit')

            try:
                with open(json_filepath, 'w', encoding='utf-8') as f:
                    call_command(
                        'dumpdata',
                        '--natural-foreign',
                        '--natural-primary',
                        '--indent', '2',
                        exclude=excludes,
                        stdout=f
                    )
                json_size_kb = json_filepath.stat().st_size / 1024
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Clean JSON backup created: {json_filename} ({json_size_kb:.2f} KB / {json_size_kb/1024:.2f} MB)")
                )
                
                # Update latest snapshot
                latest_json = backup_dir / "kashii_full_snapshot_latest.json"
                with open(json_filepath, 'r', encoding='utf-8') as src, open(latest_json, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"✕ JSON backup failed: {str(e)}"))

        # ── 2. EXPORT CSV BACKUPS FOR CORE MODELS ───────────────────────
        if fmt in ['all', 'csv']:
            try:
                # A. Job Postings CSV
                jobs_file = backup_dir / f"kashii_jobs_{timestamp}.csv"
                jobs_latest = backup_dir / "kashii_jobs_latest.csv"
                job_fields = [
                    'id', 'uuid', 'title', 'company_name', 'category_id', 'category_name',
                    'job_type', 'stipend_salary', 'location', 'is_remote', 'skills_required',
                    'apply_url', 'status', 'views_count', 'applications_count', 'posted_date',
                    'deadline', 'created_at', 'eligibility', 'selection_process'
                ]
                with open(jobs_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(job_fields)
                    for job in JobPosting.objects.select_related('category').all():
                        writer.writerow([
                            job.id, str(job.uuid), job.title, job.company_name,
                            job.category.id if job.category else '',
                            job.category.name if job.category else '',
                            job.job_type, job.stipend_salary, job.location, job.is_remote,
                            job.skills_required, job.apply_url, job.status, job.views_count,
                            job.applications_count, job.posted_date, job.deadline, job.created_at,
                            job.eligibility, job.selection_process
                        ])
                
                with open(jobs_file, 'r', encoding='utf-8') as src, open(jobs_latest, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())

                jobs_size_kb = jobs_file.stat().st_size / 1024
                self.stdout.write(
                    self.style.SUCCESS(f"✓ CSV backup created: {jobs_file.name} ({jobs_size_kb:.2f} KB, {JobPosting.objects.count()} jobs)")
                )

                # B. Categories CSV
                cat_file = backup_dir / f"kashii_categories_{timestamp}.csv"
                with open(cat_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['id', 'name', 'slug', 'icon', 'description'])
                    for cat in Category.objects.all():
                        writer.writerow([cat.id, cat.name, cat.slug, cat.icon, cat.description])

                # C. Job Groups CSV
                jg_file = backup_dir / f"kashii_jobgroups_{timestamp}.csv"
                with open(jg_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['id', 'name', 'posted_date', 'banner_tag', 'slug', 'jobs_count', 'created_at'])
                    for jg in JobGroup.objects.all():
                        writer.writerow([jg.id, jg.name, jg.posted_date, jg.banner_tag, jg.slug, jg.jobs.count(), jg.created_at])

                # D. Student Applications CSV
                app_file = backup_dir / f"kashii_applications_{timestamp}.csv"
                with open(app_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['id', 'student_name', 'student_email', 'student_phone', 'job_id', 'job_title', 'status', 'created_at'])
                    for app in StudentApplication.objects.select_related('job').all():
                        writer.writerow([
                            app.id, app.student_name, app.student_email, app.student_phone,
                            app.job.id if app.job else '',
                            app.job.title if app.job else '',
                            app.status, app.created_at
                        ])

                self.stdout.write(self.style.SUCCESS(f"✓ All core model CSV tables exported successfully."))

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"✕ CSV backup failed: {str(e)}"))

        # ── 3. PRUNE BACKUPS OLDER THAN KEEP_DAYS ───────────────────────
        cutoff = datetime.now() - timedelta(days=keep_days)
        pruned_count = 0
        for pattern in ["kashii_backup_*.json", "kashii_*_*.csv"]:
            for old_file in backup_dir.glob(pattern):
                if "latest" in old_file.name:
                    continue
                mtime = datetime.fromtimestamp(old_file.stat().st_mtime)
                if mtime < cutoff:
                    old_file.unlink()
                    pruned_count += 1
                    self.stdout.write(self.style.WARNING(f"Pruned old backup: {old_file.name}"))
