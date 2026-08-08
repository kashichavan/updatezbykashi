---
name: ig-story-video-generator
description: >-
  Enterprise guide and technical implementation patterns for client-side HTML5 Canvas 9:16 Story Card design, Pillow Python PNG image generation, and high-bitrate 60FPS MediaRecorder video export for Instagram Reels & Stories. Use this skill when building story creators, canvas video generators, social media exporters, and dynamic link sticker cards.
---

# 📱 Web Video Generation & HTML/CSS/Canvas Animation Engine

This skill provides complete architecture patterns for generating high-quality WebM and MP4 videos directly in modern web browsers using HTML5, CSS animations, JavaScript HTML5 Canvas, `html2canvas`, and the browser `MediaRecorder` API.

---

## 1. Core Architecture Overview

Web video generation operates in three main paradigms:

1. **Direct HTML5 Canvas 60FPS Streaming**: Capturing high-framerate 2D Canvas render loops directly via `canvas.captureStream(60)`.
2. **DOM-to-Canvas Animation Capture (`html2canvas`)**: Converting complex HTML & CSS animated UI elements (glassmorphism cards, badges, gradients) into Canvas frames for video recording.
3. **Client-Side MediaRecorder Export**: Encoding canvas frames into high-bitrate WebM or MP4 video blobs and triggering user downloads.

---

## 2. Client-Side HTML/CSS DOM to Video Generation (`html2canvas` + `MediaRecorder`)

To capture real HTML/CSS elements (with CSS keyframe animations, glassmorphism, Google Fonts, and flexbox/grid layouts):

```javascript
import html2canvas from 'html2canvas';

async function recordHtmlElementToVideo(targetElement, durationMs = 5000, fps = 60) {
  const canvas = document.createElement('canvas');
  canvas.width = 1080;
  canvas.height = 1920;
  const ctx = canvas.getContext('2d');

  const stream = canvas.captureStream(fps);
  let mimeType = 'video/mp4;codecs=avc1';
  if (!MediaRecorder.isTypeSupported(mimeType)) mimeType = 'video/webm;codecs=vp9';
  if (!MediaRecorder.isTypeSupported(mimeType)) mimeType = 'video/webm';

  const mediaRecorder = new MediaRecorder(stream, {
    mimeType: mimeType,
    videoBitsPerSecond: 8000000 // 8 Mbps High Quality
  });

  const chunks = [];
  mediaRecorder.ondataavailable = (e) => {
    if (e.data && e.data.size > 0) chunks.push(e.data);
  };

  mediaRecorder.onstop = () => {
    const blob = new Blob(chunks, { type: mediaRecorder.mimeType || 'video/mp4' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'generated_web_video.mp4';
    a.click();
  };

  mediaRecorder.start();

  const startTime = performance.now();
  
  async function renderStep() {
    const elapsed = performance.now() - startTime;
    
    // Render current DOM frame to Canvas
    const frameCanvas = await html2canvas(targetElement, {
      width: 1080,
      height: 1920,
      scale: 1,
      backgroundColor: null,
      useCORS: true
    });

    ctx.clearRect(0, 0, 1080, 1920);
    ctx.drawImage(frameCanvas, 0, 0, 1080, 1920);

    if (elapsed < durationMs) {
      requestAnimationFrame(renderStep);
    } else {
      mediaRecorder.stop();
    }
  }

  requestAnimationFrame(renderStep);
}
```

---

## 3. High-Performance HTML5 Canvas 60FPS Video Engine Pattern

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

    // Background Gradient
    const bgGrad = ctx.createLinearGradient(0, 0, 1080, 1920);
    bgGrad.addColorStop(0, '#0f172a');
    bgGrad.addColorStop(0.5, '#1e1b4b');
    bgGrad.addColorStop(1, '#31103f');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, 1080, 1920);

    // Glowing Ambient Orbs
    const glowScale = 1.0 + Math.sin(now / 500) * 0.08;
    const orb1 = ctx.createRadialGradient(900, 250, 10, 900, 250, 480 * glowScale);
    orb1.addColorStop(0, 'rgba(236, 72, 153, 0.35)');
    orb1.addColorStop(1, 'rgba(236, 72, 153, 0)');
    ctx.fillStyle = orb1;
    ctx.fillRect(0, 0, 1080, 1920);

    // Main Card Box
    ctx.fillStyle = 'rgba(15, 23, 42, 0.96)';
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.roundRect(90, 220, 900, 1480, 48);
    ctx.fill();
    ctx.stroke();

    ctx.textBaseline = 'top';
    ctx.textAlign = 'left';

    // Yellow Highlighted Title Text Box
    ctx.font = '900 48px Consolas, "Courier New", monospace';
    ctx.fillStyle = '#fde047';
    ctx.fillText(titleText, 160, 465);

    // Pulsing CTA Link Sticker
    const stickerPulse = 1.0 + Math.sin(now / 180) * 0.04;
    const btnY = 1200;

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

## 4. Key HTML/CSS Video Generation Guidelines & Best Practices

1. **Explicit Text Baseline & Alignment**:
   Always set `ctx.textBaseline = 'top'` before calculating layout Y-coordinates to prevent vertical shift bugs on iOS/Android devices.
2. **High Bitrate Configuration**:
   Pass `{ videoBitsPerSecond: 8000000 }` (8 Mbps) to ensure high clarity when users upload generated videos to Instagram Reels or TikTok.
3. **Consolas & Monospace Typography**:
   Use `Consolas, "Courier New", monospace` for developer, tech, and job updates to guarantee consistent character width measurements across browsers.
4. **Bounding Box Math**:
   Calculate dynamic inner container heights (`detY = Math.max(y + 80, 710)`) so long multi-line titles automatically push detail boxes down without overflowing the main outer card.

