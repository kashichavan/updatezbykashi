import sys
from django.core.management.base import BaseCommand
from django.db import transaction
from requirements.models import IndianDemoProject
from requirements.indian_demo_projects_data import INDIAN_DEMO_PROJECTS


class Command(BaseCommand):
    help = "Seed curated Indian IT industry dummy/portfolio demonstration projects into IndianDemoProject library."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate seeding without committing changes to the database.',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing curated IndianDemoProjects before seeding.',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        clear = options.get('clear', False)

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"=== {'[DRY RUN] ' if dry_run else ''}Seeding Indian Market Demo Projects Library ==="
        ))

        total_available = len(INDIAN_DEMO_PROJECTS)
        self.stdout.write(f"Loaded {total_available} curated project definitions from dataset.")

        try:
            with transaction.atomic():
                if clear:
                    existing_count = IndianDemoProject.objects.filter(is_curated=True).count()
                    self.stdout.write(self.style.WARNING(f"Clearing {existing_count} existing curated projects..."))
                    if not dry_run:
                        IndianDemoProject.objects.filter(is_curated=True).delete()

                created_count = 0
                updated_count = 0

                for item in INDIAN_DEMO_PROJECTS:
                    slug = item['slug']
                    defaults = {
                        'title': item['title'],
                        'fictional_company_name': item.get('fictional_company_name', ''),
                        'location_city': item['location_city'],
                        'location_state': item['location_state'],
                        'industry': item['industry'],
                        'target_job_roles': item.get('target_job_roles', []),
                        'difficulty_level': item.get('difficulty_level', 'Intermediate'),
                        'project_type': item.get('project_type', 'Personal Portfolio Project'),
                        'description': item['description'],
                        'problem_statement': item.get('problem_statement', ''),
                        'technical_stack': item.get('technical_stack', []),
                        'key_features': item.get('key_features', []),
                        'architecture_summary': item.get('architecture_summary', ''),
                        'database_design_summary': item.get('database_design_summary', ''),
                        'api_design_summary': item.get('api_design_summary', ''),
                        'resume_bullet_templates': item.get('resume_bullet_templates', []),
                        'estimated_duration': item.get('estimated_duration', '3-4 weeks'),
                        'learning_outcomes': item.get('learning_outcomes', []),
                        'source_type': item.get('source_type', 'CURATED_INDIAN_DEMO'),
                        'is_curated': True,
                        'is_active': True,
                    }

                    if dry_run:
                        exists = IndianDemoProject.objects.filter(slug=slug).exists()
                        if exists:
                            updated_count += 1
                        else:
                            created_count += 1
                    else:
                        obj, created = IndianDemoProject.objects.update_or_create(
                            slug=slug,
                            defaults=defaults
                        )
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1

                if dry_run:
                    self.stdout.write(self.style.SUCCESS(
                        f"[DRY RUN COMPLETE] Would create {created_count} new projects and update {updated_count} existing projects."
                    ))
                    # Atomic block exits without commit if dry_run
                    transaction.set_rollback(True)
                else:
                    self.stdout.write(self.style.SUCCESS(
                        f"[SUCCESS] Successfully seeded {created_count} created, {updated_count} updated ({created_count + updated_count} total active curated projects)."
                    ))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Seeding failed: {str(e)}"))
            sys.exit(1)
