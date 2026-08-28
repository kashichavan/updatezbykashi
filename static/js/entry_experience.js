/**
 * KASHII UPDATEZ — Ultra-Clean Minimalist Editorial Entry Experience
 * 100% Vector Sharp, Zero Canvas Grain, Silky Smooth Dissolve Veil
 */

(function () {
  const SESSION_KEY = 'kashiiEntryPlayed';
  const urlParams = new URLSearchParams(window.location.search);
  const isIntroPage = window.location.pathname === '/intro/' || window.location.pathname === '/welcome/' || window.location.pathname === '/intro' || window.location.pathname === '/welcome';
  const forceIntro = isIntroPage || urlParams.get('intro') === '1' || urlParams.get('replay') === '1';

  const entryEl = document.getElementById('kashiiEntry') || document.getElementById('entry');
  const skipBtn = document.getElementById('entrySkipBtn') || document.getElementById('skip-btn');
  const statusEl = document.getElementById('entryStatusText') || document.getElementById('entry-status');
  const wordmark = document.getElementById('entryWordmark');
  const subTag = document.getElementById('entrySubTag');

  // Bypass admin & owner portals
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

  // Hard safety timeout
  const safetyTimer = setTimeout(() => {
    if (!sequenceFinished) {
      finishSequence();
    }
  }, 3500);

  async function runSequence() {
    // 1. Initial spring entrance
    await sleep(100);
    if (entryEl) entryEl.classList.add('active');

    // 2. Animate status indicator
    await sleep(700);
    if (statusEl) {
      statusEl.textContent = "⚡ Verified Opportunities Live";
      statusEl.classList.add('ready');
    }

    // 3. Shimmer shine across brand wordmark
    if (wordmark) {
      wordmark.classList.add('shimmer');
    }

    await sleep(800);

    await finishSequence();
  }

  async function finishSequence() {
    if (sequenceFinished) return;
    sequenceFinished = true;
    clearTimeout(safetyTimer);

    // Silky smooth dissolve veil transition
    if (entryEl) {
      entryEl.classList.add('fade-veil');
    }

    await sleep(600);

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

    // Trigger headline typewriter on homepage
    if (window.startTypewriter) {
      window.startTypewriter();
    }
  }

  if (skipBtn) {
    skipBtn.addEventListener('click', finishSequence);
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') finishSequence();
  });

  // Global Replay Handler
  window.replayKashiiEntry = async function () {
    sequenceFinished = false;

    if (entryEl) {
      entryEl.style.display = 'flex';
      entryEl.classList.remove('fade-veil', 'active');
      document.body.style.overflow = 'hidden';
      document.documentElement.classList.remove('entry-done');
    }

    if (wordmark) {
      wordmark.classList.remove('shimmer');
    }

    if (statusEl) {
      statusEl.textContent = "Assembling today's opportunities...";
      statusEl.classList.remove('ready');
    }

    await runSequence();
  };

  runSequence();
})();
