"""Daily job reels: 3 slots a day (IST), each gets the newest job that has no reel yet.

Drafts are created lazily (when the owner portal asks for today's reels), so this works
on hosts that sleep and have no cron. The video is pre-rendered in the background.
"""
import logging
import os
import threading
from datetime import datetime, time

from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone

logger = logging.getLogger(__name__)

REEL_SECONDS = 12.0


def slot_hours():
    raw = os.environ.get('REEL_SLOTS', '9,13,19')
    hours = sorted({int(h) for h in raw.split(',') if h.strip().isdigit() and 0 <= int(h) <= 23})
    return hours or [9, 13, 19]


def today_slots(now=None):
    now = timezone.localtime(now or timezone.now())  # TIME_ZONE is Asia/Kolkata
    return [timezone.make_aware(datetime.combine(now.date(), time(h, 0))) for h in slot_hours()]


def build_caption(job, base_url):
    from .story_render import job_apply_url
    url = job_apply_url(job, base_url)
    exp = job.get_experience_display() if hasattr(job, 'get_experience_display') else ''
    skills = job.get_skills_list()[:5] if hasattr(job, 'get_skills_list') else []
    lines = [
        f"🚨 {job.company_name} is hiring: {job.title}",
        "",
        f"🎯 Experience: {exp}" if exp else None,
        f"💰 Salary: {job.stipend_salary}" if job.stipend_salary else None,
        f"📍 Location: {job.location}" if job.location else None,
        f"⚡ Skills: {', '.join(skills)}" if skills else None,
        "",
        "💬 Comment LINK and I'll DM you the apply link (follow first so it reaches you)",
        f"🔗 {url}",
        "",
        "#jobs #hiring #freshers #jobsearch #itjobs #careers #kashiiupdatez",
    ]
    return "\n".join(l for l in lines if l is not None)


def _next_job(exclude_ids):
    from ..models import JobPosting, ReelDraft
    used = set(ReelDraft.objects.values_list('job_id', flat=True)) | set(exclude_ids)
    return (JobPosting.objects.filter(status='ACTIVE', deadline__gt=timezone.now())
            .exclude(id__in=used).order_by('-created_at').first())


def prerender_async(draft_ids, base_url):
    def _run():
        from django.db import close_old_connections
        from ..models import ReelDraft
        from .story_render import render_video
        try:
            for d in ReelDraft.objects.filter(id__in=draft_ids).select_related('job', 'job__category'):
                try:
                    render_video(d.job, base_url, reply_cta='comment', seconds=REEL_SECONDS)
                except Exception as exc:
                    logger.warning("Reel prerender failed for draft %s: %s", d.id, exc)
        finally:
            close_old_connections()
    threading.Thread(target=_run, daemon=True, name='ReelPrerender').start()


def ensure_due_drafts(base_url, now=None, prerender=True):
    """Create drafts for today's slots that have started; returns today's drafts."""
    from ..models import ReelDraft
    now = now or timezone.now()
    created = []
    for slot in today_slots(now):
        if slot > now or ReelDraft.objects.filter(slot_at=slot).exists():
            continue
        job = _next_job([d.job_id for d in created])
        if not job:
            break
        try:
            created.append(ReelDraft.objects.create(job=job, slot_at=slot, caption=build_caption(job, base_url)))
        except IntegrityError:  # another request created this slot first
            continue
    if created and prerender:
        prerender_async([d.id for d in created], base_url)
    slots = today_slots(now)
    return list(ReelDraft.objects.filter(slot_at__in=slots).select_related('job', 'job__category').order_by('slot_at'))


def next_slot(now=None):
    now = now or timezone.now()
    for s in today_slots(now):
        if s > now:
            return s
    return None
