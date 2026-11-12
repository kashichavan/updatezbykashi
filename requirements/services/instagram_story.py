"""
Meta / Instagram Story Automation Service for KashiiUpdatez.

Capabilities:
1. High-resolution 9:16 (1080x1920) Instagram Story image generation with PIL & qrcode.
   - Prominently displays Experience Requirement (Freshers vs Experienced color-coded).
   - Company name, Role title, Stipend/Salary, Location, Eligibility, and Key Skills.
   - Embedded scannable QR Code linking directly to the job application page.
   - QR call-to-action banner. The Content Publishing API cannot add link stickers.
2. Official Meta Graph API integration (Instagram Content Publishing API).
   - Creates Media Container (media_type=STORIES) with public image_url.
   - Publishes Media Container to @ikashii_07 Instagram Professional/Creator account.
   - Tracks publication status, media ID, and timestamp on JobPosting model.
   - Provides graceful fallback with 1-click copy text & download if API token is absent or in local dev.
"""

import os
import io
import re
import time
import logging
import requests
import qrcode
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

def generate_job_story_image(job, base_url="https://kashiiupdatez.online", reply_cta=True) -> io.BytesIO:
    """1080x1920 JPEG story for a job (design lives in story_render)."""
    from .story_render import render_still
    return render_still(job, base_url, reply_cta=reply_cta)


def generate_job_story_video(job, base_url="https://kashiiupdatez.online", reply_cta=True) -> str:
    """Animated MP4 story for a job; returns a cached file path."""
    from .story_render import render_video
    return render_video(job, base_url, reply_cta=reply_cta)


class InstagramStoryPublisher:
    """
    Official Meta / Instagram Graph API Story Publisher.

    Flow:
    1. Generates 9:16 Story Image and resolves public HTTPS URL.
    2. Sends POST /{ig_user_id}/media with image_url & media_type=STORIES.
    3. Sends POST /{ig_user_id}/media_publish with creation_id.
    4. Updates JobPosting tracking fields (insta_story_published, media_id, timestamp).
    """

    def __init__(self, access_token=None, account_id=None, api_version=None):
        self.access_token = access_token or getattr(settings, 'INSTAGRAM_ACCESS_TOKEN', '')
        self.account_id = account_id or getattr(settings, 'INSTAGRAM_ACCOUNT_ID', '17841475393977759')
        self.api_version = api_version or getattr(settings, 'INSTAGRAM_API_VERSION', 'v26.0')
        # Instagram Login tokens (IG...) only work on graph.instagram.com;
        # Facebook Login tokens (EA...) only work on graph.facebook.com.
        host = 'graph.instagram.com' if self.access_token.startswith('IG') else 'graph.facebook.com'
        self.base_graph_url = f"https://{host}/{self.api_version}"

    def _wait_for_container(self, container_id, attempts=10, delay=3):
        """Waits for Meta to fetch the image. Returns (ready, last_status)."""
        status = 'UNKNOWN'
        for attempt in range(attempts):
            resp = requests.get(
                f"{self.base_graph_url}/{container_id}",
                params={'fields': 'status_code,status', 'access_token': self.access_token},
                timeout=30,
            )
            data = resp.json()
            status = data.get('status_code') or data.get('error', {}).get('message', 'UNKNOWN')
            if status == 'FINISHED':
                return True, status
            if status in ('ERROR', 'EXPIRED'):
                return False, data.get('status') or status
            if attempt < attempts - 1:
                time.sleep(delay)
        return False, status

    def publish_job_story(self, job, base_url="https://kashiiupdatez.online") -> dict:
        """
        Publishes the job story image to the connected Instagram account via Meta Graph API.

        Returns:
            dict containing success boolean, media_id, error message, and story text.
        """
        if getattr(settings, 'REELFLOW_STORY_TOKEN', ''):
            return publish_via_reelflow(job, base_url=base_url)
        # Build public image URL for Meta's crawler
        ts = int(job.updated_at.timestamp()) if hasattr(job, 'updated_at') and job.updated_at else 1
        story_image_url = f"{base_url}/api/jobs/{job.id}/ig-story-image/?v={ts}"
        story_text = job.get_insta_story_text(include_link=True, base_url=base_url) if hasattr(job, 'get_insta_story_text') else ""

        if not self.access_token:
            err_msg = (
                "INSTAGRAM_ACCESS_TOKEN is not configured in environment or settings. "
                "You can still copy the story text or download the image below."
            )
            job.insta_story_error = err_msg
            job.save(update_fields=['insta_story_error'])
            return {
                'success': False,
                'error': 'MISSING_ACCESS_TOKEN',
                'message': err_msg,
                'story_image_url': story_image_url,
                'story_text': story_text,
                'job_id': job.id,
            }

        try:
            # Step 1: Create Story Media Container
            container_url = f"{self.base_graph_url}/{self.account_id}/media"
            container_params = {
                'image_url': story_image_url,
                'media_type': 'STORIES',
                'access_token': self.access_token,
            }
            logger.info(f"[Meta IG Story] Creating container for Job #{job.id} on account {self.account_id}...")
            c_resp = requests.post(container_url, data=container_params, timeout=30)
            c_data = c_resp.json()

            if c_resp.status_code != 200 or 'id' not in c_data:
                error_detail = c_data.get('error', {}).get('message', c_resp.text)
                logger.error(f"[Meta IG Story Error] Container creation failed: {error_detail}")
                job.insta_story_error = f"Container creation failed: {error_detail}"
                job.save(update_fields=['insta_story_error'])
                return {
                    'success': False,
                    'error': 'CONTAINER_CREATION_FAILED',
                    'message': error_detail,
                    'story_image_url': story_image_url,
                    'story_text': story_text,
                    'job_id': job.id,
                }

            container_id = c_data['id']
            logger.info(f"[Meta IG Story] Container #{container_id} created. Triggering publish...")

            ready, container_status = self._wait_for_container(container_id)
            if not ready:
                error_detail = f"Container {container_id} not ready: {container_status}"
                logger.error(f"[Meta IG Story Error] {error_detail}")
                job.insta_story_error = error_detail
                job.save(update_fields=['insta_story_error'])
                return {
                    'success': False,
                    'error': 'CONTAINER_NOT_READY',
                    'message': error_detail,
                    'container_id': container_id,
                    'story_image_url': story_image_url,
                    'story_text': story_text,
                    'job_id': job.id,
                }

            # Step 2: Publish Media Container
            publish_url = f"{self.base_graph_url}/{self.account_id}/media_publish"
            p_params = {
                'creation_id': container_id,
                'access_token': self.access_token,
            }
            p_resp = requests.post(publish_url, data=p_params, timeout=30)
            p_data = p_resp.json()

            if p_resp.status_code != 200 or 'id' not in p_data:
                error_detail = p_data.get('error', {}).get('message', p_resp.text)
                logger.error(f"[Meta IG Story Error] Media publish failed: {error_detail}")
                job.insta_story_error = f"Publish failed: {error_detail}"
                job.save(update_fields=['insta_story_error'])
                return {
                    'success': False,
                    'error': 'PUBLISH_FAILED',
                    'message': error_detail,
                    'container_id': container_id,
                    'story_image_url': story_image_url,
                    'story_text': story_text,
                    'job_id': job.id,
                }

            published_media_id = p_data['id']
            logger.info(f"[Meta IG Story Success] Story published successfully for Job #{job.id}! Media ID: {published_media_id}")

            # Step 3: Record Success on JobPosting
            job.insta_story_published = True
            job.insta_story_media_id = str(published_media_id)
            job.insta_story_published_at = timezone.now()
            job.insta_story_error = ""
            job.save(update_fields=['insta_story_published', 'insta_story_media_id', 'insta_story_published_at', 'insta_story_error'])

            return {
                'success': True,
                'media_id': published_media_id,
                'container_id': container_id,
                'story_image_url': story_image_url,
                'story_text': story_text,
                'job_id': job.id,
                'message': f"Successfully published story for '{job.title}' to Instagram!",
            }

        except Exception as exc:
            logger.exception(f"[Meta IG Story Exception] Failed to post story for Job #{job.id}: {exc}")
            job.insta_story_error = str(exc)
            job.save(update_fields=['insta_story_error'])
            return {
                'success': False,
                'error': 'EXCEPTION',
                'message': str(exc),
                'story_image_url': story_image_url,
                'story_text': story_text,
                'job_id': job.id,
            }


def _public_base_url(base_url=''):
    """Meta must fetch the image over public HTTPS, so never hand it a localhost URL."""
    if base_url.startswith('https://') and 'localhost' not in base_url and '127.0.0.1' not in base_url:
        return base_url.rstrip('/')
    return getattr(settings, 'PUBLIC_SITE_URL', 'https://kashiiupdatez.online')


def reelflow_status():
    """Connection state of the Instagram account in Insta Automation (no secrets)."""
    url = getattr(settings, 'REELFLOW_URL', '')
    token = getattr(settings, 'REELFLOW_STORY_TOKEN', '')
    if not token:
        return {'configured': False, 'connected': False, 'connect_url': f"{url}/instagram/connect/start/?publish=1"}
    try:
        r = requests.get(f"{url}/internal/story/status/", headers={'X-Story-Token': token},
                         params={'username': (getattr(settings, 'REEL_ACCOUNT_HANDLE', '') or
                                             getattr(settings, 'INSTAGRAM_ACCOUNT_HANDLE', ''))}, timeout=15)
        data = r.json()
    except Exception as exc:
        return {'configured': True, 'connected': False, 'error': f'Insta Automation unreachable ({type(exc).__name__})',
                'connect_url': f"{url}/instagram/connect/start/?publish=1"}
    if r.status_code == 403:
        return {'configured': True, 'connected': False, 'error': 'Story token rejected by Insta Automation.',
                'connect_url': f"{url}/instagram/connect/start/?publish=1"}
    data['configured'] = True
    return data


def publish_via_reelflow(job, base_url='', fmt='image', on_stage=None):
    """Post the job's 9:16 story through Insta Automation's connected account.

    fmt='video' renders the animated MP4 first (falls back to the still image if that fails).
    on_stage(stage) is called with 'rendering' / 'posting' for progress reporting.
    """
    url = getattr(settings, 'REELFLOW_URL', '')
    base = _public_base_url(base_url)
    ts = int(job.updated_at.timestamp()) if getattr(job, 'updated_at', None) else 1
    image_url = f"{base}/api/jobs/{job.id}/ig-story-image/?v={ts}"
    share_url = job.get_story_sticker_url(base_url=base) if hasattr(job, 'get_story_sticker_url') else f"{base}/job/{job.id}/"
    media = {'image_url': image_url}
    if fmt == 'video':
        if on_stage:
            on_stage('rendering')
        try:
            # Warm the cache so Meta's download is served instantly from disk.
            generate_job_story_video(job, base_url=base, reply_cta=True)
            media = {'video_url': f"{base}/api/jobs/{job.id}/ig-story-video/?v={ts}"}
        except Exception as exc:
            logger.warning("Story video render failed for job %s, using image: %s", job.id, exc)
    if on_stage:
        on_stage('posting')
    out = {'story_image_url': image_url, 'story_sticker_url': share_url, 'job_id': job.id, **media}
    try:
        r = requests.post(f"{url}/internal/story/publish/",
                          headers={'X-Story-Token': settings.REELFLOW_STORY_TOKEN},
                          json={**media,
                                'link_url': share_url,
                                'title': f"{job.company_name} - {job.title}"[:255],
                                'username': (getattr(settings, 'REEL_ACCOUNT_HANDLE', '') or
                                             getattr(settings, 'INSTAGRAM_ACCOUNT_HANDLE', ''))},
                          timeout=150)
        data = r.json()
    except Exception as exc:
        data = {'success': False, 'error': 'REELFLOW_UNREACHABLE', 'message': f'Insta Automation unreachable ({type(exc).__name__}).'}
    out.update(data)
    if data.get('success'):
        job.insta_story_published = True
        job.insta_story_media_id = str(data.get('media_id', ''))
        job.insta_story_published_at = timezone.now()
        job.insta_story_error = ''
        job.save(update_fields=['insta_story_published', 'insta_story_media_id', 'insta_story_published_at', 'insta_story_error'])
        out['message'] = f"Story posted to @{data.get('username', '')}."
    else:
        job.insta_story_error = str(data.get('message') or data.get('error') or 'Unknown error')[:2000]
        job.save(update_fields=['insta_story_error'])
    return out


_STATE_TTL = 60 * 30


def story_state_key(job_id):
    return f"ig_story_publish_state_{job_id}"


def get_story_publish_state(job_id):
    from django.core.cache import cache
    return cache.get(story_state_key(job_id)) or {'state': 'idle'}


def publish_story_async(job_id, base_url='', fmt='video'):
    """Run publish_via_reelflow in a background thread; progress is kept in the cache."""
    import threading
    from django.core.cache import cache

    current = get_story_publish_state(job_id)
    if current.get('state') in ('queued', 'rendering', 'posting'):
        return current
    key = story_state_key(job_id)
    state = {'state': 'queued'}
    cache.set(key, state, _STATE_TTL)

    def _run():
        from django.db import close_old_connections
        from ..models import JobPosting
        try:
            from .ig_autopilot import get_poster
            job = JobPosting.objects.get(pk=job_id)
            poster = get_poster()
            if poster:
                from . import ig_graph
                from .ig_autopilot import publish_story
                cache.set(key, {'state': 'rendering'}, _STATE_TTL)
                try:
                    media_id = publish_story(job, poster)
                    res = {'success': True, 'media_id': media_id, 'video_url': True,
                           'message': f"Story posted to @{poster.username}."}
                except ig_graph.IGError as exc:
                    res = {'success': False, 'message': str(exc), 'needs_reconnect': exc.needs_reconnect,
                           'connect_url': getattr(settings, 'REELFLOW_URL', '') + '/instagram/connect/start/?publish=1'
                           if poster.mode == 'insta_automation' else '/instagram/connect/'}
            else:
                res = publish_via_reelflow(job, base_url=base_url, fmt=fmt,
                                           on_stage=lambda st: cache.set(key, {'state': st}, _STATE_TTL))
            if res.get('success'):
                cache.set(key, {'state': 'done', 'message': res.get('message', ''),
                                'media_id': res.get('media_id', ''), 'format': 'video' if res.get('video_url') else 'image'},
                          _STATE_TTL)
            else:
                cache.set(key, {'state': 'error', 'message': res.get('message') or res.get('error') or 'Unknown error',
                                'needs_reconnect': bool(res.get('needs_reconnect')),
                                'connect_url': res.get('connect_url', '')}, _STATE_TTL)
        except Exception as exc:
            logger.exception("Async story publish failed for job %s", job_id)
            cache.set(key, {'state': 'error', 'message': type(exc).__name__}, _STATE_TTL)
        finally:
            close_old_connections()

    threading.Thread(target=_run, daemon=True, name=f"IGStory-{job_id}").start()
    return state


def auto_publish_story_if_enabled(job, base_url="https://kashiiupdatez.online"):
    """
    Hook invoked when a new job requirement is ingested/created.
    Only proceeds if INSTAGRAM_AUTO_POST_STORY is set to True.
    Executes safely without raising uncaught exceptions.
    """
    is_auto_enabled = getattr(settings, 'INSTAGRAM_AUTO_POST_STORY', False)
    if not is_auto_enabled:
        return {'status': 'skipped', 'reason': 'INSTAGRAM_AUTO_POST_STORY is False'}

    publisher = InstagramStoryPublisher()
    try:
        res = publisher.publish_job_story(job, base_url=base_url)
        return res
    except Exception as e:
        logger.error(f"Auto publish story failed for Job #{job.id}: {e}")
        return {'status': 'error', 'error': str(e)}


def setup_instagram_signals():
    """
    Connects post_save signal to automatically post newly ingested job requirements
    to Instagram Stories when INSTAGRAM_AUTO_POST_STORY is True.
    """
    import sys
    from django.db.models.signals import post_save
    from ..models import JobPosting

    def on_job_post_save(sender, instance, created, **kwargs):
        if not created:
            return
        # Guard: do not run in tests or migrations
        if any(cmd in sys.argv for cmd in ['test', 'migrate', 'makemigrations', 'collectstatic']):
            return
        if getattr(settings, 'INSTAGRAM_AUTO_POST_STORY', False):
            import threading
            job_id = instance.id

            def _bg_post():
                try:
                    from ..models import JobPosting
                    j = JobPosting.objects.get(id=job_id)
                    auto_publish_story_if_enabled(j)
                except Exception as e:
                    logger.error(f"[IG Story Auto-Push] Background auto-publish failed for Job #{job_id}: {e}")

            t = threading.Thread(target=_bg_post, daemon=True, name=f"IGStoryAutoPost-{job_id}")
            t.start()

    post_save.connect(on_job_post_save, sender=JobPosting, dispatch_uid="auto_publish_ig_story_on_create")

