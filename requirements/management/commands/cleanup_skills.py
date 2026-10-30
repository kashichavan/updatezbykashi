from django.core.management.base import BaseCommand
from django.db.models import Q
from requirements.models import JobPosting
from requirements.skill_extractor import extract_technical_skills, JUNK_SKILLS


class Command(BaseCommand):
    help = "Audits and repairs all job postings with generic, flawed, or sparse skills using rules & AI."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Preview changes without saving')
        parser.add_argument('--all', action='store_true', help='Re-normalize skills for ALL active jobs')
        parser.add_argument('--ai', action='store_true', help='Leverage Groq AI to generate modern technical skills')
        parser.add_argument('--role', type=str, default='', help='Filter jobs by title (e.g. --role python)')
        parser.add_argument('--limit', type=int, default=0, help='Maximum number of jobs to process (0 = all)')

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        all_jobs = options.get('all', False)
        use_ai = options.get('ai', False)
        role_filter = options.get('role', '').strip()
        limit = options.get('limit', 0)

        self.stdout.write(self.style.NOTICE("🔍 Scanning database for flawed or sparse skills..."))

        if all_jobs:
            targets = JobPosting.objects.all()
        else:
            targets = JobPosting.objects.filter(
                Q(skills_required__icontains='problem solving') |
                Q(skills_required__icontains='technicle') |
                Q(skills_required__iexact='Technical') |
                Q(skills_required__iexact='Technical, Problem Solving') |
                Q(skills_required__iexact='Software Engineering, Problem Solving') |
                Q(skills_required__iexact='Technical, Problem Solving, System Design') |
                Q(skills_required__iexact='Non_technical, Problem Solving') |
                Q(skills_required__iexact='Non_technical, Problem Solving, System Design') |
                Q(skills_required__icontains='Development') |
                Q(skills_required__icontains='Software') |
                Q(skills_required='') |
                Q(skills_required__isnull=True)
            )

        if role_filter:
            targets = targets.filter(title__icontains=role_filter)

        targets = targets.order_by('-id')
        if limit > 0:
            targets = targets[:limit]

        total_count = targets.count() if limit == 0 else min(limit, targets.count())
        self.stdout.write(f"Found {total_count} job postings to review (AI Mode: {'ON' if use_ai else 'OFF'}).")

        updated_count = 0
        samples = []

        for job in targets:
            old_skills = (job.skills_required or '').strip()
            cat_slug = job.category.slug if job.category else 'software-engineering'
            
            new_skills = extract_technical_skills(
                title=job.title,
                raw_skills=old_skills,
                description=job.description or '',
                category_slug=cat_slug,
                use_ai=use_ai
            )

            if new_skills and new_skills != old_skills:
                updated_count += 1
                if len(samples) < 15:
                    samples.append((job.id, job.title, job.company_name, old_skills, new_skills))
                
                if not dry_run:
                    job.skills_required = new_skills
                    job.save(update_fields=['skills_required'])

        for j_id, title, comp, old_s, new_s in samples:
            self.stdout.write(f"  #{j_id} [{comp}] {title}:")
            self.stdout.write(f"      OLD: \"{old_s}\"")
            self.stdout.write(self.style.SUCCESS(f"      NEW: \"{new_s}\""))

        mode = "[DRY RUN] Would update" if dry_run else "Successfully repaired and stored"
        self.stdout.write(self.style.SUCCESS(f"✅ {mode} {updated_count} of {total_count} job skill sets!"))

        if not dry_run and updated_count > 0:
            try:
                from requirements.backup_service import trigger_auto_backup_async
                trigger_auto_backup_async()
                self.stdout.write(self.style.SUCCESS("💾 Triggered automatic snapshot backup to preserve skills on redeploy."))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Backup notice: {e}"))
