/* Site-wide 3D motion on the page's own elements, powered by GSAP and
   ScrollTrigger. Nothing is hidden ahead of time: an element only animates when
   it enters the screen, so content stays visible if this script does not run. */
(function () {
  'use strict';

  if (!window.gsap || !window.ScrollTrigger) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  // Editors need stable layout under the cursor.
  if (/^\/(resume-builder|resume\/?$|debugger|sql|owner)/.test(location.pathname)) return;

  var gsap = window.gsap;
  var ScrollTrigger = window.ScrollTrigger;
  gsap.registerPlugin(ScrollTrigger);

  // Hiding the mobile address bar resizes the screen. It must not re-measure the page.
  ScrollTrigger.config({ ignoreMobileResize: true });

  // Phones get a lighter entrance: no tilt, no curved video row, no layered depth.
  var fullDepth = window.matchMedia('(min-width: 861px) and (hover: hover) and (pointer: fine)').matches;

  var CARDS = '.vp-product-card, .jd-panel, .rs-card, .rs-rail-card, .upload-card, .about-two-col > *, .contact-grid > *, .kx-reveal > *';
  var SKIP = 'header, nav, footer, [role="dialog"], .kx-hero, #toastContainer';

  // Tilting objects, and the parts of each that lift toward the viewer on hover.
  var OBJECTS = [
    { selector: '.vp-product-card', tilt: 7, layers: [['.vp-card-header', 38], ['.vp-card-content', 20]] },
    { selector: '.rs-rail-card, .about-two-col > *', tilt: 4, layers: [] }
  ];
  var entering = new WeakSet();

  function isRevealable(el) {
    if (el.closest(SKIP)) return false;
    // Already on screen: hiding it to animate it in would look like a blink.
    if (el.getBoundingClientRect().top < window.innerHeight) return false;
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
      start: 'top 94%',
      once: true,
      onEnter: function (batch) {
        batch.forEach(function (el) { entering.add(el); });
        gsap.from(batch, {
          rotationX: fullDepth ? -38 : -14,
          z: fullDepth ? -140 : 0,
          y: fullDepth ? 50 : 24,
          autoAlpha: 0,
          transformPerspective: 1000,
          transformOrigin: '50% 100%',
          duration: fullDepth ? 0.95 : 0.6,
          stagger: fullDepth ? 0.08 : 0.05,
          ease: 'expo.out',
          clearProps: 'transform,opacity,visibility',
          onComplete: function () {
            batch.forEach(function (el) { entering.delete(el); });
          }
        });
      }
    });
  }

  function objectFor(target) {
    if (!target.closest) return null;
    for (var i = 0; i < OBJECTS.length; i += 1) {
      var el = target.closest(OBJECTS[i].selector);
      if (el) return { el: el, config: OBJECTS[i] };
    }
    return null;
  }

  function tiltObjects() {
    var active = null;

    function release() {
      if (!active) return;
      var el = active.el;
      gsap.to(el, { rotationX: 0, rotationY: 0, duration: 0.6, ease: 'power3.out', overwrite: 'auto' });
      gsap.to(active.parts, { z: 0, duration: 0.5, ease: 'power3.out', overwrite: 'auto' });
      el.classList.remove('is-lifted');
      active = null;
    }

    function capture(found) {
      var parts = [];
      found.config.layers.forEach(function (layer) {
        found.el.querySelectorAll(layer[0]).forEach(function (part) {
          parts.push(part);
          gsap.to(part, { z: layer[1], duration: 0.45, ease: 'power3.out', overwrite: 'auto' });
        });
      });
      gsap.set(found.el, { transformPerspective: 900 });
      found.el.classList.add('is-lifted');
      active = {
        el: found.el,
        parts: parts,
        tilt: found.config.tilt,
        x: gsap.quickTo(found.el, 'rotationX', { duration: 0.45, ease: 'power3' }),
        y: gsap.quickTo(found.el, 'rotationY', { duration: 0.45, ease: 'power3' })
      };
    }

    document.addEventListener('pointermove', function (event) {
      var found = objectFor(event.target);
      if (!found || entering.has(found.el)) {
        release();
        return;
      }
      if (!active || active.el !== found.el) {
        release();
        capture(found);
      }
      var box = active.el.getBoundingClientRect();
      var x = (event.clientX - box.left) / box.width;
      var y = (event.clientY - box.top) / box.height;
      active.el.style.setProperty('--mx', (x * 100) + '%');
      active.el.style.setProperty('--my', (y * 100) + '%');
      active.y((x - 0.5) * active.tilt * 2);
      active.x((0.5 - y) * active.tilt * 2);
    }, { passive: true });

    document.documentElement.addEventListener('pointerleave', release);
  }

  // The moving video row bends around the viewer like a curved wall.
  function curveVideoRow() {
    var wrapper = document.querySelector('.logo-marquee-wrapper');
    var cards = wrapper ? wrapper.querySelectorAll('.client-card-3d') : [];
    if (!cards.length) return;

    gsap.set(cards, { transformPerspective: 1000 });
    var inView = false;
    new IntersectionObserver(function (entries) {
      inView = entries[0].isIntersecting;
    }).observe(wrapper);

    gsap.ticker.add(function () {
      if (!inView) return;
      var box = wrapper.getBoundingClientRect();
      var middle = box.left + box.width / 2;
      cards.forEach(function (card) {
        var rect = card.getBoundingClientRect();
        var offset = (rect.left + rect.width / 2 - middle) / (box.width / 2);
        if (Math.abs(offset) > 1.4) return;
        var depth = Math.min(Math.abs(offset), 1.2);
        gsap.set(card, { rotationY: -offset * 34, z: -depth * depth * 110 });
      });
    });
  }

  reveal();
  if (fullDepth) {
    tiltObjects();
    curveVideoRow();
  }
  window.addEventListener('load', function () { ScrollTrigger.refresh(); });
})();
