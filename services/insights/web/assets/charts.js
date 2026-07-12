// =============================================================================
// charts.js — ECharts option builders, themed to the design tokens.
// Depends on the global `echarts` (loaded via <script> in index.html).
// Chart philosophy (see DESIGN.md): no chart junk — light gridlines, muted axis
// labels, restrained tooltips, colors drawn from the shared tokens.
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
  // Decade ramp, oldest→newest (warm→cool). Index 0 = 1960s … index 6 = 2020s.
  decadeRamp: ["#B15C3F", "#CC785C", "#D9A066", "#C9B458", "#7FA47B", "#5B8AA6", "#3E5C76"],
};

/** Map a decade (e.g. 1980) to its ramp color. Falls back to accent. */
export function decadeColor(decade) {
  const idx = Math.round((decade - 1960) / 10);
  return THEME.decadeRamp[idx] ?? THEME.accent;
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

/** Format an ISO date (YYYY-MM-DD) as e.g. "Mar 1984" for tooltips. */
function fmtMonth(iso) {
  const [y, m] = iso.split("-");
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${months[Number(m) - 1]} ${y}`;
}

// -----------------------------------------------------------------------------
// Section A — compact line chart for a single indicator series.
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
      axisLabel: { ...axisCommon.axisLabel, formatter: (v) => v.slice(0, 4), interval: (i, v) => v.endsWith("-01-01") && Number(v.slice(0, 4)) % 20 === 0 },
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
// Section B, treatment 1 — "By decade": scatter colored by decade, legend by decade.
// -----------------------------------------------------------------------------
export function scatterByDecadeOption(view) {
  const decades = [...new Set(view.points.map((p) => p.decade))].sort((a, b) => a - b);
  // One series per decade so the legend and per-series color work naturally.
  const series = decades.map((decade) => ({
    name: `${decade}s`,
    type: "scatter",
    symbolSize: 7,
    itemStyle: { color: decadeColor(decade), opacity: 0.55 }, // subtle opacity for overplotting
    emphasis: { itemStyle: { opacity: 0.95, borderColor: THEME.surface, borderWidth: 1 } },
    // [unemployment (x), inflation (y), date] — date carried for the tooltip.
    data: view.points.filter((p) => p.decade === decade).map((p) => [p.unemployment, p.inflation, p.date]),
  }));
  return {
    textStyle: baseTextStyle,
    color: decades.map(decadeColor),
    grid: { left: 56, right: 24, top: 16, bottom: 56 },
    legend: {
      data: decades.map((d) => `${d}s`),
      bottom: 0,
      icon: "circle",
      itemWidth: 9,
      itemHeight: 9,
      textStyle: { color: THEME.muted, fontFamily: THEME.fontSans, fontSize: 12 },
    },
    tooltip: {
      ...tooltipCommon,
      trigger: "item",
      formatter: (p) =>
        `${fmtMonth(p.data[2])} · <b>${p.seriesName}</b><br/>` +
        `Unemployment <b>${p.data[0]}%</b><br/>Inflation <b>${p.data[1]}%</b>`,
    },
    xAxis: { type: "value", name: "Unemployment (%)", nameLocation: "middle", nameGap: 30, scale: true, ...axisCommon },
    yAxis: { type: "value", name: "Inflation (%)", nameLocation: "middle", nameGap: 38, scale: true, ...axisCommon },
    series,
  };
}

// -----------------------------------------------------------------------------
// Section B, treatment 2 — "Small multiples": one mini scatter per decade.
// Built with an array of grids/axes so each panel is independently framed; the
// flattening is visible panel-to-panel via the per-panel correlation label.
// -----------------------------------------------------------------------------
export function smallMultiplesOption(view) {
  const decades = [...new Set(view.points.map((p) => p.decade))].sort((a, b) => a - b);
  const corrByDecade = Object.fromEntries(view.decade_correlations.map((d) => [d.decade, d.correlation]));

  // Shared scales across panels so panels are visually comparable.
  const xs = view.points.map((p) => p.unemployment);
  const ys = view.points.map((p) => p.inflation);
  const xMax = Math.ceil(Math.max(...xs));
  const yMax = Math.ceil(Math.max(...ys));
  const yMin = Math.floor(Math.min(...ys));

  const cols = Math.min(4, decades.length);
  const rows = Math.ceil(decades.length / cols);
  const padL = 4, padR = 3, padT = 12, padB = 4, gapX = 4, gapY = 12; // percentages
  const cellW = (100 - padL - padR - (cols - 1) * gapX) / cols;
  const cellH = (100 - padT - padB - (rows - 1) * gapY) / rows;

  const grids = [];
  const xAxes = [];
  const yAxes = [];
  const series = [];
  const titles = [];

  decades.forEach((decade, i) => {
    const r = Math.floor(i / cols);
    const c = i % cols;
    const left = padL + c * (cellW + gapX);
    const top = padT + r * (cellH + gapY);

    grids.push({ left: `${left}%`, top: `${top}%`, width: `${cellW}%`, height: `${cellH}%`, containLabel: true });
    xAxes.push({
      gridIndex: i, type: "value", min: 0, max: xMax, ...axisCommon,
      splitLine: { show: false }, axisLabel: { ...axisCommon.axisLabel, fontSize: 9 },
    });
    yAxes.push({
      gridIndex: i, type: "value", min: yMin, max: yMax, ...axisCommon,
      axisLabel: { ...axisCommon.axisLabel, fontSize: 9 },
    });
    series.push({
      type: "scatter", xAxisIndex: i, yAxisIndex: i, symbolSize: 4,
      itemStyle: { color: decadeColor(decade), opacity: 0.5 },
      data: view.points.filter((p) => p.decade === decade).map((p) => [p.unemployment, p.inflation, p.date]),
    });

    const corr = corrByDecade[decade];
    const corrStr = corr == null ? "n/a" : (corr > 0 ? "+" : "") + corr.toFixed(2);
    titles.push({
      text: `${decade}s`,
      subtext: `r = ${corrStr}`,
      left: `${left}%`,
      top: `${Math.max(top - 9, 0)}%`,
      textStyle: { color: THEME.ink, fontFamily: THEME.fontSans, fontSize: 13, fontWeight: 600 },
      subtextStyle: { color: decadeColor(decade), fontFamily: THEME.fontSans, fontSize: 11 },
    });
  });

  return {
    textStyle: baseTextStyle,
    title: titles,
    grid: grids,
    xAxis: xAxes,
    yAxis: yAxes,
    tooltip: {
      ...tooltipCommon,
      trigger: "item",
      formatter: (p) => `${fmtMonth(p.data[2])}<br/>Unemployment <b>${p.data[0]}%</b><br/>Inflation <b>${p.data[1]}%</b>`,
    },
    series,
  };
}

// -----------------------------------------------------------------------------
// Section B, treatment 3 — "Over time": time-ordered connected scatter, color
// graded by time (warm→cool). Shows the loops collapsing toward a flat cloud.
// -----------------------------------------------------------------------------
export function overTimeOption(view) {
  // Points are already date-ordered from the API. Third dim = time index (for grading).
  const data = view.points.map((p, i) => [p.unemployment, p.inflation, i, p.date]);
  const n = data.length;
  const firstYear = view.points[0].date.slice(0, 4);
  const lastYear = view.points[n - 1].date.slice(0, 4);

  return {
    textStyle: baseTextStyle,
    grid: { left: 56, right: 24, top: 16, bottom: 72 },
    // Continuous time gradient legend along the bottom.
    visualMap: {
      type: "continuous",
      min: 0,
      max: n - 1,
      dimension: 2,
      orient: "horizontal",
      bottom: 4,
      left: "center",
      itemWidth: 14,
      itemHeight: 200,
      calculable: false,
      text: [lastYear, firstYear],
      textStyle: { color: THEME.muted, fontFamily: THEME.fontSans, fontSize: 12 },
      inRange: { color: THEME.decadeRamp },
    },
    tooltip: {
      ...tooltipCommon,
      trigger: "item",
      formatter: (p) => `${fmtMonth(p.data[3])}<br/>Unemployment <b>${p.data[0]}%</b><br/>Inflation <b>${p.data[1]}%</b>`,
    },
    xAxis: { type: "value", name: "Unemployment (%)", nameLocation: "middle", nameGap: 30, scale: true, ...axisCommon },
    yAxis: { type: "value", name: "Inflation (%)", nameLocation: "middle", nameGap: 38, scale: true, ...axisCommon },
    series: [
      {
        type: "line",
        data,
        showSymbol: true,
        symbolSize: 5,
        // The connecting line is faint so the point cloud dominates; visualMap
        // colors both line segments and symbols by time.
        lineStyle: { width: 1, opacity: 0.35 },
        itemStyle: { opacity: 0.75 },
      },
    ],
  };
}

// -----------------------------------------------------------------------------
// Section B — "Correlation by decade" horizontal bar strip.
// Diverging sense around zero; each bar colored by its decade. Makes the trend
// toward zero explicit.
// -----------------------------------------------------------------------------
export function correlationStripOption(decadeCorrelations) {
  const rows = [...decadeCorrelations].sort((a, b) => a.decade - b.decade);
  const categories = rows.map((d) => `${d.decade}s`);
  return {
    textStyle: baseTextStyle,
    grid: { left: 56, right: 48, top: 8, bottom: 24 },
    tooltip: {
      ...tooltipCommon,
      trigger: "item",
      formatter: (p) => {
        const row = rows[p.dataIndex];
        return `<b>${categories[p.dataIndex]}</b><br/>Correlation <b>${row.correlation > 0 ? "+" : ""}${row.correlation}</b><br/>${row.months} months`;
      },
    },
    xAxis: {
      type: "value",
      min: -1,
      max: 1,
      ...axisCommon,
      axisLabel: { ...axisCommon.axisLabel, formatter: (v) => v.toFixed(1) },
    },
    yAxis: {
      type: "category",
      data: categories,
      inverse: true, // oldest decade on top
      ...axisCommon,
      splitLine: { show: false },
      axisLabel: { ...axisCommon.axisLabel, fontSize: 12 },
    },
    series: [
      {
        type: "bar",
        data: rows.map((d) => ({ value: d.correlation, itemStyle: { color: decadeColor(d.decade) } })),
        barWidth: "55%",
        itemStyle: { borderRadius: 3 },
        label: {
          show: true,
          position: "right",
          formatter: (p) => (p.value > 0 ? "+" : "") + p.value.toFixed(2),
          color: THEME.muted,
          fontFamily: THEME.fontSans,
          fontSize: 12,
        },
        // Reference line at zero so "toward zero" reads instantly.
        markLine: {
          symbol: "none",
          silent: true,
          lineStyle: { color: THEME.muted, type: "solid", width: 1, opacity: 0.4 },
          data: [{ xAxis: 0 }],
          label: { show: false },
        },
      },
    ],
  };
}
