/**
 * Kashii Updatez — Spider Web Interactive Canvas Engine (Spider-Man / VS Code Web Mesh)
 * Renders an ambient, high-performance particle-web mesh across both Desktop & Mobile viewports.
 * Nodes smoothly drift and form web filament connections to cursor/touch positions with elastic tension.
 */
(function () {
  'use strict';

  function initSpiderWebCanvas() {
    if (document.getElementById('spiderWebCanvas')) return;

    const canvas = document.createElement('canvas');
    canvas.id = 'spiderWebCanvas';
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100vw';
    canvas.style.height = '100vh';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '0';
    canvas.style.opacity = '0.75';
    document.body.prepend(canvas);

    const ctx = canvas.getContext('2d', { alpha: true });
    if (!ctx) return;

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    // Responsive particle density
    const isMobile = window.innerWidth < 768;
    const particleCount = isMobile ? 32 : 64;
    const maxDistance = isMobile ? 100 : 140;
    const mouseRadius = isMobile ? 120 : 180;

    const mouse = {
      x: -1000,
      y: -1000,
      active: false
    };

    class WebParticle {
      constructor() {
        this.reset();
      }

      reset() {
        this.x = Math.random() * width;
        this.y = Math.random() * height;
        this.vx = (Math.random() - 0.5) * 0.55;
        this.vy = (Math.random() - 0.5) * 0.55;
        this.radius = Math.random() * 1.5 + 1;
        this.baseAlpha = Math.random() * 0.35 + 0.25;
        // Muted luxury palette: warm dusty rose vs muted mauve-gray
        this.color = Math.random() > 0.4 ? '183, 157, 155' : '114, 103, 111';
      }

      update() {
        this.x += this.vx;
        this.y += this.vy;

        // Bounce gently off viewport edges
        if (this.x < 0 || this.x > width) this.vx *= -1;
        if (this.y < 0 || this.y > height) this.vy *= -1;

        // Mouse / Touch gravity spring pull
        if (mouse.active) {
          const dx = mouse.x - this.x;
          const dy = mouse.y - this.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < mouseRadius && dist > 1) {
            const force = (1 - dist / mouseRadius) * 0.035;
            this.vx += (dx / dist) * force;
            this.vy += (dy / dist) * force;
          }
        }

        // Velocity damping to keep movement gentle & smooth
        this.vx *= 0.99;
        this.vy *= 0.99;
      }

      draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${this.color}, ${this.baseAlpha})`;
        ctx.fill();
      }
    }

    const particles = [];
    for (let i = 0; i < particleCount; i++) {
      particles.push(new WebParticle());
    }

    function drawWebLines() {
      // Connect particle to particle
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const p1 = particles[i];
          const p2 = particles[j];
          const dx = p1.x - p2.x;
          const dy = p1.y - p2.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < maxDistance) {
            const alpha = (1 - dist / maxDistance) * 0.22;
            ctx.beginPath();
            ctx.moveTo(p1.x, p1.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = `rgba(114, 103, 111, ${alpha})`;
            ctx.lineWidth = 0.75;
            ctx.stroke();
          }
        }

        // Connect particle to interactive Cursor / Touch point (Spiderweb pull)
        if (mouse.active) {
          const p = particles[i];
          const dx = mouse.x - p.x;
          const dy = mouse.y - p.y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < mouseRadius) {
            const alpha = (1 - dist / mouseRadius) * 0.45;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(mouse.x, mouse.y);
            ctx.strokeStyle = `rgba(183, 157, 155, ${alpha})`;
            ctx.lineWidth = 1.1;
            ctx.stroke();
          }
        }
      }
    }

    let animationFrameId;
    function animate() {
      ctx.clearRect(0, 0, width, height);

      for (let i = 0; i < particles.length; i++) {
        particles[i].update();
        particles[i].draw();
      }

      drawWebLines();
      animationFrameId = requestAnimationFrame(animate);
    }

    animate();

    // Event Listeners for Desktop Cursor & Mobile Touch
    window.addEventListener('resize', () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    }, { passive: true });

    window.addEventListener('mousemove', (e) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
      mouse.active = true;
    }, { passive: true });

    window.addEventListener('mouseleave', () => {
      mouse.active = false;
    });

    window.addEventListener('touchstart', (e) => {
      if (e.touches && e.touches[0]) {
        mouse.x = e.touches[0].clientX;
        mouse.y = e.touches[0].clientY;
        mouse.active = true;
      }
    }, { passive: true });

    window.addEventListener('touchmove', (e) => {
      if (e.touches && e.touches[0]) {
        mouse.x = e.touches[0].clientX;
        mouse.y = e.touches[0].clientY;
        mouse.active = true;
      }
    }, { passive: true });

    window.addEventListener('touchend', () => {
      mouse.active = false;
    }, { passive: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSpiderWebCanvas);
  } else {
    initSpiderWebCanvas();
  }
})();
