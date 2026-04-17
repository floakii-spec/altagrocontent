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

