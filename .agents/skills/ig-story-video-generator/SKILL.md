---
name: ig-story-video-generator
description: >-
  Enterprise guide and technical implementation patterns for client-side HTML5 Canvas 9:16 Story Card design, Pillow Python PNG image generation, and high-bitrate 60FPS MediaRecorder video export for Instagram Reels & Stories. Use this skill when building story creators, canvas video generators, social media exporters, and dynamic link sticker cards.
---

# 📱 Instagram Story & 60FPS Canvas Video Generator Engine

This skill provides full architecture patterns for client-side HTML5 Canvas 9:16 vertical story cards, server-side Django Pillow PNG card generation, and client-side 60FPS `MediaRecorder` video export optimized for Instagram Reels, Stories, and social sharing.

---

## 1. Client-Side HTML5 Canvas 60FPS Video Generator Pattern

Use this JavaScript pattern to record a 5-second animated 1080x1920 HD video (`.mp4` / `.webm`) directly in the browser using `canvas.captureStream(60)` and `MediaRecorder`.

```javascript
function generateIgStoryVideo({ companyName, titleText, stipend, location, jobType, deadline, skills }) {
  const canvas = document.createElement('canvas');
  canvas.width = 1080;
  canvas.height = 1920;
  const ctx = canvas.getContext('2d');

  // roundRect Polyfill for Older Browsers
  if (!ctx.roundRect) {
    ctx.roundRect = function(x, y, w, h, r) {
      if (typeof r === 'number') r = [r, r, r, r];
      const [tl, tr, br, bl] = r;
      this.beginPath();
      this.moveTo(x + tl, y);
      this.lineTo(x + w - tr, y);
      this.quadraticCurveTo(x + w, y, x + w, y + tr);
      this.lineTo(x + w, y + h - br);
      this.quadraticCurveTo(x + w, y + h, x + w - br, y + h);
      this.lineTo(x + bl, y + h);
      this.quadraticCurveTo(x, y + h, x, y + h - bl);
      this.lineTo(x, y + tl);
      this.quadraticCurveTo(x, y, x + tl, y);
      this.closePath();
      return this;
    };
  }

  // Setup High-Bitrate MediaRecorder Stream (60 FPS, 8 Mbps)
  const stream = canvas.captureStream(60);
  let mimeType = 'video/mp4;codecs=avc1';
  if (!MediaRecorder.isTypeSupported(mimeType)) mimeType = 'video/webm;codecs=vp9';
  if (!MediaRecorder.isTypeSupported(mimeType)) mimeType = 'video/webm';

  let mediaRecorder;
  try {
    mediaRecorder = new MediaRecorder(stream, { mimeType: mimeType, videoBitsPerSecond: 8000000 });
  } catch (e) {
    mediaRecorder = new MediaRecorder(stream);
  }

  const chunks = [];
  mediaRecorder.ondataavailable = (e) => {
    if (e.data && e.data.size > 0) chunks.push(e.data);
  };

  mediaRecorder.onstop = () => {
    const blob = new Blob(chunks, { type: mediaRecorder.mimeType || 'video/mp4' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `Story_Video_${companyName}.mp4`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  mediaRecorder.start();

  let startTime = performance.now();
  const duration = 5000; // 5 Seconds

  function renderFrame(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1.0);

    // 1. Dark Gradient Background
    const bgGrad = ctx.createLinearGradient(0, 0, 1080, 1920);
    bgGrad.addColorStop(0, '#0f172a');
    bgGrad.addColorStop(0.5, '#1e1b4b');
    bgGrad.addColorStop(1, '#31103f');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, 1080, 1920);

    // 2. Ambient Soft Glow Orbs
    const glowScale = 1.0 + Math.sin(now / 500) * 0.08;
    const orb1 = ctx.createRadialGradient(900, 250, 10, 900, 250, 480 * glowScale);
    orb1.addColorStop(0, 'rgba(236, 72, 153, 0.35)');
    orb1.addColorStop(1, 'rgba(236, 72, 153, 0)');
    ctx.fillStyle = orb1;
    ctx.fillRect(0, 0, 1080, 1920);

    // 3. Main Glass Card Container
    ctx.fillStyle = 'rgba(15, 23, 42, 0.96)';
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.roundRect(90, 220, 900, 1480, 48);
    ctx.fill();
    ctx.stroke();

    ctx.textBaseline = 'top';
    ctx.textAlign = 'left';

    // 4. Header Badge & Handle
    ctx.fillStyle = '#ec4899';
    ctx.beginPath();
    ctx.roundRect(150, 270, 360, 65, 32);
    ctx.fill();

    ctx.fillStyle = '#ffffff';
    ctx.font = '900 24px Consolas, "Courier New", monospace';
    ctx.fillText('NEW REQUIREMENT', 180, 290);

    ctx.fillStyle = '#94a3b8';
    ctx.font = '800 28px Consolas, "Courier New", monospace';
    ctx.textAlign = 'right';
    ctx.fillText('@ikashii_07', 930, 290);
    ctx.textAlign = 'left';

    // 5. Divider Line
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(150, 365);
    ctx.lineTo(930, 365);
    ctx.stroke();

    // 6. Company Header
    ctx.fillStyle = '#38bdf8';
    ctx.font = '900 36px Consolas, "Courier New", monospace';
    ctx.fillText(companyName.toUpperCase(), 150, 395);

    // 7. Yellow Highlighted Job Title
    const words = titleText.split(' ');
    let line = '';
    let y = 455;
    ctx.font = '900 48px Consolas, "Courier New", monospace';

    const textHeight = Math.ceil(words.length / 2) * 58 + 20;
    ctx.fillStyle = 'rgba(253, 224, 71, 0.12)';
    ctx.strokeStyle = '#fde047';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.roundRect(140, 445, 800, textHeight, 20);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#fde047';
    for (let n = 0; n < words.length; n++) {
      let testLine = line + words[n] + ' ';
      if (ctx.measureText(testLine).width > 750 && n > 0) {
        ctx.fillText(line, 160, y + 10);
        line = words[n] + ' ';
        y += 58;
      } else {
        line = testLine;
      }
    }
    ctx.fillText(line, 160, y + 10);

    // 8. Inset Details Card
    const detY = Math.max(y + 80, 710);
    ctx.fillStyle = '#1e293b';
    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.roundRect(150, detY, 780, 360, 32);
    ctx.fill();
    ctx.stroke();

    // Details Grid Items (With Emojis)
    ctx.fillStyle = '#94a3b8';
    ctx.font = '900 20px Consolas, "Courier New", monospace';
    ctx.fillText('STIPEND / SALARY', 190, detY + 30);
    ctx.fillStyle = '#34d399';
    ctx.font = '900 30px Consolas, "Courier New", monospace';
    ctx.fillText('💰 ' + stipend, 190, detY + 60);

    ctx.fillStyle = '#94a3b8';
    ctx.font = '900 20px Consolas, "Courier New", monospace';
    ctx.fillText('JOB TYPE', 560, detY + 30);
    ctx.fillStyle = '#38bdf8';
    ctx.font = '900 30px Consolas, "Courier New", monospace';
    ctx.fillText('⚡ ' + jobType, 560, detY + 60);

    ctx.fillStyle = '#94a3b8';
    ctx.font = '900 20px Consolas, "Courier New", monospace';
    ctx.fillText('LOCATION', 190, detY + 130);
    ctx.fillStyle = '#f4f4f5';
    ctx.font = '700 28px Consolas, "Courier New", monospace';
    ctx.fillText('📍 ' + location, 190, detY + 160);

    ctx.fillStyle = '#94a3b8';
    ctx.font = '900 20px Consolas, "Courier New", monospace';
    ctx.fillText('DEADLINE', 560, detY + 130);
    ctx.fillStyle = '#f43f5e';
    ctx.font = '700 28px Consolas, "Courier New", monospace';
    ctx.fillText('⏳ ' + deadline, 560, detY + 160);

    // 9. Pulsing Link Sticker CTA
    const stickerPulse = 1.0 + Math.sin(now / 180) * 0.04;
    const btnY = detY + 395;

    ctx.save();
    ctx.translate(540, btnY + 50);
    ctx.scale(stickerPulse, stickerPulse);
    ctx.translate(-540, -(btnY + 50));

    const btnGrad = ctx.createLinearGradient(150, btnY, 930, btnY);
    btnGrad.addColorStop(0, '#e1306c');
    btnGrad.addColorStop(0.5, '#fd1d1d');
    btnGrad.addColorStop(1, '#fcb045');
    ctx.fillStyle = btnGrad;
    ctx.beginPath();
    ctx.roundRect(150, btnY, 780, 100, 50);
    ctx.fill();

    ctx.fillStyle = '#ffffff';
    ctx.font = '900 28px Consolas, "Courier New", monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('🔗 Link in Bio - Click to Apply ↗', 540, btnY + 50);
    ctx.restore();

    ctx.fillStyle = '#94a3b8';
    ctx.font = '800 24px Consolas, "Courier New", monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillText('kashiiupdatez.online', 540, btnY + 125);

    if (elapsed < duration) {
      requestAnimationFrame(renderFrame);
    } else {
      mediaRecorder.stop();
    }
  }

  requestAnimationFrame(renderFrame);
}
```

---

## 2. Server-Side Django Pillow 9:16 PNG Image Generator Pattern

Use this Django view function pattern to dynamically render 1080x1920 PNG story cards using TrueType fonts and real PNG icon overlays:

```python
import os
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from requirements.models import JobPosting

def api_job_ig_story_image(request, pk):
    job = get_object_or_404(JobPosting, pk=pk)

    # 1080x1920 Vertical HD Canvas
    img = Image.new('RGB', (1080, 1920), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)

    # Gradient Background & Glow Orbs
    for y in range(1920):
        r = int(15 + (49 - 15) * (y / 1920))
        g = int(23 + (16 - 23) * (y / 1920))
        b = int(42 + (63 - 42) * (y / 1920))
        draw.line([(0, y), (1080, y)], fill=(r, g, b))

    # Outer Glass Card Box
    draw.rounded_rectangle([90, 220, 990, 1700], radius=48, fill=(15, 23, 42), outline=(56, 189, 248), width=4)

    # Output PNG Stream Response
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    response = HttpResponse(buf.getvalue(), content_type='image/png')
    response['Content-Disposition'] = f'inline; filename="IG_Story_{job.company_name}.png"'
    return response
```

---

## 3. Key Design Rules & Best Practices

1. **Explicit Text Alignment**: Always set `ctx.textBaseline = 'top'` before calculating vertical coordinates to avoid text overlapping across browsers.
2. **Fixed Padding Offsets**: Use relative vertical positioning (`const detY = Math.max(y + 80, 710)`) so long job titles push details cards down dynamically without running over boundaries.
3. **High Bitrate Video**: Always pass `{ videoBitsPerSecond: 8000000 }` to `MediaRecorder` to prevent blurriness when uploaded to Instagram Reels.
4. **Consolas Monospace Font**: Use `Consolas, "Courier New", monospace` for ultra-clean, technical readability on mobile screens.
