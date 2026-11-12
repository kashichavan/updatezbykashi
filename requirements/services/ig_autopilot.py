"""Automatic posting from Updatez's own Instagram connection.

- Daily reels: each slot (9 AM / 1 PM / 7 PM IST by default) posts the newest job without
  a reel, with royalty-free music from static/reel_music/.
- Stories: animated job story to the same account.
- Rendered videos are deleted as soon as Instagram has published them (nothing is kept).
"""
import glob
import logging
import os
import tempfile
import threading
import time as _time

from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone

from . import ig_graph
from .daily_reels import REEL_SECONDS, ensure_due_drafts
from .story_render import job_apply_url, pick_track, render_video

logger = logging.getLogger(__name__)
_run_lock = threading.Lock()
MAX_ATTEMPTS = 3


def public_base():
    return getattr(settings, 'PUBLIC_SITE_URL', 'https://kashiiupdatez.online').rstrip('/')


def _delete(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError as exc:
        logger.warning("Could not delete %s: %s", path, exc)


def sweep_old_videos(max_age_hours=6):
    """Remove leftover rendered videos (e.g. previews) so nothing piles up on disk."""
    cutoff = _time.time() - max_age_hours * 3600
    for p in glob.glob(os.path.join(tempfile.gettempdir(), 'story_videos', '*.mp4*')):
        try:
            if os.path.getmtime(p) < cutoff:
                os.remove(p)
        except OSError:
            pass


def _video_url(kind, job, music):
    """Public URL Meta downloads from (served from the render cache by the reel/story video views)."""
    v = int(_time.time())
    if kind == 'reel':
        return f"{public_base()}/api/jobs/{job.id}/ig-reel-video/?v={v}"
    return f"{public_base()}/api/jobs/{job.id}/ig-story-video/?direct=1&v={v}"


def publish_reel(draft, account):
    """Render + publish one ReelDraft. Updates the draft; deletes the video afterwards."""
    from ..models import IGPost, ReelDraft
    job = draft.job
    music = pick_track(job)
    path = None
    draft.status = ReelDraft.STATUS_POSTING
    draft.attempts += 1
    draft.save(update_fields=['status', 'attempts'])
    try:
        path = render_video(job, public_base(), reply_cta='comment', seconds=REEL_SECONDS, music=music)
        media_id = ig_graph.publish_media(account, media_type='REELS', video_url=_video_url('reel', job, music),
                                          caption=draft.caption)
        IGPost.objects.update_or_create(media_id=media_id, defaults={
            'account': account, 'kind': IGPost.KIND_REEL, 'job': job, 'link_url': job_apply_url(job, public_base())})
        draft.status, draft.media_id, draft.error, draft.posted_at = ReelDraft.STATUS_POSTED, media_id, '', timezone.now()
    except Exception as exc:
        logger.exception("Reel publish failed for draft %s", draft.id)
        draft.status = ReelDraft.STATUS_FAILED if draft.attempts >= MAX_ATTEMPTS else ReelDraft.STATUS_READY
        draft.error = str(exc)[:2000]
        if isinstance(exc, ig_graph.IGError) and exc.needs_reconnect:
            account.last_error = str(exc)[:2000]
            account.save(update_fields=['last_error'])
    finally:
        draft.save(update_fields=['status', 'media_id', 'error', 'posted_at'])
        _delete(path)  # Instagram has its own copy now (or we will re-render on retry)
    return draft


def publish_story(job, account):
    """Post the animated job story; falls back to the still image. Returns the media id."""
    from ..models import IGPost
    path = None
    try:
        try:
            path = render_video(job, public_base(), reply_cta=True, seconds=7.0)
            media_id = ig_graph.publish_media(account, media_type='STORIES', video_url=_video_url('story', job, None))
        except ig_graph.IGError as exc:
            if exc.needs_reconnect:
                raise
            logger.warning("Video story failed for job %s, posting image: %s", job.id, exc)
            media_id = ig_graph.publish_media(
                account, media_type='STORIES',
                image_url=f"{public_base()}/api/jobs/{job.id}/ig-story-image/?direct=1&v={int(_time.time())}")
        IGPost.objects.update_or_create(media_id=media_id, defaults={
            'account': account, 'kind': IGPost.KIND_STORY, 'job': job, 'link_url': job_apply_url(job, public_base())})
        job.insta_story_published = True
        job.insta_story_media_id = media_id
        job.insta_story_published_at = timezone.now()
        job.insta_story_error = ''
        job.save(update_fields=['insta_story_published', 'insta_story_media_id', 'insta_story_published_at',
                                'insta_story_error'])
        return media_id
    finally:
        _delete(path)


def run_due(now=None):
    """Create today's due drafts and publish every due, unposted one. Safe to call repeatedly."""
    from ..models import IGAccount, ReelDraft
    if not _run_lock.acquire(blocking=False):
        return {'skipped': 'already running'}
    try:
        account = IGAccount.primary()
        if not account:
            return {'error': 'NO_ACCOUNT'}
        ig_graph.refresh_if_needed(account)
        now = now or timezone.now()
        drafts = ensure_due_drafts(public_base(), now=now, prerender=False)
        due = [d for d in drafts if d.status == ReelDraft.STATUS_READY and d.slot_at <= now]
        results = [publish_reel(d, account).status for d in due]
        sweep_old_videos()
        return {'posted': results.count(ReelDraft.STATUS_POSTED), 'attempted': len(results)}
    finally:
        _run_lock.release()
        close_old_connections()


def run_due_async():
    threading.Thread(target=run_due, daemon=True, name='ReelAutopilot').start()
