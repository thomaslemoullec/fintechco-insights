# Macro Insights — Design System

The dashboard aims for an **Anthropic-style** feel: warm, editorial, calm — the
opposite of a dark neon fintech dashboard. Generous whitespace, a refined serif
for headings, restrained charts, and a warm off-white canvas. The audience is
bank executives, so it stays legible and understated.

No build step and no web fonts: plain HTML + CSS custom properties + ES-module JS,
served as static files by FastAPI from `/`. Everything works offline. Apache
ECharts v5 is vendored locally (`assets/vendor/echarts.min.js`) and exposed as the
global `echarts` — never modify anything under `assets/vendor/`.

## App shape — multi-page, client-side hash routing

A **single-page shell** with a fixed left **sidebar nav** and a scrolling main
pane. Views are swapped client-side based on `location.hash`; there is no build
step and no framework. Routes:

| Route | Page | State |
|-------|------|-------|
| `#/home` (default) | Home — "Market Brief" news + latest-value stat strip | Populated |
| `#/indicators/macro` | Financial Indicators → Macro — indicator cards + Phillips view | Populated |
| `#/indicators/micro` | Financial Indicators → Micro | Empty ("Coming soon") |
| `#/trends` | Trends | Empty ("Coming soon") |
| `#/markets` | Markets | Empty ("Coming soon") |

`app.js` owns a small router: on `hashchange` it disposes all live ECharts
instances, clears `#view-root`, updates the active nav link (`.is-active` +
`aria-current`), sets the page title, and calls the route's render function.
Unknown hashes fall back to `#/home`. Empty pages render a tasteful
`emptyState` card — never a blank screen. A "Data as of {as_of}" pill in the top
bar is populated once at boot from `/api/views/phillips`.

## Files

| File | Role |
|------|------|
| `index.html` | App shell: sidebar nav, top bar, `#view-root`; loads ECharts then `app.js` (module). |
| `assets/styles.css` | Design tokens (`:root`) + all component + shell styling. |
| `assets/app.js` | Router + view controllers, data fetching/caching, A/B harness, chart lifecycle, errors. |
| `assets/charts.js` | ECharts option builders, themed to the tokens (`THEME` mirrors the CSS vars). |
| `assets/components.js` | DOM helpers: `el`, `mount`, `stat`, `statTile`, `indicatorCard`, `newsCard`, `emptyState`, `sectionHeader`, `segmented`, `viewMeta`. |

## Tokens

All tokens are CSS custom properties on `:root` (`styles.css`). The chart layer
mirrors the color/type values in `THEME` (`charts.js`) because ECharts can't read
CSS variables directly — keep the two in sync.

### Color

| Token | Value | Use |
|-------|-------|-----|
| `--bg` | `#FAF9F5` | Warm off-white canvas |
| `--surface` | `#FFFFFF` | Card / sidebar surface |
| `--border` | `#E7E2D8` | Hairline borders, gridlines |
| `--ink` | `#191917` | Primary text |
| `--muted` | `#6E6A5F` | Secondary / muted text, axis labels |
| `--accent` | `#CC785C` | Clay accent — line series, active states |
| `--accent-strong` | `#B15C3F` | Emphasis (wordmark, active nav, selected tab) |

### Decade categorical ramp

Ordered **oldest → newest, warm → cool** to evoke time passing. Eight colors map
to decades 1960s→2030s (`--decade-1960` … `--decade-2030`, and `THEME.decadeRamp`
in JS):

```
1960s #B15C3F  1970s #CC785C  1980s #D9A066  1990s #C9B458
2000s #7FA47B  2010s #5B8AA6  2020s #3E5C76  2030s #2E4257
```

`decadeColor(decade)` maps a decade to its color via `(decade - 1960) / 10`.
Because decades are an **ordered** category (time), a warm→cool progression is the
correct encoding. The same ramp colors the "Correlation by decade" bars and every
scatter treatment, so a decade keeps one color across every chart — **color only
ever encodes decade**, never rank or series arbitrarily.

### Type

- Headings: `Georgia, "Times New Roman", serif` — tight leading
  (`line-height: 1.15`, `letter-spacing: -0.01em`).
- Body: `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`,
  `line-height: 1.5`. No web fonts — must work offline.
- Big stats use the serif at 40px (34px on tiles) with `tabular-nums`.

### Shape, depth, spacing

- Radius: `--radius: 12px`.
- Shadow: `0 1px 2px rgba(25,25,23,.04), 0 4px 16px rgba(25,25,23,.05)` — soft.
- Spacing scale: `4 / 8 / 12 / 16 / 24 / 32 / 48` (`--space-1` … `--space-7`).
- Sidebar `248px`; content column max `1120px` — polished at 1280px with the
  sidebar. The sidebar collapses to a horizontal top strip below 1024px.

## Components

- **Card** (`.card`) — white surface, hairline border, soft shadow, 24px padding.
- **Sidebar nav** — wordmark + route links; the "Financial Indicators" group has
  a muted label and two indented sub-items (Macro / Micro). Active link gets clay
  text, a `--bg` fill and an inset accent bar.
- **Stat tile** (`.stat-tile`) — Home top strip: label + big serif value + meta.
- **Indicator card** — title, a big **stat**, and a compact line chart. 3-up
  responsive grid.
- **News card** (`.news-card`) — category **chip**, serif headline, summary,
  muted source. 2-up editorial grid on Home.
- **Segmented toggle** (`.segmented`) — pill group; the selected segment gets the
  surface color, clay text, and shadow. `role="tablist"`, `aria-selected`, and a
  visible focus ring. Used for the A/B variant switch.
- **View metadata footer** (`.view-meta`) — Sources / Methodology / Disclaimer +
  an expandable "Methodology decisions" list. **Compliance requirement:** always
  rendered and visible for the client-facing Phillips view, on **both** A/B
  variants (rendered once, outside the variant-swap region).
- **Empty state** (`.empty-state`) — dashed card with a mark, title and message
  for "Coming soon" pages.
- **Error banner / inline note** — shown in place of a blank page if a fetch
  fails; views degrade to inline notes rather than blanking.

## The Phillips view + A/B harness (`/api/views/phillips`)

The centerpiece lives on the Macro page. On load the user is assigned one of
`ab_variants` (`by-decade`, `then-vs-now`):

- The assignment is read from `localStorage["phillips_ab"]`. If absent, a stable
  first pick is made from a persisted seed and written back, so the variant is
  **stable across reloads**.
- The impression is POSTed to `/api/ab/event` `{variant, view:"phillips"}` on load
  and again on any manual switch (audit trail; no PII).
- A small labelled toggle ("Variant A · by-decade" / "Variant B · then-vs-now")
  lets a presenter switch on stage; switching re-renders and re-logs.

Above the variant chart: the `summary` lede and a **"Correlation by decade"** bar
strip (from `decade_stats`, value = correlation, zero reference line). Below it:
the compliance metadata footer, always visible on both variants.

## Chart treatments (all in `charts.js`; A/B uses #1 and #2)

1. **by-decade** — scatter, x = unemployment, y = inflation, points colored by
   decade with a decade legend and a light per-decade fit line
   (`y = slope·x + intercept` from `decade_stats`).
2. **then-vs-now** (the money chart) — two point clouds, `then.decade` vs
   `now.decade`, each with its fitted line; one steep (1960s), one flat (2010s) —
   each line's slope annotated at its end label.
3. **small-multiples** — a grid of mini scatter panels, one per decade in
   `decade_stats`, each labeled "{decade}s · slope {slope}" with a per-panel fit
   line, on shared scales so panels compare.

## Chart rules (no chart junk)

- Gridlines use `--border` (dashed, light); axis labels use `--muted`; axis lines
  are hidden or hairline. Titles/labels/legends wear text tokens, never a series
  color.
- Line charts: single 2px clay line, faint clay area gradient, symbols hidden,
  crosshair tooltip. A single series needs no legend — the card title names it.
- Scatter points carry ~0.5 opacity so overplotting reads; hover raises opacity
  and adds a surface ring.
- Scatter treatments legend by decade, so identity is never color-alone.
- Tooltips: white surface, hairline border, soft shadow, dates formatted
  "Mon YYYY".
- One ECharts instance per container, reused across variant swaps; all instances
  are disposed on route change and resized (debounced via `requestAnimationFrame`)
  on window resize.

## Accessibility notes

- Legend/labels never rely on color alone (decade legends, per-panel labels, bar
  value labels, slope annotations).
- Focus-visible ring on the toggle and nav; `role`/`aria-selected` on segments;
  `aria-current` on the active nav link; `aria-label`s on chart containers updated
  per treatment.
- Colors are drawn from the prescribed token palette; the ordered warm→cool decade
  ramp is used as an *ordered* scale (its intended purpose).
