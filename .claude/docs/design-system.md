# Design System

**Version**: 6.0
**Last Updated**: 2026-01-23
**Purpose**: UI/UX guidelines and specifications

---

## Colors

**Dark Theme** (default):
- Background: `#0a0a0a`
- Surface: `#151515`
- Border: `#2a2a2a`
- Text: `#e8e8e8`
- Accent: `#00ff88`

**Light Theme**:
- Background: `#ffffff`
- Surface: `#f5f5f5`
- Border: `#e0e0e0`
- Text: `#1a1a1a`
- Accent: `#00dd77`

**CSS Variables** (in theme, check `assets/css/`):
```css
:root {
    --bg: #0a0a0a;
    --fg: #e8e8e8;
    --accent: #00ff88;
}
```

---

## Typography

- **Headings**: Space Mono (monospace)
- **Body**: Instrument Sans (sans-serif)
- **Code**: Space Mono (monospace)

**Font Loading**: Google Fonts (preconnect in `layouts/partials/head.html`)

---

## Breakpoints

```css
/* Mobile-first approach */
@media (min-width: 768px) { /* Tablet */ }
@media (min-width: 1024px) { /* Desktop */ }
```

---

## Grid System

Homepage uses **12-column Bento grid**:
- Gap: 1rem
- Max-width: 1400px
- Responsive: 1 col (mobile), 2 cols (tablet), 3-4 cols (desktop)

---

**For architecture details**: See `.claude/docs/architecture.md`
