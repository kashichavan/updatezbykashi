/* Home hero motion, powered by GSAP. Numbers and bars are server-rendered, so
   the page stays correct if this script does not run. */
(function () {
  'use strict';

  var panel = document.querySelector('[data-hero-panel]');
  if (!panel || !window.gsap) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var gsap = window.gsap;
  var hero = panel.closest('.kx-hero');
  var ease = 'expo.out';

  function format(value) {
    return Math.round(value).toLocaleString('en-IN');
  }

  function intro() {
    var timeline = gsap.timeline({ defaults: { ease: ease } });

    timeline.from(hero.querySelectorAll('.kx-eyebrow, h1, .lead, .kx-hero-actions'), {
      y: 18, autoAlpha: 0, duration: 0.8, stagger: 0.08
    }, 0);

    timeline.from(panel.querySelectorAll('[data-hero-item]'), {
      y: 22, autoAlpha: 0, scale: 0.97, duration: 0.8, stagger: 0.07
    }, 0.1);

    timeline.from(panel.querySelectorAll('.kx-chart-bar'), {
      scaleY: 0, duration: 0.9, stagger: 0.05, ease: 'back.out(1.5)'
    }, 0.35);

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
  }

  function tilt(item) {
    var strength = item.classList.contains('kx-tool') ? 2 : 5;
    var rotateX = gsap.quickTo(item, 'rotationX', { duration: 0.5, ease: 'power3' });
    var rotateY = gsap.quickTo(item, 'rotationY', { duration: 0.5, ease: 'power3' });
    var lift = gsap.quickTo(item, 'y', { duration: 0.4, ease: 'power3' });

    item.addEventListener('pointermove', function (event) {
      var box = item.getBoundingClientRect();
      var x = (event.clientX - box.left) / box.width;
      var y = (event.clientY - box.top) / box.height;
      item.style.setProperty('--mx', (x * 100) + '%');
      item.style.setProperty('--my', (y * 100) + '%');
      rotateY((x - 0.5) * strength * 2);
      rotateX((0.5 - y) * strength * 2);
      lift(-3);
    });

    item.addEventListener('pointerleave', function () {
      rotateX(0);
      rotateY(0);
      lift(0);
    });
  }

  intro();
  if (window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    panel.querySelectorAll('[data-hero-item]').forEach(tilt);
  }
})();
