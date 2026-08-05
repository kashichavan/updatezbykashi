---
name: trending-ui-design
description: >-
  Master guide for building modern, high-converting, dynamic, and visually stunning web user interfaces.
  Use this skill when designing component systems, responsive SaaS dashboards, applying sleek dark modes, glassmorphism, fluid micro-animations, curated color palettes, typography, interactive UI elements, command palettes, and web accessibility (a11y).
---

# Modern & Trending UI/UX Design System Guide

Deliver state-of-the-art UI design with high-end typography, harmonious color systems, subtle depth elevation, glassmorphism, and responsive micro-interactions.

---

## 1. Core Visual Aesthetics & Design System Tokens

### A. Color Architecture (Modern HSL & CSS Variables)
Avoid flat primary colors (pure red, standard blue). Use rich, tailored slate/zinc neutral scales combined with vibrant neon/pastel accents:

```css
:root {
  /* Neutral Slate Scale */
  --bg-dark: hsl(222, 47%, 7%);
  --surface-card: hsl(217, 33%, 12%);
  --surface-hover: hsl(217, 33%, 17%);
  --border-subtle: hsl(217, 20%, 20%);
  --border-glow: hsl(217, 90%, 60%, 0.3);

  /* Primary Accent & Gradients */
  --accent-primary: hsl(245, 80%, 65%);
  --accent-secondary: hsl(280, 85%, 65%);
  --accent-cyan: hsl(190, 90%, 50%);
  --gradient-brand: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  --gradient-glow: radial-gradient(circle at top left, rgba(99, 102, 241, 0.15), transparent 50%);

  /* Typography Colors */
  --text-main: hsl(210, 40%, 98%);
  --text-muted: hsl(215, 20%, 65%);
  --text-faint: hsl(215, 16%, 45%);

  /* Status Colors */
  --success: hsl(150, 85%, 42%);
  --warning: hsl(38, 92%, 50%);
  --danger: hsl(355, 84%, 60%);
}
```

### B. Glassmorphism & Elevation Layering
Use translucent blurred backgrounds for topbars, modals, floating panels, and sidebars:

```css
.glass-panel {
  background: rgba(18, 24, 38, 0.7);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}

.glass-card-hover {
  transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s ease, border-color 0.25s ease;
}

.glass-card-hover:hover {
  transform: translateY(-4px);
  border-color: rgba(99, 102, 241, 0.4);
  box-shadow: 0 12px 24px -8px rgba(99, 102, 241, 0.25);
}
```

---

## 2. Modern Typography Standards

- **Primary Font**: `'Inter'`, `'Outfit'`, or `'Plus Jakarta Sans'`, sans-serif.
- **Monospace Font**: `'Fira Code'`, `'JetBrains Mono'`, monospace.
- **Hierarchy & Tracking**:
  - `h1`: `font-weight: 800; letter-spacing: -0.03em; line-height: 1.15;`
  - `h2`: `font-weight: 700; letter-spacing: -0.02em; line-height: 1.2;`
  - `body`: `font-weight: 400; font-size: 0.9375rem (15px); line-height: 1.6;`
  - `caption/badge`: `font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; font-size: 0.75rem;`

---

## 3. High-Converting SaaS UI Layout & Key Components

### A. Dashboard App Shell Layout
- **Sidebar**: Collapsible 240px navigation bar with active indicators, icon badges, org switcher, and dark-mode toggle.
- **Header**: Glassmorphism top bar with Command-K global search, notification center, and user avatar menu.
- **Main Canvas**: Fluid grid (`display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem;`).

### B. Essential Modern Components

#### 1. Command Palette (`Cmd + K`)
- Modal overlay with backdrop blur (`backdrop-filter: blur(8px)`).
- Instant search input with keyboard navigation (`ArrowUp`, `ArrowDown`, `Enter`).
- Categorized items (Actions, Pages, Recent Files).

#### 2. Dynamic Metric Cards (Stats Badge)
- Contains metric value, label, percentage change pill (+12.4% with green subtle background), and sparkline mini-chart.

#### 3. Interactive Data Tables
- Sticky headers, row hover highlight, pagination, column sort triggers, and status pills:
```html
<span class="status-badge status-active">
  <span class="status-dot"></span> Active
</span>
```

---

## 4. Micro-Animations & Smooth Transitions

Use physics-inspired bezier curves instead of linear transitions:

```css
/* Smooth Natural Spring Curve */
.interactive-element {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

/* Skeleton Loading Shimmer */
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.skeleton {
  background: linear-gradient(90deg, var(--surface-card) 25%, var(--surface-hover) 50%, var(--surface-card) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 6px;
}
```

---

## 5. UI Checklist Before Final Delivery
- [ ] Contrast ratio meets WCAG AA standards (4.5:1 ratio for normal text).
- [ ] All interactive elements (buttons, inputs, links) have explicit `:focus-visible` outline rings for keyboard accessibility.
- [ ] Empty states and loading skeletons implemented for data views.
- [ ] Mobile responsive layout tested at breakpoints: 320px, 640px, 768px, 1024px, 1280px.
- [ ] Subtle hover and active states attached to every clickable component.
