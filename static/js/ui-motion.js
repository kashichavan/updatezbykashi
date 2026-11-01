/* Small motion helpers. Reveal and progress effects live in ui-refresh.css. */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function formatCount(value) {
    return Math.round(value).toLocaleString('en-IN');
  }

  function countUp(el) {
    var target = Number(el.getAttribute('data-count'));
    if (!Number.isFinite(target) || target <= 0) return;
    var started = null;
    var duration = 800;

    function frame(now) {
      if (started === null) started = now;
      var progress = Math.min((now - started) / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = formatCount(target * eased);
      if (progress < 1) window.requestAnimationFrame(frame);
    }
    window.requestAnimationFrame(frame);
  }

  function init() {
    var counters = document.querySelectorAll('[data-count]');
    counters.forEach(function (el) {
      el.textContent = formatCount(Number(el.getAttribute('data-count')) || 0);
    });
    if (reduceMotion || !('IntersectionObserver' in window)) return;

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        observer.unobserve(entry.target);
        countUp(entry.target);
      });
    }, { threshold: 0.4 });
    counters.forEach(function (el) { observer.observe(el); });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
