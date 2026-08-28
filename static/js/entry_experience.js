/**
 * KASHII UPDATEZ — Luxury 3D Cyber-Constellation Entry Experience
 * Inspired by Awwwards, Vercel & Linear Aesthetics:
 * - High-density 3D particle constellation wordmark (Icy Cyan Pearl + Electric Violet-Blue)
 * - Deep obsidian cyber-nebula with floating ambient stardust
 * - Responsive 3D mouse & touch physics tilt
 * - Ultra-smooth cinematic dissolve transition (Zero double-zooms, Zero screen flash)
 * - Strict 2.4s fail-safe timeout & instant click/escape bypass
 */

(function () {
  const SESSION_KEY = 'kashiiEntryPlayed';
  const urlParams = new URLSearchParams(window.location.search);
  const isIntroPage = window.location.pathname === '/intro/' || window.location.pathname === '/welcome/' || window.location.pathname === '/intro' || window.location.pathname === '/welcome';
  const forceIntro = isIntroPage || urlParams.get('intro') === '1' || urlParams.get('replay') === '1';

  const entryEl = document.getElementById('kashiiEntry');
  const wipeEl = document.getElementById('kashiiWipe');
  const canvas = document.getElementById('entryCanvas');
  const statusEl = document.getElementById('entryStatus');
  const skipBtn = document.getElementById('entrySkipBtn');
  const progressBar = document.getElementById('entryProgressBar');
  const enterBtn = document.getElementById('entryEnterBtn');

  // Bypass admin & owner portals
  const isOwnerOrAdmin = window.location.pathname.startsWith('/owner') || window.location.pathname.startsWith('/admin');
  if (isOwnerOrAdmin) {
    if (entryEl) entryEl.style.display = 'none';
    if (wipeEl) wipeEl.style.display = 'none';
    document.documentElement.classList.add('entry-done');
    return;
  }

  if (!entryEl || !canvas) return;

  // Session guard: if already played and not forced, remove immediately
  if (!forceIntro && sessionStorage.getItem(SESSION_KEY)) {
    entryEl.style.display = 'none';
    if (wipeEl) wipeEl.style.display = 'none';
    document.documentElement.classList.add('entry-done');
    return;
  }

  sessionStorage.setItem(SESSION_KEY, '1');

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const lerp = (a, b, t) => a + (b - a) * t;
  const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);

  let sequenceFinished = false;
  let raf = null;

  // 2.4s Maximum Hard Safety Timeout
  const safetyTimer = setTimeout(() => {
    if (!sequenceFinished) {
      finishSequence();
    }
  }, 2400);

  // 1. High-Density Typography Rasterization
  async function buildTextPoints() {
    try {
      if (document.fonts && document.fonts.load) {
        await Promise.race([
          Promise.all([
            document.fonts.load("900 120px 'Playfair Display'"),
            document.fonts.load("italic 600 120px 'Playfair Display'"),
            document.fonts.load("800 120px 'Plus Jakarta Sans'")
          ]),
          sleep(200)
        ]);
      }
    } catch (e) {}

    const isMobile = window.innerWidth < 640;
    const isTablet = window.innerWidth >= 640 && window.innerWidth < 1024;

    const W = isMobile ? 640 : (isTablet ? 840 : 1000);
    const H = isMobile ? 300 : 220;

    const off = document.createElement('canvas');
    off.width = W;
    off.height = H;
    const ctx = off.getContext('2d');
    if (!ctx) return { pts: [], W, H, isStacked: isMobile };

    ctx.clearRect(0, 0, W, H);
    ctx.textBaseline = 'middle';

    const fontSerif = "'Playfair Display', 'Fraunces', Georgia, serif";
    const fontSize = isMobile ? 84 : (isTablet ? 98 : 114);

    if (isMobile) {
      ctx.font = `900 ${fontSize}px ${fontSerif}`;
      ctx.fillStyle = '#ffffff';
      ctx.textAlign = 'center';
      ctx.fillText('Kashii', W / 2, H / 2 - 46);

      ctx.font = `italic 600 ${fontSize}px ${fontSerif}`;
      ctx.fillStyle = '#38bdf8';
      ctx.textAlign = 'center';
      ctx.fillText('Updatez', W / 2, H / 2 + 48);
    } else {
      ctx.font = `900 ${fontSize}px ${fontSerif}`;
      const kText = 'Kashii';
      const kWidth = ctx.measureText(kText).width;

      ctx.font = `italic 600 ${fontSize}px ${fontSerif}`;
      const uText = 'Updatez';
      const uWidth = ctx.measureText(uText).width;

      const totalW = kWidth + uWidth + 16;
      const startX = (W - totalW) / 2;
      const centerY = H / 2;

      ctx.font = `900 ${fontSize}px ${fontSerif}`;
      ctx.fillStyle = '#ffffff';
      ctx.textAlign = 'left';
      ctx.fillText(kText, startX, centerY);

      ctx.font = `italic 600 ${fontSize}px ${fontSerif}`;
      ctx.fillStyle = '#38bdf8';
      ctx.textAlign = 'left';
      ctx.fillText(uText, startX + kWidth + 16, centerY);
    }

    const img = ctx.getImageData(0, 0, W, H).data;
    const gap = isMobile ? 3 : 2;
    const pts = [];

    for (let y = 0; y < H; y += gap) {
      for (let x = 0; x < W; x += gap) {
        const idx = (y * W + x) * 4;
        const alpha = img[idx + 3];
        if (alpha > 90) {
          const isKashii = isMobile ? (y < H / 2) : (x < W / 2 + 10);
          
          let r = 0.96, g = 0.98, b = 1.0; // Icy White Pearl
          if (!isKashii) {
            // Electric Cyan to Royal Violet Gradient
            const t = (x / W);
            r = lerp(0.22, 0.65, t);
            g = lerp(0.74, 0.38, t);
            b = lerp(0.97, 0.98, t);
          }

          pts.push({ x, y, r, g, b });
        }
      }
    }

    return { pts, W, H, isStacked: isMobile };
  }

  // 2. Three.js 3D Particle Universe
  let scene, camera, renderer, points, bgSparks;
  let particleCount = 0;
  let posArr, colorArr, startArr, targetArr, delayArr, endColorArr;
  let animStart = 0;
  let mouseX = 0, mouseY = 0;
  let targetMouseX = 0, targetMouseY = 0;

  function sizeRenderer() {
    if (!renderer || !canvas || !camera) return;
    const isMobile = window.innerWidth < 640;
    const w = canvas.parentElement ? Math.min(canvas.parentElement.clientWidth, 900) : window.innerWidth * 0.92;
    const h = isMobile ? 260 : 210;

    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }

  function makeGlowSprite() {
    const c = document.createElement('canvas');
    c.width = 64;
    c.height = 64;
    const cx = c.getContext('2d');
    const g = cx.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, 'rgba(255, 255, 255, 1)');
    g.addColorStop(0.3, 'rgba(186, 230, 253, 0.9)');
    g.addColorStop(0.65, 'rgba(56, 189, 248, 0.3)');
    g.addColorStop(1, 'rgba(14, 165, 233, 0)');
    cx.fillStyle = g;
    cx.fillRect(0, 0, 64, 64);
    return new THREE.CanvasTexture(c);
  }

  async function initScene() {
    if (typeof THREE === 'undefined') return false;

    try {
      const { pts, W, H, isStacked } = await buildTextPoints();
      particleCount = pts.length;
      if (particleCount === 0) return false;

      scene = new THREE.Scene();
      camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
      camera.position.z = isStacked ? 6.4 : 5.7;

      renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true, powerPreference: 'high-performance' });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      sizeRenderer();

      const scale = (isStacked ? 5.2 : 6.2) / W;
      posArr = new Float32Array(particleCount * 3);
      colorArr = new Float32Array(particleCount * 3);
      startArr = new Float32Array(particleCount * 3);
      targetArr = new Float32Array(particleCount * 3);
      delayArr = new Float32Array(particleCount);
      endColorArr = new Float32Array(particleCount * 3);

      let minX = Infinity, maxX = -Infinity;
      pts.forEach((p) => {
        if (p.x < minX) minX = p.x;
        if (p.x > maxX) maxX = p.x;
      });

      for (let i = 0; i < particleCount; i++) {
        const p = pts[i];
        const tx = (p.x - W / 2) * scale;
        const ty = -(p.y - H / 2) * scale;
        const tz = (Math.random() - 0.5) * 0.14;

        targetArr[i * 3] = tx;
        targetArr[i * 3 + 1] = ty;
        targetArr[i * 3 + 2] = tz;

        // Spiral cosmic orbit
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(Math.random() * 2 - 1);
        const rad = 3.2 + Math.random() * 2.8;

        startArr[i * 3] = rad * Math.sin(phi) * Math.cos(theta);
        startArr[i * 3 + 1] = rad * Math.sin(phi) * Math.sin(theta);
        startArr[i * 3 + 2] = rad * Math.cos(phi) * 0.6;

        posArr[i * 3] = startArr[i * 3];
        posArr[i * 3 + 1] = startArr[i * 3 + 1];
        posArr[i * 3 + 2] = startArr[i * 3 + 2];

        // Start with deep indigo-blue stardust
        colorArr[i * 3] = 0.25;
        colorArr[i * 3 + 1] = 0.45;
        colorArr[i * 3 + 2] = 0.95;

        endColorArr[i * 3] = p.r;
        endColorArr[i * 3 + 1] = p.g;
        endColorArr[i * 3 + 2] = p.b;

        delayArr[i] = Math.max(0, Math.min(1, (p.x - minX) / (maxX - minX || 1))) * 450 + Math.random() * 200;
      }

      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(posArr, 3));
      geo.setAttribute('color', new THREE.BufferAttribute(colorArr, 3));

      const sprite = makeGlowSprite();
      const isMobile = window.innerWidth < 640;

      const mat = new THREE.PointsMaterial({
        size: isMobile ? 0.040 : 0.032,
        map: sprite,
        vertexColors: true,
        transparent: true,
        opacity: 0.98,
        depthWrite: false,
        sizeAttenuation: true,
        blending: THREE.AdditiveBlending,
      });

      points = new THREE.Points(geo, mat);
      scene.add(points);

      // Ambient Floating Stardust Constellation
      const bgCount = 50;
      const bgGeo = new THREE.BufferGeometry();
      const bgPos = new Float32Array(bgCount * 3);
      for (let b = 0; b < bgCount; b++) {
        bgPos[b * 3] = (Math.random() - 0.5) * 8;
        bgPos[b * 3 + 1] = (Math.random() - 0.5) * 6;
        bgPos[b * 3 + 2] = (Math.random() - 0.5) * 4;
      }
      bgGeo.setAttribute('position', new THREE.BufferAttribute(bgPos, 3));
      const bgMat = new THREE.PointsMaterial({
        size: 0.025,
        color: 0x38bdf8,
        map: sprite,
        transparent: true,
        opacity: 0.5,
        blending: THREE.AdditiveBlending,
      });
      bgSparks = new THREE.Points(bgGeo, bgMat);
      scene.add(bgSparks);

      window.addEventListener('resize', sizeRenderer);
      window.addEventListener('mousemove', (e) => {
        targetMouseX = (e.clientX / window.innerWidth - 0.5) * 1.0;
        targetMouseY = (e.clientY / window.innerHeight - 0.5) * 1.0;
      });

      window.addEventListener('touchmove', (e) => {
        if (e.touches && e.touches.length > 0) {
          targetMouseX = (e.touches[0].clientX / window.innerWidth - 0.5) * 1.4;
          targetMouseY = (e.touches[0].clientY / window.innerHeight - 0.5) * 1.4;
        }
      }, { passive: true });

      return true;
    } catch (e) {
      return false;
    }
  }

  const FORM_DURATION = 650;
  let formationDone = false;

  function renderLoop() {
    if (sequenceFinished) return;
    raf = requestAnimationFrame(renderLoop);
    const elapsed = performance.now() - animStart;

    if (!points || !points.geometry) return;

    const posAttr = points.geometry.attributes.position;
    const colAttr = points.geometry.attributes.color;

    let allDone = true;
    let completedParticles = 0;

    for (let i = 0; i < particleCount; i++) {
      const localT = Math.max(0, Math.min(1, (elapsed - delayArr[i]) / FORM_DURATION));
      if (localT < 1) allDone = false;
      else completedParticles++;

      const eased = easeOutCubic(localT);

      posArr[i * 3] = lerp(startArr[i * 3], targetArr[i * 3], eased);
      posArr[i * 3 + 1] = lerp(startArr[i * 3 + 1], targetArr[i * 3 + 1], eased);
      posArr[i * 3 + 2] = lerp(startArr[i * 3 + 2], targetArr[i * 3 + 2], eased);

      colorArr[i * 3] = lerp(0.25, endColorArr[i * 3], eased);
      colorArr[i * 3 + 1] = lerp(0.45, endColorArr[i * 3 + 1], eased);
      colorArr[i * 3 + 2] = lerp(0.95, endColorArr[i * 3 + 2], eased);
    }

    if (progressBar && !formationDone) {
      const pct = Math.min(100, Math.round((completedParticles / particleCount) * 100));
      progressBar.style.width = `${pct}%`;
    }

    posAttr.array = posArr;
    posAttr.needsUpdate = true;
    colAttr.array = colorArr;
    colAttr.needsUpdate = true;

    if (bgSparks) {
      bgSparks.rotation.y = elapsed * 0.00012;
    }

    // Smooth physics damping
    mouseX = lerp(mouseX, targetMouseX, 0.05);
    mouseY = lerp(mouseY, targetMouseY, 0.05);

    camera.position.x = mouseX * 0.30;
    camera.position.y = -mouseY * 0.20;
    camera.lookAt(0, 0, 0);

    renderer.render(scene, camera);

    if (allDone && !formationDone) {
      formationDone = true;
      if (progressBar) progressBar.style.width = '100%';
    }
  }

  // 3. Orchestration & Dissolve Transition
  let sequenceRunning = false;
  let skipRequested = false;

  async function runEntrySequence() {
    if (sequenceRunning) return;
    sequenceRunning = true;

    const initialized = await initScene();
    if (!initialized) {
      finishSequence();
      return;
    }

    animStart = performance.now();
    renderLoop();

    await sleep(100);
    if (statusEl) {
      statusEl.classList.add('show');
      statusEl.textContent = "✨ Assembling Verified Tech Drives...";
    }

    await sleep(300);
    if (statusEl && !skipRequested) {
      statusEl.textContent = "⚡ Synchronizing 7-Day Opportunities...";
    }

    // Wait max 950ms for particle assembly
    const waitStart = performance.now();
    while (!formationDone && !skipRequested && performance.now() - waitStart < 950) {
      await sleep(25);
    }

    if (!skipRequested) {
      if (statusEl) statusEl.textContent = "🚀 Launching Feed...";
      if (enterBtn) enterBtn.classList.add('show');
      await sleep(350);
    }

    await finishSequence();
  }

  async function finishSequence() {
    if (sequenceFinished) return;
    sequenceFinished = true;
    clearTimeout(safetyTimer);

    // Clean, high-end opacity curtain dissolve (No double-zoom, No jarring flash)
    if (entryEl) {
      entryEl.classList.add('fade-out');
    }

    await sleep(450);

    if (raf) cancelAnimationFrame(raf);

    const redirectTarget = urlParams.get('redirect') || urlParams.get('to');
    if (isIntroPage) {
      window.location.href = redirectTarget || '/';
      return;
    }

    if (redirectTarget && !redirectTarget.startsWith('//') && !redirectTarget.includes('://')) {
      window.location.href = redirectTarget;
      return;
    }

    if (entryEl) {
      entryEl.style.display = 'none';
      document.body.style.overflow = '';
      document.documentElement.classList.add('entry-done');
    }

    if (wipeEl) {
      wipeEl.style.display = 'none';
    }

    // Smoothly start hero headline typewriter on homepage
    if (window.startTypewriter) {
      window.startTypewriter();
    }
  }

  // Dismissal handlers
  if (skipBtn) skipBtn.addEventListener('click', () => { skipRequested = true; finishSequence(); });
  if (enterBtn) enterBtn.addEventListener('click', () => { skipRequested = true; finishSequence(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') finishSequence(); });

  // 4. Global Replay Trigger
  window.replayKashiiEntry = async function () {
    sequenceRunning = false;
    sequenceFinished = false;
    skipRequested = false;
    formationDone = false;

    if (progressBar) progressBar.style.width = '0%';
    if (enterBtn) enterBtn.classList.remove('show');

    if (entryEl) {
      entryEl.style.display = 'flex';
      entryEl.classList.remove('fade-out');
      document.body.style.overflow = 'hidden';
      document.documentElement.classList.remove('entry-done');
    }

    if (statusEl) {
      statusEl.classList.remove('show');
      statusEl.textContent = "✨ Assembling Verified Tech Drives...";
    }

    await runEntrySequence();
  };

  runEntrySequence();
})();
