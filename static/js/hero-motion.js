/* Home hero as one 3D object, powered by GSAP. Numbers and bars are
   server-rendered, so the page stays correct if this script does not run. */
(function () {
  'use strict';

  var panel = document.querySelector('[data-hero-panel]');
  if (!panel || !window.gsap || !window.ScrollTrigger) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var gsap = window.gsap;
  var ScrollTrigger = window.ScrollTrigger;
  gsap.registerPlugin(ScrollTrigger);

  var hero = panel.closest('.kx-hero');
  var items = panel.querySelectorAll('[data-hero-item]');
  var groups = panel.querySelectorAll('.kx-bento, .kx-tools');

  // Phones stack the panel under the text, so the depth effects tied to the
  // hero's position would hit it while people are reading it.
  var fullDepth = window.matchMedia('(min-width: 861px) and (hover: hover) and (pointer: fine)').matches;

  function format(value) {
    return Math.round(value).toLocaleString('en-IN');
  }

  function intro() {
    var timeline = gsap.timeline({ defaults: { ease: 'expo.out' } });

    timeline.from(hero.querySelectorAll('.kx-eyebrow, h1, .lead, .kx-hero-actions'), {
      rotationX: fullDepth ? -55 : -16,
      z: fullDepth ? -120 : 0,
      y: 24,
      autoAlpha: 0,
      transformPerspective: 900,
      transformOrigin: '50% 100%',
      duration: fullDepth ? 1 : 0.7,
      stagger: fullDepth ? 0.09 : 0.06,
      clearProps: 'transform,opacity,visibility'
    }, 0);

    timeline.from(items, {
      rotationX: fullDepth ? -75 : -22,
      rotationY: fullDepth ? 14 : 0,
      z: fullDepth ? -260 : 0,
      y: fullDepth ? 0 : 18,
      autoAlpha: 0,
      transformPerspective: fullDepth ? 0 : 900,
      transformOrigin: '50% 100%',
      duration: fullDepth ? 1.1 : 0.7,
      stagger: fullDepth ? 0.08 : 0.06,
      clearProps: fullDepth ? '' : 'transform,opacity,visibility'
    }, 0.1);

    timeline.from(panel.querySelectorAll('.kx-chart-bar'), {
      scaleY: 0,
      duration: 0.9,
      stagger: 0.05,
      ease: 'back.out(1.5)'
    }, 0.45);

    panel.querySelectorAll('[data-hero-count]').forEach(function (el) {
      var target = Number(el.getAttribute('data-hero-count'));
      if (!Number.isFinite(target) || target <= 0) return;
      var counter = { value: 0 };
      el.textContent = '0';
      timeline.to(counter, {
        value: target,
        duration: 1.3,
        ease: 'power3.out',
        onUpdate: function () { el.textContent = format(counter.value); }
      }, 0.3);
    });

    return timeline;
  }

  // Leaving the screen, the panel falls back into the page.
  function scrollDepth() {
    gsap.to(panel, {
      rotationX: 22,
      z: -180,
      y: 30,
      autoAlpha: 0.55,
      transformOrigin: '50% 100%',
      ease: 'none',
      scrollTrigger: { trigger: hero, start: 'top top+=60', end: 'bottom top+=80', scrub: 0.6 }
    });
  }

  // The panel leans toward the cursor, and each card lifts off it.
  function pointerDepth() {
    var turn = Array.prototype.map.call(groups, function (group) {
      return {
        x: gsap.quickTo(group, 'rotationX', { duration: 0.7, ease: 'power3' }),
        y: gsap.quickTo(group, 'rotationY', { duration: 0.7, ease: 'power3' })
      };
    });

    hero.addEventListener('pointermove', function (event) {
      var box = hero.getBoundingClientRect();
      var x = (event.clientX - box.left) / box.width - 0.5;
      var y = (event.clientY - box.top) / box.height - 0.5;
      turn.forEach(function (group) {
        group.y(x * 13);
        group.x(y * -9);
      });
    }, { passive: true });

    hero.addEventListener('pointerleave', function () {
      turn.forEach(function (group) {
        group.x(0);
        group.y(0);
      });
    });

    items.forEach(function (item) {
      var parts = item.querySelectorAll('strong, .kx-chart, .kx-tool-icon, .kx-tool-text');

      item.addEventListener('pointerenter', function () {
        gsap.to(item, { z: 46, duration: 0.45, ease: 'power3.out' });
        gsap.to(parts, { z: 30, duration: 0.45, ease: 'power3.out' });
      });

      item.addEventListener('pointermove', function (event) {
        var box = item.getBoundingClientRect();
        item.style.setProperty('--mx', ((event.clientX - box.left) / box.width * 100) + '%');
        item.style.setProperty('--my', ((event.clientY - box.top) / box.height * 100) + '%');
      }, { passive: true });

      item.addEventListener('pointerleave', function () {
        gsap.to(item, { z: 0, duration: 0.5, ease: 'power3.out' });
        gsap.to(parts, { z: 0, duration: 0.5, ease: 'power3.out' });
      });
    });
  }

  // The entrance only runs while the first-visit splash covers the hero. Once
  // people can see the hero, it is never hidden and played again.
  function playBehindSplash() {
    var splash = document.getElementById('kashiiEntry');
    var root = document.documentElement;
    if (!splash || root.classList.contains('entry-done') || getComputedStyle(splash).display === 'none') return;

    var timeline = intro();
    timeline.pause();
    var play = function () { timeline.play(); };
    window.addEventListener('kashii:entry-leaving', play, { once: true });
    window.setTimeout(play, 5000);
  }

  playBehindSplash();
  if (fullDepth) {
    scrollDepth();
    pointerDepth();
  }
})();
