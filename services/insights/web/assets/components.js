// =============================================================================
// components.js — small DOM render helpers (no framework).
// Each helper returns a detached DOM node (or array) the caller mounts. Keeping
// DOM construction here keeps app.js focused on data flow and routing.
// =============================================================================

/**
 * Terse element factory.
 * @param {string} tag
 * @param {object} [attrs]  className, `text`, `html`, `dataset`, or any attribute.
 * @param {(Node|string)[]} [children]
 * @returns {HTMLElement}
 */
export function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value == null) continue;
    if (key === "className") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key === "html") node.innerHTML = value;
    else if (key === "dataset") Object.assign(node.dataset, value);
    else node.setAttribute(key, value);
  }
  for (const child of [].concat(children)) {
    if (child == null) continue;
    node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
  }
  return node;
}

/** Replace all children of a node with the given node(s). */
export function mount(target, nodes) {
  target.replaceChildren(...[].concat(nodes).filter(Boolean));
}

/**
 * A big headline stat: serif value + muted units, with an optional meta line.
 */
export function stat({ value, units, meta }) {
  return el("div", {}, [
    el("div", { className: "stat" }, [
      el("span", { className: "stat__value", text: value }),
      units ? el("span", { className: "stat__units", text: units }) : null,
    ]),
    meta ? el("p", { className: "stat__meta", text: meta }) : null,
  ]);
}

/**
 * A compact stat tile (used in the Home top strip): label, big value, meta.
 */
export function statTile({ label, value, units, meta }) {
  return el("div", { className: "card stat-tile" }, [
    el("p", { className: "stat-tile__label", text: label }),
    el("div", { className: "stat" }, [
      el("span", { className: "stat__value", text: value }),
      units ? el("span", { className: "stat__units", text: units }) : null,
    ]),
    meta ? el("p", { className: "stat__meta", text: meta }) : null,
  ]);
}

/**
 * An indicator card: title, headline stat, and a mount point for the chart.
 * Returns { card, chartEl } so the caller can render an ECharts instance into
 * chartEl after the card is in the DOM (ECharts needs measurable dimensions).
 */
export function indicatorCard({ title, value, units, meta }) {
  const chartEl = el("div", { className: "chart" });
  const card = el("div", { className: "card indicator-card" }, [
    el("h3", { className: "indicator-card__title", text: title }),
    stat({ value, units, meta }),
    chartEl,
  ]);
  return { card, chartEl };
}

/**
 * An editorial news card for the Home "Market Brief".
 */
export function newsCard({ category, headline, summary, source }) {
  return el("article", { className: "news-card" }, [
    category ? el("span", { className: "chip", text: category }) : null,
    el("h3", { className: "news-card__headline", text: headline }),
    summary ? el("p", { className: "news-card__summary", text: summary }) : null,
    source ? el("p", { className: "news-card__source", text: source }) : null,
  ]);
}

/**
 * A tasteful empty state for "Coming soon" pages — never a blank screen.
 */
export function emptyState({ title, message }) {
  return el("div", { className: "empty-state" }, [
    el("div", { className: "empty-state__mark", "aria-hidden": "true", text: "◔" }),
    el("h2", { className: "empty-state__title", text: title }),
    el("p", { className: "empty-state__message", text: message }),
  ]);
}

/**
 * A section header: serif title + optional muted sub-line.
 */
export function sectionHeader({ title, sub, tight }) {
  return el("div", { className: "section-header" + (tight ? " section-header--tight" : "") }, [
    el("h2", { className: "section-title", text: title }),
    sub ? el("p", { className: "section-sub", text: sub }) : null,
  ]);
}

/**
 * A segmented (pill) toggle. Options: [{ id, label }]. Calls onChange(id) when a
 * segment is picked. Returns the container; the initially-selected id is marked.
 */
export function segmented({ options, selected, onChange, ariaLabel }) {
  const container = el("div", { className: "segmented", role: "tablist", "aria-label": ariaLabel || "" });
  for (const opt of options) {
    const btn = el("button", {
      className: "segmented__btn",
      type: "button",
      role: "tab",
      "aria-selected": String(opt.id === selected),
      dataset: { id: opt.id },
      text: opt.label,
    });
    btn.addEventListener("click", () => {
      if (btn.getAttribute("aria-selected") === "true") return;
      for (const b of container.children) b.setAttribute("aria-selected", "false");
      btn.setAttribute("aria-selected", "true");
      onChange(opt.id);
    });
    container.appendChild(btn);
  }
  return container;
}

/**
 * The compliance metadata footer for a client-facing view (Sources / Methodology
 * / Disclaimer). Sources / Methodology / Disclaimer must ALL be visible, plus an
 * expandable "Methodology decisions" list. This is a client-facing compliance
 * requirement — any client-facing figure must render this disclosure footer.
 */
export function viewMeta({ asOf, sources, methodology, disclaimer, decisions }) {
  const sourceList = el("ul", {}, (sources || []).map((s) => el("li", { text: s })));

  const blocks = [];

  // Data as-of (vintage) — the figure's own vintage travels with it, so the disclosure
  // is complete even if the top-bar pill is unavailable (client-facing requirement).
  if (asOf) {
    blocks.push(el("div", { className: "view-meta__block" }, [
      el("p", { className: "view-meta__label", text: "Data as of" }),
      el("p", { className: "view-meta__body", text: asOf }),
    ]));
  }

  blocks.push(
    el("div", { className: "view-meta__block" }, [
      el("p", { className: "view-meta__label", text: "Sources" }),
      el("div", { className: "view-meta__body" }, [sourceList]),
    ]),
    el("div", { className: "view-meta__block" }, [
      el("p", { className: "view-meta__label", text: "Methodology" }),
      el("p", { className: "view-meta__body", text: methodology || "" }),
    ]),
  );

  // Expandable "Methodology decisions" — the analyst judgement calls.
  if (decisions && decisions.length) {
    const items = decisions.map((d) =>
      el("li", { className: "decision" }, [
        el("p", { className: "decision__q", text: d.question }),
        el("p", { className: "decision__a" }, [
          el("strong", { text: d.choice }),
          d.rationale ? el("span", { className: "decision__why", text: " — " + d.rationale }) : null,
        ]),
      ]),
    );
    blocks.push(
      el("details", { className: "view-meta__decisions" }, [
        el("summary", { text: "Methodology decisions" }),
        el("ul", { className: "decision-list" }, items),
      ]),
    );
  }

  blocks.push(el("p", { className: "view-meta__disclaimer", text: disclaimer || "" }));

  return el("footer", { className: "view-meta", "aria-label": "Data provenance and disclaimer" }, blocks);
}
