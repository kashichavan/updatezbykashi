"""Versioned cache for the /api/jobs/ feed.

Every feed cache key carries a version number. Any change to a job, or to which
groups a job belongs to, bumps the version, so the next request misses the
cache instead of serving a list that is up to five minutes old.
"""
from django.core.cache import cache

VERSION_KEY = 'jobs_feed_ver'


def feed_version():
    try:
        return cache.get(VERSION_KEY) or 0
    except Exception:
        return 0


def bump_feed_version(*_args, **_kwargs):
    try:
        cache.incr(VERSION_KEY)
    except ValueError:  # key missing or evicted
        cache.set(VERSION_KEY, 1, None)
    except Exception:
        pass


def setup_feed_cache_signals():
    from django.db.models.signals import m2m_changed, post_delete, post_save
    from .models import JobGroup, JobPosting

    post_save.connect(bump_feed_version, sender=JobPosting, dispatch_uid='feed_ver_job_save')
    post_delete.connect(bump_feed_version, sender=JobPosting, dispatch_uid='feed_ver_job_delete')
    post_save.connect(bump_feed_version, sender=JobGroup, dispatch_uid='feed_ver_group_save')
    post_delete.connect(bump_feed_version, sender=JobGroup, dispatch_uid='feed_ver_group_delete')
    m2m_changed.connect(bump_feed_version, sender=JobGroup.jobs.through, dispatch_uid='feed_ver_group_jobs')
