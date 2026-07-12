// =============================================================================
// charts.js — ECharts option builders, themed to the design tokens.
// Depends on the global `echarts` (loaded via <script> in index.html).
// Chart philosophy (see DESIGN.md): no chart junk — hairline gridlines, muted
// axis labels, white tooltips, ~0.5 scatter opacity. Color ONLY encodes decade.
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
  // Decade ramp, oldest→newest (warm→cool). Index 0 = 1960s … index 7 = 2030s.
  decadeRamp: ["#B15C3F", "#CC785C", "#D9A066", "#C9B458", "#7FA47B", "#5B8AA6", "#3E5C76", "#2E4257"],
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

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** Format an ISO date (YYYY-MM-DD) as e.g. "Mar 1984" for tooltips. */
function fmtMonth(iso) {
  const [y, m] = iso.split("-");
  return `${MONTHS[Number(m) - 1]} ${y}`;
}

/** Signed, fixed-precision helper for slopes / correlations. */
function signed(n, digits = 2) {
  return (n > 0 ? "+" : "") + Number(n).toFixed(digits);
}

/**
 * Endpoints of a fitted line y = slope*x + intercept spanning a decade's actual
 * unemployment range, so the fit only extends across observed data.
 */
function fitLine(points, decade, slope, intercept) {
  const xs = points.filter((p) => p.decade === decade).map((p) => p.unemployment);
  if (!xs.length) return [];
  const xMin = Math.min(...xs);
  const xMax = Math.max(...xs);
  return [
    [xMin, slope * xMin + intercept],
    [xMax, slope * xMax + intercept],
  ];
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
// Treatment 1 (A/B variant A) — "By decade": scatter colored by decade, with a
// decade legend and a light per-decade fit line (slope/intercept from stats).
// -----------------------------------------------------------------------------
export function scatterByDecadeOption(view) {
  const decades = [...new Set(view.points.map((p) => p.decade))].sort((a, b) => a - b);
  const statsByDecade = Object.fromEntries((view.decade_stats || []).map((s) => [s.decade, s]));

  const pointSeries = decades.map((decade) => ({
    name: `${decade}s`,
    type: "scatter",
    symbolSize: 7,
    itemStyle: { color: decadeColor(decade), opacity: 0.5 }, // subtle opacity for overplotting
    emphasis: { itemStyle: { opacity: 0.95, borderColor: THEME.surface, borderWidth: 1 } },
    // [unemployment (x), inflation (y), date] — date carried for the tooltip.
    data: view.points.filter((p) => p.decade === decade).map((p) => [p.unemployment, p.inflation, p.date]),
  }));

  // Light per-decade fit lines (only where we reported stats for that decade).
  const fitSeries = decades
    .filter((decade) => statsByDecade[decade])
    .map((decade) => {
      const s = statsByDecade[decade];
      return {
        name: `${decade}s`, // share legend entry with its scatter so toggling hides both
        type: "line",
        data: fitLine(view.points, decade, s.slope, s.intercept),
        showSymbol: false,
        silent: true,
        lineStyle: { color: decadeColor(decade), width: 1.5, opacity: 0.45 },
        tooltip: { show: false },
        z: 1,
      };
    });

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
        p.componentSubType !== "scatter"
          ? ""
          : `${fmtMonth(p.data[2])} · <b>${p.seriesName}</b><br/>` +
            `Unemployment <b>${p.data[0]}%</b><br/>Inflation <b>${p.data[1]}%</b>`,
    },
    xAxis: { type: "value", name: "Unemployment (%)", nameLocation: "middle", nameGap: 30, scale: true, ...axisCommon },
    yAxis: { type: "value", name: "Inflation (%)", nameLocation: "middle", nameGap: 38, scale: true, ...axisCommon },
    series: [...pointSeries, ...fitSeries],
  };
}

// -----------------------------------------------------------------------------
// Treatment 2 (A/B variant B) — "Then vs now": the money chart. Two point clouds
// (then.decade vs now.decade), each with its fitted line; one steep, one flat —
// the flattening made obvious. Each fit line is annotated with its slope.
// -----------------------------------------------------------------------------
export function thenVsNowOption(view) {
  const { then, now } = view;

  const cloud = (stat) => ({
    name: `${stat.decade}s`,
    type: "scatter",
    symbolSize: 8,
    itemStyle: { color: decadeColor(stat.decade), opacity: 0.5 },
    emphasis: { itemStyle: { opacity: 0.95, borderColor: THEME.surface, borderWidth: 1 } },
    data: view.points.filter((p) => p.decade === stat.decade).map((p) => [p.unemployment, p.inflation, p.date]),
    z: 2,
  });

  const fit = (stat) => ({
    name: `${stat.decade}s`,
    type: "line",
    data: fitLine(view.points, stat.decade, stat.slope, stat.intercept),
    showSymbol: false,
    silent: true,
    lineStyle: { color: decadeColor(stat.decade), width: 2.5 },
    tooltip: { show: false },
    z: 3,
    // Annotate the line end with the decade slope — the headline number.
    endLabel: {
      show: true,
      formatter: `${stat.decade}s · slope ${signed(stat.slope)}`,
      color: decadeColor(stat.decade),
      fontFamily: THEME.fontSans,
      fontSize: 12,
      fontWeight: 600,
      backgroundColor: "rgba(255,255,255,0.85)",
      padding: [2, 4],
    },
  });

  return {
    textStyle: baseTextStyle,
    grid: { left: 56, right: 90, top: 16, bottom: 56 }, // extra right pad for end labels
    legend: {
      data: [`${then.decade}s`, `${now.decade}s`],
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
        p.componentSubType !== "scatter"
          ? ""
          : `${fmtMonth(p.data[2])} · <b>${p.seriesName}</b><br/>` +
            `Unemployment <b>${p.data[0]}%</b><br/>Inflation <b>${p.data[1]}%</b>`,
    },
    xAxis: { type: "value", name: "Unemployment (%)", nameLocation: "middle", nameGap: 30, scale: true, ...axisCommon },
    yAxis: { type: "value", name: "Inflation (%)", nameLocation: "middle", nameGap: 38, scale: true, ...axisCommon },
    series: [cloud(then), cloud(now), fit(then), fit(now)],
  };
}

// -----------------------------------------------------------------------------
// Treatment 3 — "Small multiples": one mini scatter per decade in decade_stats,
// each labeled "{decade}s · slope {slope}", on shared scales so panels compare.
// -----------------------------------------------------------------------------
export function smallMultiplesOption(view) {
  const stats = [...(view.decade_stats || [])].sort((a, b) => a.decade - b.decade);
  const decades = stats.map((s) => s.decade);

  // Shared scales across panels so panels are visually comparable.
  const xs = view.points.map((p) => p.unemployment);
  const ys = view.points.map((p) => p.inflation);
  const xMax = Math.ceil(Math.max(...xs));
  const yMax = Math.ceil(Math.max(...ys));
  const yMin = Math.floor(Math.min(...ys));

  const cols = Math.min(4, decades.length || 1);
  const rows = Math.ceil(decades.length / cols);
  const padL = 4, padR = 3, padT = 12, padB = 4, gapX = 4, gapY = 14; // percentages
  const cellW = (100 - padL - padR - (cols - 1) * gapX) / cols;
  const cellH = (100 - padT - padB - (rows - 1) * gapY) / rows;

  const grids = [];
  const xAxes = [];
  const yAxes = [];
  const series = [];
  const titles = [];

  stats.forEach((s, i) => {
    const decade = s.decade;
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
    // Light per-panel fit line so the slope is visible, not just labelled.
    series.push({
      type: "line", xAxisIndex: i, yAxisIndex: i, silent: true, showSymbol: false,
      data: fitLine(view.points, decade, s.slope, s.intercept),
      lineStyle: { color: decadeColor(decade), width: 1.5, opacity: 0.6 },
      tooltip: { show: false },
    });

    titles.push({
      text: `${decade}s`,
      subtext: `slope ${signed(s.slope)}`,
      left: `${left}%`,
      top: `${Math.max(top - 10, 0)}%`,
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
      formatter: (p) =>
        p.componentSubType !== "scatter"
          ? ""
          : `${fmtMonth(p.data[2])}<br/>Unemployment <b>${p.data[0]}%</b><br/>Inflation <b>${p.data[1]}%</b>`,
    },
    series,
  };
}

// -----------------------------------------------------------------------------
// "Correlation by decade" horizontal bar strip (from decade_stats). Each bar is
// colored by its decade; a zero reference line makes the trend toward zero read.
// -----------------------------------------------------------------------------
export function correlationStripOption(decadeStats) {
  const rows = [...(decadeStats || [])].sort((a, b) => a.decade - b.decade);
  const categories = rows.map((d) => `${d.decade}s`);
  return {
    textStyle: baseTextStyle,
    grid: { left: 56, right: 48, top: 8, bottom: 24 },
    tooltip: {
      ...tooltipCommon,
      trigger: "item",
      formatter: (p) => {
        const row = rows[p.dataIndex];
        return `<b>${categories[p.dataIndex]}</b><br/>Correlation <b>${signed(row.correlation)}</b><br/>${row.months} months`;
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
          formatter: (p) => signed(p.value),
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
