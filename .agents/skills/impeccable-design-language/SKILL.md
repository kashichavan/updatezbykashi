---
name: impeccable-design-language
description: >-
  Design vocabulary, anti-slop detectors, and visual steering framework from Impeccable (impeccable.style by Paul Bakaus).
  Use when refining frontend UI, auditing design quality, eliminating AI tells (AI beige, generic italic serifs, status-chip soup),
  clarifying visual hierarchy, typesetting, color harmonizing, and structuring DESIGN.md and PRODUCT.md artifacts.
---

# Impeccable: The Missing Design Vocabulary for Frontend & AI Agents

Based on the [Impeccable Design System & Vocabulary](https://impeccable.style/) by Paul Bakaus.

---

## 1. The Core Impeccable Commands & Operations

Impeccable categorizes frontend design actions into 6 clear functional groups:

```
+-------------------------------------------------------------------------------+
|                       Impeccable Design Command Matrix                        |
+---------------+---------------------------------------------------------------+
| 1. CREATE     | · shape      - Define early product brief & intent            |
|               | · impeccable - Freeform aesthetic generation                  |
+---------------+---------------------------------------------------------------+
| 2. EVALUATE   | · critique   - Score hierarchy, clarity, craft (P0-P3 issues) |
|               | · audit      - Production quality, accessibility & contrast   |
+---------------+---------------------------------------------------------------+
| 3. REFINE     | · typeset    - Optical font sizes, line height, measure       |
|               | · layout     - Spatial rhythm, grids, alignments              |
|               | · colorize   - Harmonious palettes, semantic token swatches   |
|               | · animate    - Micro-interactions, spring curves, state morph |
|               | · delight    - Atmospheric details, tasteful polish touches   |
|               | · bolder     - Increase emphasis, high-contrast focal points  |
|               | · quieter    - Lower visual noise, soften secondary elements  |
|               | · overdrive  - Vibrant, energetic high-impact styling         |
+---------------+---------------------------------------------------------------+
| 4. SIMPLIFY   | · distill    - Strip nonessential UI, establish 1 primary task|
|               | · clarify    - Make onboarding and tasks unmistakable         |
|               | · adapt      - Responsive viewport reflows (Mobile/Tablet/PC) |
+---------------+---------------------------------------------------------------+
| 5. HARDEN     | · polish     - Final production pass, remove all AI tells     |
|               | · optimize   - Web vitals, LCP, bundle & image size hygiene   |
|               | · harden     - Internationalization (de-DE), long strings     |
|               | · onboard    - Progressive disclosure for first-time users    |
+---------------+---------------------------------------------------------------+
| 6. SYSTEM     | · init       - Setup PRODUCT.md & DESIGN.md context           |
|               | · extract    - Isolate reusable component tokens              |
|               | · document   - Write design tokens to DESIGN.md               |
|               | · live       - In-browser interactive element steering        |
+---------------+---------------------------------------------------------------+
```

---

## 2. AI Slop Anti-Patterns to Detect & Eliminate

When polishing (`/impeccable polish`) or critiquing (`/impeccable critique`), detect and eliminate these common AI tells:

1. **AI Beige & Low Contrast Washes**:
   - *Tell*: Pale beige backgrounds with low-contrast gray text (`#94a3b8` on `#fdfbf7`).
   - *Fix*: High-contrast dark charcoal/slate (`#0f172a` / `#334155`) on crisp white/porcelain or deep obsidian dark mode.
2. **Generic Italic Serif Headings**:
   - *Tell*: Slapping random decorative italicized words inside technical headings.
   - *Fix*: Purposeful typography where serifs are reserved strictly for authenticated brand marks, paired with modern geometric grotesque sans-serifs for UI.
3. **Status-Chip Soup**:
   - *Tell*: Every badge, pill, and tag having the exact same bright color or pulsing dot.
   - *Fix*: Establish a strict priority hierarchy (e.g. 1 primary `HOT` / `NEW` badge, quiet secondary metadata pills).
4. **Cards Inside Cards (Nested Container Hell)**:
   - *Tell*: Excessive nested boxes, double borders, and claustrophobic padding.
   - *Fix*: Flatter surface hierarchy using whitespace, subtle separator rules, and unified elevation.
5. **Vague AI Copy**:
   - *Tell*: "Unlock your potential today", "Seamless solutions for tomorrow".
   - *Fix*: Concrete, actionable developer/user copy (e.g. "Direct official application links for 2026 batches").

---

## 3. The 4 Surface Modes

Impeccable categorizes user interfaces into 4 distinct modes:

1. **Persuade (Landing & Marketing Pages)**:
   - High visual impact, social proof, bold headlines, prominent primary CTAs.
2. **Operate (Dashboards & Developer Tooling)**:
   - High data density, calm focus, keyboard navigation, unmistakable primary actions, responsive sidebars.
3. **Read (Documentation & Blogs)**:
   - Optimal reading width (60-75 characters per line), high legibility, clear semantic headings (`h2`, `h3`), code blocks with copy buttons.
4. **Experience (Interactive Sandboxes & Playgrounds)**:
   - Real-time feedback, visual debuggers, state inspection, minimal chrome distractions.

---

## 4. Context File Standards (`DESIGN.md` & `PRODUCT.md`)

- **`DESIGN.md`**: Tracks active color tokens, font pairings, border radii, shadow steps, and component variants.
- **`PRODUCT.md`**: Defines target users, key product principles, primary workflows, and accessibility requirements.
