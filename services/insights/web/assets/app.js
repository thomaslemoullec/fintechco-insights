// =============================================================================
// app.js — entrypoint + client-side hash router for the multi-page dashboard.
// ES module; relies on the global `echarts` loaded before it. Fetches same-origin
// /api data, renders one view per route into #view-root, and manages the ECharts
// instance lifecycle (dispose on route change, debounced resize).
// =============================================================================
import {
  el, mount, statTile, indicatorCard, newsCard, emptyState, sectionHeader, viewMeta,
} from "/assets/components.js";
import { lineOption, scatterOption } from "/assets/charts.js";

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
  chart.setOption(option, true); // notMerge so swaps are clean
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
// "Data as of" pill (top bar). Derived from the UNRATE series' as-of date.
// Fetched once at boot; failure is non-fatal (pill just stays hidden).
// -----------------------------------------------------------------------------
async function initAsOfPill() {
  try {
    const series = await getJSON("/api/series/UNRATE");
    $("asof-date").textContent = series.as_of;
    $("asof-pill").hidden = false;
  } catch (e) {
    console.warn("as-of pill unavailable:", e);
  }
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

// Join inflation and unemployment series by date (only dates present in both) and
// derive the decade bucket — mirrors the decade formula in app/analysis.py so the
// two stay consistent.
function buildPhillipsPoints(inflationSeries, unemploymentSeries) {
  const unemploymentByDate = new Map(unemploymentSeries.points.map((p) => [p.date, p.value]));
  const points = [];
  for (const p of inflationSeries.points) {
    const u = unemploymentByDate.get(p.date);
    if (u == null) continue;
    const decade = Math.floor(Number(p.date.slice(0, 4)) / 10) * 10;
    points.push({ x: u, y: p.value, date: p.date, decade });
  }
  return points;
}

// --- Financial Indicators → Macro: indicator cards. --------------------------
async function renderMacro(root) {
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

  // --- Inflation vs. unemployment (Phillips curve) ---------------------------
  const phillipsSection = el("section", { className: "section" });
  phillipsSection.appendChild(sectionHeader({
    title: "Inflation vs. unemployment",
    sub: "Does the Phillips-curve tradeoff still hold? Each point is one month.",
  }));
  const phillipsChartEl = el("div", { className: "chart chart--tall" });
  phillipsSection.appendChild(el("div", { className: "card" }, [phillipsChartEl]));
  root.appendChild(phillipsSection);

  const points = buildPhillipsPoints(seriesById.INFLATION, seriesById.UNRATE);
  renderChart(phillipsChartEl, scatterOption(points, {
    xLabel: "Unemployment", yLabel: "Inflation (YoY)",
  }));

  phillipsSection.appendChild(viewMeta({
    sources: [...new Set([
      seriesById.INFLATION.indicator.source,
      seriesById.UNRATE.indicator.source,
    ])],
    methodology: "Each point pairs a month's unemployment rate with year-over-year "
      + "CPI inflation for that same month; point color marks the decade.",
    disclaimer: seriesById.INFLATION.disclaimer,
  }));
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
