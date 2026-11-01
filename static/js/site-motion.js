/* Site-wide motion, powered by GSAP and ScrollTrigger. Nothing is hidden ahead
   of time: an element only animates when it enters the screen, so content stays
   visible if this script does not run. */
(function () {
  'use strict';

  if (!window.gsap || !window.ScrollTrigger) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  // Editors need stable layout under the cursor.
  if (/^\/(resume-builder|resume\/?$|debugger|sql|owner)/.test(location.pathname)) return;

  var gsap = window.gsap;
  var ScrollTrigger = window.ScrollTrigger;
  gsap.registerPlugin(ScrollTrigger);

  var CARDS = '.vp-product-card, .jd-panel, .rs-card, .rs-rail-card, .upload-card, .kx-reveal > *';
  var SKIP = 'header, nav, footer, [role="dialog"], .kx-hero, .kx-flow, #toastContainer';

  function isRevealable(el) {
    if (el.closest(SKIP)) return false;
    var style = getComputedStyle(el);
    return style.position !== 'fixed' && style.display !== 'none';
  }

  function topLevel(list) {
    return list.filter(function (el) {
      return !list.some(function (other) { return other !== el && other.contains(el); });
    });
  }

  function reveal() {
    var found = Array.prototype.slice.call(document.querySelectorAll(CARDS + ', section, article'));
    var targets = topLevel(found.filter(isRevealable));
    if (!targets.length) return;

    ScrollTrigger.batch(targets, {
      start: 'top 92%',
      once: true,
      onEnter: function (batch) {
        gsap.from(batch, {
          y: 26,
          autoAlpha: 0,
          duration: 0.7,
          stagger: 0.06,
          ease: 'expo.out',
          clearProps: 'transform,opacity,visibility'
        });
      }
    });
  }

  function cardTilt() {
    if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;
    var movers = new WeakMap();

    function moverFor(card) {
      if (!movers.has(card)) {
        gsap.set(card, { transformPerspective: 800 });
        movers.set(card, {
          x: gsap.quickTo(card, 'rotationX', { duration: 0.45, ease: 'power3' }),
          y: gsap.quickTo(card, 'rotationY', { duration: 0.45, ease: 'power3' })
        });
      }
      return movers.get(card);
    }

    document.addEventListener('pointermove', function (event) {
      var card = event.target.closest && event.target.closest('.vp-product-card');
      if (!card) return;
      var box = card.getBoundingClientRect();
      var mover = moverFor(card);
      mover.y(((event.clientX - box.left) / box.width - 0.5) * 5);
      mover.x((0.5 - (event.clientY - box.top) / box.height) * 5);
    }, { passive: true });

    document.addEventListener('pointerout', function (event) {
      var card = event.target.closest && event.target.closest('.vp-product-card');
      if (!card || card.contains(event.relatedTarget) || !movers.has(card)) return;
      var mover = movers.get(card);
      mover.x(0);
      mover.y(0);
    }, { passive: true });
  }

  reveal();
  cardTilt();
  window.addEventListener('load', function () { ScrollTrigger.refresh(); });
})();
