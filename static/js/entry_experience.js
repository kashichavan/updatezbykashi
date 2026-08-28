/**
 * KASHII UPDATEZ — High-Illumination 3D Particle Morphing & Radiant Reveal
 * Key Highlights:
 * - High-Density (6,000+ Points) Crisp Particle Swarm
 * - Ultra-Bright, High-Contrast Palette (Rich Deep Onyx + Radiant Electric Royal Blue)
 * - Seamless Transition to Razor-Sharp Luminous Editorial Serif Typography
 * - Floating Radiant Sparkle Motes & Ambient Pulsing Illumination
 * - High-Contrast Illuminated HUD Status Badge
 * - Silky Iris Bloom Wipe into Homepage Feed
 */

(function () {
  const SESSION_KEY = 'kashiiEntryPlayed';
  const urlParams = new URLSearchParams(window.location.search);
  const isIntroPage = window.location.pathname === '/intro/' || window.location.pathname === '/welcome/' || window.location.pathname === '/intro' || window.location.pathname === '/welcome';
  const forceIntro = isIntroPage || urlParams.get('intro') === '1' || urlParams.get('replay') === '1';

  const entryEl = document.getElementById('kashiiEntry');
  const wipeEl = document.getElementById('kashiiWipe');
  const canvas = document.getElementById('entryCanvas');
  const solidText = document.getElementById('entrySolidText');
  const statusEl = document.getElementById('entryStatus');
  const statusText = document.getElementById('entryStatusText');
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
  const easeInOutQuad = (t) => t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;

  let sequenceFinished = false;
  let raf = null;

  // Hard safety timeout
  const safetyTimer = setTimeout(() => {
    if (!sequenceFinished) {
      finishSequence();
    }
  }, 3200);

  // 1. High-Resolution Serif Typography Sampling (Dense 2px Grid)
  async function buildTextPoints() {
    try {
      if (document.fonts && document.fonts.load) {
        await Promise.race([
          Promise.all([
            document.fonts.load("900 120px 'Playfair Display'"),
            document.fonts.load("italic 600 120px 'Playfair Display'")
          ]),
          sleep(250)
        ]);
      }
    } catch (e) {}

    const W = 1000, H = 260;
    const off = document.createElement('canvas');
    off.width = W;
    off.height = H;
    const ctx = off.getContext('2d');
    if (!ctx) return { pts: [], W, H };

    ctx.clearRect(0, 0, W, H);
    ctx.textBaseline = 'alphabetic';

    const fontSerif = "'Playfair Display', Georgia, serif";
    ctx.font = `900 120px ${fontSerif}`;
    const kText = 'Kashii';
    const kWidth = ctx.measureText(kText).width;

    ctx.font = `italic 600 120px ${fontSerif}`;
    const uText = 'Updatez';
    const uWidth = ctx.measureText(uText).width;

    const totalW = kWidth + uWidth + 12;
    const startX = (W - totalW) / 2;
    const baseY = H / 2 + 42;

    // Crisp high-contrast rendering
    ctx.font = `900 120px ${fontSerif}`;
    ctx.fillStyle = '#0f172a'; // Deep Onyx
    ctx.fillText(kText, startX, baseY);

    ctx.font = `italic 600 120px ${fontSerif}`;
    ctx.fillStyle = '#2563eb'; // Vibrant Royal Blue
    ctx.fillText(uText, startX + kWidth + 12, baseY);

    const img = ctx.getImageData(0, 0, W, H).data;
    const gap = 2; // High-Density Grid
    const pts = [];

    for (let y = 0; y < H; y += gap) {
      for (let x = 0; x < W; x += gap) {
        const idx = (y * W + x) * 4;
        if (img[idx + 3] > 110) {
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

  // 2. High-Illumination Particle Engine
  let scene, camera, renderer, points, bgMotes;
  let particleCount = 0;
  let posArr, colorArr, startArr, targetArr, delayArr, endColorArr;
  let animStart = 0;
  let mouseX = 0, mouseY = 0;

  function sizeRenderer() {
    if (!renderer || !canvas || !camera) return;
    const w = canvas.clientWidth || Math.min(window.innerWidth * 0.86, 740);
    const h = canvas.clientHeight || Math.min(window.innerWidth * 0.35, 250);
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }

  function makeCrispSprite() {
    const c = document.createElement('canvas');
    c.width = 64;
    c.height = 64;
    const cx = c.getContext('2d');
    
    // Core solid disc with soft anti-aliased edge and subtle bloom ring
    const g = cx.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, 'rgba(255,255,255,1)');
    g.addColorStop(0.55, 'rgba(255,255,255,0.98)');
    g.addColorStop(0.85, 'rgba(255,255,255,0.45)');
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
      camera.position.z = 6.4;

      renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      sizeRenderer();

      const scale = 7.0 / W;
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
        const tz = (Math.random() - 0.5) * 0.12;

        targetArr[i * 3] = tx;
        targetArr[i * 3 + 1] = ty;
        targetArr[i * 3 + 2] = tz;

        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(Math.random() * 2 - 1);
        const rad = 4.0 + Math.random() * 3.2;

        startArr[i * 3] = rad * Math.sin(phi) * Math.cos(theta);
        startArr[i * 3 + 1] = rad * Math.sin(phi) * Math.sin(theta);
        startArr[i * 3 + 2] = rad * Math.cos(phi) * 0.7;

        posArr[i * 3] = startArr[i * 3];
        posArr[i * 3 + 1] = startArr[i * 3 + 1];
        posArr[i * 3 + 2] = startArr[i * 3 + 2];

        // Radiant electric blue-white initialization
        colorArr[i * 3] = 0.40;
        colorArr[i * 3 + 1] = 0.65;
        colorArr[i * 3 + 2] = 1.00;

        endColorArr[i * 3] = p.r;
        endColorArr[i * 3 + 1] = p.g;
        endColorArr[i * 3 + 2] = p.b;

        delayArr[i] = Math.max(0, Math.min(1, (p.x - minX) / (maxX - minX || 1))) * 600 + Math.random() * 280;
      }

      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(posArr, 3));
      geo.setAttribute('color', new THREE.BufferAttribute(colorArr, 3));

      const mat = new THREE.PointsMaterial({
        size: 0.046, // Solid, High-Contrast Particle Size
        map: makeCrispSprite(),
        vertexColors: true,
        transparent: true,
        depthWrite: false,
        sizeAttenuation: true,
      });

      points = new THREE.Points(geo, mat);
      scene.add(points);

      // Ambient Sparkling Floating Light Motes
      const moteCount = 60;
      const moteGeo = new THREE.BufferGeometry();
      const motePos = new Float32Array(moteCount * 3);
      for (let m = 0; m < moteCount * 3; m += 3) {
        motePos[m] = (Math.random() - 0.5) * 8;
        motePos[m + 1] = (Math.random() - 0.5) * 4;
        motePos[m + 2] = (Math.random() - 0.5) * 3;
      }
      moteGeo.setAttribute('position', new THREE.BufferAttribute(motePos, 3));
      const moteMat = new THREE.PointsMaterial({
        size: 0.040,
        color: 0x38bdf8,
        transparent: true,
        opacity: 0.55,
        map: makeCrispSprite(),
        depthWrite: false,
      });
      bgMotes = new THREE.Points(moteGeo, moteMat);
      scene.add(bgMotes);

      window.addEventListener('resize', sizeRenderer);
      window.addEventListener('mousemove', (e) => {
        mouseX = e.clientX / window.innerWidth - 0.5;
        mouseY = e.clientY / window.innerHeight - 0.5;
      });

      window.addEventListener('touchmove', (e) => {
        if (e.touches && e.touches.length > 0) {
          mouseX = (e.touches[0].clientX / window.innerWidth - 0.5) * 1.4;
          mouseY = (e.touches[0].clientY / window.innerHeight - 0.5) * 1.4;
        }
      }, { passive: true });

      return true;
    } catch (e) {
      return false;
    }
  }

  const FORM_DURATION = 850;
  let formationDone = false;

  function renderLoop() {
    if (sequenceFinished) return;
    raf = requestAnimationFrame(renderLoop);
    const elapsed = performance.now() - animStart;

    if (bgMotes) {
      bgMotes.rotation.y = elapsed * 0.0002;
      bgMotes.rotation.x = elapsed * 0.0001;
    }

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

      colorArr[i * 3] = lerp(0.40, endColorArr[i * 3], eased);
      colorArr[i * 3 + 1] = lerp(0.65, endColorArr[i * 3 + 1], eased);
      colorArr[i * 3 + 2] = lerp(1.00, endColorArr[i * 3 + 2], eased);
    }

    posAttr.array = posArr;
    posAttr.needsUpdate = true;
    colAttr.array = colorArr;
    colAttr.needsUpdate = true;

    camera.position.x = lerp(camera.position.x, mouseX * 0.35, 0.06);
    camera.position.y = lerp(camera.position.y, -mouseY * 0.22, 0.06);
    camera.lookAt(0, 0, 0);

    renderer.render(scene, camera);

    if (allDone && !formationDone) {
      formationDone = true;
      if (solidText) {
        solidText.classList.add('visible', 'shine-sweep');
      }
    }
  }

  // 3. Natural Flow & Radiant Reveal
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

    await sleep(200);
    if (statusEl) {
      statusEl.classList.add('show');
    }
    if (statusText) {
      statusText.textContent = "Assembling today's opportunities...";
    }

    // Wait for assembly
    const startWait = performance.now();
    while (!formationDone && !skipRequested && performance.now() - startWait < 1200) {
      await sleep(30);
    }

    if (!skipRequested) {
      if (statusText) {
        statusText.textContent = "⚡ Verified Stream Ready";
      }
      await sleep(450);
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

    await sleep(600);

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

      await sleep(750);
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

    if (solidText) {
      solidText.classList.remove('visible', 'shine-sweep');
    }

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
    }
    if (statusText) {
      statusText.textContent = "Assembling today's opportunities...";
    }

    await runEntrySequence();
  };

  runEntrySequence();
})();
