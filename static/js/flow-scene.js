/* Home 3D scene: a resume, a briefcase and a score badge, built with Three.js.
   three.js is only fetched when the section is close to the screen. If WebGL or
   the download fails, the section shows its steps on their own. */
const section = document.querySelector('[data-flow]');
const canvas = section && section.querySelector('canvas');

function roundedRect(width, height, radius) {
  const x = -width / 2;
  const y = -height / 2;
  const shape = new window.THREE_NS.Shape();
  shape.moveTo(x + radius, y);
  shape.lineTo(x + width - radius, y);
  shape.quadraticCurveTo(x + width, y, x + width, y + radius);
  shape.lineTo(x + width, y + height - radius);
  shape.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
  shape.lineTo(x + radius, y + height);
  shape.quadraticCurveTo(x, y + height, x, y + height - radius);
  shape.lineTo(x, y + radius);
  shape.quadraticCurveTo(x, y, x + radius, y);
  return shape;
}

function slab(THREE, width, height, depth, radius, material) {
  const geometry = new THREE.ExtrudeGeometry(roundedRect(width, height, radius), {
    depth, bevelEnabled: true, bevelSize: 0.015, bevelThickness: 0.015, bevelSegments: 3, curveSegments: 10
  });
  geometry.center();
  return new THREE.Mesh(geometry, material);
}

function buildResume(THREE, mats) {
  const group = new THREE.Group();
  group.add(slab(THREE, 2.1, 2.9, 0.05, 0.08, mats.paper));

  const add = (width, height, x, y, material) => {
    const bar = slab(THREE, width, height, 0.012, Math.min(height / 2, 0.02), material);
    bar.position.set(x, y, 0.05);
    group.add(bar);
  };
  add(1.0, 0.13, -0.38, 1.12, mats.blue);
  add(0.62, 0.06, -0.57, 0.93, mats.soft);
  add(1.72, 0.03, 0, 0.78, mats.line);
  [0.58, 0.44, 0.3].forEach((y, i) => add(1.72 - i * 0.28, 0.05, -i * 0.14, y, mats.soft));
  add(0.6, 0.07, -0.56, 0.06, mats.blue);
  [-0.1, -0.24, -0.38, -0.52].forEach((y, i) => add(1.72 - (i % 2) * 0.34, 0.05, -(i % 2) * 0.17, y, mats.soft));
  add(0.6, 0.07, -0.56, -0.74, mats.blue);
  [-0.9, -1.04].forEach((y, i) => add(1.6 - i * 0.3, 0.05, -0.06 - i * 0.15, y, mats.soft));
  return group;
}

function buildBriefcase(THREE, mats) {
  const group = new THREE.Group();
  group.add(slab(THREE, 1.5, 1.05, 0.42, 0.13, mats.navy));
  const handle = new THREE.Mesh(new THREE.TorusGeometry(0.22, 0.04, 12, 28, Math.PI), mats.steel);
  handle.position.y = 0.53;
  group.add(handle);
  const band = slab(THREE, 1.5, 0.05, 0.02, 0.01, mats.steel);
  band.position.set(0, 0.05, 0.23);
  group.add(band);
  const clasp = slab(THREE, 0.2, 0.18, 0.04, 0.03, mats.gold);
  clasp.position.set(0, 0.05, 0.25);
  group.add(clasp);
  return group;
}

function buildBadge(THREE, mats) {
  const group = new THREE.Group();
  const disc = new THREE.Mesh(new THREE.CylinderGeometry(0.56, 0.56, 0.1, 48), mats.paper);
  disc.rotation.x = Math.PI / 2;
  group.add(disc);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.46, 0.05, 14, 64, Math.PI * 1.55), mats.green);
  ring.position.z = 0.07;
  ring.rotation.z = Math.PI / 2;
  group.add(ring);
  const short = slab(THREE, 0.26, 0.07, 0.03, 0.03, mats.green);
  short.position.set(-0.12, -0.06, 0.08);
  short.rotation.z = -Math.PI / 4;
  group.add(short);
  const long = slab(THREE, 0.46, 0.07, 0.03, 0.03, mats.green);
  long.position.set(0.09, 0.03, 0.08);
  long.rotation.z = Math.PI / 3.6;
  group.add(long);
  return group;
}

function start(THREE) {
  window.THREE_NS = THREE;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(32, 1, 0.1, 50);
  camera.position.set(0, 0, 8.4);

  scene.add(new THREE.HemisphereLight(0xffffff, 0xbfdbfe, 2.1));
  const key = new THREE.DirectionalLight(0xffffff, 2.2);
  key.position.set(3, 4, 6);
  scene.add(key);
  const rim = new THREE.DirectionalLight(0x93c5fd, 1.6);
  rim.position.set(-5, 1, -3);
  scene.add(rim);

  const standard = (color, roughness = 0.55, metalness = 0) =>
    new THREE.MeshStandardMaterial({ color, roughness, metalness });
  const mats = {
    paper: standard(0xffffff, 0.45),
    blue: standard(0x2563eb, 0.4),
    soft: standard(0xcbd5e1, 0.6),
    line: standard(0x93c5fd, 0.5),
    navy: standard(0x1e3a8a, 0.42, 0.15),
    steel: standard(0x94a3b8, 0.3, 0.7),
    gold: standard(0xf59e0b, 0.35, 0.4),
    green: standard(0x16a34a, 0.4)
  };

  const rig = new THREE.Group();
  const resume = buildResume(THREE, mats);
  const briefcase = buildBriefcase(THREE, mats);
  briefcase.position.set(-1.75, -0.95, -0.7);
  briefcase.rotation.set(0.1, 0.55, -0.12);
  const badge = buildBadge(THREE, mats);
  badge.position.set(1.45, 1.05, 0.8);
  badge.rotation.y = -0.35;
  rig.add(resume, briefcase, badge);
  scene.add(rig);

  const state = { scroll: -0.45, pointerX: 0, pointerY: 0 };
  let visible = false;

  function draw(time) {
    const float = reduced ? 0 : Math.sin(time * 0.9);
    rig.rotation.y = state.scroll + state.pointerX * 0.22;
    rig.rotation.x = -0.05 + state.pointerY * 0.14;
    resume.position.y = float * 0.05;
    briefcase.position.y = -0.95 + Math.sin(time * 0.7 + 1) * (reduced ? 0 : 0.08);
    badge.position.y = 1.05 + Math.sin(time * 1.1 + 2) * (reduced ? 0 : 0.07);
    if (!reduced) badge.rotation.y = -0.35 + Math.sin(time * 0.6) * 0.25;
    renderer.render(scene, camera);
  }

  function resize() {
    const box = canvas.parentElement.getBoundingClientRect();
    if (!box.width || !box.height) return;
    renderer.setSize(box.width, box.height, false);
    camera.aspect = box.width / box.height;
    camera.position.z = camera.aspect < 1 ? 10.4 : 8.4;
    camera.updateProjectionMatrix();
    draw(0);
  }

  new ResizeObserver(resize).observe(canvas.parentElement);
  resize();
  section.classList.add('is-3d');

  canvas.addEventListener('webglcontextlost', () => section.classList.remove('is-3d'));

  new IntersectionObserver((entries) => {
    visible = entries[0].isIntersecting;
  }).observe(section);

  if (reduced || !window.gsap) return;

  const gsap = window.gsap;
  gsap.registerPlugin(window.ScrollTrigger);
  const steps = section.querySelectorAll('[data-flow-step]');
  window.ScrollTrigger.create({
    trigger: section,
    start: 'top 85%',
    end: 'bottom 25%',
    scrub: 0.8,
    onUpdate(self) {
      state.scroll = -0.45 + self.progress * 0.9;
      const active = Math.min(steps.length - 1, Math.floor(self.progress * steps.length));
      steps.forEach((step, index) => step.classList.toggle('is-active', index === active));
    }
  });

  gsap.from(rig.scale, { x: 0.8, y: 0.8, z: 0.8, duration: 1.2, ease: 'expo.out' });
  gsap.from(badge.scale, { x: 0, y: 0, z: 0, duration: 0.9, delay: 0.35, ease: 'back.out(2)' });

  if (window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    const pointerX = gsap.quickTo(state, 'pointerX', { duration: 0.8, ease: 'power3' });
    const pointerY = gsap.quickTo(state, 'pointerY', { duration: 0.8, ease: 'power3' });
    section.addEventListener('pointermove', (event) => {
      const box = section.getBoundingClientRect();
      pointerX((event.clientX - box.left) / box.width - 0.5);
      pointerY((event.clientY - box.top) / box.height - 0.5);
    }, { passive: true });
    section.addEventListener('pointerleave', () => { pointerX(0); pointerY(0); });
  }

  gsap.ticker.add((time) => { if (visible) draw(time); });
}

function canUse3d() {
  const connection = navigator.connection;
  if (connection && (connection.saveData || /2g/.test(connection.effectiveType || ''))) return false;
  try {
    return !!document.createElement('canvas').getContext('webgl2');
  } catch (err) {
    return false;
  }
}

if (canvas && canUse3d()) {
  const watcher = new IntersectionObserver(async (entries) => {
    if (!entries[0].isIntersecting) return;
    watcher.disconnect();
    try {
      start(await import(canvas.dataset.three));
    } catch (err) {
      console.warn('3D scene skipped:', err);
    }
  }, { rootMargin: '300px' });
  watcher.observe(section);
}
