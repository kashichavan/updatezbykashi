---
name: composio-top-design-skills
description: >-
  Enterprise design intelligence framework based on Composio's top UI/UX engineering skills.
  Encompasses Bento grid layouts, micro-animations, atmospheric depth, accessible color systems,
  Lucide iconography, smooth scrolling, and conversion-focused SaaS design patterns.
  Use when architecting product landing pages, developer tooling, dashboard interfaces,
  and high-polish web applications.
---

# Composio Top Design Skills & UI Engineering Standards

A synthesized master framework combining the top UI/UX design skills and patterns curated by Composio (including Bento grids, craft typography, tactile animations, atmospheric lighting, and high-converting layouts).

---

## 1. The 6 Pillars of Elite Modern Web Design

```
+-----------------------------------------------------------------------+
|                 Composio Top UI/UX Design Stack                       |
+-----------------------------------------------------------------------+
|  1. ATMOSPHERIC DEPTH      - Specular borders, subtle mesh glows,     |
|                              and multi-tier shadow elevations.        |
|  2. ASYMMETRIC BENTO GRIDS - 12-column dynamic spans with rich visual |
|                              weight hierarchy (hero feature + chips). |
|  3. TACTILE MICRO-PHYSICS  - Spring-curve transitions, active press   |
|                              scale feedback, and shimmer badges.      |
|  4. EDITORIAL TYPOGRAPHY   - High-contrast display serifs paired with |
|                              geometric/grotesk sans-serif body.       |
|  5. VECTOR ICONOGRAPHY     - Crisp Lucide SVG icons with consistent   |
|                              2px stroke width and optical alignment.  |
|  6. ACCESSIBLE CONTRAST    - WCAG AAA contrast, semantic focus rings, |
|                              and zero muddy flat AI borders.          |
+-----------------------------------------------------------------------+
```

---

## 2. Bento Grid Architecture Patterns

Use dynamic Bento cards to showcase product features, live code runners, and data metrics:

```html
<div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4 p-4">
  <!-- Feature Card: 2 Column Span with Gradient Glow -->
  <div class="col-span-1 md:col-span-2 relative overflow-hidden rounded-2xl border border-slate-200/80 bg-gradient-to-b from-white to-slate-50/50 p-6 shadow-sm hover:shadow-md transition-all">
    <div class="flex items-center gap-3 mb-4">
      <div class="p-2 rounded-lg bg-blue-50 text-blue-600">
        <i data-lucide="terminal" class="w-5 h-5"></i>
      </div>
      <h3 class="font-bold text-slate-900 text-lg">Interactive Code Execution</h3>
    </div>
    <p class="text-sm text-slate-600 leading-relaxed">Execute Python, Java, and JavaScript with inline variable tracing and live call-stack inspection.</p>
  </div>

  <!-- Metric Card: 1 Column Span -->
  <div class="col-span-1 rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm flex flex-col justify-between">
    <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Fresh Updates</span>
    <div class="text-3xl font-extrabold text-slate-900 mt-2">100% Verified</div>
    <span class="text-xs text-emerald-600 font-medium mt-1">&uarr; Direct official links</span>
  </div>

  <!-- Live Pulse Card: 1 Column Span -->
  <div class="col-span-1 rounded-2xl border border-blue-200/60 bg-blue-50/30 p-6 shadow-sm flex flex-col justify-between">
    <div class="flex items-center gap-2">
      <span class="relative flex h-2.5 w-2.5">
        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
        <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-blue-600"></span>
      </span>
      <span class="text-xs font-bold uppercase tracking-wider text-blue-700">Live Jobs</span>
    </div>
    <div class="text-sm font-semibold text-slate-800 mt-4">24/7 Placement Feeds</div>
  </div>
</div>
```

---

## 3. Micro-Interactions & Spring Physics

1. **Button Sheen / Shimmer**:
   ```css
   .btn-sheen {
     position: relative;
     overflow: hidden;
   }
   .btn-sheen::after {
     content: '';
     position: absolute;
     top: -50%;
     left: -50%;
     width: 200%;
     height: 200%;
     background: linear-gradient(
       60deg,
       transparent,
       rgba(255, 255, 255, 0.25),
       transparent
     );
     transform: rotate(25deg) translateY(-100%);
     transition: transform 0.6s ease;
   }
   .btn-sheen:hover::after {
     transform: rotate(25deg) translateY(100%);
   }
   ```

2. **Tactile Button Press**:
   ```css
   .tactile-btn {
     transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s ease;
   }
   .tactile-btn:active {
     transform: scale(0.96);
   }
   ```

---

## 4. Design Guidelines Checklist

- [x] **No Generic AI Slop**: Avoid centered text blobs, pure gray `#888` borders, and flat generic button templates.
- [x] **High-Contrast Dark / Light Modes**: Maintain legible typography (`#0f172a` text on light, `#f8fafc` text on dark).
- [x] **Consistent Vector Icons**: Render Lucide SVG icons everywhere instead of mismatched bitmap PNGs.
- [x] **Touch-Friendly Hitboxes**: Ensure all interactive controls have at least 44x44px touch targets on mobile.
