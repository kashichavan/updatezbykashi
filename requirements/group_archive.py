"""
Keep shared group links alive across deploys.

Production resets to what is committed in git on every deploy, so a group created
since the last commit would otherwise disappear and its shared link would 404.

The archive holds groups and their jobs, public data only. Merging it is
add-only: an existing group is never renamed, re-dated, emptied or deleted.
"""

import json
import logging
import uuid as py_uuid
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from .models import Category, JobGroup, JobPosting

logger = logging.getLogger(__name__)

ARCHIVE_PATH = Path(settings.BASE_DIR) / 'backups' / 'groups_archive.json'
LIVE_URL = 'https://kashiiupdatez.online'

# Fields copied as they are. Anything that identifies a person stays out, because
# this file is committed to a public repository.
JOB_FIELDS = (
    'title', 'company_name', 'company_logo_icon', 'job_type', 'stipend_salary',
    'location', 'is_remote', 'skills_required', 'apply_url', 'allow_direct_apply',
    'description', 'eligibility', 'selection_process', 'status', 'is_featured',
    'source_name', 'source_job_id', 'source_url', 'timestamp_precision',
    'industry_domain', 'experience_tier', 'normalized_city',
)
GROUP_FIELDS = ('name', 'slug', 'banner_tag', 'description', 'is_active', 'views_count')


def export_groups(since):
    """Every group created at or after `since`, plus the jobs inside them."""
    groups = JobGroup.objects.filter(created_at__gte=since).prefetch_related('jobs__category').order_by('id')
    out_groups, out_jobs = [], {}
    for group in groups:
        job_uuids = []
        for job in group.jobs.all():
            key = str(job.uuid)
            job_uuids.append(key)
            if key not in out_jobs:
                row = {field: getattr(job, field) for field in JOB_FIELDS}
                row.update(
                    uuid=key,
                    category_slug=job.category.slug,
                    posted_date=job.posted_date.isoformat() if job.posted_date else None,
                    deadline=job.deadline.isoformat() if job.deadline else None,
                )
                out_jobs[key] = row
        row = {field: getattr(group, field) for field in GROUP_FIELDS}
        row.update(
            created_at=group.created_at.isoformat(),
            posted_date=group.posted_date.isoformat() if group.posted_date else None,
            deadline=group.deadline.isoformat() if group.deadline else None,
            job_uuids=job_uuids,
        )
        out_groups.append(row)
    return {'groups': out_groups, 'jobs': list(out_jobs.values())}


def _when(value):
    parsed = parse_datetime(str(value or ''))
    if parsed is None:
        return None
    return timezone.make_aware(parsed) if timezone.is_naive(parsed) else parsed


def _new_job(row, category):
    fields = {field: row[field] for field in JOB_FIELDS if row.get(field) is not None}
    posted = parse_date(str(row.get('posted_date') or '')[:10])
    return JobPosting(
        uuid=py_uuid.UUID(str(row['uuid'])),
        category=category,
        posted_date=posted or timezone.localtime(timezone.now()).date(),
        deadline=_when(row.get('deadline')) or timezone.now() + timedelta(days=7),
        **fields,
    )


def merge_archive(data):
    """
    Add the groups and jobs this database is missing. Returns what was added.

    Groups match on slug and jobs on uuid, because those are what appear in shared
    links. Numeric ids are left to the database: an id from another copy can
    already belong to a different group here.
    """
    data = data or {}
    groups = data.get('groups') or []
    jobs_by_uuid = {str(row['uuid']): row for row in data.get('jobs') or [] if row.get('uuid')}
    added_groups = added_jobs = 0

    with transaction.atomic():
        present_slugs = set(JobGroup.objects.values_list('slug', flat=True))
        wanted = {key for g in groups if g.get('slug') not in present_slugs for key in g.get('job_uuids') or []}
        known = {str(key): pk for key, pk in JobPosting.objects.filter(uuid__in=wanted).values_list('uuid', 'id')}
        categories = {c.slug: c for c in Category.objects.all()}
        default_category = categories.get('software-engineering') or next(iter(categories.values()), None)

        for group_row in groups:
            slug = group_row.get('slug')
            if not slug or slug in present_slugs:
                continue

            job_ids = []
            for key in group_row.get('job_uuids') or []:
                if key not in known and key in jobs_by_uuid and default_category:
                    row = jobs_by_uuid[key]
                    job = _new_job(row, categories.get(row.get('category_slug')) or default_category)
                    # bulk_create skips save() and signals: restoring an old job must
                    # not start a backup or post it to Instagram again.
                    job = JobPosting.objects.bulk_create([job])[0]
                    known[key] = job.id
                    added_jobs += 1
                if key in known:
                    job_ids.append(known[key])

            posted = parse_date(str(group_row.get('posted_date') or '')[:10])
            group = JobGroup(
                name=group_row.get('name') or 'Hiring Drive',
                slug=slug,
                banner_tag=group_row.get('banner_tag') or '🔥 KASHIIUPDATEZ TECH DRIVE',
                description=group_row.get('description') or '',
                is_active=group_row.get('is_active', True),
                views_count=group_row.get('views_count') or 0,
                posted_date=posted or timezone.localtime(timezone.now()).date(),
                deadline=_when(group_row.get('deadline')) or timezone.now() + timedelta(days=30),
            )
            group = JobGroup.objects.bulk_create([group])[0]
            group.jobs.set(job_ids)
            created_at = _when(group_row.get('created_at'))
            if created_at:
                # auto_now_add ignores a value passed to create().
                JobGroup.objects.filter(pk=group.pk).update(created_at=created_at)
            present_slugs.add(slug)
            added_groups += 1

    return {'groups': added_groups, 'jobs': added_jobs}


def load_archive_file(path=None):
    path = Path(path or ARCHIVE_PATH)
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as handle:
        return json.load(handle)


def newest_group_time():
    """Everything older than this is already committed, so the pull can skip it."""
    latest = JobGroup.objects.order_by('-created_at').values_list('created_at', flat=True).first()
    return (latest or timezone.now() - timedelta(days=365)) - timedelta(days=1)


def fetch_live_groups(since, base_url=LIVE_URL, timeout=60):
    """Ask the running site for its recent groups. Raises if it cannot answer."""
    import requests

    response = requests.get(
        f"{base_url}/api/groups/archive/",
        params={'since': since.isoformat()},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()
