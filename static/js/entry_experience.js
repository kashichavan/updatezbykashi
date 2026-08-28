/**
 * KASHII UPDATEZ — Ultra-Polished 3D Particle Morphing & Iris Wipe Entry Experience
 * Designed with modern glassmorphism, responsive particle viewport fitting,
 * ambient aura atmosphere, interactive 3D physics parallax, and cinematic iris transition.
 */

(function () {
  const SESSION_KEY = 'kashiiEntryPlayed';
  const urlParams = new URLSearchParams(window.location.search);
  const forceIntro = urlParams.get('intro') === '1' || urlParams.get('replay') === '1';

  const entryEl = document.getElementById('kashiiEntry');
  const wipeEl = document.getElementById('kashiiWipe');
  const canvas = document.getElementById('entryCanvas');
  const statusEl = document.getElementById('entryStatus');
  const skipBtn = document.getElementById('entrySkipBtn');
  const progressBar = document.getElementById('entryProgressBar');
  const enterBtn = document.getElementById('entryEnterBtn');

  if (!entryEl || !canvas) return;

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const lerp = (a, b, t) => a + (b - a) * t;
  const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);
  const easeInOutQuad = (t) => t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;

  // 1. Precise Rasterization of Typography into 3D Coordinate Point Cloud
  async function buildTextPoints() {
    try {
      if (document.fonts && document.fonts.load) {
        await Promise.all([
          document.fonts.load("900 120px 'Playfair Display'"),
          document.fonts.load("italic 600 120px 'Playfair Display'"),
          document.fonts.load("800 120px 'Plus Jakarta Sans'")
        ]);
      }
    } catch (e) {}

    const isMobile = window.innerWidth < 640;
    const isTablet = window.innerWidth >= 640 && window.innerWidth < 1024;

    const W = isMobile ? 640 : (isTablet ? 840 : 1000);
    const H = isMobile ? 320 : 220;

    const off = document.createElement('canvas');
    off.width = W;
    off.height = H;
    const ctx = off.getContext('2d');
    if (!ctx) return { pts: [], W, H, isStacked: isMobile };

    ctx.clearRect(0, 0, W, H);
    ctx.textBaseline = 'middle';

    const fontSerif = "'Playfair Display', 'Fraunces', Georgia, serif";
    const fontSize = isMobile ? 86 : (isTablet ? 100 : 115);

    if (isMobile) {
      // Stacked layout on small mobile screens for maximum readability
      ctx.font = `900 ${fontSize}px ${fontSerif}`;
      ctx.fillStyle = '#0f172a'; // Deep Obsidian Ink
      ctx.textAlign = 'center';
      ctx.fillText('Kashii', W / 2, H / 2 - 45);

      ctx.font = `italic 600 ${fontSize}px ${fontSerif}`;
      ctx.fillStyle = '#2563eb'; // Electric Royal Blue
      ctx.textAlign = 'center';
      ctx.fillText('Updatez', W / 2, H / 2 + 50);
    } else {
      // Single inline row layout on desktop & tablet
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
    const gap = isMobile ? 3 : 2; // Ultra high density
    const pts = [];

    for (let y = 0; y < H; y += gap) {
      for (let x = 0; x < W; x += gap) {
        const idx = (y * W + x) * 4;
        const alpha = img[idx + 3];
        if (alpha > 110) {
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
  let scene, camera, renderer, points, bgSparks, raf;
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
      finishSequence();
      return;
    }

    const { pts, W, H, isStacked } = await buildTextPoints();
    particleCount = pts.length;
    if (particleCount === 0) {
      finishSequence();
      return;
    }

    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
    camera.position.z = isStacked ? 6.5 : 5.8;

    renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
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

      // 3D Orbital Spiral Spawn Distribution
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(Math.random() * 2 - 1);
      const rad = 3.5 + Math.random() * 3.2;

      startArr[i * 3] = rad * Math.sin(phi) * Math.cos(theta);
      startArr[i * 3 + 1] = rad * Math.sin(phi) * Math.sin(theta);
      startArr[i * 3 + 2] = rad * Math.cos(phi) * 0.7;

      posArr[i * 3] = startArr[i * 3];
      posArr[i * 3 + 1] = startArr[i * 3 + 1];
      posArr[i * 3 + 2] = startArr[i * 3 + 2];

      // Subtle glowing blue-white beginning color
      colorArr[i * 3] = 0.90;
      colorArr[i * 3 + 1] = 0.94;
      colorArr[i * 3 + 2] = 0.99;

      endColorArr[i * 3] = p.r;
      endColorArr[i * 3 + 1] = p.g;
      endColorArr[i * 3 + 2] = p.b;

      // Smooth cascading wave delay from left to right
      delayArr[i] = Math.max(0, Math.min(1, (p.x - minX) / (maxX - minX || 1))) * 650 + Math.random() * 300;
    }

    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(posArr, 3));
    geo.setAttribute('color', new THREE.BufferAttribute(colorArr, 3));

    const sprite = makeCircleSprite();
    const isMobile = window.innerWidth < 640;

    const mat = new THREE.PointsMaterial({
      size: isMobile ? 0.040 : 0.032,
      map: sprite,
      vertexColors: true,
      transparent: true,
      opacity: 0.98,
      depthWrite: false,
      sizeAttenuation: true,
    });

    points = new THREE.Points(geo, mat);
    scene.add(points);

    // Add ambient background floating stardust particles
    const bgCount = 45;
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
      opacity: 0.6,
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
  }

  const FORM_DURATION = 900;
  let formationDone = false;
  let isZoomingIn = false;
  let zoomStartTime = 0;

  function renderLoop() {
    raf = requestAnimationFrame(renderLoop);
    const elapsed = performance.now() - animStart;

    if (!points) return;

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

    // Update progress bar
    if (progressBar && !formationDone) {
      const pct = Math.min(100, Math.round((completedParticles / particleCount) * 100));
      progressBar.style.width = `${pct}%`;
    }

    posAttr.array = posArr;
    posAttr.needsUpdate = true;
    colAttr.array = colorArr;
    colAttr.needsUpdate = true;

    // Ambient floating stardust oscillation
    if (bgSparks) {
      bgSparks.rotation.y = elapsed * 0.00015;
      bgSparks.rotation.x = Math.sin(elapsed * 0.0002) * 0.05;
    }

    // Interactive mouse damping
    mouseX = lerp(mouseX, targetMouseX, 0.06);
    mouseY = lerp(mouseY, targetMouseY, 0.06);

    camera.position.x = mouseX * 0.40;
    camera.position.y = -mouseY * 0.28;

    // Cinematic zoom in on transition
    if (isZoomingIn) {
      const zProgress = Math.min(1, (performance.now() - zoomStartTime) / 600);
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

    await initScene();
    animStart = performance.now();
    renderLoop();

    await sleep(200);
    if (statusEl) {
      statusEl.classList.add('show');
      statusEl.textContent = "✨ Assembling Verified Tech Drives...";
    }

    // Progress updates during formation
    await sleep(400);
    if (statusEl && !skipRequested) {
      statusEl.textContent = "⚡ Synchronizing 7-Day Active Opportunities...";
    }

    // Wait for full particle convergence
    while (!formationDone && !skipRequested) {
      await sleep(35);
    }

    if (!skipRequested) {
      if (statusEl) statusEl.textContent = "🚀 Welcome to Kashii Updatez";
      if (enterBtn) {
        enterBtn.classList.add('show');
      }
      await sleep(650);
    }

    await finishSequence();
  }

  async function finishSequence() {
    isZoomingIn = true;
    zoomStartTime = performance.now();

    if (entryEl) {
      entryEl.classList.add('fade-out');
    }

    if (wipeEl) {
      wipeEl.classList.add('expand');
    }

    await sleep(650);

    if (raf) cancelAnimationFrame(raf);

    const redirectTarget = urlParams.get('redirect') || urlParams.get('to');
    if (redirectTarget && !redirectTarget.startsWith('//') && !redirectTarget.includes('://')) {
      // Automatic redirection to destination page
      window.location.href = redirectTarget;
      return;
    }

    if (entryEl) {
      entryEl.style.display = 'none';
      document.body.style.overflow = '';
    }

    if (wipeEl) {
      await sleep(100);
      wipeEl.classList.remove('expand');
      wipeEl.classList.add('contract');

      // Trigger typewriter effect on homepage hero
      if (window.startTypewriter) {
        window.startTypewriter();
      }

      await sleep(850);
      wipeEl.classList.remove('contract');
      wipeEl.style.display = 'none';
    }
  }

  if (skipBtn) {
    skipBtn.addEventListener('click', () => {
      skipRequested = true;
    });
  }

  if (enterBtn) {
    enterBtn.addEventListener('click', () => {
      skipRequested = true;
    });
  }

  // 4. Global Replay Trigger
  window.replayKashiiEntry = async function () {
    sequenceRunning = false;
    skipRequested = false;
    formationDone = false;
    isZoomingIn = false;

    if (progressBar) progressBar.style.width = '0%';
    if (enterBtn) enterBtn.classList.remove('show');

    if (entryEl) {
      entryEl.style.display = 'flex';
      entryEl.classList.remove('fade-out');
      document.body.style.overflow = 'hidden';
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

  // 5. Entry Initialization Guard (Once per browser session)
  if (!sessionStorage.getItem(SESSION_KEY) || forceIntro) {
    sessionStorage.setItem(SESSION_KEY, '1');
    document.body.style.overflow = 'hidden';
    runEntrySequence();
  } else {
    if (entryEl) entryEl.style.display = 'none';
    if (wipeEl) wipeEl.style.display = 'none';
    document.body.style.overflow = '';
  }
})();
