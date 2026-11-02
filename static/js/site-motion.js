/* Kashii Updatez motion. One small module, GSAP for the tweens, IntersectionObserver for timing.

   How it works
   - REVEAL: blocks below the screen fade up as they arrive. The observer fires a little before an
     element reaches the screen, so it is solid by the time you read it.
   - FRESH: job cards that app.js renders (filters, pages) fade in once, with a short capped stagger.
   - Nothing that is on screen at load is touched. The home hero entrance is CSS (ui-refresh.css).
   - Tool pages (resume builder, debuggers, owner) stay still: people work there.
   - Off for reduced motion, data saver and low-memory phones (html.lite).

   Safety: the browser computes intersections live, so there are no stale trigger positions. If GSAP
   or IntersectionObserver is missing, or anything throws, every element is shown at once. */
(function () {
  'use strict';

  var gsap = window.gsap;
  var root = document.documentElement;
  if (!gsap || !('IntersectionObserver' in window)) return;
  if (root.classList.contains('lite')) return;
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  if (/^\/(resume|resume-builder|debugger|sql|owner)(\/|$)/.test(location.pathname)) return;

  var CFG = {
    distance: 18,        // px the block rises
    duration: 0.4,       // s
    stagger: 0.05,       // s between blocks arriving together
    maxStagger: 0.2,     // s cap, so a long list never waits
    lead: '0px 0px 20% 0px', // start just before the block reaches the screen
    ease: 'power2.out'
  };

  // Blocks that reveal. Order does not matter; nested matches are skipped so nothing animates twice.
  var REVEAL = [
    '.vp-product-card:not(.vp-shimmer-card)',  // job cards: home, category, group, related
    '.logo-marquee-wrapper',                    // video row moves as one block
    '.jd-panel', '.jd-rail-card',               // job page sections
    '.rs-card', '.transform-card', '.upload-card', '.score-banner-card',
    '.site-footer .footer-col',
    'body > .wrap > div', 'body > .wrap > section', // plain content pages (about, contact, legal)
    '[data-reveal]'
  ].join(',');

  var hidden = new Set();

  function show(el) {
    gsap.set(el, { clearProps: 'opacity,visibility,transform' });
    hidden.delete(el);
  }
  function showAll() { hidden.forEach(show); }
  window.addEventListener('error', showAll);

  function onScreen(el) {
    var r = el.getBoundingClientRect();
    return r.top < (window.innerHeight || root.clientHeight) && r.bottom > 0;
  }

  // Blocks that arrive in the same frame animate together with a capped stagger.
  var arriving = [];
  var frame = 0;
  function play(list, from) {
    var step = Math.min(CFG.stagger, CFG.maxStagger / Math.max(1, list.length - 1));
    gsap.fromTo(list, from, {
      autoAlpha: 1, y: 0, duration: CFG.duration, ease: CFG.ease, stagger: step, overwrite: true,
      onComplete: function () { list.forEach(show); }
    });
  }
  function flush() {
    frame = 0;
    var list = arriving.splice(0).sort(function (a, b) {
      return a.getBoundingClientRect().top - b.getBoundingClientRect().top;
    });
    if (list.length) play(list, { autoAlpha: 0, y: CFG.distance });
  }

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      io.unobserve(e.target);
      arriving.push(e.target);
    });
    if (arriving.length && !frame) frame = requestAnimationFrame(flush);
  }, { rootMargin: CFG.lead, threshold: 0 });

  // The most specific target wins: a block that contains other targets (a section full of cards)
  // stays still and its children animate; a block inside a target that animates is skipped.
  function skip(el, set) {
    var p = el.parentElement;
    while (p && p !== document.body) {
      if (set.has(p) && !holdsTargets(p, set)) return true;
      p = p.parentElement;
    }
    return holdsTargets(el, set);
  }
  function holdsTargets(el, set) {
    var found = false;
    set.forEach(function (other) { if (!found && other !== el && el.contains(other)) found = true; });
    return found;
  }

  function prepare(els) {
    var set = new Set(els);
    els.forEach(function (el) {
      if (el.dataset.motion || el.offsetParent === null || skip(el, set)) return;
      el.dataset.motion = 'reveal';
      if (onScreen(el)) return;            // visible at load: leave it alone
      gsap.set(el, { autoAlpha: 0, y: CFG.distance });
      hidden.add(el);
      io.observe(el);
    });
  }

  // Cards replaced by app.js: on-screen ones fade in now, the rest reveal on arrival.
  function fresh(cards) {
    var now = [];
    var later = [];
    cards.forEach(function (el) {
      if (el.dataset.motion || el.classList.contains('vp-shimmer-card')) return;
      (onScreen(el) ? now : later).push(el);
    });
    if (now.length) {
      now.forEach(function (el) { el.dataset.motion = 'fresh'; hidden.add(el); });
      play(now, { autoAlpha: 0, y: 10 });
    }
    if (later.length) prepare(later);
  }

  function start() {
    try {
      prepare(Array.prototype.slice.call(document.querySelectorAll(REVEAL)));
      var grid = document.getElementById('jobsGrid');
      if (grid && window.MutationObserver) {
        new MutationObserver(function () {
          try { fresh(Array.prototype.slice.call(grid.querySelectorAll('.vp-product-card'))); }
          catch (e) { showAll(); }
        }).observe(grid, { childList: true });
      }
    } catch (e) {
      showAll();
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();
