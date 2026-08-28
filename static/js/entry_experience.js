/**
 * KASHII UPDATEZ — Natural 3D Particle Morphing Entry Experience
 * Authentic Organic Implementation:
 * - Editorial Serif typography: "Kashii" (#111111) + "Updatez" (#3457e6)
 * - Soft organic ambient auroras
 * - 3D particle left-to-right staggered wave assembly with cubic easing
 * - Interactive mouse/touch parallax tilt
 * - Iris wipe transition revealing the clean student portal
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

  // Bypass admin & owner portals
  const isOwnerOrAdmin = window.location.pathname.startsWith('/owner') || window.location.pathname.startsWith('/admin');
  if (isOwnerOrAdmin) {
    if (entryEl) entryEl.style.display = 'none';
    if (wipeEl) wipeEl.style.display = 'none';
    document.documentElement.classList.add('entry-done');
    return;
  }

  if (!entryEl || !canvas) return;

  // Session guard: if already played in this session and not forced
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

  // Safety timer
  const safetyTimer = setTimeout(() => {
    if (!sequenceFinished) {
      finishSequence();
    }
  }, 2800);

  // 1. Natural Serif Typography Rasterization
  async function buildTextPoints() {
    try {
      if (document.fonts && document.fonts.load) {
        await Promise.race([
          Promise.all([
            document.fonts.load("900 110px 'Playfair Display'"),
            document.fonts.load("italic 600 110px 'Playfair Display'")
          ]),
          sleep(200)
        ]);
      }
    } catch (e) {}

    const W = 900, H = 220;
    const off = document.createElement('canvas');
    off.width = W;
    off.height = H;
    const ctx = off.getContext('2d');
    if (!ctx) return { pts: [], W, H };

    ctx.clearRect(0, 0, W, H);
    ctx.textBaseline = 'alphabetic';

    const fontSerif = "'Playfair Display', Georgia, serif";
    ctx.font = `900 110px ${fontSerif}`;
    const kText = 'Kashii';
    const kWidth = ctx.measureText(kText).width;

    ctx.font = `italic 600 110px ${fontSerif}`;
    const uText = 'Updatez';
    const uWidth = ctx.measureText(uText).width;

    const totalW = kWidth + uWidth + 8;
    const startX = (W - totalW) / 2;
    const baseY = H / 2 + 38;

    ctx.font = `900 110px ${fontSerif}`;
    ctx.fillStyle = '#111111';
    ctx.fillText(kText, startX, baseY);

    ctx.font = `italic 600 110px ${fontSerif}`;
    ctx.fillStyle = '#3457e6';
    ctx.fillText(uText, startX + kWidth + 8, baseY);

    const img = ctx.getImageData(0, 0, W, H).data;
    const gap = 3;
    const pts = [];

    for (let y = 0; y < H; y += gap) {
      for (let x = 0; x < W; x += gap) {
        const idx = (y * W + x) * 4;
        if (img[idx + 3] > 128) {
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

    return { pts, W, H };
  }

  // 2. Three.js Organic Particle Universe
  let scene, camera, renderer, points;
  let particleCount = 0;
  let posArr, colorArr, startArr, targetArr, delayArr, endColorArr;
  let animStart = 0;
  let mouseX = 0, mouseY = 0;

  function sizeRenderer() {
    if (!renderer || !canvas || !camera) return;
    const w = canvas.clientWidth || Math.min(window.innerWidth * 0.82, 680);
    const h = canvas.clientHeight || Math.min(window.innerWidth * 0.32, 220);
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }

  function makeSprite() {
    const c = document.createElement('canvas');
    c.width = 64;
    c.height = 64;
    const cx = c.getContext('2d');
    const g = cx.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, 'rgba(255,255,255,1)');
    g.addColorStop(0.3, 'rgba(255,255,255,0.85)');
    g.addColorStop(1, 'rgba(255,255,255,0)');
    cx.fillStyle = g;
    cx.fillRect(0, 0, 64, 64);
    return new THREE.CanvasTexture(c);
  }

  async function initScene() {
    if (typeof THREE === 'undefined') return false;

    try {
      const { pts, W, H } = await buildTextPoints();
      particleCount = pts.length;
      if (particleCount === 0) return false;

      scene = new THREE.Scene();
      camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
      camera.position.z = 6.2;

      renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      sizeRenderer();

      const scale = 6.6 / W;
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
        const tz = (Math.random() - 0.5) * 0.15;

        targetArr[i * 3] = tx;
        targetArr[i * 3 + 1] = ty;
        targetArr[i * 3 + 2] = tz;

        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(Math.random() * 2 - 1);
        const rad = 3.6 + Math.random() * 2.8;

        startArr[i * 3] = rad * Math.sin(phi) * Math.cos(theta);
        startArr[i * 3 + 1] = rad * Math.sin(phi) * Math.sin(theta);
        startArr[i * 3 + 2] = rad * Math.cos(phi) * 0.65;

        posArr[i * 3] = startArr[i * 3];
        posArr[i * 3 + 1] = startArr[i * 3 + 1];
        posArr[i * 3 + 2] = startArr[i * 3 + 2];

        // Soft starting blue-white tint
        colorArr[i * 3] = 0.92;
        colorArr[i * 3 + 1] = 0.95;
        colorArr[i * 3 + 2] = 0.99;

        endColorArr[i * 3] = p.r;
        endColorArr[i * 3 + 1] = p.g;
        endColorArr[i * 3 + 2] = p.b;

        delayArr[i] = Math.max(0, Math.min(1, (p.x - minX) / (maxX - minX || 1))) * 650 + Math.random() * 320;
      }

      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(posArr, 3));
      geo.setAttribute('color', new THREE.BufferAttribute(colorArr, 3));

      const mat = new THREE.PointsMaterial({
        size: 0.030,
        map: makeSprite(),
        vertexColors: true,
        transparent: true,
        depthWrite: false,
        sizeAttenuation: true,
      });

      points = new THREE.Points(geo, mat);
      scene.add(points);

      window.addEventListener('resize', sizeRenderer);
      window.addEventListener('mousemove', (e) => {
        mouseX = e.clientX / window.innerWidth - 0.5;
        mouseY = e.clientY / window.innerHeight - 0.5;
      });

      window.addEventListener('touchmove', (e) => {
        if (e.touches && e.touches.length > 0) {
          mouseX = (e.touches[0].clientX / window.innerWidth - 0.5) * 1.5;
          mouseY = (e.touches[0].clientY / window.innerHeight - 0.5) * 1.5;
        }
      }, { passive: true });

      return true;
    } catch (e) {
      return false;
    }
  }

  const FORM_DURATION = 920;
  let formationDone = false;

  function renderLoop() {
    if (sequenceFinished) return;
    raf = requestAnimationFrame(renderLoop);
    const elapsed = performance.now() - animStart;

    if (!points || !points.geometry) return;

    const posAttr = points.geometry.attributes.position;
    const colAttr = points.geometry.attributes.color;

    let allDone = true;
    for (let i = 0; i < particleCount; i++) {
      const localT = Math.max(0, Math.min(1, (elapsed - delayArr[i]) / FORM_DURATION));
      if (localT < 1) allDone = false;

      const eased = easeOutCubic(localT);

      posArr[i * 3] = lerp(startArr[i * 3], targetArr[i * 3], eased);
      posArr[i * 3 + 1] = lerp(startArr[i * 3 + 1], targetArr[i * 3 + 1], eased);
      posArr[i * 3 + 2] = lerp(startArr[i * 3 + 2], targetArr[i * 3 + 2], eased);

      colorArr[i * 3] = lerp(0.92, endColorArr[i * 3], eased);
      colorArr[i * 3 + 1] = lerp(0.95, endColorArr[i * 3 + 1], eased);
      colorArr[i * 3 + 2] = lerp(0.99, endColorArr[i * 3 + 2], eased);
    }

    posAttr.array = posArr;
    posAttr.needsUpdate = true;
    colAttr.array = colorArr;
    colAttr.needsUpdate = true;

    camera.position.x = lerp(camera.position.x, mouseX * 0.35, 0.05);
    camera.position.y = lerp(camera.position.y, -mouseY * 0.22, 0.05);
    camera.lookAt(0, 0, 0);

    renderer.render(scene, camera);

    if (allDone && !formationDone) {
      formationDone = true;
    }
  }

  // 3. Natural Lifecycle & Iris Transition
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

    await sleep(250);
    if (statusEl) {
      statusEl.classList.add('show');
      statusEl.textContent = "Assembling today's opportunities";
    }

    // Wait for organic particle assembly
    const startWait = performance.now();
    while (!formationDone && !skipRequested && performance.now() - startWait < 1400) {
      await sleep(30);
    }

    if (!skipRequested) {
      await sleep(400);
      if (statusEl) statusEl.textContent = "Taking you home";
      await sleep(350);
    }

    await finishSequence();
  }

  async function finishSequence() {
    if (sequenceFinished) return;
    sequenceFinished = true;
    clearTimeout(safetyTimer);

    if (entryEl) {
      entryEl.classList.add('fade-out');
    }

    if (wipeEl) {
      wipeEl.classList.add('expand');
    }

    await sleep(650);

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
      await sleep(100);
      wipeEl.classList.remove('expand');
      wipeEl.classList.add('contract');

      if (window.startTypewriter) {
        window.startTypewriter();
      }

      await sleep(800);
      wipeEl.classList.remove('contract');
      wipeEl.style.display = 'none';
    }
  }

  if (skipBtn) skipBtn.addEventListener('click', () => { skipRequested = true; finishSequence(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') finishSequence(); });

  // Global Replay
  window.replayKashiiEntry = async function () {
    sequenceRunning = false;
    sequenceFinished = false;
    skipRequested = false;
    formationDone = false;

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
      statusEl.textContent = "Assembling today's opportunities";
    }

    await runEntrySequence();
  };

  runEntrySequence();
})();
