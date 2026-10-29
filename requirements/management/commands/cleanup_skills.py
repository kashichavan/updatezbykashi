from django.core.management.base import BaseCommand
from django.db.models import Q
from requirements.models import JobPosting
from requirements.skill_extractor import extract_technical_skills, JUNK_SKILLS


class Command(BaseCommand):
    help = "Audits and repairs all job postings with generic or flawed skills (e.g. 'Technical, Problem Solving')."

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Preview changes without saving')
        parser.add_argument('--all', action='store_true', help='Re-normalize skills for ALL active jobs')

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        all_jobs = options.get('all', False)

        self.stdout.write(self.style.NOTICE("🔍 Scanning database for flawed or generic skills..."))

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
                Q(skills_required='') |
                Q(skills_required__isnull=True)
            )

        total_count = targets.count()
        self.stdout.write(f"Found {total_count} job postings needing skill review/repair.")

        updated_count = 0
        samples = []

        for job in targets:
            old_skills = (job.skills_required or '').strip()
            cat_slug = job.category.slug if job.category else 'software-engineering'
            
            new_skills = extract_technical_skills(
                title=job.title,
                raw_skills=old_skills,
                description=job.description or '',
                category_slug=cat_slug
            )

            if new_skills and new_skills != old_skills:
                updated_count += 1
                if len(samples) < 10:
                    samples.append((job.id, job.title, job.company_name, old_skills, new_skills))
                
                if not dry_run:
                    job.skills_required = new_skills
                    job.save(update_fields=['skills_required'])

        for j_id, title, comp, old_s, new_s in samples:
            self.stdout.write(f"  #{j_id} [{comp}] {title}:")
            self.stdout.write(f"      OLD: \"{old_s}\"")
            self.stdout.write(self.style.SUCCESS(f"      NEW: \"{new_s}\""))

        mode = "[DRY RUN] Would update" if dry_run else "Successfully repaired"
        self.stdout.write(self.style.SUCCESS(f"✅ {mode} {updated_count} of {total_count} job skill sets!"))
