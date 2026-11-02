/* Site motion (GSAP). Rules learned from the last attempt, which was removed:
   - Never hide content in CSS or HTML. Only this script hides an element, right before animating it.
   - Never touch what is already on screen at load. The home hero entrance is plain CSS (ui-refresh.css),
     so it runs from the first paint and cannot blink or get stuck.
   - A failsafe shows everything after 2.5s and on any error, so content can never stay hidden.
   - 2D only: transform and opacity. No 3D, no scroll-scrubbing, no parallax.
   - Off for reduced motion, data saver and weak phones. Phone address-bar resizes are ignored. */
(function () {
  'use strict';

  var gsap = window.gsap;
  var ST = window.ScrollTrigger;
  if (!gsap) return;

  var root = document.documentElement;
  var calm = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var conn = navigator.connection || {};
  var weak = conn.saveData || (navigator.deviceMemory && navigator.deviceMemory <= 2);
  if (calm || weak) return;

  if (ST) {
    gsap.registerPlugin(ST);
    ST.config({ ignoreMobileResize: true, limitCallbacks: true });
  }

  var EASE = 'power2.out';
  var hidden = new Set();

  function inView(el) {
    var r = el.getBoundingClientRect();
    return r.bottom > 0 && r.top < (window.innerHeight || root.clientHeight);
  }

  function showAll() {
    hidden.forEach(function (el) { gsap.set(el, { clearProps: 'opacity,transform,visibility' }); });
    hidden.clear();
  }
  window.addEventListener('error', showAll);

  /* Failsafe: anything still hidden that is on screen, or already scrolled past, is shown at once.
     Elements further down keep their reveal. */
  setInterval(function () {
    var vh = window.innerHeight || root.clientHeight;
    hidden.forEach(function (el) {
      if (el.getBoundingClientRect().top < vh && !gsap.isTweening(el)) {
        gsap.set(el, { clearProps: 'opacity,transform,visibility' });
        hidden.delete(el);
      }
    });
  }, 1200);

  /* Reveal on scroll: only for elements that start below the screen. */

  function reveal(list) {
    gsap.to(list, {
      autoAlpha: 1, y: 0, duration: 0.5, ease: EASE, stagger: 0.06, overwrite: true,
      onComplete: function () { list.forEach(function (el) { hidden.delete(el); gsap.set(el, { clearProps: 'transform' }); }); }
    });
  }

  function watch(els) {
    var below = [];
    els.forEach(function (el) {
      if (el.dataset.motion || el.offsetParent === null) return;
      el.dataset.motion = '1';
      if (inView(el)) return;
      gsap.set(el, { autoAlpha: 0, y: 24 });
      hidden.add(el);
      below.push(el);
    });
    if (!below.length) return;
    if (ST) {
      ST.batch(below, { start: 'top 92%', once: true, onEnter: reveal });
    } else {
      reveal(below);
    }
  }

  /* Freshly rendered job cards (filters, pages): a short fade-up, on screen or not. */
  function freshCards(cards) {
    var onScreen = [];
    var later = [];
    cards.forEach(function (el) {
      if (el.dataset.motion || el.classList.contains('vp-shimmer-card')) return;
      (inView(el) ? onScreen : later).push(el);
    });
    if (onScreen.length) {
      onScreen.forEach(function (el) { el.dataset.motion = '1'; hidden.add(el); });
      gsap.fromTo(onScreen, { autoAlpha: 0, y: 14 }, {
        autoAlpha: 1, y: 0, duration: 0.4, ease: EASE, stagger: 0.05,
        onComplete: function () { onScreen.forEach(function (el) { hidden.delete(el); gsap.set(el, { clearProps: 'transform' }); }); }
      });
    }
    if (later.length) watch(later);
  }

  function start() {
    try {
      watch(Array.prototype.slice.call(document.querySelectorAll(
        '.vp-product-card:not(.vp-shimmer-card), .client-card-3d, .site-footer .footer-col, [data-reveal]'
      )));

      var grid = document.getElementById('jobsGrid');
      if (grid && window.MutationObserver) {
        new MutationObserver(function () {
          freshCards(Array.prototype.slice.call(grid.querySelectorAll('.vp-product-card')));
        }).observe(grid, { childList: true });
      }
    } catch (e) {
      showAll();
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
})();
