---
name: shadcn-ui-patterns
description: >-
  Enterprise guide and implementation patterns for shadcn/ui accessible component architecture,
  Tailwind CSS design tokens, Radix UI primitives, CVA (class-variance-authority), and copy-paste component engineering.
  Use this skill when building modern web interfaces, accessible design systems, reusable button/dialog/dropdown primitives,
  command palettes (cmdk), data tables, dark mode theming, and zero-runtime styled UI components.
---

# shadcn/ui Component Architecture & Design Patterns

A complete, production-grade guide for building accessible, high-performance UI components using the **shadcn/ui** philosophy: open-code, copy-pasteable, highly customizable primitives built on top of Tailwind CSS and accessible primitives.

---

## 1. Core Principles of shadcn/ui

1. **Not a Component Library / Dependency**:
   - Components live directly in your codebase (`components/ui/`).
   - You own the code. You customize colors, padding, transitions, and variants directly without overriding bloated CSS packages.
2. **Accessible by Default (Radix Primitives / WAI-ARIA)**:
   - Full keyboard navigation (Tab, Enter, Escape, Arrow keys).
   - Proper ARIA attributes (`aria-expanded`, `aria-controls`, `aria-describedby`, `role="dialog"`).
   - Screen-reader support with `sr-only` utility classes.
3. **Composable Variants via CVA (Class Variance Authority)**:
   - Type-safe, declarative variant mapping for size, intent, state, and themes.
4. **Tailwind CSS & CSS Variables Integration**:
   - Uses semantic design tokens (`--background`, `--foreground`, `--primary`, `--secondary`, `--muted`, `--accent`, `--destructive`, `--border`, `--ring`).

---

## 2. Global Design Token Architecture (CSS Variables)

```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;

  --card: 0 0% 100%;
  --card-foreground: 222.2 84% 4.9%;

  --popover: 0 0% 100%;
  --popover-foreground: 222.2 84% 4.9%;

  --primary: 221.2 83.2% 53.3%;
  --primary-foreground: 210 40% 98%;

  --secondary: 210 40% 96.1%;
  --secondary-foreground: 222.2 47.4% 11.2%;

  --muted: 210 40% 96.1%;
  --muted-foreground: 215.4 16.3% 46.9%;

  --accent: 210 40% 96.1%;
  --accent-foreground: 222.2 47.4% 11.2%;

  --destructive: 0 84.2% 60.2%;
  --destructive-foreground: 210 40% 98%;

  --border: 214.3 31.8% 91.4%;
  --input: 214.3 31.8% 91.4%;
  --ring: 221.2 83.2% 53.3%;

  --radius: 0.5rem;
}

.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;

  --card: 222.2 84% 4.9%;
  --card-foreground: 210 40% 98%;

  --popover: 222.2 84% 4.9%;
  --popover-foreground: 210 40% 98%;

  --primary: 217.2 91.2% 59.8%;
  --primary-foreground: 222.2 47.4% 11.2%;

  --secondary: 217.2 32.6% 17.5%;
  --secondary-foreground: 210 40% 98%;

  --muted: 217.2 32.6% 17.5%;
  --muted-foreground: 215 20.2% 65.1%;

  --accent: 217.2 32.6% 17.5%;
  --accent-foreground: 210 40% 98%;

  --destructive: 0 62.8% 30.6%;
  --destructive-foreground: 210 40% 98%;

  --border: 217.2 32.6% 17.5%;
  --input: 217.2 32.6% 17.5%;
  --ring: 224.3 76.3% 48%;
}
```

---

## 3. Essential Component Patterns

### A. Button Primitive (CVA Pattern)
```html
<!-- Base Button Class Structure -->
<button class="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2 active:scale-[0.98]">
  <i data-lucide="sparkles" class="mr-2 h-4 w-4"></i>
  Explore Opportunities
</button>
```

### B. Interactive Card Component
```html
<div class="rounded-xl border bg-card text-card-foreground shadow-sm hover:shadow-md transition-all duration-200 hover:border-primary/50">
  <div class="flex flex-col space-y-1.5 p-6">
    <div class="flex items-center justify-between">
      <h3 class="text-lg font-semibold leading-none tracking-tight">Software Engineering Intern</h3>
      <span class="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold bg-secondary text-secondary-foreground">NEW</span>
    </div>
    <p class="text-sm text-muted-foreground">Google &middot; Bengaluru, India</p>
  </div>
  <div class="p-6 pt-0">
    <p class="text-sm text-foreground/80">Build distributed systems and next-gen cloud infra with Python and Go.</p>
  </div>
  <div class="flex items-center p-6 pt-0 gap-2">
    <button class="w-full bg-primary text-primary-foreground rounded-md h-9 px-3 text-xs font-medium hover:bg-primary/90">Apply Now</button>
  </div>
</div>
```

### C. Dialog / Modal (Accessible Radix Pattern)
```html
<div class="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out" aria-hidden="true"></div>
<div role="dialog" aria-modal="true" class="fixed left-[50%] top-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 sm:rounded-lg">
  <div class="flex flex-col space-y-1.5 text-center sm:text-left">
    <h2 class="text-lg font-semibold leading-none tracking-tight">Job Application Verification</h2>
    <p class="text-sm text-muted-foreground">Confirm you meet all eligible graduation batches before submitting.</p>
  </div>
</div>
```

---

## 4. Integration Guidelines for Django / Vanilla JS / React
- **Vanilla / Django Templates**: Structure class tokens in CSS with BEM or Tailwind utility strings mirroring shadcn/ui classes.
- **Lucide Icons**: Pair every shadcn component with `lucide-icons` for clean SVG line consistency (`stroke-width="2"`).
- **Transitions**: Keep duration between `150ms` and `250ms` with `cubic-bezier(0.16, 1, 0.3, 1)`.
