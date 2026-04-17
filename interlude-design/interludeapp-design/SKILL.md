---
name: interludeapp-design
description: Design system skill for interludeapp. Activate when building UI components, pages, or any visual elements. Provides exact color tokens, typography scale, spacing grid, component patterns, and craft rules. Read references/DESIGN.md before writing any CSS or JSX. Includes ultra-mode visual journey: read references/ANIMATIONS.md, references/LAYOUT.md, references/COMPONENTS.md, and references/INTERACTIONS.md for full motion and layout details.
---

# interludeapp Design System

You are building UI for **interludeapp**. Light-themed, neutral palette, monospace typography (Nanum Myeongjo), standard density on a 5px grid, flat elevation (no shadows).

## Visual Reference

**IMPORTANT**: Study ALL screenshots below before writing any UI. Match colors, typography, spacing, layout, and motion exactly as shown.

### Homepage

![interludeapp Homepage](screenshots/homepage.png)

### Scroll Journey (Cinematic Visual States)

> These screenshots capture the website at different scroll depths. The design changes dramatically as you scroll — each frame shows a different cinematic state. Replicate these exact visual transitions.

#### 0% — Hero / Above the fold

![Scroll 0%](screens/scroll/scroll-000.png)

#### 17% — Mid-page at 17% scroll

![Scroll 17%](screens/scroll/scroll-017.png)

#### 33% — Mid-page at 33% scroll

![Scroll 33%](screens/scroll/scroll-033.png)

#### 50% — Mid-page at 50% scroll

![Scroll 50%](screens/scroll/scroll-050.png)

#### 67% — Mid-page at 67% scroll

![Scroll 67%](screens/scroll/scroll-067.png)

#### 83% — Mid-page at 83% scroll

![Scroll 83%](screens/scroll/scroll-083.png)

#### 100% — Footer / End of page

![Scroll 100%](screens/scroll/scroll-100.png)

### Video Backgrounds (First Frames)

![Video 1 (content)](screens/scroll/video-1-frame.png)

> Read `references/DESIGN.md` for full token details. Read `references/ANIMATIONS.md` for motion specs. Read `references/LAYOUT.md` for layout structure. Read `references/COMPONENTS.md` for component patterns.

## Ultra Reference Files

This package includes extended documentation. **Read these files before implementing:**

| File | Contents |
|------|----------|
| `references/DESIGN.md` | Full design system tokens, colors, typography, spacing |
| `references/VISUAL_GUIDE.md` | **START HERE** — Master visual guide with all screenshots embedded |
| `references/ANIMATIONS.md` | CSS keyframes, scroll triggers, motion library stack, video specs |
| `references/LAYOUT.md` | Flex/grid containers, page structure, spacing relationships |
| `references/COMPONENTS.md` | DOM component patterns, HTML structure, class fingerprints |
| `references/INTERACTIONS.md` | Hover/focus states with before/after style diffs |
| `screens/scroll/` | 7 scroll journey screenshots showing cinematic states |

## Design Philosophy

- **Solid colors only** — no gradients anywhere. Every surface is a single flat color.
- **Single typeface** — Nanum Myeongjo carries all text. Hierarchy comes from size, weight, and color — never font mixing.
- **standard density** — 5px base grid. Every dimension is a multiple of 5.
- **neutral palette** — the color temperature runs neutral, matching the monospace typography.
- **Minimal motion** — prefer instant state changes. Only use transitions for loading and page transitions.

## Color System

### Core Palette

| Role | Token | Hex | Use |
|------|-------|-----|-----|
| Background | `--background` | `#ffffff` | Page/app background |
| Text Primary | `--text-primary` | `#000000` | Headings, body text |

### Extended Palette

- `#0000ee`

### CSS Variable Tokens

```css
--border-bottom-width: 1px;
--border-color: #000;
--border-left-width: 1px;
--border-right-width: 1px;
--border-style: solid;
--border-top-width: 1px;
--framer-text-background-color: initial;
--framer-text-background-radius: initial;
--framer-text-background-corner-shape: initial;
--framer-text-background-padding: initial;
```

## Typography

### Font Stack

- **Nanum Myeongjo** — Heading 1, Heading 2, Heading 3
- **IBM Plex Mono** — Body, Caption, Code

### Font Sources

```css
@font-face {
  font-family: "IBM Plex Mono";
  src: url("fonts/IBMPlexMono-Bold.ttf") format("truetype");
  font-weight: 700;
}
@font-face {
  font-family: "IBM Plex Mono";
  src: url("fonts/IBMPlexMono-Regular.ttf") format("truetype");
  font-weight: 400;
}
@font-face {
  font-family: "Nanum Myeongjo";
  src: url("fonts/NanumMyeongjo-Bold.ttf") format("truetype");
  font-weight: 700;
}
@font-face {
  font-family: "Nanum Myeongjo";
  src: url("fonts/NanumMyeongjo-Regular.ttf") format("truetype");
  font-weight: 400;
}
@font-face {
  font-family: "Inter";
  src: url("fonts/Inter-Bold.ttf") format("truetype");
  font-weight: 700;
}
@font-face {
  font-family: "Inter";
  src: url("fonts/Inter-Regular.ttf") format("truetype");
  font-weight: 400;
}
```

### Type Scale

| Role | Family | Size | Weight |
|------|--------|------|--------|
| Heading 1 | Nanum Myeongjo | calc(var(--framer-blockquote-font-size,var(--framer-font-size,16px))*var(--framer-font-size-scale,1)) | 700 |
| Heading 2 | Nanum Myeongjo | calc(var(--framer-link-hover-font-size,var(--framer-blockquote-font-size,var(--framer-font-size,16px)))*var(--framer-font-size-scale,1)) | 700 |
| Heading 3 | Nanum Myeongjo | calc(var(--framer-link-current-font-size,var(--framer-link-font-size,var(--framer-font-size,16px)))*var(--framer-font-size-scale,1)) | 700 |
| Body | IBM Plex Mono | calc(var(--framer-link-hover-font-size,var(--framer-link-current-font-size,var(--framer-link-font-size,var(--framer-font-size,16px))))*var(--framer-font-size-scale,1)) | 400 |
| Caption | IBM Plex Mono | var(--framer-font-size,16px) | 400 |
| Code | IBM Plex Mono | 14px | 400 |

### Typography Rules

- All text uses **Nanum Myeongjo** — never add another font family
- Max 3-4 font sizes per screen
- Headings: weight 600-700, body: weight 400
- Use color and opacity for text hierarchy, not additional font sizes
- Line height: 1.5 for body, 1.2 for headings

## Spacing & Layout

### Base Grid: 5px

Every dimension (margin, padding, gap, width, height) must be a multiple of **5px**.

### Spacing Scale

`5, 10, 20, 25, 30, 40, 50, 60, 70, 80, 100` px

### Spacing as Meaning

| Spacing | Use |
|---------|-----|
| 2.5-5px | Tight: related items within a group |
| 10px | Medium: between groups |
| 15-20px | Wide: between sections |
| 30px+ | Vast: major section breaks |

### Border Radius

Scale: `40px, inherit, 26px`
Default: `inherit`

### Container

Max-width: `1199.98px`, centered with auto margins.

### Breakpoints

| Name | Value |
|------|-------|
| lg | 809px |
| lg | 809.98px |
| lg | 810px |
| xl | 1199px |
| xl | 1199.98px |
| xl | 1200px |
| 2xl | 1439px |
| 2xl | 1439.98px |
| 2xl | 1440px |
| 2xl | 1599px |
| 2xl | 1600px |
| 2xl | 1799px |
| 2xl | 1800px |
| 2xl | 2099px |

Mobile-first: design for small screens, layer on responsive overrides.

## Component Patterns

### Card

```css
.card {
  background: #ffffff;
  border-radius: inherit;
  padding: 20px;
}
```

```html
<div class="card">
  <h3>Card Title</h3>
  <p>Card content goes here.</p>
</div>
```

### Button

```css
/* Primary */
.btn-primary {
  background: #cccccc;
  color: #000000;
  border-radius: inherit;
  padding: 10px 20px;
  font-weight: 500;
  transition: opacity 150ms ease;
}
.btn-primary:hover { opacity: 0.9; }

/* Ghost */
.btn-ghost {
  background: transparent;
  border: 1px solid #cccccc;
  color: #000000;
  border-radius: inherit;
  padding: 10px 20px;
}
```

```html
<button class="btn-primary">Get Started</button>
<button class="btn-ghost">Learn More</button>
```

### Input

```css
.input {
  background: #ffffff;
  border: 1px solid #cccccc;
  border-radius: inherit;
  padding: 10px 10px;
  color: #000000;
  font-size: 14px;
}
.input:focus { border-color: var(--accent); outline: none; }
```

```html
<input class="input" type="text" placeholder="Search..." />
```

### Badge / Chip

```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 5px 10px;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 500;
  background: #ffffff;
  color: #000000;
}
```

```html
<span class="badge">New</span>
<span class="badge">Beta</span>
```

### Modal / Dialog

```css
.modal-backdrop { background: rgba(0, 0, 0, 0.6); }
.modal {
  background: #ffffff;
  border-radius: 26px;
  padding: 30px;
  max-width: 480px;
  width: 90vw;
}
```

```html
<div class="modal-backdrop">
  <div class="modal">
    <h2>Dialog Title</h2>
    <p>Dialog content.</p>
    <button class="btn-primary">Confirm</button>
    <button class="btn-ghost">Cancel</button>
  </div>
</div>
```

### Table

```css
.table { width: 100%; border-collapse: collapse; }
.table th {
  text-align: left;
  padding: 10px 10px;
  font-weight: 500;
  font-size: 12px;
  color: #000000;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #cccccc;
}
.table td {
  padding: 10px;
  border-bottom: 1px solid #cccccc;
}
```

```html
<table class="table">
  <thead><tr><th>Name</th><th>Status</th><th>Date</th></tr></thead>
  <tbody>
    <tr><td>Item One</td><td>Active</td><td>Jan 1</td></tr>
    <tr><td>Item Two</td><td>Pending</td><td>Jan 2</td></tr>
  </tbody>
</table>
```

### Navigation

```css
.nav {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
}
.nav-link {
  color: #000000;
  padding: 10px 10px;
  border-radius: inherit;
  transition: color 150ms;
}
.nav-link:hover { color: #000000; }
```

```html
<nav class="nav">
  <a href="/" class="nav-link active">Home</a>
  <a href="/about" class="nav-link">About</a>
  <a href="/pricing" class="nav-link">Pricing</a>
  <button class="btn-primary" style="margin-left: auto">Get Started</button>
</nav>
```

## Page Structure

The following page sections were detected:

- **Hero** — Hero section (detected from heading structure)
- **Faq** — FAQ/accordion section

When building pages, follow this section order and structure.

## Animation & Motion

This project uses **subtle motion**. Transitions smooth state changes without calling attention.

### Motion Guidelines

- **Duration:** 150-300ms for micro-interactions, 300-500ms for page transitions
- **Easing:** `ease-out` for enters, `ease-in` for exits
- **Direction:** Elements enter from bottom/right, exit to top/left
- **Reduced motion:** Always respect `prefers-reduced-motion` — disable animations when set

## Depth & Elevation

This design uses **flat elevation** — no box-shadows anywhere.

### Elevation Strategy

| Level | Technique | Use |
|-------|-----------|-----|
| 0 — Base | Background color | Page background |
| 1 — Raised | Lighter surface + subtle border | Cards, panels |
| 2 — Floating | Even lighter surface + stronger border | Dropdowns, popovers |
| 3 — Overlay | Backdrop + modal surface | Modals, dialogs |

### Z-Index Scale

`0, 1`

Use these exact values — never invent z-index values.

## Anti-Patterns (Never Do)

- **No box-shadow** on any element — use borders and surface colors for depth
- **No gradients** — solid colors only, everywhere
- **No blur effects** — no backdrop-blur, no filter: blur()
- **No zebra striping** — tables and lists use borders for separation
- **No invented colors** — every hex value must come from the palette above
- **No arbitrary spacing** — every dimension is a multiple of 5px
- **No extra fonts** — only Nanum Myeongjo and IBM Plex Mono are allowed
- **No arbitrary border-radius** — use the scale: 40px, 26px
- **No opacity for disabled states** — use muted colors instead
- **No pill shapes** — this design doesn't use rounded-full / 9999px radius

## Workflow

1. **Read** `references/DESIGN.md` before writing any UI code
2. **Pick colors** from the Color System section — never invent new ones
3. **Set typography** — Nanum Myeongjo, IBM Plex Mono only, using the type scale
4. **Build layout** on the 5px grid — check every margin, padding, gap
5. **Match components** to patterns above before creating new ones
6. **Apply elevation** — flat, surface color shifts only
7. **Validate** — every value traces back to a design token. No magic numbers.

## Brand Spec

- **Favicon:** `https://framerusercontent.com/images/zcTQ3MIvizCSVRO01WdKpi8XLk.png`
- **Site URL:** `https://interludeapp.net`
- **Brand typeface:** Nanum Myeongjo

## Quick Reference

```
Background:     #ffffff
Surface:        (not extracted)
Text:           #000000 / (not extracted)
Accent:         (not extracted)
Border:         (not extracted)
Font:           Nanum Myeongjo
Spacing:        5px grid
Radius:         inherit
Components:     1 detected
```

## When to Trigger

Activate this skill when:
- Creating new components, pages, or visual elements for interludeapp
- Writing CSS, Tailwind classes, styled-components, or inline styles
- Building page layouts, templates, or responsive designs
- Reviewing UI code for design consistency
- The user mentions "interludeapp" design, style, UI, or theme
- Generating mockups, wireframes, or visual prototypes

---

# Full Reference Files

> Every output file is embedded below. Claude has full design system context from /skills alone.

## Design System Tokens (DESIGN.md)

# interludeapp DESIGN.md

> Auto-generated design system — reverse-engineered via static analysis by skillui.
> Frameworks: None detected
> Colors: 3 · Fonts: 2 · Components: 1
> Icon library: not detected · State: not detected
> Primary theme: light · Dark mode toggle: no · Motion: none

## Visual Reference

**Match this design exactly** — study colors, fonts, spacing, and component shapes before writing any UI code.

![interludeapp Homepage](../screenshots/homepage.png)

---

## 1. Visual Theme & Atmosphere

This is a **light-themed** interface with a neutral, approachable feel. The light background emphasizes content clarity. Typography uses **Nanum Myeongjo** throughout — a technical, developer-focused choice that maintains consistency. Spacing follows a **5px base grid** (standard density), with scale: 5, 10, 20, 25, 30, 40, 50, 60px.

---

## 2. Color Palette & Roles

| Token | Hex | Role | Use |
|---|---|---|---|
| background | `#ffffff` | background | Page background, darkest surface |
| border-color | `#000000` | text-primary | Headings and body text |
| info | `#0000ee` | info | Informational highlights |

### CSS Variable Tokens

```css
--border-bottom-width: 1px;
--border-color: #000;
--border-left-width: 1px;
--border-right-width: 1px;
--border-style: solid;
--border-top-width: 1px;
--framer-text-background-color: initial;
--framer-text-background-radius: initial;
--framer-text-background-corner-shape: initial;
--framer-text-background-padding: initial;
```


---

## 3. Typography Rules

**Font Stack:**
- **Nanum Myeongjo** — Heading 1, Heading 2, Heading 3
- **IBM Plex Mono** — Body, Caption, Code

**Font Sources:**

```css
@font-face {
  font-family: "IBM Plex Mono";
  src: url("fonts/IBMPlexMono-Bold.ttf") format("truetype");
  font-weight: 700;
}
@font-face {
  font-family: "IBM Plex Mono";
  src: url("fonts/IBMPlexMono-Regular.ttf") format("truetype");
  font-weight: 400;
}
@font-face {
  font-family: "Nanum Myeongjo";
  src: url("fonts/NanumMyeongjo-Bold.ttf") format("truetype");
  font-weight: 700;
}
@font-face {
  font-family: "Nanum Myeongjo";
  src: url("fonts/NanumMyeongjo-Regular.ttf") format("truetype");
  font-weight: 400;
}
@font-face {
  font-family: "Inter";
  src: url("fonts/Inter-Bold.ttf") format("truetype");
  font-weight: 700;
}
@font-face {
  font-family: "Inter";
  src: url("fonts/Inter-Regular.ttf") format("truetype");
  font-weight: 400;
}
```

| Role | Font | Size | Weight |
|---|---|---|---|
| Heading 1 | Nanum Myeongjo | calc(var(--framer-blockquote-font-size,var(--framer-font-size,16px))*var(--framer-font-size-scale,1)) | 700 |
| Heading 2 | Nanum Myeongjo | calc(var(--framer-link-hover-font-size,var(--framer-blockquote-font-size,var(--framer-font-size,16px)))*var(--framer-font-size-scale,1)) | 700 |
| Heading 3 | Nanum Myeongjo | calc(var(--framer-link-current-font-size,var(--framer-link-font-size,var(--framer-font-size,16px)))*var(--framer-font-size-scale,1)) | 700 |
| Body | IBM Plex Mono | calc(var(--framer-link-hover-font-size,var(--framer-link-current-font-size,var(--framer-link-font-size,var(--framer-font-size,16px))))*var(--framer-font-size-scale,1)) | 400 |
| Caption | IBM Plex Mono | var(--framer-font-size,16px) | 400 |
| Code | IBM Plex Mono | 14px | 400 |

**Typographic Rules:**
- Use **Nanum Myeongjo** for all text — do not mix font families
- Maintain consistent hierarchy: no more than 3-4 font sizes per screen
- Headings use bold (600-700), body uses regular (400)
- Line height: 1.5 for body text, 1.2 for headings
- Use color and opacity for secondary hierarchy, not additional font sizes


---

## 4. Component Stylings

### Media (1)

**Image** — `html`



---

## 5. Layout Principles

- **Base spacing unit:** 5px
- **Spacing scale:** 5, 10, 20, 25, 30, 40, 50, 60, 70, 80, 100
- **Border radius:** 40px, inherit, 26px
- **Max content width:** 1199.98px

**Spacing as Meaning:**
| Spacing | Use |
|---|---|
| 2.5-5px | Tight: related items within a group |
| 10px | Medium: between groups |
| 15-20px | Wide: between sections |
| 30px+ | Vast: major section breaks |


---

## 6. Depth & Elevation

No box-shadow values detected. The design appears to use a flat visual style.

**Z-Index Scale:** `0, 1`


---

## 8. Do's and Don'ts

### Do's

- Use `#ffffff` as the primary page background
- Use **Nanum Myeongjo** for all UI text
- Follow the **5px** spacing grid for all margins, padding, and gaps
- Use border and background shifts for elevation — not shadows
- Use border-radius from the scale: 40px, inherit, 26px
- Reuse existing components from Section 4 before creating new ones

### Don'ts

- Don't introduce colors outside this palette — extend the design tokens first
- Don't mix font families — use Nanum Myeongjo consistently
- Don't use arbitrary spacing values — stick to multiples of 5px
- Don't add box-shadow — this design system uses flat elevation
- Don't use gradients — the design uses solid colors only
- Don't use arbitrary border-radius values — pick from the defined scale
- Don't duplicate component patterns — check Section 4 first
- Don't use backdrop-blur or blur effects

### Anti-Patterns (detected from codebase)

- No box-shadow on any element
- No gradient backgrounds
- No blur or backdrop-blur effects
- No zebra striping on tables/lists


---

## 9. Responsive Behavior

| Name | Value | Source |
|---|---|---|
| lg | 809px | css |
| lg | 809.98px | css |
| lg | 810px | css |
| xl | 1199px | css |
| xl | 1199.98px | css |
| xl | 1200px | css |
| 2xl | 1439px | css |
| 2xl | 1439.98px | css |
| 2xl | 1440px | css |
| 2xl | 1599px | css |
| 2xl | 1600px | css |
| 2xl | 1799px | css |
| 2xl | 1800px | css |
| 2xl | 2099px | css |

**Approach:** Use `@media (min-width: ...)` queries matching the breakpoints above.


---

## 10. Agent Prompt Guide

Use these as starting points when building new UI:

### Build a Card

```
Background: #ffffff
Border: 1px solid var(--border)
Radius: inherit
Padding: 20px
Font: Nanum Myeongjo
No shadows — use borders and surface colors for depth.
```

### Build a Button

```
Primary: bg var(--accent), text white
Ghost: bg transparent, border var(--border)
Padding: 10px 20px
Radius: inherit
Hover: opacity 0.9 or lighter shade
Focus: ring with var(--accent)
```

### Build a Page Layout

```
Background: #ffffff
Max-width: 1199.98px, centered
Grid: 5px base
Responsive: mobile-first, breakpoints from Section 9
```

### Build a Stats Card

```
Surface: #ffffff
Label: var(--text-muted) (muted, 12px, uppercase)
Value: #000000 (primary, 24-32px, bold)
Status: use success/warning/danger from Section 2
```

### Build a Form

```
Input bg: #ffffff
Input border: 1px solid var(--border)
Focus: border-color var(--accent)
Label: var(--text-muted) 12px
Spacing: 20px between fields
Radius: inherit
```

### General Component

```
1. Read DESIGN.md Sections 2-6 for tokens
2. Colors: only from palette
3. Font: Nanum Myeongjo, type scale from Section 3
4. Spacing: 5px grid
5. Components: match patterns from Section 4
6. Elevation: flat, surface shifts
```

## Visual Guide — Screenshots (VISUAL_GUIDE.md)

# interludeapp — Visual Guide

> Master visual reference. Study every screenshot carefully before implementing any UI.
> Match colors, layout, typography, spacing, and motion states exactly.

## Scroll Journey

The page has cinematic scroll animations. Each screenshot below shows the exact visual state at that scroll depth.
**Replicate these transitions precisely** — the design changes dramatically as you scroll.

### Hero — Above the fold

*Scroll position: 0px of 5602px total*

![Hero — Above the fold](../screens/scroll/scroll-000.png)

### 17% scroll depth

*Scroll position: 799px of 5602px total*

![17% scroll depth](../screens/scroll/scroll-017.png)

### 33% scroll depth

*Scroll position: 1552px of 5602px total*

![33% scroll depth](../screens/scroll/scroll-033.png)

### 50% scroll depth

*Scroll position: 2351px of 5602px total*

![50% scroll depth](../screens/scroll/scroll-050.png)

### 67% scroll depth

*Scroll position: 3150px of 5602px total*

![67% scroll depth](../screens/scroll/scroll-067.png)

### 83% scroll depth

*Scroll position: 3903px of 5602px total*

![83% scroll depth](../screens/scroll/scroll-083.png)

### Footer — End of page

*Scroll position: 4702px of 5602px total*

![Footer — End of page](../screens/scroll/scroll-100.png)

## Video Backgrounds

These videos play as background elements. Use first-frame as poster image while video loads.

### Video 1 (content)

*Source: `https://framerusercontent.com/assets/iXftkIHRWyygk1gHpsrKZBQSauQ.mp4...`*

![Video 1 first frame](../screens/scroll/video-1-frame.png)

## Full Page Screenshots

### Interlude

*URL: `https://interludeapp.net`*

![Interlude](../screens/pages/home.png)

## Animations & Motion (ANIMATIONS.md)

# Animation Reference

> Cinematic motion design extracted from live DOM. Follow these specs exactly to recreate the experience.

## Motion Technology Stack

Pure CSS animations — no external animation libraries detected.

## Scroll Journey

The page is **5,602px** tall. Each frame below shows what the user sees at that scroll depth.

> **Use these screenshots to understand WHAT animates, WHEN it animates, and HOW it moves.**

### 0% — Top / Hero
Scroll position: 0px

![Scroll 0%](../screens/scroll/scroll-000.png)

### 17% — Opening Section
Scroll position: 799px

![Scroll 17%](../screens/scroll/scroll-017.png)

### 33% — First Feature Section
Scroll position: 1,552px

![Scroll 33%](../screens/scroll/scroll-033.png)

### 50% — Mid-Page
Scroll position: 2,351px

![Scroll 50%](../screens/scroll/scroll-050.png)

### 67% — Lower Content
Scroll position: 3,150px

![Scroll 67%](../screens/scroll/scroll-067.png)

### 83% — Near Footer
Scroll position: 3,903px

![Scroll 83%](../screens/scroll/scroll-083.png)

### 100% — Bottom / Footer
Scroll position: 4,702px

![Scroll 100%](../screens/scroll/scroll-100.png)

## Video Elements

| # | Role | Autoplay | Loop | Muted | Size | First Frame |
|---|------|----------|------|-------|------|-------------|
| 1 | content | ✓ | ✓ | ✓ | 312×682 | [view](../screens/scroll/video-1-frame.png) |

**Video 1 first frame:**

![Video 1 Frame](../screens/scroll/video-1-frame.png)

- **Source:** `https://framerusercontent.com/assets/iXftkIHRWyygk1gHpsrKZBQSauQ.mp4`

## CSS Keyframes (1 extracted)

### `@keyframes __framer-loading-spin`

Duration: `800ms` · Easing: `linear` · Iteration: `infinite`

Used by: `#__framer-editorbar-loading-spinner`

```css
@keyframes __framer-loading-spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}
```

> Transform/motion animation

## Global Transition Declarations

These `transition` values were extracted from CSS rules across the site:

```css
transition: opacity 0.4s ease-out;
transition: unset;
```

## How to Recreate This Motion Design

### Step 2 — Scroll-Reveal Pattern

Elements that animate into view follow this pattern:

```css
/* Initial hidden state */
.reveal {
  opacity: 0;
  transform: translateY(40px);
  transition: opacity 0.4s cubic-bezier(0.4, 0, 0.2, 1),
              transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.reveal.visible {
  opacity: 1;
  transform: translateY(0);
}
```

### Step 3 — Key Motion Principles

- **Duration scale:** `0.4s` — use these values, never invent new durations
- **Always add** `@media (prefers-reduced-motion: reduce) { * { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; } }`

### Step 4 — Scroll Journey Reference

Match what happens at each scroll position:

- **0%** (`0px`) → `screens/scroll/scroll-000.png`
- **17%** (`799px`) → `screens/scroll/scroll-017.png`
- **33%** (`1552px`) → `screens/scroll/scroll-033.png`
- **50%** (`2351px`) → `screens/scroll/scroll-050.png`
- **67%** (`3150px`) → `screens/scroll/scroll-067.png`
- **83%** (`3903px`) → `screens/scroll/scroll-083.png`
- **100%** (`4702px`) → `screens/scroll/scroll-100.png`

## Layout & Grid (LAYOUT.md)

# Layout Reference

> Auto-extracted from live DOM. Use this to understand how the site is structured spatially.

## Spacing System

**Base grid:** 5px

**Scale:** `5, 10, 20, 25, 30, 40, 50, 60, 70, 80, 100` px

| Spacing | Semantic Use |
|---------|-------------|
| 5px | Tight — within a component |
| 10px | Medium — between sibling items |
| 20px | Wide — between sections |
| 40px | Vast — major section breaks |

## Layout Rules

- Every spacing value must be a multiple of **5px**
- Never use arbitrary margin/padding values outside the spacing scale

## Component Patterns (COMPONENTS.md)

# Component Reference

> Repeated DOM patterns detected by structural analysis. Each component appeared 3+ times.

## Detected Components

| Component | Category | Instances | Key Classes |
|-----------|----------|-----------|-------------|
| **Framer Styles Preset 1jwr960** | unknown | 5× | `.framer-styles-preset-1jwr960`, `.framer-text` |

## Other Components

### Framer Styles Preset 1jwr960

**Instances found:** 5

**CSS classes:** `.framer-styles-preset-1jwr960` `.framer-text`

**HTML structure:**

```html
<p class="framer-text framer-styles-preset-1jwr960" data-styles-preset="aAztYuv2o" style="--framer-text-alignment:center">Interlude is a shared canvas where strangers draw light trails. Everything fades within seconds. You draw with your finger. Others around the world draw too. Their trails appear as white light on your screen. When your light touches theirs, both phones vibrate softly.</p>
```

**Base styles (from design tokens):**

```css
.framer-styles-preset-1jwr960 {
  padding: 5px;
}```

## Component Rules

- Match class names exactly from the patterns above
- Each component instance must be visually identical to others of its type
- Do not add extra wrappers or change the DOM structure

## Interactions & States (INTERACTIONS.md)

# Interaction Reference

> Micro-interactions extracted from live DOM. Recreate these exactly for authentic feel.

## Coverage

| Component Type | Count | States Captured |
|----------------|-------|----------------|
| Link | 3 | default, hover, focus |

## Transition System

These transition declarations were extracted from interactive elements:

```css
transition: all;
```

Apply these to all interactive elements. Never invent new durations or easings.

## Link Interactions

### Link 1 — `DOWNLOAD APP NOW`

**States:**

- Default: `../screens/states/link-1-default.png`
- Hover: `../screens/states/link-1-hover.png`
- Focus: `../screens/states/link-1-focus.png`

**On focus:**

```css
/* outline: rgb(0, 0, 238) none 3px → */ outline: rgb(0, 95, 204) auto 1px;
/* outline-color: rgb(0, 0, 238) → */ outline-color: rgb(0, 95, 204);
```

**Transition:** `all`

### Link 2 — `a`

**States:**

- Default: `../screens/states/link-2-default.png`
- Hover: `../screens/states/link-2-hover.png`
- Focus: `../screens/states/link-2-focus.png`

**On focus:**

```css
/* outline: rgb(0, 0, 238) none 3px → */ outline: rgb(0, 95, 204) auto 1px;
/* outline-color: rgb(0, 0, 238) → */ outline-color: rgb(0, 95, 204);
```

**Transition:** `all`

### Link 3 — `MADE BY SIDDHARTH`

**States:**

- Default: `../screens/states/link-3-default.png`
- Hover: `../screens/states/link-3-hover.png`
- Focus: `../screens/states/link-3-focus.png`

**On focus:**

```css
/* outline: rgb(0, 0, 0) none 3px → */ outline: rgb(0, 95, 204) auto 1px;
/* outline-color: rgb(0, 0, 0) → */ outline-color: rgb(0, 95, 204);
```

**Transition:** `all`

## Interaction Rules

- Focus states use **outline** (not box-shadow) — always match the extracted focus ring
- Always respect `prefers-reduced-motion` — set all transitions to `0s` when enabled

## Design Tokens — JSON Files

### tokens/colors.json
```json
{
  "$schema": "https://design-tokens.github.io/community-group/format/",
  "core": {
    "text-primary": {
      "value": "#000000",
      "role": "text-primary",
      "name": "border-color"
    },
    "background": {
      "value": "#ffffff",
      "role": "background"
    }
  },
  "status": {},
  "extended": {
    "color-0000ee": {
      "value": "#0000ee",
      "role": "info"
    }
  },
  "meta": {
    "theme": "light",
    "extracted": "2026-04-17"
  }
}
```

### tokens/spacing.json
```json
{
  "base": {
    "value": "5px",
    "description": "Grid unit — all spacing must be multiples of this"
  },
  "unit": "px",
  "scale": {
    "xs": {
      "value": "5px",
      "px": 5
    },
    "sm": {
      "value": "10px",
      "px": 10
    },
    "md": {
      "value": "20px",
      "px": 20
    },
    "lg": {
      "value": "25px",
      "px": 25
    },
    "xl": {
      "value": "30px",
      "px": 30
    },
    "2xl": {
      "value": "40px",
      "px": 40
    },
    "3xl": {
      "value": "50px",
      "px": 50
    },
    "4xl": {
      "value": "60px",
      "px": 60
    },
    "5xl": {
      "value": "70px",
      "px": 70
    },
    "6xl": {
      "value": "80px",
      "px": 80
    }
  },
  "multipliers": {
    "1x": {
      "value": "5px",
      "raw": 5
    },
    "2x": {
      "value": "10px",
      "raw": 10
    },
    "3x": {
      "value": "15px",
      "raw": 15
    },
    "4x": {
      "value": "20px",
      "raw": 20
    },
    "5x": {
      "value": "25px",
      "raw": 25
    },
    "6x": {
      "value": "30px",
      "raw": 30
    },
    "7x": {
      "value": "35px",
      "raw": 35
    },
    "8x": {
      "value": "40px",
      "raw": 40
    },
    "9x": {
      "value": "45px",
      "raw": 45
    },
    "10x": {
      "value": "50px",
      "raw": 50
    },
    "11x": {
      "value": "55px",
      "raw": 55
    },
    "12x": {
      "value": "60px",
      "raw": 60
    },
    "13x": {
      "value": "65px",
      "raw": 65
    },
    "14x": {
      "value": "70px",
      "raw": 70
    },
    "15x": {
      "value": "75px",
      "raw": 75
    },
    "16x": {
      "value": "80px",
      "raw": 80
    }
  },
  "meta": {
    "totalValues": 11,
    "min": 5,
    "max": 100
  }
}
```

### tokens/typography.json
```json
{
  "families": [
    "Nanum Myeongjo",
    "IBM Plex Mono"
  ],
  "scale": {
    "heading-1": {
      "fontFamily": "Nanum Myeongjo",
      "fontSize": "calc(var(--framer-blockquote-font-size,var(--framer-font-size,16px))*var(--framer-font-size-scale,1))",
      "fontWeight": "700",
      "lineHeight": null,
      "source": "css"
    },
    "heading-2": {
      "fontFamily": "Nanum Myeongjo",
      "fontSize": "calc(var(--framer-link-hover-font-size,var(--framer-blockquote-font-size,var(--framer-font-size,16px)))*var(--framer-font-size-scale,1))",
      "fontWeight": "700",
      "lineHeight": null,
      "source": "css"
    },
    "heading-3": {
      "fontFamily": "Nanum Myeongjo",
      "fontSize": "calc(var(--framer-link-current-font-size,var(--framer-link-font-size,var(--framer-font-size,16px)))*var(--framer-font-size-scale,1))",
      "fontWeight": "700",
      "lineHeight": null,
      "source": "css"
    },
    "body": {
      "fontFamily": "IBM Plex Mono",
      "fontSize": "calc(var(--framer-link-hover-font-size,var(--framer-link-current-font-size,var(--framer-link-font-size,var(--framer-font-size,16px))))*var(--framer-font-size-scale,1))",
      "fontWeight": "400",
      "lineHeight": null,
      "source": "css"
    },
    "caption": {
      "fontFamily": "IBM Plex Mono",
      "fontSize": "var(--framer-font-size,16px)",
      "fontWeight": "400",
      "lineHeight": null,
      "source": "css"
    },
    "code": {
      "fontFamily": "IBM Plex Mono",
      "fontSize": "14px",
      "fontWeight": "400",
      "lineHeight": null,
      "source": "css"
    }
  },
  "fontFaces": [
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6pfjptAgt5VM-kVkqdyU8n1ioa2Hdgv-s.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6pfjptAgt5VM-kVkqdyU8n1ioa0Xdgv-s.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6pfjptAgt5VM-kVkqdyU8n1ioa2ndgv-s.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6pfjptAgt5VM-kVkqdyU8n1ioa23dgv-s.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6pfjptAgt5VM-kVkqdyU8n1ioa1Xdg.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6sfjptAgt5VM-kVkqdyU8n1ioSJlR1jcoQLNg.woff2",
      "format": "woff2",
      "weight": "500"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6sfjptAgt5VM-kVkqdyU8n1ioSJlR1hMoQLNg.woff2",
      "format": "woff2",
      "weight": "500"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6sfjptAgt5VM-kVkqdyU8n1ioSJlR1j8oQLNg.woff2",
      "format": "woff2",
      "weight": "500"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6sfjptAgt5VM-kVkqdyU8n1ioSJlR1jsoQLNg.woff2",
      "format": "woff2",
      "weight": "500"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6sfjptAgt5VM-kVkqdyU8n1ioSJlR1gMoQ.woff2",
      "format": "woff2",
      "weight": "500"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6sfjptAgt5VM-kVkqdyU8n1ioSblJ1jcoQLNg.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6sfjptAgt5VM-kVkqdyU8n1ioSblJ1hMoQLNg.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6sfjptAgt5VM-kVkqdyU8n1ioSblJ1j8oQLNg.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6sfjptAgt5VM-kVkqdyU8n1ioSblJ1jsoQLNg.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6sfjptAgt5VM-kVkqdyU8n1ioSblJ1gMoQ.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6qfjptAgt5VM-kVkqdyU8n3oQIwl1FgtIU.woff2",
      "format": "woff2",
      "weight": "300"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6qfjptAgt5VM-kVkqdyU8n3oQIwlRFgtIU.woff2",
      "format": "woff2",
      "weight": "300"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6qfjptAgt5VM-kVkqdyU8n3oQIwl9FgtIU.woff2",
      "format": "woff2",
      "weight": "300"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6qfjptAgt5VM-kVkqdyU8n3oQIwl5FgtIU.woff2",
      "format": "woff2",
      "weight": "300"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6qfjptAgt5VM-kVkqdyU8n3oQIwlBFgg.woff2",
      "format": "woff2",
      "weight": "300"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F63fjptAgt5VM-kVkqdyU8n1iIq129k.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F63fjptAgt5VM-kVkqdyU8n1isq129k.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F63fjptAgt5VM-kVkqdyU8n1iAq129k.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F63fjptAgt5VM-kVkqdyU8n1iEq129k.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F63fjptAgt5VM-kVkqdyU8n1i8q1w.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6qfjptAgt5VM-kVkqdyU8n3twJwl1FgtIU.woff2",
      "format": "woff2",
      "weight": "500"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6qfjptAgt5VM-kVkqdyU8n3twJwlRFgtIU.woff2",
      "format": "woff2",
      "weight": "500"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6qfjptAgt5VM-kVkqdyU8n3twJwl9FgtIU.woff2",
      "format": "woff2",
      "weight": "500"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6qfjptAgt5VM-kVkqdyU8n3twJwl5FgtIU.woff2",
      "format": "woff2",
      "weight": "500"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6qfjptAgt5VM-kVkqdyU8n3twJwlBFgg.woff2",
      "format": "woff2",
      "weight": "500"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6qfjptAgt5VM-kVkqdyU8n3pQPwl1FgtIU.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6qfjptAgt5VM-kVkqdyU8n3pQPwlRFgtIU.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6qfjptAgt5VM-kVkqdyU8n3pQPwl9FgtIU.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6qfjptAgt5VM-kVkqdyU8n3pQPwl5FgtIU.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "IBM Plex Mono",
      "src": "https://fonts.gstatic.com/s/ibmplexmono/v20/-F6qfjptAgt5VM-kVkqdyU8n3pQPwlBFgg.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.0.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.2.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.3.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.4.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.5.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.6.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.7.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.8.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.9.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.10.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.11.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.12.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.13.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.14.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.15.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.16.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.17.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.18.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.19.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.20.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.21.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.22.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.23.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.24.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.25.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.26.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.27.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.28.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.29.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.30.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.31.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.32.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.33.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.34.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.35.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.36.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.37.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.38.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.39.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.40.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.41.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.42.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.43.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.44.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.45.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.46.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.47.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.48.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.49.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.50.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.51.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.52.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.53.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.54.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.55.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.56.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.57.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.58.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.59.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.60.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.61.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.62.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.63.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.64.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.65.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.94.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.95.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.96.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.97.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.98.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.99.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.100.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.101.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.102.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.103.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.104.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.105.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.106.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.107.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.108.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.109.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.110.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.111.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.112.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.113.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.114.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.115.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.116.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.117.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.118.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy1LuEGI-gZ_Ll9dMHVruCTvHYAnNT2g.119.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Btx3DZF0dXLMZlywRbVRNhxy2LscnU.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.0.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.2.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.3.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.4.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.5.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.6.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.7.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.8.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.9.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.10.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.11.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.12.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.13.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.14.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.15.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.16.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.17.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.18.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.19.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.20.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.21.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.22.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.23.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.24.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.25.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.26.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.27.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.28.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.29.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.30.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.31.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.32.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.33.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.34.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.35.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.36.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.37.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.38.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.39.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.40.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.41.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.42.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.43.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.44.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.45.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.46.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.47.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.48.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.49.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.50.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.51.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.52.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.53.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.54.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.55.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.56.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.57.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.58.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.59.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.60.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.61.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.62.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.63.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.64.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.65.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.94.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.95.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.96.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.97.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.98.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.99.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.100.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.101.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.102.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.103.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.104.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.105.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.106.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.107.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.108.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.109.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.110.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.111.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.112.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.113.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.114.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.115.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.116.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.117.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.118.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV1Axzeau69lCAWDrAgLCcAPYKgRK4K8.119.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Nanum Myeongjo",
      "src": "https://fonts.gstatic.com/s/nanummyeongjo/v31/9Bty3DZF0dXLMZlywRbVRNhxy2pXV2Azr_E.woff2",
      "format": "woff2",
      "weight": "700"
    },
    {
      "family": "Inter",
      "src": "https://framerusercontent.com/assets/5vvr9Vy74if2I6bQbJvbw7SY1pQ.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Inter",
      "src": "https://framerusercontent.com/assets/EOr0mi4hNtlgWNn9if640EZzXCo.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Inter",
      "src": "https://framerusercontent.com/assets/Y9k9QrlZAqio88Klkmbd8VoMQc.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Inter",
      "src": "https://framerusercontent.com/assets/OYrD2tBIBPvoJXiIHnLoOXnY9M.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Inter",
      "src": "https://framerusercontent.com/assets/JeYwfuaPfZHQhEG8U5gtPDZ7WQ.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Inter",
      "src": "https://framerusercontent.com/assets/GrgcKwrN6d3Uz8EwcLHZxwEfC4.woff2",
      "format": "woff2",
      "weight": "400"
    },
    {
      "family": "Inter",
      "src": "https://framerusercontent.com/assets/b6Y37FthZeALduNqHicBT6FutY.woff2",
      "format": "woff2",
      "weight": "400"
    }
  ],
  "rules": {
    "maxSizesPerScreen": 4,
    "headingWeightRange": "600-700",
    "bodyWeight": 400,
    "lineHeightBody": 1.5,
    "lineHeightHeading": 1.2
  }
}
```

## Bundled Fonts (fonts/)

The following font files are bundled in the `fonts/` directory:

- `fonts/IBMPlexMono-Bold.ttf`
- `fonts/IBMPlexMono-ExtraLight.ttf`
- `fonts/IBMPlexMono-Light.ttf`
- `fonts/IBMPlexMono-Medium.ttf`
- `fonts/IBMPlexMono-Regular.ttf`
- `fonts/IBMPlexMono-SemiBold.ttf`
- `fonts/IBMPlexMono-Thin.ttf`
- `fonts/Inter-Black.ttf`
- `fonts/Inter-Bold.ttf`
- `fonts/Inter-ExtraBold.ttf`
- `fonts/Inter-ExtraLight.ttf`
- `fonts/Inter-Light.ttf`
- `fonts/Inter-Medium.ttf`
- `fonts/Inter-Regular.ttf`
- `fonts/Inter-SemiBold.ttf`
- `fonts/Inter-Thin.ttf`
- `fonts/NanumMyeongjo-Bold.ttf`
- `fonts/NanumMyeongjo-ExtraBold.ttf`
- `fonts/NanumMyeongjo-Regular.ttf`

Use these local font files in `@font-face` declarations instead of fetching from Google Fonts.

## Screenshots Inventory (screens/)

> Study all screenshots carefully before implementing any UI. Match every visual detail exactly.

### Scroll Journey (screens/scroll/)

*Cinematic scroll states — page visual at each scroll depth*

![scroll-000.png](screens/scroll/scroll-000.png)

![scroll-017.png](screens/scroll/scroll-017.png)

![scroll-033.png](screens/scroll/scroll-033.png)

![scroll-050.png](screens/scroll/scroll-050.png)

![scroll-067.png](screens/scroll/scroll-067.png)

![scroll-083.png](screens/scroll/scroll-083.png)

![scroll-100.png](screens/scroll/scroll-100.png)

![video-1-frame.png](screens/scroll/video-1-frame.png)

### Full Page Screenshots (screens/pages/)

*Full-page screenshots of each crawled URL*

![home.png](screens/pages/home.png)

### Interaction States (screens/states/)

*Hover, focus, and active state captures*

![link-1-default.png](screens/states/link-1-default.png)

![link-1-focus.png](screens/states/link-1-focus.png)

![link-1-hover.png](screens/states/link-1-hover.png)

![link-2-default.png](screens/states/link-2-default.png)

![link-2-focus.png](screens/states/link-2-focus.png)

![link-2-hover.png](screens/states/link-2-hover.png)

![link-3-default.png](screens/states/link-3-default.png)

![link-3-focus.png](screens/states/link-3-focus.png)

![link-3-hover.png](screens/states/link-3-hover.png)

### Screenshot Index (screens/INDEX.md)

# Screenshot Index

## Scroll Journey

> Shows the cinematic state at each point of the page

| Scroll | Y Position | File |
|--------|-----------|------|
| 0% | 0px | `screens/scroll/scroll-000.png` |
| 17% | 799px | `screens/scroll/scroll-017.png` |
| 33% | 1552px | `screens/scroll/scroll-033.png` |
| 50% | 2351px | `screens/scroll/scroll-050.png` |
| 67% | 3150px | `screens/scroll/scroll-067.png` |
| 83% | 3903px | `screens/scroll/scroll-083.png` |
| 100% | 4702px | `screens/scroll/scroll-100.png` |

## Video First Frames

- Video 1 (content): `screens/scroll/video-1-frame.png`

## Pages

| Page | URL | File |
|------|-----|------|
| Interlude | `https://interludeapp.net` | `screens/pages/home.png` |

## Homepage Screenshots (screenshots/)

![homepage.png](screenshots/homepage.png)

