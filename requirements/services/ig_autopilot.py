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


class OwnPoster:
    """Posts with an account connected to Updatez's own Meta app (comment DMs handled by our webhook)."""
    mode = 'own'

    def __init__(self, account):
        self.account = account
        self.username = account.username

    def prepare(self):
        ig_graph.refresh_if_needed(self.account)

    def publish(self, kind, *, video_url='', image_url='', caption='', link_url='', title='', job=None):
        from ..models import IGPost
        media_id = ig_graph.publish_media(self.account, media_type='REELS' if kind == 'reel' else 'STORIES',
                                          video_url=video_url, image_url=image_url, caption=caption)
        IGPost.objects.update_or_create(media_id=media_id, defaults={
            'account': self.account, 'kind': kind, 'job': job, 'link_url': link_url})
        return media_id


class InstaAutomationPoster:
    """Posts through Insta Automation (insta.kashiiupdatez.online) with the account connected there.

    It registers each post's link, so its comment 'LINK' automation DMs the right job.
    """
    mode = 'insta_automation'

    def __init__(self, username):
        self.username = username
        self.base = getattr(settings, 'REELFLOW_URL', '').rstrip('/')
        self.headers = {'X-Story-Token': getattr(settings, 'REELFLOW_STORY_TOKEN', '')}

    def prepare(self):
        pass

    def publish(self, kind, *, video_url='', image_url='', caption='', link_url='', title='', job=None):
        import requests
        r = requests.post(f"{self.base}/internal/media/publish/", headers=self.headers, timeout=60, json={
            'kind': kind, 'username': self.username, 'video_url': video_url, 'image_url': image_url,
            'caption': caption, 'link_url': link_url, 'title': title})
        data = r.json()
        if r.status_code != 202:
            raise ig_graph.IGError(data.get('message') or data.get('error') or f'HTTP {r.status_code}',
                                   needs_reconnect=bool(data.get('needs_reconnect')))
        deadline = _time.time() + 8 * 60
        while _time.time() < deadline:
            _time.sleep(5)
            st = requests.get(f"{self.base}/internal/media/publish/{data['job_id']}/", headers=self.headers,
                              timeout=30).json()
            if st.get('status') == 'done':
                return st['media_id']
            if st.get('status') == 'failed':
                raise ig_graph.IGError(st.get('error') or 'Publish failed', needs_reconnect=bool(st.get('needs_reconnect')))
        raise ig_graph.IGError('Insta Automation did not finish publishing in 8 minutes.')


def posting_handle():
    return (getattr(settings, 'REEL_ACCOUNT_HANDLE', '') or getattr(settings, 'INSTAGRAM_ACCOUNT_HANDLE', '')).lstrip('@')


def get_poster():
    """Insta Automation when its token is set (default), else an own connected account, else None."""
    from ..models import IGAccount
    if getattr(settings, 'REELFLOW_STORY_TOKEN', '') and posting_handle():
        return InstaAutomationPoster(posting_handle())
    own = IGAccount.primary()
    return OwnPoster(own) if own else None


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


def publish_reel(draft, poster):
    """Render + publish one ReelDraft. Updates the draft; deletes the video afterwards."""
    from ..models import ReelDraft
    job = draft.job
    music = pick_track(job)
    path = None
    draft.status = ReelDraft.STATUS_POSTING
    draft.attempts += 1
    draft.save(update_fields=['status', 'attempts'])
    try:
        path = render_video(job, public_base(), reply_cta='comment', seconds=REEL_SECONDS, music=music)
        media_id = poster.publish('reel', video_url=_video_url('reel', job, music), caption=draft.caption,
                                  link_url=job_apply_url(job, public_base()),
                                  title=f"{job.company_name} - {job.title}", job=job)
        draft.status, draft.media_id, draft.error, draft.posted_at = ReelDraft.STATUS_POSTED, media_id, '', timezone.now()
    except Exception as exc:
        logger.exception("Reel publish failed for draft %s", draft.id)
        draft.status = ReelDraft.STATUS_FAILED if draft.attempts >= MAX_ATTEMPTS else ReelDraft.STATUS_READY
        draft.error = str(exc)[:2000]
    finally:
        draft.save(update_fields=['status', 'media_id', 'error', 'posted_at'])
        _delete(path)  # Instagram has its own copy now (or we will re-render on retry)
    return draft


def publish_story(job, poster):
    """Post the animated job story; falls back to the still image. Returns the media id."""
    path = None
    link = job_apply_url(job, public_base())
    title = f"{job.company_name} - {job.title}"
    try:
        try:
            path = render_video(job, public_base(), reply_cta=True, seconds=7.0)
            media_id = poster.publish('story', video_url=_video_url('story', job, None), link_url=link, title=title, job=job)
        except ig_graph.IGError as exc:
            if exc.needs_reconnect:
                raise
            logger.warning("Video story failed for job %s, posting image: %s", job.id, exc)
            media_id = poster.publish('story', link_url=link, title=title, job=job,
                                      image_url=f"{public_base()}/api/jobs/{job.id}/ig-story-image/?v={int(_time.time())}")
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
    from ..models import ReelDraft
    if not _run_lock.acquire(blocking=False):
        return {'skipped': 'already running'}
    try:
        poster = get_poster()
        if not poster:
            return {'error': 'NO_ACCOUNT'}
        poster.prepare()
        now = now or timezone.now()
        drafts = ensure_due_drafts(public_base(), now=now, prerender=False)
        due = [d for d in drafts if d.status == ReelDraft.STATUS_READY and d.slot_at <= now]
        results = [publish_reel(d, poster).status for d in due]
        sweep_old_videos()
        return {'posted': results.count(ReelDraft.STATUS_POSTED), 'attempted': len(results)}
    finally:
        _run_lock.release()
        close_old_connections()


def run_due_async():
    threading.Thread(target=run_due, daemon=True, name='ReelAutopilot').start()
