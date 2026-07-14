---
paths:
  - "services/insights/web/**"
---

# UI / design-system rule

Any change under `services/insights/web/**` MUST follow the Macro Insights design system.
Before editing the UI, read **`services/insights/web/DESIGN.md`** and conform to it:

- Use the design tokens (color, type, spacing, radius) — never introduce ad-hoc values.
- Reuse the existing components in `assets/components.js` rather than bespoke markup.
- Charts follow the chart rules (no chart junk; color encodes category only).
- Keep the `:root` tokens in `assets/styles.css` and the `THEME` object in
  `assets/charts.js` in sync.
