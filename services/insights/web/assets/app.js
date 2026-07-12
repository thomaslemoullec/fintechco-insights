// =============================================================================
// app.js — entrypoint. Fetches data from the same-origin /api and renders the
// dashboard. ES module; relies on the global `echarts` loaded before it.
// =============================================================================
import { indicatorCard, segmented, viewMeta, mount, el } from "/assets/components.js";
import {
  lineOption,
  scatterByDecadeOption,
  smallMultiplesOption,
  overTimeOption,
  correlationStripOption,
} from "/assets/charts.js";

/* --- Element ids, kept in one place so they stay in sync with index.html. --- */
const IDS = {
  errorBanner: "error-banner",
  asofPill: "asof-pill",
  asofDate: "asof-date",
  indicatorGrid: "indicator-grid",
  phillipsSummary: "phillips-summary",
  phillipsToggle: "phillips-toggle",
  phillipsCaption: "phillips-caption",
  phillipsChart: "phillips-chart",
  corrStrip: "corr-strip",
  phillipsMeta: "phillips-meta",
};

const $ = (id) => document.getElementById(id);

// Track live ECharts instances so we can resize them on window resize.
const instances = new Set();

/** Create (or reuse) an ECharts instance on a node, apply option, register it. */
function renderChart(node, option) {
  let chart = echarts.getInstanceByDom(node);
  if (!chart) {
    chart = echarts.init(node, null, { renderer: "canvas" });
    instances.add(chart);
  }
  chart.setOption(option, true); // notMerge: treatments swap cleanly
  return chart;
}

/** Fetch JSON from the same-origin API, throwing a helpful error on failure. */
async function getJSON(path) {
  const res = await fetch(path, { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`${path} → HTTP ${res.status}`);
  return res.json();
}

/** Show the error banner instead of leaving a blank page. */
function showError(message) {
  const banner = $(IDS.errorBanner);
  banner.textContent = `Couldn’t load the dashboard: ${message}. Please retry; if it persists, contact the Insights team.`;
  banner.hidden = false;
}

/** Put a small inline message inside a chart container when it can't render. */
function chartEmpty(node, message) {
  mount(node, el("div", { className: "chart-empty", text: message }));
}

// -----------------------------------------------------------------------------
// Section A — key indicators
// -----------------------------------------------------------------------------
async function renderIndicators() {
  const grid = $(IDS.indicatorGrid);
  const { indicators } = await getJSON("/api/indicators");

  // Fixed display order: Inflation, Unemployment, Fed Funds.
  const order = ["INFLATION", "UNRATE", "FEDFUNDS"];
  const byId = Object.fromEntries(indicators.map((i) => [i.id, i]));
  const ordered = order.filter((id) => byId[id]).map((id) => byId[id]);

  // Fetch every series in parallel.
  const seriesById = {};
  await Promise.all(
    ordered.map(async (ind) => {
      seriesById[ind.id] = await getJSON(`/api/series/${ind.id}`);
    }),
  );

  mount(grid, []); // clear any prior state
  for (const ind of ordered) {
    const series = seriesById[ind.id];
    const latest = series.points[series.points.length - 1];
    const { card, chartEl } = indicatorCard({
      title: ind.title,
      value: latest ? latest.value.toFixed(1) : "—",
      units: "%",
      meta: latest ? `Latest · ${latest.date} · ${ind.frequency}` : ind.frequency,
    });
    grid.appendChild(card);
    // Chart must be rendered after the node is in the DOM (needs dimensions).
    renderChart(chartEl, lineOption(series, ind.indicator ?? ind));
  }
}

// -----------------------------------------------------------------------------
// Section B — Phillips curve view (three treatments of the same data)
// -----------------------------------------------------------------------------
const TREATMENTS = {
  decade: {
    label: "By decade",
    caption: "Each point is one month; color marks the decade.",
    build: scatterByDecadeOption,
  },
  multiples: {
    label: "Small multiples",
    caption: "One panel per decade — the curve flattens as r approaches zero.",
    build: smallMultiplesOption,
  },
  overtime: {
    label: "Over time",
    caption: "Points joined in date order, graded by time — loops collapse to a cloud.",
    build: overTimeOption,
  },
};

async function renderPhillips() {
  const view = await getJSON("/api/views/phillips");

  // As-of pill (header) — sourced from the phillips endpoint.
  $(IDS.asofDate).textContent = view.as_of;
  $(IDS.asofPill).hidden = false;

  // Intro line.
  $(IDS.phillipsSummary).textContent = view.summary;

  // Main chart + segmented toggle.
  const chartNode = $(IDS.phillipsChart);
  const captionNode = $(IDS.phillipsCaption);
  let current = "decade";

  const draw = (treatmentId) => {
    current = treatmentId;
    const t = TREATMENTS[treatmentId];
    captionNode.textContent = t.caption;
    chartNode.setAttribute("aria-label", `Phillips curve — ${t.label}`);
    renderChart(chartNode, t.build(view));
  };

  const toggle = segmented({
    options: Object.entries(TREATMENTS).map(([id, t]) => ({ id, label: t.label })),
    selected: current,
    onChange: draw,
  });
  mount($(IDS.phillipsToggle), toggle);

  draw(current); // initial render (default: by decade)

  // Correlation-by-decade strip.
  renderChart($(IDS.corrStrip), correlationStripOption(view.decade_correlations));

  // Compliance metadata footer.
  mount(
    $(IDS.phillipsMeta),
    viewMeta({ sources: view.sources, methodology: view.methodology, disclaimer: view.disclaimer }),
  );
}

// -----------------------------------------------------------------------------
// Boot
// -----------------------------------------------------------------------------
async function main() {
  if (typeof echarts === "undefined") {
    showError("charting library failed to load");
    return;
  }

  // Render sections independently so one failing endpoint doesn't blank the rest.
  const results = await Promise.allSettled([renderIndicators(), renderPhillips()]);
  const failed = results.filter((r) => r.status === "rejected");
  if (failed.length) {
    console.error("Dashboard load errors:", failed.map((f) => f.reason));
    showError(failed.map((f) => f.reason?.message ?? "unknown error").join("; "));
    // Leave a hint in any chart container that never got populated.
    for (const id of [IDS.indicatorGrid, IDS.phillipsChart, IDS.corrStrip]) {
      const node = $(id);
      if (node && !node.hasChildNodes()) chartEmpty(node, "Data unavailable");
    }
  }

  // Keep charts crisp on resize / screen-share layout changes.
  let raf = 0;
  window.addEventListener("resize", () => {
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(() => instances.forEach((c) => c.resize()));
  });
}

main();
