/**
 * KASHII UPDATEZ — Ultra-Resilient 3D Particle Morphing & Iris Wipe Entry Experience
 * 100% Fail-Safe Architecture:
 * - Guaranteed Maximum 2.2s Hard Timeout (never gets stuck or blocks page load)
 * - 250ms Font Race with instant serif fallback
 * - Instant Skip & Dismiss on Click / Touch / Escape key
 * - Clean Iris circular wipe transition into live website feed
 * - Zero-latency session guard for repeat navigation
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
  const easeInOutQuad = (t) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);

  let sequenceFinished = false;
  let raf = null;

  // Hard safety timeout: under ANY circumstance, dismiss after 2.2 seconds max
  const safetyTimer = setTimeout(() => {
    if (!sequenceFinished) {
      finishSequence();
    }
  }, 2200);

  // 1. Rasterize Wordmark typography into coordinate point cloud
  async function buildTextPoints() {
    // Race font loading with a 250ms strict timeout
    try {
      if (document.fonts && document.fonts.load) {
        await Promise.race([
          Promise.all([
            document.fonts.load("900 120px 'Playfair Display'"),
            document.fonts.load("italic 600 120px 'Playfair Display'"),
            document.fonts.load("800 120px 'Plus Jakarta Sans'")
          ]),
          sleep(250)
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
    const fontSize = isMobile ? 84 : (isTablet ? 98 : 112);

    if (isMobile) {
      ctx.font = `900 ${fontSize}px ${fontSerif}`;
      ctx.fillStyle = '#0f172a';
      ctx.textAlign = 'center';
      ctx.fillText('Kashii', W / 2, H / 2 - 44);

      ctx.font = `italic 600 ${fontSize}px ${fontSerif}`;
      ctx.fillStyle = '#2563eb';
      ctx.textAlign = 'center';
      ctx.fillText('Updatez', W / 2, H / 2 + 48);
    } else {
      ctx.font = `900 ${fontSize}px ${fontSerif}`;
      const kText = 'Kashii';
      const kWidth = ctx.measureText(kText).width;

      ctx.font = `italic 600 ${fontSize}px ${fontSerif}`;
      const uText = 'Updatez';
      const uWidth = ctx.measureText(uText).width;

      const totalW = kWidth + uWidth + 14;
      const startX = (W - totalW) / 2;
      const centerY = H / 2;

      ctx.font = `900 ${fontSize}px ${fontSerif}`;
      ctx.fillStyle = '#0f172a';
      ctx.textAlign = 'left';
      ctx.fillText(kText, startX, centerY);

      ctx.font = `italic 600 ${fontSize}px ${fontSerif}`;
      ctx.fillStyle = '#2563eb';
      ctx.textAlign = 'left';
      ctx.fillText(uText, startX + kWidth + 14, centerY);
    }

    const img = ctx.getImageData(0, 0, W, H).data;
    const gap = isMobile ? 3 : 2;
    const pts = [];

    for (let y = 0; y < H; y += gap) {
      for (let x = 0; x < W; x += gap) {
        const idx = (y * W + x) * 4;
        const alpha = img[idx + 3];
        if (alpha > 100) {
          pts.push({
            x,
            y,
            r: img[idx] / 255,
            g: img[idx + 1] / 255,
            b: img[idx + 2] / 255,
          });
        }
      }
    }

    return { pts, W, H, isStacked: isMobile };
  }

  // 2. Three.js Particle Universe
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

  function makeCircleSprite() {
    const c = document.createElement('canvas');
    c.width = 64;
    c.height = 64;
    const cx = c.getContext('2d');
    const g = cx.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, 'rgba(255,255,255,1)');
    g.addColorStop(0.35, 'rgba(255,255,255,0.9)');
    g.addColorStop(0.7, 'rgba(255,255,255,0.25)');
    g.addColorStop(1, 'rgba(255,255,255,0)');
    cx.fillStyle = g;
    cx.fillRect(0, 0, 64, 64);
    return new THREE.CanvasTexture(c);
  }

  async function initScene() {
    if (typeof THREE === 'undefined') {
      return false;
    }

    try {
      const { pts, W, H, isStacked } = await buildTextPoints();
      particleCount = pts.length;
      if (particleCount === 0) {
        return false;
      }

      scene = new THREE.Scene();
      camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
      camera.position.z = isStacked ? 6.5 : 5.8;

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
        const tz = (Math.random() - 0.5) * 0.16;

        targetArr[i * 3] = tx;
        targetArr[i * 3 + 1] = ty;
        targetArr[i * 3 + 2] = tz;

        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(Math.random() * 2 - 1);
        const rad = 3.2 + Math.random() * 3.0;

        startArr[i * 3] = rad * Math.sin(phi) * Math.cos(theta);
        startArr[i * 3 + 1] = rad * Math.sin(phi) * Math.sin(theta);
        startArr[i * 3 + 2] = rad * Math.cos(phi) * 0.7;

        posArr[i * 3] = startArr[i * 3];
        posArr[i * 3 + 1] = startArr[i * 3 + 1];
        posArr[i * 3 + 2] = startArr[i * 3 + 2];

        colorArr[i * 3] = 0.90;
        colorArr[i * 3 + 1] = 0.94;
        colorArr[i * 3 + 2] = 0.99;

        endColorArr[i * 3] = p.r;
        endColorArr[i * 3 + 1] = p.g;
        endColorArr[i * 3 + 2] = p.b;

        delayArr[i] = Math.max(0, Math.min(1, (p.x - minX) / (maxX - minX || 1))) * 550 + Math.random() * 250;
      }

      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(posArr, 3));
      geo.setAttribute('color', new THREE.BufferAttribute(colorArr, 3));

      const sprite = makeCircleSprite();
      const isMobile = window.innerWidth < 640;

      const mat = new THREE.PointsMaterial({
        size: isMobile ? 0.042 : 0.032,
        map: sprite,
        vertexColors: true,
        transparent: true,
        opacity: 0.98,
        depthWrite: false,
        sizeAttenuation: true,
      });

      points = new THREE.Points(geo, mat);
      scene.add(points);

      // Ambient background sparks
      const bgCount = 35;
      const bgGeo = new THREE.BufferGeometry();
      const bgPos = new Float32Array(bgCount * 3);
      for (let b = 0; b < bgCount; b++) {
        bgPos[b * 3] = (Math.random() - 0.5) * 8;
        bgPos[b * 3 + 1] = (Math.random() - 0.5) * 6;
        bgPos[b * 3 + 2] = (Math.random() - 0.5) * 4;
      }
      bgGeo.setAttribute('position', new THREE.BufferAttribute(bgPos, 3));
      const bgMat = new THREE.PointsMaterial({
        size: 0.024,
        color: 0x93c5fd,
        map: sprite,
        transparent: true,
        opacity: 0.55,
      });
      bgSparks = new THREE.Points(bgGeo, bgMat);
      scene.add(bgSparks);

      window.addEventListener('resize', sizeRenderer);
      window.addEventListener('mousemove', (e) => {
        targetMouseX = (e.clientX / window.innerWidth - 0.5) * 1.2;
        targetMouseY = (e.clientY / window.innerHeight - 0.5) * 1.2;
      });

      window.addEventListener('touchmove', (e) => {
        if (e.touches && e.touches.length > 0) {
          targetMouseX = (e.touches[0].clientX / window.innerWidth - 0.5) * 1.8;
          targetMouseY = (e.touches[0].clientY / window.innerHeight - 0.5) * 1.8;
        }
      }, { passive: true });

      return true;
    } catch (e) {
      return false;
    }
  }

  const FORM_DURATION = 800;
  let formationDone = false;
  let isZoomingIn = false;
  let zoomStartTime = 0;

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

      colorArr[i * 3] = lerp(0.90, endColorArr[i * 3], eased);
      colorArr[i * 3 + 1] = lerp(0.94, endColorArr[i * 3 + 1], eased);
      colorArr[i * 3 + 2] = lerp(0.99, endColorArr[i * 3 + 2], eased);
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
      bgSparks.rotation.y = elapsed * 0.00015;
    }

    mouseX = lerp(mouseX, targetMouseX, 0.06);
    mouseY = lerp(mouseY, targetMouseY, 0.06);

    camera.position.x = mouseX * 0.40;
    camera.position.y = -mouseY * 0.28;

    if (isZoomingIn) {
      const zProgress = Math.min(1, (performance.now() - zoomStartTime) / 500);
      const zEase = easeInOutQuad(zProgress);
      camera.position.z = lerp(5.8, 1.8, zEase);
    }

    camera.lookAt(0, 0, 0);
    renderer.render(scene, camera);

    if (allDone && !formationDone) {
      formationDone = true;
      if (progressBar) progressBar.style.width = '100%';
    }
  }

  // 3. Orchestration & Status Steps
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

    await sleep(150);
    if (statusEl) {
      statusEl.classList.add('show');
      statusEl.textContent = "✨ Assembling Verified Tech Drives...";
    }

    await sleep(350);
    if (statusEl && !skipRequested) {
      statusEl.textContent = "⚡ Synchronizing 7-Day Active Opportunities...";
    }

    // Wait max 1.2s for formation
    const waitStart = performance.now();
    while (!formationDone && !skipRequested && performance.now() - waitStart < 1200) {
      await sleep(30);
    }

    if (!skipRequested) {
      if (statusEl) statusEl.textContent = "🚀 Welcome to Kashii Updatez";
      if (enterBtn) enterBtn.classList.add('show');
      await sleep(450);
    }

    await finishSequence();
  }

  async function finishSequence() {
    if (sequenceFinished) return;
    sequenceFinished = true;
    clearTimeout(safetyTimer);

    isZoomingIn = true;
    zoomStartTime = performance.now();

    if (entryEl) {
      entryEl.classList.add('fade-out');
    }

    if (wipeEl) {
      wipeEl.classList.add('expand');
    }

    await sleep(550);

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
      await sleep(80);
      wipeEl.classList.remove('expand');
      wipeEl.classList.add('contract');

      if (window.startTypewriter) {
        window.startTypewriter();
      }

      await sleep(750);
      wipeEl.classList.remove('contract');
      wipeEl.style.display = 'none';
    }
  }

  // User click/key bypass handlers
  if (skipBtn) skipBtn.addEventListener('click', () => { skipRequested = true; finishSequence(); });
  if (enterBtn) enterBtn.addEventListener('click', () => { skipRequested = true; finishSequence(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') finishSequence(); });

  // 4. Global Replay Trigger
  window.replayKashiiEntry = async function () {
    sequenceRunning = false;
    sequenceFinished = false;
    skipRequested = false;
    formationDone = false;
    isZoomingIn = false;

    if (progressBar) progressBar.style.width = '0%';
    if (enterBtn) enterBtn.classList.remove('show');

    if (entryEl) {
      entryEl.style.display = 'flex';
      entryEl.classList.remove('fade-out');
      document.body.style.overflow = 'hidden';
      document.documentElement.classList.remove('entry-done');
    }

    if (wipeEl) {
      wipeEl.style.display = 'block';
      wipeEl.classList.remove('expand', 'contract');
    }

    if (statusEl) {
      statusEl.classList.remove('show');
      statusEl.textContent = "✨ Assembling Verified Tech Drives...";
    }

    await runEntrySequence();
  };

  // Launch sequence safely
  runEntrySequence();
})();
