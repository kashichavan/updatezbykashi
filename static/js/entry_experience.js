/**
 * KASHII UPDATEZ — Exact Clean Prototype Entry Experience
 * - Pure white background with soft blue auroras
 * - 3D Three.js particle wave assembling "Kashii" (#111111) & "Updatez" (#3457e6)
 * - Subtle status indicator: "Assembling today's opportunities" -> "Taking you home"
 * - Clean Iris Wipe transition revealing the homepage
 */

(function () {
  const SESSION_KEY = 'kashiiEntryPlayed';
  const urlParams = new URLSearchParams(window.location.search);
  const isIntroPage = window.location.pathname === '/intro/' || window.location.pathname === '/welcome/' || window.location.pathname === '/intro' || window.location.pathname === '/welcome';
  const forceIntro = isIntroPage || urlParams.get('intro') === '1' || urlParams.get('replay') === '1';

  const entry = document.getElementById('entry') || document.getElementById('kashiiEntry');
  const wipe = document.getElementById('wipe') || document.getElementById('kashiiWipe');
  const canvas = document.getElementById('entry-canvas') || document.getElementById('entryCanvas');
  const status = document.getElementById('entry-status') || document.getElementById('entryStatus');
  const skip = document.getElementById('skip-btn') || document.getElementById('entrySkipBtn');

  // Bypass admin and owner portals
  const isOwnerOrAdmin = window.location.pathname.startsWith('/owner') || window.location.pathname.startsWith('/admin');
  if (isOwnerOrAdmin) {
    if (entry) entry.style.display = 'none';
    if (wipe) wipe.style.display = 'none';
    document.documentElement.classList.add('entry-done');
    return;
  }

  if (!entry || !canvas) return;

  // Session guard: if already played in this session and not forced
  if (!forceIntro && sessionStorage.getItem(SESSION_KEY)) {
    entry.style.display = 'none';
    if (wipe) wipe.style.display = 'none';
    document.documentElement.classList.add('entry-done');
    return;
  }

  sessionStorage.setItem(SESSION_KEY, '1');

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const lerp = (a, b, t) => a + (b - a) * t;
  const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);

  let sequenceFinished = false;

  // Safety timer to prevent any freeze
  const safetyTimer = setTimeout(() => {
    if (!sequenceFinished) {
      finish();
    }
  }, 4000);

  async function buildTextPoints() {
    try {
      if (document.fonts && document.fonts.ready) {
        await document.fonts.ready;
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

  let scene, camera, renderer, points;
  let particleCount = 0;
  let posArr, colorArr, startArr, targetArr, delayArr, endColorArr;
  let animStart = 0;
  let mouseX = 0, mouseY = 0;

  function sizeRenderer() {
    if (!renderer || !canvas || !camera) return;
    const w = canvas.clientWidth || Math.min(window.innerWidth * 0.80, 680);
    const h = canvas.clientHeight || Math.min(window.innerWidth * 0.32, 220);
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }

  function makeSprite() {
    const c = document.createElement('canvas');
    c.width = 32;
    c.height = 32;
    const cx = c.getContext('2d');
    const g = cx.createRadialGradient(16, 16, 0, 16, 16, 16);
    g.addColorStop(0, 'rgba(255,255,255,1)');
    g.addColorStop(0.4, 'rgba(255,255,255,0.8)');
    g.addColorStop(1, 'rgba(255,255,255,0)');
    cx.fillStyle = g;
    cx.fillRect(0, 0, 32, 32);
    return new THREE.CanvasTexture(c);
  }

  async function initScene() {
    if (typeof THREE === 'undefined') return false;

    try {
      const { pts, W, H } = await buildTextPoints();
      particleCount = pts.length;
      if (!particleCount) return false;

      scene = new THREE.Scene();
      camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
      camera.position.z = 5.6;

      renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      sizeRenderer();

      const scale = 6.2 / W;
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
        const tz = (Math.random() - 0.5) * 0.1;

        targetArr[i * 3] = tx;
        targetArr[i * 3 + 1] = ty;
        targetArr[i * 3 + 2] = tz;

        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(Math.random() * 2 - 1);
        const rad = 3.2 + Math.random() * 2.4;

        startArr[i * 3] = rad * Math.sin(phi) * Math.cos(theta);
        startArr[i * 3 + 1] = rad * Math.sin(phi) * Math.sin(theta);
        startArr[i * 3 + 2] = rad * Math.cos(phi) * 0.6;

        posArr[i * 3] = startArr[i * 3];
        posArr[i * 3 + 1] = startArr[i * 3 + 1];
        posArr[i * 3 + 2] = startArr[i * 3 + 2];

        colorArr[i * 3] = 0.95;
        colorArr[i * 3 + 1] = 0.96;
        colorArr[i * 3 + 2] = 0.98;

        endColorArr[i * 3] = p.r;
        endColorArr[i * 3 + 1] = p.g;
        endColorArr[i * 3 + 2] = p.b;

        delayArr[i] = ((p.x - minX) / (maxX - minX || 1)) * 500 + Math.random() * 250;
      }

      const geo = new THREE.BufferGeometry();
      geo.setAttribute('position', new THREE.BufferAttribute(posArr, 3));
      geo.setAttribute('color', new THREE.BufferAttribute(colorArr, 3));

      const mat = new THREE.PointsMaterial({
        size: 0.024,
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
        mouseX = (e.clientX / window.innerWidth - 0.5) * 0.4;
        mouseY = (e.clientY / window.innerHeight - 0.5) * 0.4;
      });

      return true;
    } catch (e) {
      return false;
    }
  }

  const FORM_DURATION = 800;
  let formationDone = false;

  function renderLoop() {
    if (sequenceFinished) return;
    requestAnimationFrame(renderLoop);
    const elapsed = performance.now() - animStart;

    if (!points) return;
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

      colorArr[i * 3] = lerp(0.95, endColorArr[i * 3], eased);
      colorArr[i * 3 + 1] = lerp(0.96, endColorArr[i * 3 + 1], eased);
      colorArr[i * 3 + 2] = lerp(0.98, endColorArr[i * 3 + 2], eased);
    }

    posAttr.array = posArr;
    posAttr.needsUpdate = true;
    colAttr.array = colorArr;
    colAttr.needsUpdate = true;

    camera.position.x = lerp(camera.position.x, mouseX, 0.05);
    camera.position.y = lerp(camera.position.y, -mouseY, 0.05);
    camera.lookAt(0, 0, 0);

    renderer.render(scene, camera);

    if (allDone && !formationDone) {
      formationDone = true;
    }
  }

  let skipped = false;

  async function finish() {
    if (sequenceFinished) return;
    sequenceFinished = true;
    clearTimeout(safetyTimer);

    if (entry) entry.classList.add('fade-out');
    if (wipe) wipe.classList.add('expand');

    await sleep(700);

    const redirectTarget = urlParams.get('redirect') || urlParams.get('to');
    if (isIntroPage) {
      window.location.href = redirectTarget || '/';
      return;
    }

    if (redirectTarget && !redirectTarget.startsWith('//') && !redirectTarget.includes('://')) {
      window.location.href = redirectTarget;
      return;
    }

    if (entry) {
      entry.style.display = 'none';
      document.body.style.overflow = '';
      document.documentElement.classList.add('entry-done');
    }

    if (wipe) {
      await sleep(100);
      wipe.classList.remove('expand');
      wipe.classList.add('contract');

      if (window.startTypewriter) {
        window.startTypewriter();
      }

      await sleep(800);
      wipe.style.display = 'none';
    }
  }

  async function runSequence() {
    if (skip) {
      skip.addEventListener('click', () => {
        skipped = true;
        finish();
      });
    }

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') finish();
    });

    const ready = await initScene();
    if (!ready) {
      finish();
      return;
    }

    animStart = performance.now();
    renderLoop();

    await sleep(200);
    if (status) status.classList.add('show');

    while (!formationDone && !skipped) {
      await sleep(30);
    }

    if (!skipped) {
      await sleep(300);
      if (status) status.textContent = "Taking you home";
      await sleep(200);
    }

    await finish();
  }

  // Global Replay
  window.replayKashiiEntry = async function () {
    sequenceFinished = false;
    skipped = false;
    formationDone = false;

    if (entry) {
      entry.style.display = 'flex';
      entry.classList.remove('fade-out');
      document.body.style.overflow = 'hidden';
      document.documentElement.classList.remove('entry-done');
    }

    if (wipe) {
      wipe.style.display = 'block';
      wipe.classList.remove('expand', 'contract');
    }

    if (status) {
      status.classList.remove('show');
      status.textContent = "Assembling today's opportunities";
    }

    await runSequence();
  };

  runSequence();
})();
