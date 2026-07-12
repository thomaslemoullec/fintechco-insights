# Macro Insights — Design System

The dashboard aims for an **Anthropic-style** feel: warm, editorial, calm — the
opposite of a dark neon fintech dashboard. Generous whitespace, a refined serif
for headings, restrained charts, and a warm off-white canvas.

No build step and no web fonts: plain HTML + CSS custom properties + ES-module JS,
served as static files by FastAPI. Everything works offline. Apache ECharts v5 is
vendored locally and exposed as the global `echarts`.

## Files

| File | Role |
|------|------|
| `index.html` | Structure + element ids; loads ECharts then `app.js` (module). |
| `assets/styles.css` | Design tokens (`:root`) + all component styling. |
| `assets/app.js` | Entry: fetch `/api/*`, orchestrate rendering, error handling, resize. |
| `assets/charts.js` | ECharts option builders, themed to the tokens. |
| `assets/components.js` | Small DOM helpers: `el`, `stat`, `indicatorCard`, `segmented`, `viewMeta`. |

## Tokens

All tokens are CSS custom properties on `:root` (`styles.css`). The chart layer
mirrors the color/type values in `THEME` (`charts.js`) because ECharts can't read
CSS variables directly — keep the two in sync.

### Color

| Token | Value | Use |
|-------|-------|-----|
| `--bg` | `#FAF9F5` | Warm off-white canvas |
| `--surface` | `#FFFFFF` | Card surface |
| `--border` | `#E7E2D8` | Hairline borders, gridlines |
| `--ink` | `#191917` | Primary text |
| `--muted` | `#6E6A5F` | Secondary / muted text, axis labels |
| `--accent` | `#CC785C` | Clay accent — line series, active states |
| `--accent-strong` | `#B15C3F` | Emphasis (eyebrow, selected tab) |

### Decade categorical ramp

Ordered **oldest → newest, warm → cool** to evoke time passing. Seven colors map to
the seven decades 1960s→2020s (`--decade-1960` … `--decade-2020`, and
`THEME.decadeRamp` in JS):

```
1960s #B15C3F  1970s #CC785C  1980s #D9A066  1990s #C9B458
2000s #7FA47B  2010s #5B8AA6  2020s #3E5C76
```

`decadeColor(decade)` maps a decade to its color via `(decade - 1960) / 10`.
Because decades are an **ordered** category (time), a warm→cool progression is the
correct encoding — it doubles as a time gradient in the "Over time" treatment.
The same ramp colors the "Correlation by decade" bars so a decade keeps one color
across every chart (color follows the entity, never its rank).

### Type

- Headings: `Georgia, "Times New Roman", serif` — slightly tight leading
  (`line-height: 1.15`, `letter-spacing: -0.01em`).
- Body: `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`,
  `line-height: 1.5`. No web fonts — must work offline.
- Big stats use the serif at 40px with `tabular-nums`.

### Shape, depth, spacing

- Radius: `--radius: 12px`.
- Shadow: `0 1px 2px rgba(25,25,23,.04), 0 4px 16px rgba(25,25,23,.05)` — soft.
- Spacing scale: `4 / 8 / 12 / 16 / 24 / 32 / 48` (`--space-1` … `--space-7`).
- Content max width 1200px; polished at 1280px (screen-share).

## Components

- **Card** (`.card`) — white surface, hairline border, soft shadow, 24px padding.
- **Indicator card** — title, a big **stat** (value + units + meta line), and a
  compact line chart. 3-up responsive grid (`repeat(3, 1fr)` → 2 → 1).
- **Stat** — serif value + muted units, optional meta line.
- **Section header** — serif title + muted sub-line.
- **Segmented toggle** (`.segmented`) — pill group; the selected segment gets the
  surface color, clay text, and shadow. `role="tablist"`, `aria-selected`, and a
  visible focus ring.
- **View metadata footer** (`.view-meta`) — Sources / Methodology / Disclaimer.
  **Compliance requirement:** these are always rendered and visible for the
  client-facing Phillips view; the disclaimer is smaller and muted.
- **Error banner** — shown in place of a blank page if a fetch fails.

## Chart rules (no chart junk)

- Gridlines use `--border` (dashed, light); axis labels use `--muted`; axis lines
  are hidden or hairline. Titles/labels/legends wear text tokens, never a series
  color.
- Line charts: single 2px clay line, faint clay area gradient, symbols hidden,
  crosshair tooltip. A single series needs no legend — the card title names it.
- Scatter points carry a subtle opacity (~0.5–0.55) so overplotting reads; hover
  raises opacity and adds a surface ring.
- The scatter treatments legend by decade (≥2 series → legend always present), so
  identity is never color-alone.
- Tooltips: white surface, hairline border, soft shadow, dates formatted
  "Mon YYYY".
- All chart instances resize on window resize (debounced via `requestAnimationFrame`).

## The three Phillips treatments (same data, `/api/views/phillips`)

1. **By decade** (default) — scatter, x = unemployment, y = inflation, colored by
   decade with a decade legend.
2. **Small multiples** — a grid of mini scatter panels (ECharts multi-grid), one
   per decade, each labeled with the decade and its correlation `r`, so the
   flattening is visible panel to panel.
3. **Over time** — a time-ordered connected scatter graded by time (the decade
   ramp as a continuous `visualMap`), showing the loops collapsing to a flat cloud.

Below the main chart, a **Correlation by decade** horizontal bar strip (from
`decade_correlations`) with a zero reference line makes the trend toward zero
explicit.

## Accessibility notes

- Legend/labels never rely on color alone (decade legends, per-panel labels,
  bar value labels).
- Focus-visible ring on the toggle; `role`/`aria-selected` on segments;
  `aria-label`s on chart containers updated per treatment.
- Colors are drawn from the prescribed token palette; the ordered warm→cool decade
  ramp is used as an *ordered* scale (its intended purpose), not as an arbitrary
  categorical cycle.
