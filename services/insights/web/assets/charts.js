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
  // Ordered oldest→newest, warm→cool decade ramp (mirrors --decade-* in styles.css /
  // DESIGN.md). Color only ever encodes the ordered time-category (decade), never rank.
  decadeRamp: ["#B15C3F", "#CC785C", "#D9A066", "#C9B458", "#7FA47B", "#5B8AA6", "#3E5C76", "#2E4257"],
};

/** Map a decade (e.g. 1980) to its ordered-ramp color; clamps outside 1960s–2030s. */
export function decadeColor(decade) {
  const i = Math.round((decade - 1960) / 10);
  return THEME.decadeRamp[Math.max(0, Math.min(THEME.decadeRamp.length - 1, i))];
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

const decadeLabel = (d) => `${d}s`;

// -----------------------------------------------------------------------------
// Connected time-path ("Phillips path"): monthly points joined in chronological
// order, split into one line series per decade so color encodes the ordered
// time-category only. A marker-less "bridge" copy of each decade's first point
// is appended to the prior decade so the path stays unbroken across boundaries.
// -----------------------------------------------------------------------------
export function pathOption(points, decades) {
  const idxOf = (d) => decades.indexOf(d);
  const mk = (p, bridge) => ({
    value: [p.unemployment, p.inflation],
    date: p.date,
    decade: p.decade,
    ...(bridge ? { symbol: "none" } : {}), // bridge copy draws the line, not a duplicate marker
  });

  const buckets = decades.map(() => []);
  points.forEach((p) => buckets[idxOf(p.decade)].push(mk(p, false)));
  for (let k = 1; k < decades.length; k++) {
    const firstOfK = points.find((p) => p.decade === decades[k]);
    if (firstOfK) buckets[k - 1].push(mk(firstOfK, true));
  }

  const series = decades.map((d, i) => ({
    type: "line",
    name: decadeLabel(d),
    data: buckets[i],
    showSymbol: true,
    symbolSize: 5,
    smooth: false,
    z: i,
    lineStyle: { color: decadeColor(d), width: 1.5, opacity: 0.9 },
    itemStyle: { color: decadeColor(d), opacity: 0.7 }, // slight opacity so dense loops read
    emphasis: { itemStyle: { opacity: 1, borderColor: THEME.surface, borderWidth: 2 } },
  }));

  return {
    textStyle: baseTextStyle,
    grid: { left: 56, right: 24, top: 24, bottom: 48 },
    tooltip: {
      ...tooltipCommon,
      trigger: "item",
      formatter: (pr) => {
        const d = pr.data;
        return `${fmtMonth(d.date)}<br/>Unemployment <b>${d.value[0]}%</b><br/>Inflation <b>${d.value[1]}%</b>`;
      },
    },
    xAxis: {
      type: "value", scale: true, name: "Unemployment (%)", nameLocation: "middle", nameGap: 30,
      ...axisCommon, axisLabel: { ...axisCommon.axisLabel, formatter: "{value}%" },
    },
    yAxis: {
      type: "value", scale: true, name: "Inflation, YoY (%)", nameLocation: "middle", nameGap: 42,
      ...axisCommon, axisLine: { show: false }, axisLabel: { ...axisCommon.axisLabel, formatter: "{value}%" },
    },
    series,
  };
}

// -----------------------------------------------------------------------------
// Small-multiples: one identical-scale scatter panel per decade. Pass shared
// bounds (from scatterBounds) so every panel is directly comparable; the panel
// title carries identity, so color (decade) is never the sole encoding.
// -----------------------------------------------------------------------------
export function scatterBounds(points) {
  const pad = (min, max) => { const p = (max - min) * 0.08 || 1; return [Math.floor(min - p), Math.ceil(max + p)]; };
  const [xMin, xMax] = pad(Math.min(...points.map((p) => p.unemployment)), Math.max(...points.map((p) => p.unemployment)));
  const [yMin, yMax] = pad(Math.min(...points.map((p) => p.inflation)), Math.max(...points.map((p) => p.inflation)));
  return { xMin, xMax, yMin, yMax };
}

export function smallMultipleOption(decade, pts, bounds) {
  const panelAxis = { ...axisCommon, axisLabel: { ...axisCommon.axisLabel, fontSize: 10, formatter: "{value}%" } };
  return {
    textStyle: baseTextStyle,
    grid: { left: 36, right: 12, top: 10, bottom: 24 },
    tooltip: {
      ...tooltipCommon,
      trigger: "item",
      formatter: (p) => {
        const [u, i, date] = p.data;
        return `${fmtMonth(date)}<br/>Unemployment <b>${u}%</b><br/>Inflation <b>${i}%</b>`;
      },
    },
    xAxis: { type: "value", min: bounds.xMin, max: bounds.xMax, ...panelAxis },
    yAxis: { type: "value", min: bounds.yMin, max: bounds.yMax, ...panelAxis, axisLine: { show: false } },
    series: [{
      type: "scatter",
      symbolSize: 6,
      itemStyle: { color: decadeColor(decade), opacity: 0.5 },
      emphasis: { itemStyle: { opacity: 0.9, borderColor: THEME.surface, borderWidth: 1 } },
      data: pts.map((p) => [p.unemployment, p.inflation, p.date]),
    }],
  };
}
