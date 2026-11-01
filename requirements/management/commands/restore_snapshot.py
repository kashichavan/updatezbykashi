import json
import uuid as py_uuid
from pathlib import Path
from datetime import date, datetime, time, timedelta
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_date
from requirements.models import Category as JobCategory, JobPosting, JobGroup


LISTING_DAYS = 7


def listing_deadline(posted_date, fallback):
    """A listing closes seven days after it was posted, however often we redeploy."""
    posted = posted_date if isinstance(posted_date, date) else parse_date(str(posted_date or '')[:10])
    if not posted:
        return fallback
    return timezone.make_aware(datetime.combine(posted + timedelta(days=LISTING_DAYS), time.max))


class Command(BaseCommand):
    help = "Fast bulk-restore of the snapshot. Listings older than seven days stay closed."

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='backups/kashii_full_snapshot_latest.json',
            help='Path to the backup JSON file'
        )

    def handle(self, *args, **options):
        file_path = Path(options['file'])
        if not file_path.is_absolute():
            file_path = Path(settings.BASE_DIR) / file_path

        if not file_path.exists():
            self.stderr.write(self.style.ERROR(f"Backup file not found: {file_path}"))
            return

        self.stdout.write(self.style.NOTICE(f"Loading snapshot from {file_path}..."))
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        now = timezone.now()
        default_deadline = now + timedelta(days=7)
        default_posted_date = timezone.localtime(now).date()

        data_by_model = {}
        for item in data:
            m = item.get('model')
            if m:
                data_by_model.setdefault(m, []).append(item)

        with transaction.atomic():
            # 1. Job Categories
            cat_id_map = {}
            for item in data_by_model.get('requirements.category', []):
                old_pk = item.get('pk')
                f = item.get('fields', {})
                slug = f.get('slug') or f"cat-{old_pk}"
                name = f.get('name') or "Software & Tech"
                obj = JobCategory.objects.filter(slug=slug).first() or JobCategory.objects.filter(name=name).first()
                if not obj:
                    obj = JobCategory.objects.create(
                        name=name,
                        slug=slug,
                        icon=f.get('icon', 'code'),
                        description=f.get('description', '')
                    )
                cat_id_map[old_pk] = obj
                cat_id_map[slug] = obj

            default_cat = JobCategory.objects.filter(slug='software-tech').first() or JobCategory.objects.first()
            if not default_cat:
                default_cat = JobCategory.objects.create(
                    name="Software & Tech",
                    slug="software-tech",
                    icon="code",
                    description="All software engineering and technology opportunities."
                )

            # 4. Job Postings Bulk Upsert
            existing_jobs = {j.id: j for j in JobPosting.objects.all()}
            existing_urls = {j.apply_url: j for j in existing_jobs.values() if j.apply_url}

            jobs_to_create = []
            jobs_to_update = []
            job_id_map = {}

            for item in data_by_model.get('requirements.jobposting', []):
                old_pk = item.get('pk')
                f = item.get('fields', {})
                cat_val = f.get('category')
                resolved_cat = cat_id_map.get(cat_val) or default_cat

                apply_url = f.get('apply_url') or ''
                title = f.get('title') or 'Job Opening'
                company = f.get('company_name') or 'Company'

                posted_date = f.get('posted_date') or default_posted_date
                job_deadline = listing_deadline(posted_date, default_deadline)
                job_status = 'ACTIVE' if job_deadline > now else 'EXPIRED'

                target_obj = existing_jobs.get(old_pk) or (existing_urls.get(apply_url) if apply_url else None)

                if target_obj:
                    target_obj.title = title
                    target_obj.company_name = company
                    target_obj.company_logo_icon = f.get('company_logo_icon', 'building')
                    target_obj.category = resolved_cat
                    target_obj.job_type = f.get('job_type', 'INTERNSHIP')
                    target_obj.stipend_salary = f.get('stipend_salary', 'Competitive')
                    target_obj.location = f.get('location', 'Pan India')
                    target_obj.is_remote = f.get('is_remote', False)
                    target_obj.skills_required = f.get('skills_required', '')
                    target_obj.apply_url = apply_url
                    target_obj.allow_direct_apply = f.get('allow_direct_apply', True)
                    target_obj.description = f.get('description', '')
                    target_obj.eligibility = f.get('eligibility', '')
                    target_obj.selection_process = f.get('selection_process', '')
                    target_obj.status = job_status
                    target_obj.deadline = job_deadline
                    target_obj.posted_date = posted_date
                    target_obj.is_featured = f.get('is_featured', False)
                    jobs_to_update.append(target_obj)
                    job_id_map[old_pk] = target_obj
                else:
                    raw_uuid = f.get('uuid')
                    stable_uuid = None
                    if raw_uuid:
                        try:
                            stable_uuid = py_uuid.UUID(str(raw_uuid))
                        except Exception:
                            stable_uuid = None

                    new_job = JobPosting(
                        id=old_pk,
                        uuid=stable_uuid or py_uuid.uuid4(),
                        title=title,
                        company_name=company,
                        company_logo_icon=f.get('company_logo_icon', 'building'),
                        category=resolved_cat,
                        job_type=f.get('job_type', 'INTERNSHIP'),
                        stipend_salary=f.get('stipend_salary', 'Competitive'),
                        location=f.get('location', 'Pan India'),
                        is_remote=f.get('is_remote', False),
                        skills_required=f.get('skills_required', ''),
                        apply_url=apply_url,
                        allow_direct_apply=f.get('allow_direct_apply', True),
                        description=f.get('description', ''),
                        eligibility=f.get('eligibility', ''),
                        selection_process=f.get('selection_process', ''),
                        study_materials=f.get('study_materials', []),
                        posted_by=f.get('posted_by', 'Kashii Updatez Admin'),
                        poster_email=f.get('poster_email', 'admin@kashiiupdatez.com'),
                        status=job_status,
                        deadline=job_deadline,
                        posted_date=posted_date,
                        is_featured=f.get('is_featured', False),
                        is_referral=f.get('is_referral', False),
                        referrer_name=f.get('referrer_name', ''),
                        referrer_linkedin=f.get('referrer_linkedin', ''),
                        referral_instructions=f.get('referral_instructions', ''),
                        source_name=f.get('source_name', 'Jobdexo'),
                        source_job_id=f.get('source_job_id', ''),
                        source_url=f.get('source_url', ''),
                        source_published_at=f.get('source_published_at'),
                        timestamp_precision=f.get('timestamp_precision', 'DATE_ONLY'),
                        industry_domain=f.get('industry_domain', 'TECHNICAL'),
                        experience_tier=f.get('experience_tier', 'FRESHER'),
                        normalized_city=f.get('normalized_city', 'Bengaluru'),
                        views_count=f.get('views_count', 0),
                        applications_count=f.get('applications_count', 0),
                    )
                    jobs_to_create.append(new_job)

            if jobs_to_update:
                JobPosting.objects.bulk_update(
                    jobs_to_update,
                    fields=[
                        'title', 'company_name', 'company_logo_icon', 'category', 'job_type',
                        'stipend_salary', 'location', 'is_remote', 'skills_required', 'apply_url',
                        'allow_direct_apply', 'description', 'eligibility', 'selection_process',
                        'status', 'deadline', 'posted_date', 'is_featured'
                    ],
                    batch_size=200
                )

            if jobs_to_create:
                created_jobs = JobPosting.objects.bulk_create(jobs_to_create, batch_size=200)
                for j in created_jobs:
                    job_id_map[j.id] = j

            # Re-map all jobs
            all_db_jobs = {j.id: j for j in JobPosting.objects.all()}
            for old_pk in [item.get('pk') for item in data_by_model.get('requirements.jobposting', [])]:
                if old_pk in all_db_jobs:
                    job_id_map[old_pk] = all_db_jobs[old_pk]

            # 5. Job Groups Bulk Upsert
            existing_groups = {g.slug: g for g in JobGroup.objects.all()}
            existing_groups_by_id = {g.id: g for g in existing_groups.values()}

            groups_to_create = []
            groups_to_update = []
            group_jobs_map = {}

            for item in data_by_model.get('requirements.jobgroup', []):
                old_pk = item.get('pk')
                f = item.get('fields', {})
                slug = f.get('slug') or f"group-{old_pk}"
                name = f.get('name') or "Hiring Drive"
                jobs_pks = f.get('jobs', [])

                target_grp = existing_groups.get(slug) or existing_groups_by_id.get(old_pk)
                if target_grp:
                    target_grp.name = name
                    target_grp.slug = slug
                    target_grp.banner_tag = f.get('banner_tag', '🔥 HIRING DRIVE')
                    target_grp.description = f.get('description', '')
                    target_grp.posted_date = f.get('posted_date') or default_posted_date
                    target_grp.deadline = listing_deadline(target_grp.posted_date, default_deadline)
                    target_grp.is_active = target_grp.deadline > now
                    groups_to_update.append(target_grp)
                    group_jobs_map[target_grp.id] = jobs_pks
                else:
                    new_grp = JobGroup(
                        id=old_pk,
                        name=name,
                        slug=slug,
                        banner_tag=f.get('banner_tag', '🔥 HIRING DRIVE'),
                        description=f.get('description', ''),
                        posted_date=f.get('posted_date') or default_posted_date,
                        deadline=listing_deadline(f.get('posted_date') or default_posted_date, default_deadline),
                        is_active=listing_deadline(f.get('posted_date') or default_posted_date, default_deadline) > now,
                    )
                    groups_to_create.append(new_grp)
                    group_jobs_map[old_pk] = jobs_pks

            if groups_to_update:
                JobGroup.objects.bulk_update(
                    groups_to_update,
                    fields=['name', 'slug', 'banner_tag', 'description', 'posted_date', 'deadline', 'is_active'],
                    batch_size=100
                )

            if groups_to_create:
                JobGroup.objects.bulk_create(groups_to_create, batch_size=100)

            # Re-map group M2M associations in bulk ONLY for restored groups (preserves other existing groups!)
            all_db_groups = {g.id: g for g in JobGroup.objects.all()}
            ThroughModel = JobGroup.jobs.through
            restored_group_ids = [gid for gid in group_jobs_map.keys() if gid in all_db_groups]
            if restored_group_ids:
                ThroughModel.objects.filter(jobgroup_id__in=restored_group_ids).delete()

            m2m_relations = []
            for grp_id, j_pks in group_jobs_map.items():
                if grp_id in all_db_groups:
                    for j_pk in j_pks:
                        if j_pk in job_id_map:
                            m2m_relations.append(ThroughModel(jobgroup_id=grp_id, jobposting_id=job_id_map[j_pk].id))

            if m2m_relations:
                ThroughModel.objects.bulk_create(m2m_relations, batch_size=500, ignore_conflicts=True)

        # Align Postgres Sequences
        if connection.vendor == 'postgresql':
            with connection.cursor() as cursor:
                for ModelClass in [JobPosting, JobGroup, JobCategory]:
                    table = ModelClass._meta.db_table
                    pk_name = ModelClass._meta.pk.name
                    if ModelClass._meta.pk.get_internal_type() in ['AutoField', 'BigAutoField', 'SmallAutoField']:
                        try:
                            cursor.execute(f"SELECT setval(pg_get_serial_sequence('{table}', '{pk_name}'), coalesce(max({pk_name}), 1)) FROM {table};")
                        except Exception:
                            pass

        total_jobs = JobPosting.objects.filter(status='ACTIVE', deadline__gt=timezone.now()).count()
        total_groups = JobGroup.objects.filter(is_active=True, deadline__gt=timezone.now()).count()
        self.stdout.write(self.style.SUCCESS(
            f"Snapshot restore completed.\n"
            f"  - Active Jobs: {total_jobs} (posted in the last 7 days)\n"
            f"  - Active Groups: {total_groups} (All Unexpired)\n"
            f"  - Group-Job Links: {JobGroup.jobs.through.objects.count()}"
        ))
