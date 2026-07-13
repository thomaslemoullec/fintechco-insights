// =============================================================================
// charts.js — ECharts option builders, themed to the design tokens.
// Depends on the global `echarts` (loaded via <script> in index.html).
// Chart philosophy (see DESIGN.md): no chart junk — hairline gridlines, muted
// axis labels, white tooltips.
// =============================================================================

/* --- Design tokens mirrored for the canvas (JS can't read CSS vars for ECharts). --- */
export const THEME = {
  ink: "#191917",
  muted: "#6E6A5F",
  border: "#E7E2D8",
  surface: "#FFFFFF",
  accent: "#CC785C",
  accentStrong: "#B15C3F",
  fontSans: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
  // Ordered oldest -> newest, warm -> cool time-category ramp (mirrors --decade-* in
  // styles.css). Use only as an *ordered* scale — one color per decade, never per series.
  decadeRamp: {
    1960: "#B15C3F",
    1970: "#CC785C",
    1980: "#D9A066",
    1990: "#C9B458",
    2000: "#7FA47B",
    2010: "#5B8AA6",
    2020: "#3E5C76",
    2030: "#2E4257",
  },
};

/** Map a decade (e.g. 1990) to its ramp color. */
export function decadeColor(decade) {
  return THEME.decadeRamp[decade] || THEME.muted;
}

/* --- Shared building blocks so every chart looks like one system. --- */
const baseTextStyle = { color: THEME.ink, fontFamily: THEME.fontSans };

const axisCommon = {
  axisLine: { lineStyle: { color: THEME.border } },
  axisTick: { show: false },
  axisLabel: { color: THEME.muted, fontFamily: THEME.fontSans, fontSize: 11 },
  nameTextStyle: { color: THEME.muted, fontFamily: THEME.fontSans, fontSize: 12 },
  splitLine: { lineStyle: { color: THEME.border, type: "dashed" } },
};

const tooltipCommon = {
  backgroundColor: THEME.surface,
  borderColor: THEME.border,
  borderWidth: 1,
  padding: [8, 12],
  textStyle: { color: THEME.ink, fontFamily: THEME.fontSans, fontSize: 12 },
  extraCssText: "box-shadow: 0 4px 16px rgba(25,25,23,.08); border-radius: 8px;",
};

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** Format an ISO date (YYYY-MM-DD) as e.g. "Mar 1984" for tooltips. */
function fmtMonth(iso) {
  const [y, m] = iso.split("-");
  return `${MONTHS[Number(m) - 1]} ${y}`;
}

// -----------------------------------------------------------------------------
// Compact line chart for a single indicator series (Macro cards + Home tiles).
// -----------------------------------------------------------------------------
export function lineOption(series, indicator) {
  const dates = series.points.map((p) => p.date);
  const values = series.points.map((p) => p.value);
  return {
    textStyle: baseTextStyle,
    grid: { left: 40, right: 12, top: 12, bottom: 24 },
    tooltip: {
      ...tooltipCommon,
      trigger: "axis",
      axisPointer: { type: "line", lineStyle: { color: THEME.border } },
      formatter: (params) => {
        const p = params[0];
        return `${fmtMonth(p.axisValue)}<br/><b>${p.data}</b> ${indicator.units}`;
      },
    },
    xAxis: {
      type: "category",
      data: dates,
      boundaryGap: false,
      ...axisCommon,
      splitLine: { show: false },
      axisLabel: {
        ...axisCommon.axisLabel,
        formatter: (v) => v.slice(0, 4),
        interval: (i, v) => v.endsWith("-01-01") && Number(v.slice(0, 4)) % 20 === 0,
      },
    },
    yAxis: {
      type: "value",
      scale: true,
      ...axisCommon,
      axisLine: { show: false },
      axisLabel: { ...axisCommon.axisLabel, formatter: "{value}%" },
    },
    series: [
      {
        type: "line",
        data: values,
        showSymbol: false,
        smooth: false,
        lineStyle: { color: THEME.accent, width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(204,120,92,0.18)" },
            { offset: 1, color: "rgba(204,120,92,0.00)" },
          ]),
        },
      },
    ],
  };
}

/** Ordinary least-squares fit (inflation ~ unemployment) for the optional trend overlay. */
function olsFit(points) {
  const n = points.length;
  const meanX = points.reduce((s, p) => s + p.unemployment, 0) / n;
  const meanY = points.reduce((s, p) => s + p.inflation, 0) / n;
  let num = 0, den = 0;
  for (const p of points) {
    num += (p.unemployment - meanX) * (p.inflation - meanY);
    den += (p.unemployment - meanX) ** 2;
  }
  const slope = den === 0 ? 0 : num / den;
  return { slope, intercept: meanY - slope * meanX };
}

const relationTooltip = {
  ...tooltipCommon,
  formatter: (p) =>
    `${fmtMonth(p.data[2])}<br/>Unemployment <b>${p.data[0]}%</b><br/>Inflation <b>${p.data[1]}%</b>`,
};
const relationAxis = (name, gap) => ({
  type: "value",
  name,
  nameLocation: "middle",
  nameGap: gap,
  ...axisCommon,
  axisLine: { show: false },
  axisLabel: { ...axisCommon.axisLabel, formatter: "{value}%" },
});

// -----------------------------------------------------------------------------
// Scatter chart for a relationship between two series (e.g. unemployment vs.
// inflation), one series per ordered category (decade) so color never carries
// identity alone — the legend does that. `trend` overlays an OLS fit line (per
// DESIGN.md: "a scatter ... optionally with a fitted line"); it's excluded from
// the legend since it's a statistical overlay, not a category.
// -----------------------------------------------------------------------------
export function scatterOption(points, { trend = false } = {}) {
  const decades = [...new Set(points.map((p) => p.decade))].sort((a, b) => a - b);
  const series = decades.map((decade) => ({
    name: `${decade}s`,
    type: "scatter",
    symbolSize: 8,
    data: points
      .filter((p) => p.decade === decade)
      .map((p) => [p.unemployment, p.inflation, p.date]),
    itemStyle: { color: decadeColor(decade), opacity: 0.5 },
    emphasis: {
      itemStyle: { opacity: 1, borderColor: THEME.surface, borderWidth: 2 },
    },
  }));

  if (trend) {
    const { slope, intercept } = olsFit(points);
    const xs = points.map((p) => p.unemployment);
    const xMin = Math.min(...xs), xMax = Math.max(...xs);
    series.push({
      name: "Trend",
      type: "line",
      showSymbol: false,
      silent: true,
      tooltip: { show: false },
      lineStyle: { color: THEME.accentStrong, width: 2, type: "dashed" },
      data: [
        [xMin, intercept + slope * xMin],
        [xMax, intercept + slope * xMax],
      ],
    });
  }

  return {
    textStyle: baseTextStyle,
    grid: { left: 48, right: 16, top: 12, bottom: 56 },
    legend: {
      data: decades.map((d) => `${d}s`), // explicit: keeps the "Trend" overlay out of the legend
      bottom: 0,
      icon: "circle",
      itemWidth: 8,
      itemHeight: 8,
      textStyle: { color: THEME.muted, fontFamily: THEME.fontSans, fontSize: 11 },
    },
    tooltip: relationTooltip,
    xAxis: relationAxis("Unemployment", 28),
    yAxis: relationAxis("Inflation (YoY)", 36),
    series,
  };
}

// -----------------------------------------------------------------------------
// Small multiples: one mini scatter panel per decade on shared axis scales, per
// DESIGN.md's small-multiples building block. No per-panel legend needed — the
// panel title is the category label, and every panel uses the single accent
// color (same "single series needs no legend" convention as the line chart).
// -----------------------------------------------------------------------------
export function smallMultiplesOption(points) {
  const decades = [...new Set(points.map((p) => p.decade))].sort((a, b) => a - b);
  const xs = points.map((p) => p.unemployment);
  const ys = points.map((p) => p.inflation);
  const xMin = Math.floor(Math.min(...xs)), xMax = Math.ceil(Math.max(...xs));
  const yMin = Math.floor(Math.min(...ys)), yMax = Math.ceil(Math.max(...ys));

  const cols = 4;
  const rows = Math.ceil(decades.length / cols);
  const gap = 4;
  const cellW = (100 - gap * (cols - 1)) / cols;
  const cellH = (100 - gap * (rows - 1)) / rows;

  const grid = [], xAxis = [], yAxis = [], series = [], title = [];
  decades.forEach((decade, i) => {
    const col = i % cols;
    const row = Math.floor(i / cols);
    const left = col * (cellW + gap);
    const top = row * (cellH + gap) + 8;
    grid.push({
      left: `${left}%`, top: `${top}%`, width: `${cellW}%`, height: `${cellH - 8}%`,
      show: true, borderColor: THEME.border, borderWidth: 1, backgroundColor: THEME.surface,
    });
    xAxis.push({ gridIndex: i, type: "value", min: xMin, max: xMax, show: false });
    yAxis.push({ gridIndex: i, type: "value", min: yMin, max: yMax, show: false });
    title.push({
      text: `${decade}s`,
      left: `${left}%`,
      top: `${top - 7}%`,
      textStyle: { color: THEME.muted, fontFamily: THEME.fontSans, fontSize: 11, fontWeight: "normal" },
    });
    series.push({
      type: "scatter",
      xAxisIndex: i,
      yAxisIndex: i,
      symbolSize: 5,
      data: points.filter((p) => p.decade === decade).map((p) => [p.unemployment, p.inflation, p.date]),
      itemStyle: { color: THEME.accent, opacity: 0.55 },
    });
  });

  return {
    textStyle: baseTextStyle,
    title,
    grid,
    xAxis,
    yAxis,
    tooltip: relationTooltip,
    series,
  };
}
