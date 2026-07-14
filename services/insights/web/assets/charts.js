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
};

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

// -----------------------------------------------------------------------------
// Dual-line chart: inflation vs. unemployment over time (Phillips-curve view).
// Two series always need a legend — color alone can't carry series identity.
// -----------------------------------------------------------------------------
export function phillipsLineOption(points) {
  const dates = points.map((p) => p.date);
  const inflation = points.map((p) => p.inflation);
  const unemployment = points.map((p) => p.unemployment);
  return {
    textStyle: baseTextStyle,
    grid: { left: 40, right: 12, top: 40, bottom: 24 },
    legend: {
      top: 0,
      left: 0,
      icon: "roundRect",
      itemWidth: 12,
      itemHeight: 4,
      textStyle: { color: THEME.muted, fontFamily: THEME.fontSans, fontSize: 12 },
    },
    tooltip: {
      ...tooltipCommon,
      trigger: "axis",
      axisPointer: { type: "line", lineStyle: { color: THEME.border } },
      formatter: (params) =>
        [fmtMonth(params[0].axisValue)]
          .concat(params.map((p) => `<b>${p.data}%</b> ${p.seriesName}`))
          .join("<br/>"),
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
        name: "Inflation (CPI, YoY)",
        type: "line",
        data: inflation,
        showSymbol: false,
        smooth: false,
        lineStyle: { color: THEME.accent, width: 2 },
      },
      {
        name: "Unemployment rate",
        type: "line",
        data: unemployment,
        showSymbol: false,
        smooth: false,
        lineStyle: { color: THEME.accentStrong, width: 2, type: "dashed" },
      },
    ],
  };
}
