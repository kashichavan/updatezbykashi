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
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# System font discovery paths across macOS, Linux, and Windows
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "Arial.ttf"
]


def _get_font(size: int, bold: bool = False):
    """Safely loads a TrueType font at requested size, with fallback to default PIL font."""
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def generate_job_story_image(job, base_url="https://kashiiupdatez.online") -> io.BytesIO:
    """
    Renders a high-conversion 1080x1920 (9:16) Instagram Story image for a JobPosting.

    Features:
    - Prominently highlights Experience Requirement (Freshers Eligible vs Experienced).
    - Bold company badge, role title, salary, location, and eligibility.
    - Embedded high-res scannable QR code for instant direct apply.
    - QR call-to-action footer banner.
    """
    canvas_w, canvas_h = 1080, 1920
    img = Image.new('RGB', (canvas_w, canvas_h), color='#090d16')
    draw = ImageDraw.Draw(img)

    # 1. Atmospheric Deep Background Gradient
    for y in range(canvas_h):
        factor = y / canvas_h
        r = int(9 + (15 - 9) * factor)
        g = int(13 + (23 - 13) * factor)
        b = int(22 + (42 - 22) * factor)
        draw.line([(0, y), (canvas_w, y)], fill=(r, g, b))

    # 2. Ambient Atmosphere Glow Orbs
    # Top-Right Magenta Glow (Instagram branding touch)
    draw.ellipse([650, 60, 1250, 620], fill=(131, 58, 180, 50))
    # Bottom-Left Azure Glow
    draw.ellipse([-120, 1250, 480, 1850], fill=(37, 99, 235, 45))
    # Top-Left Warm Orange Ambient Touch
    draw.ellipse([-80, 80, 420, 580], fill=(234, 88, 12, 35))

    # 3. Main Specular Card Shell (Padding 70px)
    card_left = 70
    card_top = 180
    card_right = 1010
    card_bottom = 1740

    # Outer border with specular illumination
    draw.rounded_rectangle(
        [card_left, card_top, card_right, card_bottom],
        radius=44,
        fill=(15, 23, 42),
        outline=(56, 189, 248),
        width=2
    )
    # Inner dark surface
    draw.rounded_rectangle(
        [card_left + 3, card_top + 3, card_right - 3, card_bottom - 3],
        radius=42,
        fill=(17, 24, 39)
    )

    # Top Accent Gradient Line
    draw.rounded_rectangle(
        [card_left + 4, card_top + 4, card_right - 4, card_top + 10],
        radius=4,
        fill=(234, 88, 12)
    )

    # Load Fonts
    font_badge = _get_font(26, bold=True)
    font_handle = _get_font(30, bold=True)
    font_company = _get_font(42, bold=True)
    font_title = _get_font(52, bold=True)
    font_exp_head = _get_font(24, bold=True)
    font_exp_val = _get_font(36, bold=True)
    font_label = _get_font(24, bold=True)
    font_val = _get_font(32, bold=True)
    font_skills = _get_font(26, bold=True)
    font_qr_title = _get_font(28, bold=True)
    font_qr_sub = _get_font(22)
    font_btn = _get_font(34, bold=True)
    font_footer = _get_font(24, bold=True)

    # 4. Top Header: Category Badge & Creator Handle
    pad_x = 120
    draw.rounded_rectangle([pad_x, 240, pad_x + 380, 305], radius=32, fill=(234, 88, 12))
    draw.text((pad_x + 22, 258), "URGENT REQUIREMENT", fill=(255, 255, 255), font=font_badge)
    
    # Creator handle right-aligned
    handle_text = f"@{getattr(settings, 'INSTAGRAM_ACCOUNT_HANDLE', 'ikashii_07')}"
    draw.text((700, 258), handle_text, fill=(148, 163, 184), font=font_handle)

    # Subtle divider
    draw.line([(pad_x, 335), (960, 335)], fill=(51, 65, 85), width=2)

    # 5. Company Name & Title
    company_name = (job.company_name or "TOP TECH COMPANY").strip().upper()
    draw.text((pad_x, 365), company_name, fill=(56, 189, 248), font=font_company)

    # Multiline Job Title
    words = (job.title or "Software Engineer Requirement").split()
    lines = []
    curr = ""
    for w in words:
        test = (curr + " " + w).strip()
        if len(test) > 24 and curr:
            lines.append(curr)
            curr = w
        else:
            curr = test
    if curr:
        lines.append(curr)

    y_title = 430
    for l in lines[:3]:  # Cap at 3 lines max
        draw.text((pad_x, y_title), l, fill=(255, 255, 255), font=font_title)
        y_title += 68

    # 6. CRITICAL REQUIREMENT: Prominently Highlight Experience Requirement
    exp_display = job.get_experience_display() if hasattr(job, 'get_experience_display') else "Fresher (0-1 Yrs)"
    is_fresher = any(k in exp_display.lower() for k in ['fresher', '0-', '0 yr', 'intern', 'entry'])

    exp_box_top = max(y_title + 25, 620)
    exp_box_bottom = exp_box_top + 115

    if is_fresher:
        # Vibrant Emerald Box for Freshers
        draw.rounded_rectangle(
            [pad_x, exp_box_top, 960, exp_box_bottom],
            radius=24,
            fill=(6, 78, 59),
            outline=(16, 185, 129),
            width=2
        )
        draw.text((pad_x + 24, exp_box_top + 16), "EXPERIENCE REQUIREMENT", fill=(110, 231, 183), font=font_exp_head)
        draw.text((pad_x + 24, exp_box_top + 54), f"{exp_display.upper()} · FRESHERS ELIGIBLE", fill=(255, 255, 255), font=font_exp_val)
    else:
        # High-Contrast Indigo / Violet Box for Experienced Professionals
        draw.rounded_rectangle(
            [pad_x, exp_box_top, 960, exp_box_bottom],
            radius=24,
            fill=(49, 46, 129),
            outline=(99, 102, 241),
            width=2
        )
        draw.text((pad_x + 24, exp_box_top + 16), "EXPERIENCE REQUIREMENT", fill=(199, 210, 254), font=font_exp_head)
        draw.text((pad_x + 24, exp_box_top + 54), f"{exp_display.upper()} · EXPERIENCED PROS", fill=(255, 255, 255), font=font_exp_val)

    # 7. Key Specs Card Inset (Salary, Location, Eligibility, Skills)
    specs_top = exp_box_bottom + 25
    specs_bottom = specs_top + 390
    draw.rounded_rectangle(
        [pad_x, specs_top, 960, specs_bottom],
        radius=28,
        fill=(30, 41, 59),
        outline=(71, 85, 105),
        width=2
    )

    # Helper icon loader
    static_img_dir = os.path.join(settings.BASE_DIR, 'static', 'images')
    def load_png(name, size=(34, 34)):
        try:
            p = os.path.join(static_img_dir, name)
            if os.path.exists(p):
                ico = Image.open(p).convert("RGBA")
                return ico.resize(size, Image.Resampling.LANCZOS)
        except Exception:
            pass
        return None

    icon_salary = load_png('icon-salary.png')
    icon_loc = load_png('icon-location.png')
    icon_type = load_png('icon-type.png')

    # Row 1: Salary / Stipend
    draw.text((pad_x + 30, specs_top + 30), "STIPEND / SALARY", fill=(148, 163, 184), font=font_label)
    sal_y = specs_top + 65
    sal_text = job.stipend_salary or "Competitive Package (Best in Industry)"
    if icon_salary:
        img.paste(icon_salary, (pad_x + 30, sal_y), icon_salary)
        draw.text((pad_x + 75, sal_y + 2), sal_text[:40], fill=(52, 211, 153), font=font_val)
    else:
        draw.text((pad_x + 30, sal_y + 2), sal_text[:40], fill=(52, 211, 153), font=font_val)

    # Row 2: Location
    draw.text((pad_x + 30, specs_top + 125), "LOCATION", fill=(148, 163, 184), font=font_label)
    loc_y = specs_top + 160
    loc_text = job.location or "Pan India / Remote"
    if icon_loc:
        img.paste(icon_loc, (pad_x + 30, loc_y), icon_loc)
        draw.text((pad_x + 75, loc_y + 2), loc_text[:40], fill=(244, 244, 245), font=font_val)
    else:
        draw.text((pad_x + 30, loc_y + 2), loc_text[:40], fill=(244, 244, 245), font=font_val)

    # Row 3: Eligibility
    draw.text((pad_x + 30, specs_top + 220), "ELIGIBLE BATCHES & DEGREES", fill=(148, 163, 184), font=font_label)
    elig_y = specs_top + 255
    raw_elig = (job.eligibility or "Any Graduate / BE / B.Tech / MCA / All Batches").strip()
    if len(raw_elig) > 42:
        raw_elig = raw_elig[:39] + "..."
    if icon_type:
        img.paste(icon_type, (pad_x + 30, elig_y), icon_type)
        draw.text((pad_x + 75, elig_y + 2), raw_elig, fill=(244, 244, 245), font=font_val)
    else:
        draw.text((pad_x + 30, elig_y + 2), raw_elig, fill=(244, 244, 245), font=font_val)

    # Row 4: Key Skills Chips
    skills_list = job.get_skills_list() if hasattr(job, 'get_skills_list') else []
    skills_chips = ", ".join(skills_list[:4]) if skills_list else (job.skills_required or "Software Development, Problem Solving")
    if len(skills_chips) > 42:
        skills_chips = skills_chips[:39] + "..."
    draw.text((pad_x + 30, specs_top + 318), f"KEY SKILLS: {skills_chips}", fill=(147, 197, 253), font=font_skills)

    # 8. Apply Link & Scannable QR Code Section
    qr_card_top = specs_bottom + 25
    qr_card_bottom = qr_card_top + 230
    draw.rounded_rectangle(
        [pad_x, qr_card_top, 960, qr_card_bottom],
        radius=28,
        fill=(15, 23, 42),
        outline=(51, 65, 85),
        width=2
    )

    # Determine Job Share URL
    if hasattr(job, 'category') and job.category and job.uuid:
        target_apply_url = f"{base_url}/category/{job.category.slug}/job/{job.uuid}/"
    elif job.uuid:
        target_apply_url = f"{base_url}/job/{job.uuid}/"
    else:
        target_apply_url = base_url

    # Generate QR Code
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=5,
            border=2,
        )
        qr.add_data(target_apply_url)
        qr.make(fit=True)
        qr_pil = qr.make_image(fill_color='#090d16', back_color='#ffffff').convert('RGBA')
        qr_size = 180
        qr_pil = qr_pil.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        img.paste(qr_pil, (pad_x + 30, qr_card_top + 25), qr_pil)
    except Exception as qr_err:
        logger.warning(f"Failed to generate story QR code: {qr_err}")

    # Text next to QR code
    text_x = pad_x + 235
    draw.text((text_x, qr_card_top + 38), "SCAN QR CODE TO APPLY", fill=(255, 255, 255), font=font_qr_title)
    draw.text((text_x, qr_card_top + 80), "Screenshot or scan with phone camera", fill=(148, 163, 184), font=font_qr_sub)
    draw.text((text_x, qr_card_top + 115), "Opens the full job details", fill=(110, 231, 183), font=font_qr_sub)
    
    # Display site name (the QR code holds the full job URL)
    short_display = "kashiiupdatez.online"
    draw.text((text_x, qr_card_top + 160), short_display, fill=(56, 189, 248), font=font_qr_sub)

    # 9. Link Sticker Call-To-Action Button (Instagram Gradient)
    btn_y = qr_card_bottom + 25
    draw.rounded_rectangle([pad_x, btn_y, 960, btn_y + 110], radius=55, fill=(234, 88, 12))
    draw.text((540, btn_y + 55), "SCAN THE QR CODE TO APPLY", fill=(255, 255, 255), font=font_btn, anchor="mm")

    # 10. Footer Attribution
    draw.text((540, btn_y + 155), "kashiiupdatez.online · 100% Verified 7-Day Opportunities", fill=(148, 163, 184), font=font_footer, anchor="mm")

    buf = io.BytesIO()
    # Instagram's Content Publishing API accepts JPEG only.
    img.save(buf, format='JPEG', quality=92, optimize=True)
    buf.seek(0)
    return buf


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
                         params={'username': getattr(settings, 'INSTAGRAM_ACCOUNT_HANDLE', '')}, timeout=15)
        data = r.json()
    except Exception as exc:
        return {'configured': True, 'connected': False, 'error': f'Insta Automation unreachable ({type(exc).__name__})',
                'connect_url': f"{url}/instagram/connect/start/?publish=1"}
    if r.status_code == 403:
        return {'configured': True, 'connected': False, 'error': 'Story token rejected by Insta Automation.',
                'connect_url': f"{url}/instagram/connect/start/?publish=1"}
    data['configured'] = True
    return data


def publish_via_reelflow(job, base_url=''):
    """Post the job's 9:16 story through Insta Automation's connected account."""
    url = getattr(settings, 'REELFLOW_URL', '')
    base = _public_base_url(base_url)
    ts = int(job.updated_at.timestamp()) if getattr(job, 'updated_at', None) else 1
    image_url = f"{base}/api/jobs/{job.id}/ig-story-image/?v={ts}"
    share_url = job.get_story_sticker_url(base_url=base) if hasattr(job, 'get_story_sticker_url') else f"{base}/job/{job.id}/"
    out = {'story_image_url': image_url, 'story_sticker_url': share_url, 'job_id': job.id}
    try:
        r = requests.post(f"{url}/internal/story/publish/",
                          headers={'X-Story-Token': settings.REELFLOW_STORY_TOKEN},
                          json={'image_url': image_url,
                                'username': getattr(settings, 'INSTAGRAM_ACCOUNT_HANDLE', '')},
                          timeout=90)
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

