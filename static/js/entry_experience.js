/**
 * KASHII UPDATEZ — Apple / Linear Style Kinetic Glowing Vector & Iridescent Beam Entry
 * Features:
 * - 100% Razor-Sharp Vector Typography with 3D Spring-Physics Letter Split
 * - Rotating Iridescent Conic-Gradient Neon Beam Gem
 * - High-Velocity Specular Laser Light Sweep
 * - Live HUD Telemetry Counter (0% -> 100% Active Verification)
 * - Silky Smooth Curtain Slide-Up Transition (Zero Double-Zoom, Zero Canvas Grain)
 * - Strict 2.0s Safety Timeout & Instant Click/Escape Bypass
 */

(function () {
  const SESSION_KEY = 'kashiiEntryPlayed';
  const urlParams = new URLSearchParams(window.location.search);
  const isIntroPage = window.location.pathname === '/intro/' || window.location.pathname === '/welcome/' || window.location.pathname === '/intro' || window.location.pathname === '/welcome';
  const forceIntro = isIntroPage || urlParams.get('intro') === '1' || urlParams.get('replay') === '1';

  const entryEl = document.getElementById('kashiiEntry');
  const skipBtn = document.getElementById('entrySkipBtn');
  const counterEl = document.getElementById('entryMetricCount');
  const statusEl = document.getElementById('entryStatusText');
  const progressFill = document.getElementById('entryProgressFill');
  const brandWordmark = document.getElementById('entryWordmark');

  // Bypass admin and owner portals
  const isOwnerOrAdmin = window.location.pathname.startsWith('/owner') || window.location.pathname.startsWith('/admin');
  if (isOwnerOrAdmin) {
    if (entryEl) entryEl.style.display = 'none';
    document.documentElement.classList.add('entry-done');
    return;
  }

  if (!entryEl) return;

  // Session guard: if already played in this session and not forced
  if (!forceIntro && sessionStorage.getItem(SESSION_KEY)) {
    entryEl.style.display = 'none';
    document.documentElement.classList.add('entry-done');
    return;
  }

  sessionStorage.setItem(SESSION_KEY, '1');

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  let sequenceFinished = false;

  // 2.0s Maximum Hard Safety Timeout
  const safetyTimer = setTimeout(() => {
    if (!sequenceFinished) {
      finishSequence();
    }
  }, 2000);

  // Split wordmark into individual staggered 3D kinetic spans
  function initKineticTypography() {
    if (!brandWordmark) return;

    const kashiiText = 'Kashii';
    const updatezText = 'Updatez';

    let html = '<span class="word-kashii">';
    for (let i = 0; i < kashiiText.length; i++) {
      html += `<span class="k-char" style="animation-delay: ${i * 45}ms">${kashiiText[i]}</span>`;
    }
    html += '</span><span class="word-updatez">';
    for (let j = 0; j < updatezText.length; j++) {
      html += `<span class="k-char u-char" style="animation-delay: ${(kashiiText.length + j) * 45}ms">${updatezText[j]}</span>`;
    }
    html += '</span>';

    brandWordmark.innerHTML = html;
  }

  // Smooth Telemetry Counter Animation (0 -> 100)
  function animateCounter(duration) {
    const start = performance.now();
    return new Promise((resolve) => {
      function tick(now) {
        if (sequenceFinished) {
          if (counterEl) counterEl.textContent = '100%';
          if (progressFill) progressFill.style.width = '100%';
          resolve();
          return;
        }

        const elapsed = now - start;
        const progress = Math.min(1, elapsed / duration);
        const currentVal = Math.round(progress * 100);

        if (counterEl) counterEl.textContent = `${currentVal}%`;
        if (progressFill) progressFill.style.width = `${currentVal}%`;

        if (progress < 1) {
          requestAnimationFrame(tick);
        } else {
          resolve();
        }
      }
      requestAnimationFrame(tick);
    });
  }

  // Interactive mouse/touch radiant spotlight
  function initSpotlight() {
    window.addEventListener('mousemove', (e) => {
      const x = (e.clientX / window.innerWidth) * 100;
      const y = (e.clientY / window.innerHeight) * 100;
      if (entryEl) {
        entryEl.style.setProperty('--spotlight-x', `${x}%`);
        entryEl.style.setProperty('--spotlight-y', `${y}%`);
      }
    });
  }

  async function runSequence() {
    initKineticTypography();
    initSpotlight();

    if (entryEl) entryEl.classList.add('animating');

    // Trigger typography split
    await sleep(150);

    // Fast metric telemetry count-up (650ms)
    await animateCounter(650);

    if (statusEl) {
      statusEl.textContent = '⚡ Verified Stream Live';
      statusEl.classList.add('active');
    }

    // Trigger specular light streak sweep
    if (brandWordmark) {
      brandWordmark.classList.add('laser-sweep');
    }

    await sleep(400);

    await finishSequence();
  }

  async function finishSequence() {
    if (sequenceFinished) return;
    sequenceFinished = true;
    clearTimeout(safetyTimer);

    // Apple/Linear Silky Curtain Slide-Up Transition
    if (entryEl) {
      entryEl.classList.add('curtain-slide-up');
    }

    await sleep(650);

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

    // Trigger hero headline typewriter on homepage
    if (window.startTypewriter) {
      window.startTypewriter();
    }
  }

  // User skip triggers
  if (skipBtn) skipBtn.addEventListener('click', finishSequence);
  if (entryEl) {
    entryEl.addEventListener('click', (e) => {
      if (e.target.id === 'entrySkipBtn') return;
      finishSequence();
    });
  }
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') finishSequence();
  });

  // Global Replay Handler
  window.replayKashiiEntry = async function () {
    sequenceFinished = false;

    if (entryEl) {
      entryEl.style.display = 'flex';
      entryEl.classList.remove('curtain-slide-up', 'animating');
      document.body.style.overflow = 'hidden';
      document.documentElement.classList.remove('entry-done');
    }

    if (brandWordmark) {
      brandWordmark.classList.remove('laser-sweep');
    }

    if (counterEl) counterEl.textContent = '0%';
    if (progressFill) progressFill.style.width = '0%';
    if (statusEl) {
      statusEl.textContent = 'Synchronizing 7-Day Live Feed...';
      statusEl.classList.remove('active');
    }

    await runSequence();
  };

  runSequence();
})();
