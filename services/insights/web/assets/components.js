// =============================================================================
// components.js — small DOM render helpers (no framework).
// Each helper returns a detached DOM node the caller mounts. Keeping DOM
// construction here keeps app.js focused on data flow.
// =============================================================================

/**
 * Terse element factory.
 * @param {string} tag
 * @param {object} [attrs]  className, textContent, or any attribute/dataset key.
 * @param {(Node|string)[]} [children]
 * @returns {HTMLElement}
 */
export function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value == null) continue;
    if (key === "className") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key === "dataset") Object.assign(node.dataset, value);
    else node.setAttribute(key, value);
  }
  for (const child of [].concat(children)) {
    if (child == null) continue;
    node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
  }
  return node;
}

/**
 * A big headline stat with units and a small meta line.
 * @returns {HTMLElement}
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
 * A segmented (pill) toggle. Options: [{ id, label }]. Calls onChange(id) when a
 * segment is picked. Returns the container; the initially-selected id is marked.
 */
export function segmented({ options, selected, onChange }) {
  const container = el("div", { className: "segmented", role: "tablist" });
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
 * The compliance metadata footer for the Phillips view.
 * Sources / Methodology / Disclaimer must all be visible.
 */
export function viewMeta({ sources, methodology, disclaimer }) {
  const sourceList = el(
    "ul",
    {},
    (sources || []).map((s) => el("li", { text: s })),
  );
  return [
    el("div", { className: "view-meta__block" }, [
      el("p", { className: "view-meta__label", text: "Sources" }),
      el("div", { className: "view-meta__body" }, [sourceList]),
    ]),
    el("div", { className: "view-meta__block" }, [
      el("p", { className: "view-meta__label", text: "Methodology" }),
      el("p", { className: "view-meta__body", text: methodology || "" }),
    ]),
    el("p", { className: "view-meta__disclaimer", text: disclaimer || "" }),
  ];
}

/** Replace all children of a node with the given nodes. */
export function mount(target, nodes) {
  target.replaceChildren(...[].concat(nodes).filter(Boolean));
}
