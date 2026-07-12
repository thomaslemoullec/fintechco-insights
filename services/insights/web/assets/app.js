// =============================================================================
// app.js — entrypoint + client-side hash router for the multi-page dashboard.
// ES module; relies on the global `echarts` loaded before it. Fetches same-origin
// /api data, renders one view per route into #view-root, and manages the ECharts
// instance lifecycle (dispose on route change, debounced resize).
// =============================================================================
import {
  el, mount, statTile, indicatorCard, newsCard, emptyState, sectionHeader,
  segmented, viewMeta,
} from "/assets/components.js";
// Note: smallMultiplesOption (treatment #3) is built in charts.js per spec but is
// not part of the two-way A/B toggle, so it is not imported here.
import {
  lineOption, scatterByDecadeOption, thenVsNowOption, correlationStripOption,
} from "/assets/charts.js";

const $ = (id) => document.getElementById(id);

// Indicator display order (Inflation, Unemployment, Fed Funds) reused across pages.
const INDICATOR_ORDER = [
  { id: "INFLATION", label: "Inflation (CPI, YoY)" },
  { id: "UNRATE", label: "Unemployment" },
  { id: "FEDFUNDS", label: "Fed Funds" },
];

// -----------------------------------------------------------------------------
// Data fetching (with a tiny cache so navigating between pages doesn't refetch).
// -----------------------------------------------------------------------------
const cache = new Map();

async function getJSON(path) {
  if (cache.has(path)) return cache.get(path);
  const res = await fetch(path, { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`${path} → HTTP ${res.status}`);
  const data = await res.json();
  cache.set(path, data);
  return data;
}

// -----------------------------------------------------------------------------
// ECharts instance lifecycle. All live instances are tracked so we can dispose
// them on route change (their DOM nodes are replaced) and resize them together.
// -----------------------------------------------------------------------------
const instances = new Set();

function renderChart(node, option) {
  let chart = echarts.getInstanceByDom(node);
  if (!chart) {
    chart = echarts.init(node, null, { renderer: "canvas" });
    instances.add(chart);
  }
  chart.setOption(option, true); // notMerge so treatment swaps are clean
  return chart;
}

function disposeCharts() {
  for (const c of instances) c.dispose();
  instances.clear();
}

// -----------------------------------------------------------------------------
// Error surfaces — always inline notes, never a blank page.
// -----------------------------------------------------------------------------
function showError(message) {
  const banner = $("error-banner");
  banner.textContent = `Couldn’t load this view: ${message}. Please retry; if it persists, contact the Insights team.`;
  banner.hidden = false;
}

function clearError() {
  const banner = $("error-banner");
  banner.hidden = true;
  banner.textContent = "";
}

function inlineNote(text) {
  return el("div", { className: "inline-note", text });
}

// -----------------------------------------------------------------------------
// "Data as of" pill (top bar). Sourced from the phillips endpoint per spec.
// Fetched once at boot; failure is non-fatal (pill just stays hidden).
// -----------------------------------------------------------------------------
async function initAsOfPill() {
  try {
    const view = await getJSON("/api/views/phillips");
    $("asof-date").textContent = view.as_of;
    $("asof-pill").hidden = false;
  } catch (e) {
    console.warn("as-of pill unavailable:", e);
  }
}

// =============================================================================
// A/B harness for the Phillips view.
// =============================================================================
const AB_KEY = "phillips_ab";

/**
 * Assign the user to a variant. Persisted in localStorage so the choice is
 * stable across reloads; if absent, pick one via a stable hash of the browser's
 * assignment seed (which is itself persisted the first time).
 */
function assignVariant(variants) {
  let v = null;
  try {
    v = localStorage.getItem(AB_KEY);
  } catch { /* storage may be blocked; fall through to a fresh pick */ }
  if (variants.includes(v)) return v;

  // Stable pseudo-random first assignment, then persisted so it never changes.
  let seed;
  try {
    seed = Number(localStorage.getItem(AB_KEY + "_seed"));
    if (!Number.isFinite(seed) || seed === 0) {
      seed = Date.now() % 100000;
      localStorage.setItem(AB_KEY + "_seed", String(seed));
    }
  } catch {
    seed = Date.now() % 100000;
  }
  v = variants[seed % variants.length];
  try { localStorage.setItem(AB_KEY, v); } catch { /* ignore */ }
  return v;
}

function setVariant(v) {
  try { localStorage.setItem(AB_KEY, v); } catch { /* ignore */ }
}

/** Log a variant impression to the audit trail. Best-effort; never blocks UI. */
function logImpression(variant) {
  fetch("/api/ab/event", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ variant, view: "phillips" }),
  }).catch((e) => console.warn("ab/event log failed:", e));
}

// =============================================================================
// Views
// =============================================================================

// --- Home: "Market Brief" news + optional latest-value stat strip. -----------
async function renderHome(root) {
  const section = el("section", { className: "section" });

  // Top strip: latest value of each indicator (last point of each series).
  const strip = el("div", { className: "stat-strip" });
  section.appendChild(strip);
  try {
    const series = await Promise.all(INDICATOR_ORDER.map((i) => getJSON(`/api/series/${i.id}`)));
    const tiles = INDICATOR_ORDER.map((i, idx) => {
      const s = series[idx];
      const latest = s.points[s.points.length - 1];
      return statTile({
        label: i.label,
        value: latest ? latest.value.toFixed(1) : "—",
        units: "%",
        meta: latest ? `Latest · ${latest.date}` : "",
      });
    });
    mount(strip, tiles);
  } catch (e) {
    console.warn("stat strip unavailable:", e);
    mount(strip, inlineNote("Latest indicator values are unavailable right now."));
  }

  // Market Brief — editorial news list.
  section.appendChild(sectionHeader({
    title: "Market Brief",
    sub: "Today’s macro, rates, inflation and markets read from the FinTechCo desk.",
  }));

  const brief = el("div", { className: "news-list" });
  section.appendChild(brief);
  root.appendChild(section);

  const { news } = await getJSON("/api/news");
  if (!news || !news.length) {
    mount(brief, inlineNote("No briefing items available."));
    return;
  }
  mount(brief, news.map(newsCard));
}

// --- Financial Indicators → Macro: indicator cards + the Phillips view. -------
async function renderMacro(root) {
  // --- 1) Indicator cards (compact line chart + latest stat) ---
  const cardsSection = el("section", { className: "section" });
  cardsSection.appendChild(sectionHeader({
    title: "Key indicators",
    sub: "Full monthly history · U.S. series via FRED",
  }));
  const grid = el("div", { className: "card-grid" });
  cardsSection.appendChild(grid);
  root.appendChild(cardsSection);

  const seriesById = {};
  await Promise.all(
    INDICATOR_ORDER.map(async ({ id }) => {
      seriesById[id] = await getJSON(`/api/series/${id}`);
    }),
  );

  const chartMounts = [];
  for (const { id } of INDICATOR_ORDER) {
    const series = seriesById[id];
    const ind = series.indicator;
    const latest = series.points[series.points.length - 1];
    const { card, chartEl } = indicatorCard({
      title: ind.title,
      value: latest ? latest.value.toFixed(1) : "—",
      units: "%",
      meta: latest ? `Latest · ${latest.date} · ${ind.frequency}` : ind.frequency,
    });
    grid.appendChild(card);
    chartMounts.push([chartEl, lineOption(series, ind)]);
  }
  // Render after cards are in the DOM (ECharts needs measurable dimensions).
  for (const [node, option] of chartMounts) renderChart(node, option);

  // --- 2) Phillips view (the centerpiece) ---
  await renderPhillips(root);
}

/**
 * Phillips view. A/B tested between two chart treatments; the compliance
 * metadata footer is rendered ONCE outside the swap region so it is always
 * present on both variants.
 */
async function renderPhillips(root) {
  const view = await getJSON("/api/views/phillips");
  const variants = view.ab_variants || ["by-decade", "then-vs-now"];

  const section = el("section", { className: "section" });

  // Header + summary lede.
  section.appendChild(sectionHeader({ title: view.title }));
  section.appendChild(el("p", { className: "lede", text: view.summary }));

  // Correlation-by-decade mini strip.
  const stripCard = el("div", { className: "card" }, [
    sectionHeader({
      title: "Correlation by decade",
      sub: "Pearson correlation of inflation vs. unemployment, per decade — a strong early negative relationship decays toward zero.",
      tight: true,
    }),
  ]);
  const stripChart = el("div", { className: "chart chart--strip", role: "img", "aria-label": "Correlation by decade bar chart" });
  stripCard.appendChild(stripChart);
  section.appendChild(stripCard);

  // Main A/B card: labelled toggle + swap-able chart.
  const VARIANT_META = {
    "by-decade": { label: "Variant A · by-decade", caption: "Each point is one month, colored by decade, with a light per-decade fit line.", build: scatterByDecadeOption },
    "then-vs-now": { label: "Variant B · then-vs-now", caption: `The ${view.then.decade}s vs the ${view.now.decade}s — two clouds and their fitted lines; one steep, one flat.`, build: thenVsNowOption },
  };

  let current = assignVariant(variants);
  if (!VARIANT_META[current]) current = variants[0];

  const caption = el("p", { className: "chart-caption" });
  const chartNode = el("div", { className: "chart chart--tall", role: "img", "aria-label": "Phillips curve chart" });

  const draw = (variant, { log } = { log: false }) => {
    current = variant;
    const meta = VARIANT_META[variant] || VARIANT_META[variants[0]];
    caption.textContent = meta.caption;
    chartNode.setAttribute("aria-label", `Phillips curve — ${meta.label}`);
    renderChart(chartNode, meta.build(view));
    if (log) logImpression(variant);
  };

  const toggle = segmented({
    ariaLabel: "Chart variant",
    options: variants.filter((v) => VARIANT_META[v]).map((v) => ({ id: v, label: VARIANT_META[v].label })),
    selected: current,
    onChange: (v) => { setVariant(v); draw(v, { log: true }); }, // manual switch re-renders + re-logs
  });

  const phillipsCard = el("div", { className: "card phillips-card" }, [
    el("div", { className: "chart-toolbar" }, [toggle, caption]),
    chartNode,
  ]);
  section.appendChild(phillipsCard);

  // Compliance metadata footer — rendered once, outside the A/B swap, so it is
  // ALWAYS visible regardless of which variant is shown.
  section.appendChild(viewMeta({
    sources: view.sources,
    methodology: view.methodology,
    disclaimer: view.disclaimer,
    decisions: view.decisions,
  }));

  root.appendChild(section);

  // Render charts now that nodes are in the DOM.
  renderChart(stripChart, correlationStripOption(view.decade_stats));
  draw(current, { log: true }); // initial impression logged on load
}

// --- Empty placeholder pages -------------------------------------------------
function renderComingSoon(root, title, message) {
  root.appendChild(el("section", { className: "section" }, [emptyState({ title, message })]));
}
const renderMicro = (root) =>
  renderComingSoon(root, "Micro indicators — coming soon", "Firm- and household-level series (spending, credit, delinquency) will land here.");
const renderTrends = (root) =>
  renderComingSoon(root, "Trends — coming soon", "Cross-indicator trend decompositions and regime markers are in the works.");
const renderMarkets = (root) =>
  renderComingSoon(root, "Markets — coming soon", "Rates, curves and cross-asset context will be wired up in a later release.");

// =============================================================================
// Router
// =============================================================================
const ROUTES = {
  "#/home": { title: "Home", render: renderHome },
  "#/indicators/macro": { title: "Financial Indicators · Macro", render: renderMacro },
  "#/indicators/micro": { title: "Financial Indicators · Micro", render: renderMicro },
  "#/trends": { title: "Trends", render: renderTrends },
  "#/markets": { title: "Markets", render: renderMarkets },
};
const DEFAULT_ROUTE = "#/home";

function currentRoute() {
  const hash = location.hash || DEFAULT_ROUTE;
  return ROUTES[hash] ? hash : DEFAULT_ROUTE;
}

function setActiveNav(hash) {
  for (const link of document.querySelectorAll(".nav__link")) {
    const active = link.dataset.route === hash;
    link.classList.toggle("is-active", active);
    if (active) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
}

async function handleRoute() {
  clearError();
  disposeCharts(); // tear down old instances before their nodes are replaced

  const hash = currentRoute();
  const route = ROUTES[hash];
  setActiveNav(hash);
  $("page-title").textContent = route.title;

  const root = $("view-root");
  mount(root, []); // clear previous view
  window.scrollTo(0, 0);

  try {
    await route.render(root);
  } catch (e) {
    console.error("View render error:", e);
    showError(e.message || "unknown error");
    if (!root.hasChildNodes()) {
      mount(root, el("section", { className: "section" }, [
        emptyState({ title: "Data unavailable", message: "This view couldn’t be loaded. Please retry shortly." }),
      ]));
    }
  }
}

// =============================================================================
// Boot
// =============================================================================
function main() {
  if (typeof echarts === "undefined") {
    showError("charting library failed to load");
    return;
  }

  initAsOfPill();
  window.addEventListener("hashchange", handleRoute);

  // Normalize to the default route so the first paint always has a valid hash.
  // If we rewrite the hash, the resulting `hashchange` drives the first render;
  // otherwise render the (already valid) current route directly. Avoids a
  // double initial render.
  if (!ROUTES[location.hash]) {
    location.replace(DEFAULT_ROUTE);
  } else {
    handleRoute();
  }

  // Keep charts crisp on resize / screen-share layout changes (debounced).
  let raf = 0;
  window.addEventListener("resize", () => {
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(() => instances.forEach((c) => c.resize()));
  });
}

main();
