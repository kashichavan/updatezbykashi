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
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

_FONT_PATH = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Inter-Variable.ttf')
_FALLBACK_FONTS = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
_WEIGHTS = {400: b'Regular', 500: b'Medium', 600: b'SemiBold', 700: b'Bold', 800: b'ExtraBold', 900: b'Black'}


def _font(size: int, weight: int = 700):
    """Inter at the given weight; falls back to a system font if the bundled file is missing."""
    try:
        f = ImageFont.truetype(_FONT_PATH, size)
        try:
            f.set_variation_by_name(_WEIGHTS.get(weight, b'Bold'))
        except Exception:
            pass
        return f
    except Exception:
        for path in _FALLBACK_FONTS:
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _get_font(size: int, bold: bool = False):
    """Backward-compatible helper."""
    return _font(size, 700 if bold else 400)


def _fit(draw, text, font, max_w):
    """Truncate text with an ellipsis so it fits max_w pixels."""
    text = (text or '').strip()
    if draw.textlength(text, font=font) <= max_w:
        return text
    while text and draw.textlength(text + '…', font=font) > max_w:
        text = text[:-1]
    return text.rstrip(' ,.-/') + '…'


def _wrap(draw, text, font, max_w, max_lines):
    words, lines, cur = (text or '').split(), [], ''
    for w in words:
        t = f'{cur} {w}'.strip()
        if draw.textlength(t, font=font) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = _fit(draw, lines[-1] + ' …', font, max_w)
    return lines


def _ig_gradient(w, h):
    """Horizontal Instagram-style gradient (purple → pink → orange)."""
    stops = [(0.0, (131, 58, 180)), (0.5, (253, 29, 29)), (1.0, (252, 176, 69))]
    grad = Image.new('RGB', (w, 1))
    px = grad.load()
    for x in range(w):
        t = x / max(w - 1, 1)
        for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
            if t0 <= t <= t1:
                k = (t - t0) / (t1 - t0)
                px[x, 0] = tuple(int(c0[i] + (c1[i] - c0[i]) * k) for i in range(3))
                break
    return grad.resize((w, h))


def _paste_rounded(img, src, box, radius):
    x0, y0, x1, y1 = box
    mask = Image.new('L', (x1 - x0, y1 - y0), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, x1 - x0 - 1, y1 - y0 - 1], radius=radius, fill=255)
    img.paste(src.resize((x1 - x0, y1 - y0)), (x0, y0), mask)


def _job_apply_url(job, base_url):
    if getattr(job, 'category', None) and getattr(job, 'uuid', None):
        return f"{base_url}/category/{job.category.slug}/job/{job.uuid}/"
    if getattr(job, 'uuid', None):
        return f"{base_url}/job/{job.uuid}/"
    return base_url


def generate_job_story_image(job, base_url="https://kashiiupdatez.online", reply_cta=True) -> io.BytesIO:
    """
    Renders a 1080x1920 Instagram Story (JPEG) for a JobPosting.

    Content stays inside Instagram's safe area (top ~250px and bottom ~250px are covered
    by the progress bar and reply bar). Rendered at 2x then downscaled for smooth edges.
    reply_cta adds the "Reply APPLY" prompt that Insta Automation answers with the job link.
    """
    S = 2
    W, H = 1080 * S, 1920 * S

    def u(v):
        return int(v * S)

    # Background: near-black with soft blurred colour glows.
    img = Image.new('RGB', (W, H), (7, 10, 18))
    glow = Image.new('RGB', (W // 8, H // 8), (7, 10, 18))
    gd = ImageDraw.Draw(glow)
    for (cx, cy, r, col) in [(980, 160, 420, (110, 40, 170)), (60, 330, 300, (200, 60, 40)),
                             (120, 1700, 460, (30, 70, 200)), (1000, 1250, 300, (180, 30, 110))]:
        gd.ellipse([(cx - r) // 8, (cy - r) // 8, (cx + r) // 8, (cy + r) // 8], fill=col)
    glow = glow.filter(ImageFilter.GaussianBlur(28)).resize((W, H), Image.Resampling.BICUBIC)
    img = Image.blend(img, glow, 0.55)
    draw = ImageDraw.Draw(img, 'RGBA')
    # Faint grid texture
    for gx in range(0, W, u(60)):
        draw.line([(gx, 0), (gx, H)], fill=(255, 255, 255, 6), width=1)
    for gy in range(0, H, u(60)):
        draw.line([(0, gy), (W, gy)], fill=(255, 255, 255, 6), width=1)

    L, R = u(84), u(1080 - 84)
    CW = R - L
    white, muted, faint = (255, 255, 255), (161, 170, 189), (100, 110, 130)

    # 1. Brand row
    y = u(250)
    logo = u(56)
    _paste_rounded(img, _ig_gradient(logo, logo), (L, y, L + logo, y + logo), u(16))
    draw.text((L + logo // 2, y + logo // 2), "K", fill=white, font=_font(u(34), 900), anchor='mm')
    draw.text((L + logo + u(18), y + logo // 2), "KASHII UPDATEZ", fill=white, font=_font(u(28), 800), anchor='lm')
    handle = f"@{getattr(settings, 'INSTAGRAM_ACCOUNT_HANDLE', 'ikashii_07')}"
    draw.text((R, y + logo // 2), handle, fill=muted, font=_font(u(26), 600), anchor='rm')

    # 2. Status pills
    y += u(100)
    exp_display = job.get_experience_display() if hasattr(job, 'get_experience_display') else "Fresher"
    is_fresher = any(k in exp_display.lower() for k in ['fresher', '0-', '0 yr', 'intern', 'entry'])
    pill_font = _font(u(24), 800)
    t1 = "NOW HIRING"
    pw = int(draw.textlength(t1, font=pill_font)) + u(56)
    ph = u(56)
    _paste_rounded(img, _ig_gradient(pw, ph), (L, y, L + pw, y + ph), ph // 2)
    draw.text((L + pw // 2, y + ph // 2), t1, fill=white, font=pill_font, anchor='mm')
    if is_fresher:
        t2 = "FRESHERS WELCOME"
        x2 = L + pw + u(14)
        pw2 = int(draw.textlength(t2, font=pill_font)) + u(56)
        draw.rounded_rectangle([x2, y, x2 + pw2, y + ph], radius=ph // 2, fill=(16, 185, 129, 40),
                               outline=(52, 211, 153), width=u(2))
        draw.text((x2 + pw2 // 2, y + ph // 2), t2, fill=(110, 231, 183), font=pill_font, anchor='mm')

    # 3. Company + title
    y += ph + u(44)
    company = (job.company_name or "Top Tech Company").strip().upper()
    draw.text((L, y), _fit(draw, company, _font(u(38), 800), CW), fill=(125, 211, 252), font=_font(u(38), 800))
    y += u(62)
    title = job.title or "Software Engineer"
    for size in (88, 78, 68, 60):
        tf = _font(u(size), 800)
        lines = _wrap(draw, title, tf, CW, 3)
        if len(lines) <= 2 or size == 60:
            break
    lh = int(tf.size * 1.12)
    for line in lines:
        draw.text((L, y), line, fill=white, font=tf)
        y += lh
    y += u(34)

    # 4. 2x2 detail tiles
    def tile(x0, y0, x1, y1, label, value, accent):
        draw.rounded_rectangle([x0, y0, x1, y1], radius=u(28), fill=(255, 255, 255, 14),
                               outline=(255, 255, 255, 30), width=u(2))
        draw.rounded_rectangle([x0 + u(26), y0 + u(30), x0 + u(34), y0 + u(52)], radius=u(4), fill=accent)
        draw.text((x0 + u(48), y0 + u(41)), label, fill=muted, font=_font(u(21), 700), anchor='lm')
        vf = _font(u(34), 700)
        draw.text((x0 + u(26), y0 + u(78)), _fit(draw, value, vf, x1 - x0 - u(52)), fill=white, font=vf)

    gap = u(18)
    tw = (CW - gap) // 2
    th = u(150)
    skills_list = job.get_skills_list() if hasattr(job, 'get_skills_list') else []
    tiles = [
        ("EXPERIENCE", exp_display, (52, 211, 153) if is_fresher else (129, 140, 248)),
        ("SALARY", job.stipend_salary or "Competitive", (250, 204, 21)),
        ("LOCATION", job.location or "Pan India", (56, 189, 248)),
        ("ELIGIBILITY", (job.eligibility or "Any Graduate").strip(), (244, 114, 182)),
    ]
    for i, (lab, val, acc) in enumerate(tiles):
        cx = L + (i % 2) * (tw + gap)
        cy = y + (i // 2) * (th + gap)
        tile(cx, cy, cx + tw, cy + th, lab, val, acc)
    y += 2 * th + gap + u(30)

    # 5. Skill chips (one row; overflow is dropped rather than crowding the apply card)
    if not skills_list and getattr(job, 'skills_required', ''):
        skills_list = [x.strip() for x in job.skills_required.split(',') if x.strip()]
    chip_f = _font(u(25), 600)
    cx, row, chip_h = L, 0, u(52)
    for sk in skills_list[:8]:
        label = _fit(draw, sk, chip_f, u(300))
        cw = int(draw.textlength(label, font=chip_f)) + u(40)
        if cx + cw > R:
            row += 1
            cx = L
            if row > 0:
                row = 0
                break
        cy = y + row * (chip_h + u(12))
        draw.rounded_rectangle([cx, cy, cx + cw, cy + chip_h], radius=chip_h // 2, fill=(59, 130, 246, 30),
                               outline=(96, 165, 250, 120), width=u(2))
        draw.text((cx + cw // 2, cy + chip_h // 2), label, fill=(191, 219, 254), font=chip_f, anchor='mm')
        cx += cw + u(12)
    if skills_list:
        y += (row + 1) * (chip_h + u(12)) + u(22)

    # 6. Apply card (white) with QR + website link
    apply_url = _job_apply_url(job, base_url)
    card_h = u(250)
    y = min(y, u(1560) - card_h - u(110))
    draw.rounded_rectangle([L, y, R, y + card_h], radius=u(36), fill=(255, 255, 255))
    qs = card_h - u(50)
    try:
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=1)
        qr.add_data(apply_url)
        qr.make(fit=True)
        qimg = qr.make_image(fill_color=(7, 10, 18), back_color='white').convert('RGB')
        img.paste(qimg.resize((qs, qs), Image.Resampling.NEAREST), (L + u(25), y + u(25)))
    except Exception as qr_err:
        logger.warning(f"Failed to generate story QR code: {qr_err}")
    tx = L + u(25) + qs + u(32)
    tmax = R - tx - u(24)
    draw.text((tx, y + u(40)), "APPLY ON", fill=(100, 116, 139), font=_font(u(22), 800))
    draw.text((tx, y + u(72)), _fit(draw, "kashiiupdatez.online", _font(u(40), 800), tmax),
              fill=(7, 10, 18), font=_font(u(40), 800))
    path = apply_url.replace(base_url, '') or '/'
    draw.text((tx, y + u(130)), _fit(draw, path, _font(u(22), 500), tmax), fill=(100, 116, 139), font=_font(u(22), 500))
    draw.text((tx, y + u(178)), "Scan the QR with your camera", fill=(37, 99, 235), font=_font(u(23), 700))
    y += card_h + u(28)

    # 7. Reply CTA (Insta Automation DMs the link) pointing at the reply bar
    cta_h = u(96)
    if reply_cta:
        _paste_rounded(img, _ig_gradient(CW, cta_h), (L, y, R, y + cta_h), cta_h // 2)
        draw.text(((L + R) // 2, y + cta_h // 2), "REPLY “APPLY” · GET THE LINK IN DM",
                  fill=white, font=_font(u(32), 900), anchor='mm')
        ay = y + cta_h + u(34)
        mid = (L + R) // 2
        for k in range(2):
            yy = ay + k * u(26)
            draw.line([(mid - u(26), yy), (mid, yy + u(20)), (mid + u(26), yy)],
                      fill=(255, 255, 255, 200 - k * 90), width=u(5), joint='curve')
    else:
        # Leave room just below for the Link sticker added in the Instagram app.
        draw.rounded_rectangle([L, y, R, y + cta_h], radius=cta_h // 2, outline=(255, 255, 255, 90), width=u(3))
        draw.text(((L + R) // 2, y + cta_h // 2), "TAP THE LINK BELOW TO APPLY",
                  fill=white, font=_font(u(32), 900), anchor='mm')

    out = img.resize((1080, 1920), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    # Instagram's Content Publishing API accepts JPEG only.
    out.save(buf, format='JPEG', quality=93, optimize=True)
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
                                'link_url': share_url,
                                'title': f"{job.company_name} - {job.title}"[:255],
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

