"""Layered Instagram story renderer: one design, rendered as a still JPEG or an animated MP4.

The layout is built once as a list of sprites (small RGBA images with a position and an
entrance animation). A still image composites every sprite in its final state; the video
composites them per frame with motion (slide, fade, pop, stagger) over a drifting
background, then pipes the frames to ffmpeg.

Coordinates are designed on a 1080x1920 canvas and scaled by `k`.
"""
import io
import logging
import math
import os
import subprocess
import tempfile
from dataclasses import dataclass, field

import qrcode
from django.conf import settings
from PIL import Image, ImageDraw, ImageFilter, ImageFont

logger = logging.getLogger(__name__)

_FONT_PATH = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Inter-Variable.ttf')
_FALLBACK_FONTS = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
_WEIGHTS = {400: b'Regular', 500: b'Medium', 600: b'SemiBold', 700: b'Bold', 800: b'ExtraBold', 900: b'Black'}
_font_cache = {}

WHITE = (255, 255, 255)
MUTED = (161, 170, 189)
BG = (7, 10, 18)


def font(size: int, weight: int = 700):
    key = (size, weight)
    if key in _font_cache:
        return _font_cache[key]
    f = None
    try:
        f = ImageFont.truetype(_FONT_PATH, size)
        try:
            f.set_variation_by_name(_WEIGHTS.get(weight, b'Bold'))
        except Exception:
            pass
    except Exception:
        for path in _FALLBACK_FONTS:
            try:
                f = ImageFont.truetype(path, size)
                break
            except Exception:
                continue
    f = f or ImageFont.load_default()
    _font_cache[key] = f
    return f


_measure = ImageDraw.Draw(Image.new('L', (1, 1)))


def fit(text, f, max_w):
    text = (text or '').strip()
    if _measure.textlength(text, font=f) <= max_w:
        return text
    while text and _measure.textlength(text + '…', font=f) > max_w:
        text = text[:-1]
    return text.rstrip(' ,.-/') + '…'


def wrap(text, f, max_w, max_lines):
    words, lines, cur = (text or '').split(), [], ''
    for w in words:
        t = f'{cur} {w}'.strip()
        if _measure.textlength(t, font=f) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = fit(lines[-1] + ' …', f, max_w)
    return lines


def ig_gradient(w, h, shift=0.0):
    """Horizontal purple → red → orange gradient; `shift` (0..1) slides it for shimmer."""
    stops = [(0.0, (131, 58, 180)), (0.5, (253, 29, 29)), (1.0, (252, 176, 69))]
    row = Image.new('RGB', (max(w, 1), 1))
    px = row.load()
    for x in range(w):
        t = (x / max(w - 1, 1) + shift) % 2.0
        t = 2.0 - t if t > 1.0 else t  # ping-pong so the loop is seamless
        for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
            if t0 <= t <= t1:
                q = (t - t0) / (t1 - t0)
                px[x, 0] = tuple(int(c0[i] + (c1[i] - c0[i]) * q) for i in range(3))
                break
    return row.resize((max(w, 1), max(h, 1)))


def rounded_mask(w, h, r):
    m = Image.new('L', (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255)
    return m


def job_apply_url(job, base_url):
    if getattr(job, 'category', None) and getattr(job, 'uuid', None):
        return f"{base_url}/category/{job.category.slug}/job/{job.uuid}/"
    if getattr(job, 'uuid', None):
        return f"{base_url}/job/{job.uuid}/"
    return base_url


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

@dataclass
class Sprite:
    img: Image.Image
    x: int
    y: int
    start: float = 0.0          # seconds when the entrance begins
    dur: float = 0.55
    kind: str = 'rise'          # rise | pop | fade | drop | wipe
    loop: str = ''              # '' | shimmer | bounce | pulse | scan
    meta: dict = field(default_factory=dict)


CTA_TEXT = {
    'reply': "REPLY “APPLY” · GET THE LINK IN DM",
    'comment': "COMMENT “LINK” · GET THE APPLY LINK",
}


def _cta_mode(reply_cta):
    if reply_cta is True:
        return 'reply'
    if reply_cta is False or reply_cta is None:
        return 'sticker'
    return reply_cta


def build_layout(job, base_url, reply_cta, k):
    """Return (W, H, sprites) for a story scaled by k (1.0 = 1080x1920).

    reply_cta: True/'reply' (story replies), 'comment' (reels), False/'sticker' (manual Link sticker).
    """
    cta_mode = _cta_mode(reply_cta)
    def u(v):
        return int(round(v * k))

    W, H = u(1080), u(1920)
    L, R = u(84), u(1080 - 84)
    CW = R - L
    sprites = []
    t = 0.25  # running start time for the stagger

    # Brand row
    row_h = u(56)
    row = Image.new('RGBA', (CW, row_h), (0, 0, 0, 0))
    logo = ig_gradient(row_h, row_h).convert('RGBA')
    row.paste(logo, (0, 0), rounded_mask(row_h, row_h, u(16)))
    d = ImageDraw.Draw(row)
    d.text((row_h // 2, row_h // 2), "K", fill=WHITE, font=font(u(34), 900), anchor='mm')
    d.text((row_h + u(18), row_h // 2), "KASHII UPDATEZ", fill=WHITE, font=font(u(28), 800), anchor='lm')
    reel_handle = getattr(settings, 'REEL_ACCOUNT_HANDLE', '') if cta_mode == 'comment' else ''
    handle = f"@{reel_handle or getattr(settings, 'INSTAGRAM_ACCOUNT_HANDLE', 'ikashii_07')}"
    d.text((CW, row_h // 2), handle, fill=MUTED, font=font(u(26), 600), anchor='rm')
    sprites.append(Sprite(row, L, u(250), start=0.15, kind='drop'))

    # Pills
    y = u(350)
    exp_display = job.get_experience_display() if hasattr(job, 'get_experience_display') else "Fresher"
    is_fresher = any(s in exp_display.lower() for s in ['fresher', '0-', '0 yr', 'intern', 'entry'])
    pf = font(u(24), 800)
    ph = u(56)
    txt = "NOW HIRING"
    pw = int(_measure.textlength(txt, font=pf)) + u(76)
    pill = Image.new('RGBA', (pw, ph), (0, 0, 0, 0))
    pill.paste(ig_gradient(pw, ph).convert('RGBA'), (0, 0), rounded_mask(pw, ph, ph // 2))
    pd = ImageDraw.Draw(pill)
    dot = u(10)
    pd.ellipse([u(22), ph // 2 - dot // 2, u(22) + dot, ph // 2 + dot // 2], fill=WHITE)
    pd.text((u(22) + dot + u(12), ph // 2), txt, fill=WHITE, font=pf, anchor='lm')
    sprites.append(Sprite(pill, L, y, start=0.45, kind='pop', loop='pulse',
                          meta={'dot': (u(22) + dot // 2, ph // 2, dot)}))
    if is_fresher:
        txt2 = "FRESHERS WELCOME"
        pw2 = int(_measure.textlength(txt2, font=pf)) + u(56)
        p2 = Image.new('RGBA', (pw2, ph), (0, 0, 0, 0))
        ImageDraw.Draw(p2).rounded_rectangle([0, 0, pw2 - 1, ph - 1], radius=ph // 2, fill=(16, 185, 129, 45),
                                             outline=(52, 211, 153, 255), width=max(1, u(2)))
        ImageDraw.Draw(p2).text((pw2 // 2, ph // 2), txt2, fill=(110, 231, 183), font=pf, anchor='mm')
        sprites.append(Sprite(p2, L + pw + u(14), y, start=0.6, kind='pop'))

    # Company + title
    y += ph + u(44)
    cf = font(u(38), 800)
    company = fit((job.company_name or "Top Tech Company").strip().upper(), cf, CW)
    cimg = Image.new('RGBA', (CW, u(50)), (0, 0, 0, 0))
    ImageDraw.Draw(cimg).text((0, 0), company, fill=(125, 211, 252), font=cf)
    sprites.append(Sprite(cimg, L, y, start=0.75, kind='rise'))
    y += u(62)
    title = job.title or "Software Engineer"
    for size in (88, 78, 68, 60):
        tf = font(u(size), 800)
        lines = wrap(title, tf, CW, 3)
        if len(lines) <= 2 or size == 60:
            break
    lh = int(tf.size * 1.12)
    t = 0.9
    for line in lines:
        li = Image.new('RGBA', (CW, lh + u(12)), (0, 0, 0, 0))
        ImageDraw.Draw(li).text((0, 0), line, fill=WHITE, font=tf)
        sprites.append(Sprite(li, L, y, start=t, kind='wipe', dur=0.6))
        y += lh
        t += 0.12
    y += u(34)

    # Detail tiles
    gap = u(18)
    tw = (CW - gap) // 2
    th = u(150)
    tiles = [
        ("EXPERIENCE", exp_display, (52, 211, 153) if is_fresher else (129, 140, 248)),
        ("SALARY", job.stipend_salary or "Competitive", (250, 204, 21)),
        ("LOCATION", job.location or "Pan India", (56, 189, 248)),
        ("ELIGIBILITY", (job.eligibility or "Any Graduate").strip(), (244, 114, 182)),
    ]
    t = max(t, 1.35)
    for i, (lab, val, acc) in enumerate(tiles):
        ti = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
        td = ImageDraw.Draw(ti)
        td.rounded_rectangle([0, 0, tw - 1, th - 1], radius=u(28), fill=(255, 255, 255, 16),
                             outline=(255, 255, 255, 34), width=max(1, u(2)))
        td.rounded_rectangle([u(26), u(30), u(34), u(52)], radius=u(4), fill=acc)
        td.text((u(48), u(41)), lab, fill=MUTED, font=font(u(21), 700), anchor='lm')
        vf = font(u(34), 700)
        td.text((u(26), u(78)), fit(val, vf, tw - u(52)), fill=WHITE, font=vf)
        sprites.append(Sprite(ti, L + (i % 2) * (tw + gap), y + (i // 2) * (th + gap),
                              start=t + i * 0.1, kind='rise'))
    y += 2 * th + gap + u(30)
    t += 0.45

    # Skill chips (one row)
    skills = job.get_skills_list() if hasattr(job, 'get_skills_list') else []
    if not skills and getattr(job, 'skills_required', ''):
        skills = [s.strip() for s in job.skills_required.split(',') if s.strip()]
    chf = font(u(25), 600)
    chh = u(52)
    cx = L
    for j, sk in enumerate(skills[:8]):
        label = fit(sk, chf, u(300))
        cw = int(_measure.textlength(label, font=chf)) + u(40)
        if cx + cw > R:
            break
        ch = Image.new('RGBA', (cw, chh), (0, 0, 0, 0))
        cd = ImageDraw.Draw(ch)
        cd.rounded_rectangle([0, 0, cw - 1, chh - 1], radius=chh // 2, fill=(59, 130, 246, 34),
                             outline=(96, 165, 250, 130), width=max(1, u(2)))
        cd.text((cw // 2, chh // 2), label, fill=(191, 219, 254), font=chf, anchor='mm')
        sprites.append(Sprite(ch, cx, y, start=t + j * 0.06, kind='pop', dur=0.4))
        cx += cw + u(12)
    if skills:
        y += chh + u(34)
    t += 0.35

    # Apply card
    apply_url = job_apply_url(job, base_url)
    card_h = u(250)
    y = min(y, u(1560) - card_h - u(110))
    card = Image.new('RGBA', (CW, card_h), (0, 0, 0, 0))
    cdraw = ImageDraw.Draw(card)
    cdraw.rounded_rectangle([0, 0, CW - 1, card_h - 1], radius=u(36), fill=(255, 255, 255, 255))
    qs = card_h - u(50)
    try:
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=1)
        qr.add_data(apply_url)
        qr.make(fit=True)
        qimg = qr.make_image(fill_color=BG, back_color='white').convert('RGBA')
        card.paste(qimg.resize((qs, qs), Image.Resampling.NEAREST), (u(25), u(25)))
    except Exception as exc:
        logger.warning("Story QR generation failed: %s", exc)
    tx = u(25) + qs + u(32)
    tmax = CW - tx - u(24)
    cdraw.text((tx, u(40)), "APPLY ON", fill=(100, 116, 139), font=font(u(22), 800))
    cdraw.text((tx, u(72)), fit("kashiiupdatez.online", font(u(40), 800), tmax), fill=BG, font=font(u(40), 800))
    path = apply_url.replace(base_url, '') or '/'
    cdraw.text((tx, u(130)), fit(path, font(u(22), 500), tmax), fill=(100, 116, 139), font=font(u(22), 500))
    cdraw.text((tx, u(178)), "Scan the QR with your camera", fill=(37, 99, 235), font=font(u(23), 700))
    sprites.append(Sprite(card, L, y, start=t, kind='rise', dur=0.65, loop='scan',
                          meta={'qr': (u(25), u(25), qs)}))
    y += card_h + u(28)
    t += 0.4

    # CTA
    cta_h = u(96)
    if cta_mode in CTA_TEXT:
        cta = Image.new('RGBA', (CW, cta_h), (0, 0, 0, 0))
        cta.paste(ig_gradient(CW, cta_h).convert('RGBA'), (0, 0), rounded_mask(CW, cta_h, cta_h // 2))
        ImageDraw.Draw(cta).text((CW // 2, cta_h // 2), CTA_TEXT[cta_mode],
                                 fill=WHITE, font=font(u(32), 900), anchor='mm')
        sprites.append(Sprite(cta, L, y, start=t, kind='pop', dur=0.55, loop='shimmer'))
        aw, ah = u(60), u(56)
        arrow = Image.new('RGBA', (aw, ah), (0, 0, 0, 0))
        ad = ImageDraw.Draw(arrow)
        for n in range(2):
            yy = u(6) + n * u(26)
            ad.line([(u(4), yy), (aw // 2, yy + u(20)), (aw - u(4), yy)],
                    fill=(255, 255, 255, 220 - n * 100), width=max(2, u(5)), joint='curve')
        sprites.append(Sprite(arrow, (L + R) // 2 - aw // 2, y + cta_h + u(28), start=t + 0.3,
                              kind='fade', loop='bounce'))
    else:
        cta = Image.new('RGBA', (CW, cta_h), (0, 0, 0, 0))
        cd = ImageDraw.Draw(cta)
        cd.rounded_rectangle([0, 0, CW - 1, cta_h - 1], radius=cta_h // 2, outline=(255, 255, 255, 110),
                             width=max(2, u(3)))
        cd.text((CW // 2, cta_h // 2), "TAP THE LINK BELOW TO APPLY", fill=WHITE, font=font(u(32), 900), anchor='mm')
        sprites.append(Sprite(cta, L, y, start=t, kind='pop'))

    return W, H, sprites


# ---------------------------------------------------------------------------
# Background
# ---------------------------------------------------------------------------

_GLOWS = [  # (cx, cy, r, colour, drift_x, drift_y, phase)
    (980, 160, 420, (110, 40, 170), 70, 50, 0.0),
    (60, 330, 300, (200, 60, 40), 60, 80, 1.7),
    (120, 1700, 460, (30, 70, 200), 90, 60, 3.1),
    (1000, 1250, 300, (180, 30, 110), 60, 90, 4.4),
]


def background(W, H, k, t=0.0):
    """Dark canvas with soft colour glows (drifting with t) and a faint grid."""
    lw, lh = max(W // 8, 1), max(H // 8, 1)
    glow = Image.new('RGB', (lw, lh), BG)
    gd = ImageDraw.Draw(glow)
    for cx, cy, r, col, dx, dy, ph in _GLOWS:
        ox = dx * math.sin(t * 0.9 + ph)
        oy = dy * math.cos(t * 0.7 + ph)
        x, y, rr = (cx + ox) * k / 8, (cy + oy) * k / 8, r * k / 8
        gd.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col)
    glow = glow.filter(ImageFilter.GaussianBlur(28 * k)).resize((W, H), Image.Resampling.BICUBIC)
    return Image.blend(Image.new('RGB', (W, H), BG), glow, 0.55).convert('RGBA')


def grid_overlay(W, H, k):
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    step = max(int(60 * k), 8)
    for x in range(0, W, step):
        d.line([(x, 0), (x, H)], fill=(255, 255, 255, 7))
    for y in range(0, H, step):
        d.line([(0, y), (W, y)], fill=(255, 255, 255, 7))
    return g


# ---------------------------------------------------------------------------
# Still image
# ---------------------------------------------------------------------------

def render_still(job, base_url, reply_cta=True) -> io.BytesIO:
    """1080x1920 JPEG, rendered at 2x and downscaled for smooth edges."""
    W, H, sprites = build_layout(job, base_url, reply_cta, 2.0)
    frame = background(W, H, 2.0)
    frame.alpha_composite(grid_overlay(W, H, 2.0))
    for s in sprites:
        frame.alpha_composite(s.img, (s.x, s.y))
    out = frame.convert('RGB').resize((1080, 1920), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    out.save(buf, format='JPEG', quality=93, optimize=True)  # the Graph API accepts JPEG only
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# Animated video
# ---------------------------------------------------------------------------

def _ease_out_cubic(p):
    return 1 - (1 - p) ** 3


def _ease_out_back(p, s=1.7):
    p -= 1
    return p * p * ((s + 1) * p + s) + 1


def _with_alpha(img, a):
    if a >= 0.999:
        return img
    out = img.copy()
    out.putalpha(img.getchannel('A').point(lambda v: int(v * a)))
    return out


def _draw_sprite(frame, s, t, k, W):
    p = 0.0 if t < s.start else min(1.0, (t - s.start) / s.dur)
    if p <= 0:
        return
    img, x, y = s.img, s.x, s.y
    if s.kind == 'rise':
        e = _ease_out_cubic(p)
        y += int((1 - e) * 60 * k)
        img = _with_alpha(img, e)
    elif s.kind == 'drop':
        e = _ease_out_cubic(p)
        y -= int((1 - e) * 40 * k)
        img = _with_alpha(img, e)
    elif s.kind == 'fade':
        img = _with_alpha(img, _ease_out_cubic(p))
    elif s.kind == 'pop':
        e = _ease_out_back(p)
        sc = max(0.05, 0.6 + 0.4 * e)
        if abs(sc - 1) > 0.01:
            w, h = max(1, int(img.width * sc)), max(1, int(img.height * sc))
            x += (img.width - w) // 2
            y += (img.height - h) // 2
            img = img.resize((w, h), Image.Resampling.BILINEAR)
        img = _with_alpha(img, min(1.0, p * 2.2))
    elif s.kind == 'wipe':
        e = _ease_out_cubic(p)
        cut = max(1, int(img.width * e))
        img = _with_alpha(img.crop((0, 0, cut, img.height)), min(1.0, p * 1.6))
        y += int((1 - e) * 24 * k)

    # Ambient loops once the entrance is done
    if p >= 1 and s.loop:
        lt = t - s.start - s.dur
        if s.loop == 'bounce':
            y += int(abs(math.sin(lt * 3.2)) * 16 * k)
        elif s.loop == 'shimmer':
            img = img.copy()
            band = Image.new('RGBA', img.size, (0, 0, 0, 0))
            bd = ImageDraw.Draw(band)
            bx = int(((lt * 0.55) % 1.6 - 0.3) * img.width)
            bw = int(90 * k)
            bd.polygon([(bx, 0), (bx + bw, 0), (bx + bw - int(40 * k), img.height), (bx - int(40 * k), img.height)],
                       fill=(255, 255, 255, 70))
            band.putalpha(Image.composite(band.getchannel('A'), Image.new('L', img.size, 0), img.getchannel('A')))
            img.alpha_composite(band)
        elif s.loop == 'pulse':
            cx, cy, r = s.meta['dot']
            ring = (lt * 1.2) % 1.0
            img = img.copy()
            rd = ImageDraw.Draw(img)
            rr = r / 2 + ring * r * 1.4
            rd.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=(255, 255, 255, int(200 * (1 - ring))),
                       width=max(1, int(2 * k)))
        elif s.loop == 'scan':
            qx, qy, qs = s.meta['qr']
            sweep = (lt * 0.6) % 1.4
            if sweep <= 1.0:
                img = img.copy()
                sd = ImageDraw.Draw(img)
                ly = qy + int(sweep * qs)
                sd.rectangle([qx, ly, qx + qs, ly + max(2, int(4 * k))], fill=(37, 99, 235, 200))
    frame.alpha_composite(img, (x, max(0, y)))


def _ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return 'ffmpeg'


def video_cache_path(job, variant='reply', seconds=7.0):
    ts = int(job.updated_at.timestamp()) if getattr(job, 'updated_at', None) else 0
    folder = os.path.join(tempfile.gettempdir(), 'story_videos')
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, f"job_{job.id}_{ts}_{_video_width()}_{variant}_{int(seconds)}s.mp4")


def _video_width():
    try:
        return max(480, min(1080, int(os.environ.get('STORY_VIDEO_WIDTH', '720'))))
    except ValueError:
        return 720


def render_video(job, base_url, reply_cta=True, seconds=7.0, fps=24) -> str:
    """Render (or reuse) an animated MP4 story; returns the file path."""
    path = video_cache_path(job, _cta_mode(reply_cta), seconds)
    if os.path.exists(path) and os.path.getsize(path) > 0:
        return path
    w = _video_width()
    k = w / 1080
    W, H, sprites = build_layout(job, base_url, reply_cta, k)
    grid = grid_overlay(W, H, k)
    tmp = path + '.part.mp4'
    cmd = [
        _ffmpeg_exe(), '-y', '-loglevel', 'error',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(fps), '-i', '-',
        '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
        '-shortest', '-map', '0:v', '-map', '1:a',
        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p',
        '-profile:v', 'high', '-c:a', 'aac', '-b:a', '64k', '-movflags', '+faststart', tmp,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for n in range(int(seconds * fps)):
            t = n / fps
            frame = background(W, H, k, t)
            frame.alpha_composite(grid)
            for s in sprites:
                _draw_sprite(frame, s, t, k, W)
            proc.stdin.write(frame.convert('RGB').tobytes())
        proc.stdin.close()
        err = proc.stderr.read().decode(errors='replace')
        if proc.wait() != 0:
            raise RuntimeError(f'ffmpeg failed: {err[-400:]}')
    except Exception:
        proc.kill()
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    os.replace(tmp, path)
    return path
