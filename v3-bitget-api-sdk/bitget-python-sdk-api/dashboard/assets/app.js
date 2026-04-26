"use strict";

const MARK_CSS = {
  "◎": "cell-mark-bull",
  "○": "cell-mark-aux",
  "△": "cell-mark-cond",
  "×": "cell-mark-na",
  "?": "cell-mark-tbd",
  "✅": "cell-mark-live",
  "❌": "cell-mark-nogo",
  "⚠": "cell-mark-warn",
};

document.querySelectorAll("header nav button").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("header nav button").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll("main .tab").forEach((s) => s.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
  });
});

async function fetchJSON(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`fetch ${path} failed: ${r.status}`);
  return r.json();
}

function fmtUSD(v) {
  const sign = v >= 0 ? "+" : "−";
  return `${sign}$${Math.abs(v).toFixed(2)}`;
}

function classNum(v) { return v >= 0 ? "num pos" : "num neg"; }

async function renderProgress() {
  const d = await fetchJSON("data/progress.json");
  document.getElementById("source-note").textContent = `source: ${d.source_csv}`;
  document.getElementById("kpi-goal").textContent = d.goal_per_day.toFixed(0);
  document.getElementById("kpi-current").textContent = fmtUSD(d.current_per_day) + "/day";
  document.getElementById("kpi-current").className = "kpi-value " + (d.current_per_day >= 0 ? "" : "gap");
  document.getElementById("kpi-gap").textContent = fmtUSD(-d.gap_per_day) + "/day";
  document.getElementById("kpi-days").textContent = d.period_days + " days";
  document.getElementById("kpi-total").textContent = fmtUSD(d.total_net_usd);

  const pct = Math.max(0, Math.min(100, (d.current_per_day / d.goal_per_day) * 100));
  document.getElementById("progress-fill").style.width = pct + "%";
  document.getElementById("progress-pct").textContent = pct.toFixed(1) + "%";

  const rTbody = document.querySelector("#regime-table tbody");
  rTbody.innerHTML = "";
  for (const r of d.regimes) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${r.regime}</td><td class="num">${r.days}</td>` +
      `<td class="${classNum(r.net_usd)}">${fmtUSD(r.net_usd)}</td>` +
      `<td class="${classNum(r.per_regime_day)}">${fmtUSD(r.per_regime_day)}/rg-day</td>`;
    rTbody.appendChild(tr);
  }

  const pTbody = document.querySelector("#priority-table tbody");
  pTbody.innerHTML = "";
  const sorted = d.priorities.slice().sort((a, b) => b.net_usd - a.net_usd);
  for (const p of sorted) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>P${p.priority}</td><td>${p.regime}</td>` +
      `<td class="num">${p.trades}</td>` +
      `<td class="${classNum(p.net_usd)}">${fmtUSD(p.net_usd)}</td>` +
      `<td class="${classNum(p.per_regime_day)}">${fmtUSD(p.per_regime_day)}</td>`;
    pTbody.appendChild(tr);
  }
}

let firesData = null;
let pricesData = null;
let regimeData = null;
let firesChart = null;
const enabledPriorities = new Set();

const REGIME_BG = {
  downtrend: "rgba(198, 40, 40, 0.10)",
  range:     "rgba(249, 168, 37, 0.13)",
  uptrend:   "rgba(46, 125, 50, 0.10)",
  mixed:     "rgba(106, 76, 147, 0.13)",
  unknown:   "rgba(158, 158, 158, 0.06)",
};

const regimeBgPlugin = {
  id: "regimeBg",
  beforeDatasetsDraw(chart) {
    if (!document.getElementById("fires-regime-bg")?.checked) return;
    if (!regimeData?.days?.length) return;
    const { ctx, chartArea, scales } = chart;
    const xs = scales.x;
    if (!xs) return;
    const xMin = xs.min, xMax = xs.max;
    ctx.save();
    for (const d of regimeData.days) {
      const start = new Date(d.date + "T00:00:00Z").getTime();
      const end = start + 86400000;
      if (end < xMin || start > xMax) continue;
      const x1 = xs.getPixelForValue(Math.max(start, xMin));
      const x2 = xs.getPixelForValue(Math.min(end, xMax));
      ctx.fillStyle = REGIME_BG[d.regime] || REGIME_BG.unknown;
      ctx.fillRect(x1, chartArea.top, x2 - x1, chartArea.bottom - chartArea.top);
    }
    ctx.restore();
  },
};

const PRIO_COLOR = {
  1: "#1f7a1f", 2: "#2e7d32", 3: "#388e3c", 4: "#7b1fa2",
  21: "#1565c0", 22: "#0288d1", 23: "#5d4037", 24: "#ef6c00",
  25: "#c62828",
};
function prioColor(p) { return PRIO_COLOR[p] || "#666"; }

const EXIT_STYLE = {
  TP_FILLED: { color: "#00b8d4", marker: "triangle", label: "TP" },
  SL_FILLED: { color: "#000", marker: "triangle", label: "SL" },
  TIME_EXIT: { color: "#555", marker: "triangle", label: "TIME_EXIT" },
  TRAIL_EXIT: { color: "#1976d2", marker: "triangle", label: "TRAIL_EXIT" },
  STOCH_REVERSE_EXIT: { color: "#ff6f00", marker: "triangle", label: "STOCH_REV" },
  RSI_REVERSE_EXIT: { color: "#e64a19", marker: "triangle", label: "RSI_REV" },
  MFE_STALE_CUT: { color: "#6a1b9a", marker: "triangle", label: "MFE_STALE" },
  PROFIT_LOCK: { color: "#00838f", marker: "triangle", label: "PROFIT_LOCK" },
};
function exitStyle(reason) {
  return EXIT_STYLE[reason] || { color: "#999", marker: "triangle", label: reason };
}

function buildPriorityChecks(priorities) {
  const wrap = document.getElementById("fires-priority-checks");
  wrap.innerHTML = "";
  for (const p of priorities) {
    enabledPriorities.add(p);
    const lbl = document.createElement("label");
    lbl.style.borderColor = prioColor(p);
    lbl.innerHTML = `<input type="checkbox" data-p="${p}" checked>P${p}`;
    lbl.querySelector("input").addEventListener("change", (e) => {
      const v = parseInt(e.target.dataset.p);
      if (e.target.checked) enabledPriorities.add(v); else enabledPriorities.delete(v);
      renderFiresChart();
    });
    wrap.appendChild(lbl);
  }
}

function getWindowRange() {
  const v = document.getElementById("fires-window").value;
  if (!pricesData?.bars?.length) return { from: 0, to: 8.64e15 };
  const lastMs = new Date(pricesData.bars[pricesData.bars.length - 1].t.replace(" ", "T") + "Z").getTime();
  if (v === "all") return { from: 0, to: 8.64e15 };
  if (v.startsWith("recent")) {
    const days = parseInt(v.slice(6), 10);
    return { from: lastMs - days * 86400000, to: 8.64e15 };
  }
  // YYYY-MM
  if (/^\d{4}-\d{2}$/.test(v)) {
    const [y, m] = v.split("-").map(Number);
    return {
      from: Date.UTC(y, m - 1, 1),
      to: Date.UTC(y, m, 1),
    };
  }
  return { from: 0, to: 8.64e15 };
}

function filterTrades() {
  const rf = document.getElementById("fires-regime").value;
  const { from, to } = getWindowRange();
  return firesData.trades.filter((t) => {
    if (!enabledPriorities.has(t.priority)) return false;
    if (rf !== "all" && t.regime !== rf) return false;
    const et = new Date(t.entry_time.replace(" ", "T") + "Z").getTime();
    if (et < from || et >= to) return false;
    return true;
  });
}

function filterBars() {
  if (!pricesData?.bars?.length) return [];
  const { from, to } = getWindowRange();
  return pricesData.bars.filter((b) => {
    const ms = new Date(b.t.replace(" ", "T") + "Z").getTime();
    return ms >= from && ms < to;
  });
}

function populateMonthOptions() {
  const sel = document.getElementById("fires-window");
  if (!regimeData?.days?.length) return;
  const months = [...new Set(regimeData.days.map((d) => d.date.slice(0, 7)))].sort();
  for (const m of months) {
    const o = document.createElement("option");
    o.value = m; o.textContent = m;
    sel.appendChild(o);
  }
}

function renderFiresChart() {
  const trades = filterTrades();
  const bars = filterBars();
  document.getElementById("fires-count").textContent =
    `${trades.length} trades / ${bars.length} bars`;

  const toMs = (s) => new Date(s.replace(" ", "T") + "Z").getTime();

  // Entry: priority 別に dataset を分ける（凡例で識別）
  const entryByPri = {};
  for (const t of trades) {
    if (!entryByPri[t.priority]) entryByPri[t.priority] = [];
    entryByPri[t.priority].push({
      x: toMs(t.entry_time), y: t.entry_price, _t: t,
    });
  }

  // Exit: exit_reason 別に dataset を分ける
  const exitByReason = {};
  for (const t of trades) {
    const r = t.exit_reason || "OTHER";
    if (!exitByReason[r]) exitByReason[r] = [];
    exitByReason[r].push({
      x: toMs(t.exit_time), y: t.exit_price, _t: t,
    });
  }

  const priceLine = {
    type: "line",
    label: "BTC close",
    data: bars.map((b) => ({ x: toMs(b.t), y: b.c })),
    borderColor: "rgba(40, 40, 50, 0.6)",
    borderWidth: 1,
    pointRadius: 0,
    tension: 0,
    order: 99,
  };

  const entryDatasets = Object.keys(entryByPri).sort((a, b) => a - b).map((p) => ({
    type: "scatter",
    label: `Entry P${p}`,
    data: entryByPri[p],
    backgroundColor: prioColor(p),
    pointRadius: 4,
    pointHoverRadius: 6,
    order: 1,
  }));

  const exitDatasets = Object.keys(exitByReason).map((r) => {
    const s = exitStyle(r);
    return {
      type: "scatter",
      label: s.label,
      data: exitByReason[r],
      backgroundColor: s.color,
      pointStyle: "triangle",
      pointRadius: 5,
      pointHoverRadius: 7,
      pointRotation: 180,
      order: 2,
    };
  });

  if (firesChart) firesChart.destroy();
  const ctx = document.getElementById("fires-chart");
  firesChart = new Chart(ctx, {
    plugins: [regimeBgPlugin],
    data: { datasets: [priceLine, ...entryDatasets, ...exitDatasets] },
    options: {
      maintainAspectRatio: false,
      animation: false,
      scales: {
        x: {
          type: "time",
          time: { unit: "day", tooltipFormat: "yyyy-MM-dd HH:mm" },
          ticks: { autoSkip: true, maxTicksLimit: 12 },
        },
        y: { title: { display: true, text: "Price (USD)" } },
      },
      plugins: {
        legend: { position: "top", labels: { boxWidth: 12, font: { size: 11 } } },
        tooltip: {
          callbacks: {
            label: (c) => {
              const t = c.raw._t;
              const xs = new Date(c.raw.x).toISOString().slice(0, 16).replace("T", " ");
              if (t) {
                const kind = c.dataset.label.startsWith("Entry") ? "Entry" : "Exit";
                return `${kind} P${t.priority} ${t.side} ${t.regime} NET=${fmtUSD(t.net_usd)} @ ${xs} ($${c.raw.y.toFixed(0)})`;
              }
              return `BTC ${xs}: $${c.raw.y.toFixed(0)}`;
            },
          },
        },
      },
    },
  });

  const tbody = document.querySelector("#fires-table tbody");
  tbody.innerHTML = "";
  trades.slice(-50).reverse().forEach((t) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${t.entry_time}</td><td>P${t.priority}</td><td>${t.side}</td>` +
      `<td>${t.regime}</td>` +
      `<td class="num">$${Math.round(t.entry_price)}</td>` +
      `<td class="num">$${Math.round(t.exit_price)}</td>` +
      `<td>${t.exit_reason}</td>` +
      `<td class="num">${t.hold_min}</td>` +
      `<td class="${classNum(t.net_usd)}">${fmtUSD(t.net_usd)}</td>`;
    tbody.appendChild(tr);
  });
}

async function renderFires() {
  [firesData, pricesData, regimeData] = await Promise.all([
    fetchJSON("data/fires.json"),
    fetchJSON("data/prices.json"),
    fetchJSON("data/regime_timeline.json"),
  ]);
  const ps = [...new Set(firesData.trades.map((t) => t.priority))].sort((a, b) => a - b);
  buildPriorityChecks(ps);
  populateMonthOptions();
  document.getElementById("fires-window").addEventListener("change", renderFiresChart);
  document.getElementById("fires-regime").addEventListener("change", renderFiresChart);
  document.getElementById("fires-regime-bg").addEventListener("change", renderFiresChart);
  renderRegimeStrip();
  renderFiresChart();
}

function renderRegimeStrip() {
  if (!regimeData?.days?.length) return;
  const strip = document.getElementById("regime-strip");
  strip.innerHTML = "";
  const map = { downtrend: "rg-dt", range: "rg-rg", uptrend: "rg-up", mixed: "rg-mx", unknown: "rg-uk" };
  for (const d of regimeData.days) {
    const cell = document.createElement("div");
    cell.className = "cell " + (map[d.regime] || "rg-uk");
    cell.title = `${d.date}: ${d.regime}`;
    strip.appendChild(cell);
  }
}

let signalsData = null;

function cellHtml(text) {
  const css = MARK_CSS[text] || "";
  return `<td class="${css}">${text}</td>`;
}

function renderSignalsTable() {
  const cat = document.getElementById("signals-category").value;
  const rows = signalsData.rows.filter((r) => cat === "all" || r.id.startsWith(cat));
  document.getElementById("signals-count").textContent = `${rows.length} / ${signalsData.rows.length} 候補`;
  const tbody = document.querySelector("#signals-table tbody");
  tbody.innerHTML = "";
  for (const r of rows) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td class="id">${r.id}</td><td class="name">${r.name}</td>` +
      cellHtml(r.dt_long) + cellHtml(r.dt_short) +
      cellHtml(r.rg_long) + cellHtml(r.rg_short) +
      cellHtml(r.up_long) + cellHtml(r.up_short) +
      `<td class="memo">${r.memo}</td>`;
    tbody.appendChild(tr);
  }
}

async function renderSignals() {
  signalsData = await fetchJSON("data/signals.json");
  const legend = document.getElementById("legend");
  legend.innerHTML = "";
  for (const l of signalsData.legend) {
    const span = document.createElement("span");
    span.className = l.css;
    span.textContent = `${l.symbol} ${l.label}`;
    legend.appendChild(span);
  }
  document.getElementById("signals-category").addEventListener("change", renderSignalsTable);
  renderSignalsTable();
}

// ====== Ground Truth タブ（週単位・案B 一括適用）======
const GT_STATE = {};        // week_start -> {label, note}
const GT_SELECTED = new Set();  // 選択中の week_start 集合
let GT_DATA = null;
let GT_CHART = null;

function gtFmtPct(v) {
  const sign = v >= 0 ? "+" : "";
  return `${sign}${v.toFixed(2)}%`;
}

function gtCandleColor(o, c) {
  if (c > o) return "🟢陽";
  if (c < o) return "🔴陰";
  return "⚪同値";
}

function gtFormatRegimeDist(dist) {
  const order = ["uptrend", "downtrend", "range", "mixed", "unknown"];
  const parts = [];
  for (const k of order) {
    if (dist[k]) parts.push(`${k}:${dist[k]}`);
  }
  return parts.join(" / ") || "—";
}

function gtUpdateCsvOutput() {
  const weeks = GT_DATA.weeks.map((w) => w.week_start);
  const lines = ["week_start,label,note"];
  for (const ws of weeks) {
    const s = GT_STATE[ws] || {label: "", note: ""};
    const noteEsc = s.note.includes(",") || s.note.includes("\"")
      ? `"${s.note.replace(/"/g, "\"\"")}"`
      : s.note;
    lines.push(`${ws},${s.label},${noteEsc}`);
  }
  document.getElementById("gt-csv-output").value = lines.join("\n");

  const total = weeks.length;
  const filled = weeks.filter((w) => (GT_STATE[w]?.label || "") !== "").length;
  const dist = {uptrend: 0, downtrend: 0, range: 0};
  for (const w of weeks) {
    const lab = GT_STATE[w]?.label;
    if (lab && dist[lab] !== undefined) dist[lab]++;
  }
  document.getElementById("gt-stats").textContent =
    `入力済 ${filled}/${total} 週（uptrend:${dist.uptrend} / downtrend:${dist.downtrend} / range:${dist.range} / 空欄:${total - filled}）`;
}

function gtUpdateSelectedCount() {
  document.getElementById("gt-selected-count").textContent = String(GT_SELECTED.size);
}

function gtRenderChart(weekStart) {
  const w = GT_DATA.weeks.find((x) => x.week_start === weekStart);
  if (!w) return;

  document.getElementById("gt-chart-wrap").style.display = "";
  document.getElementById("gt-chart-title").textContent = `${w.week_start} 〜 ${w.week_end} の日足`;
  document.getElementById("gt-chart-meta").textContent =
    `週足 O:${w.weekly_candle.o.toFixed(0)} H:${w.weekly_candle.h.toFixed(0)} L:${w.weekly_candle.l.toFixed(0)} C:${w.weekly_candle.c.toFixed(0)} ` +
    `/ 騰落率 ${gtFmtPct(w.return_pct)} / レンジ ${w.range_pct.toFixed(2)}% / ADX平均 ${(w.adx_mean ?? 0).toFixed(1)}`;

  const labels = w.daily_candles.map((d) => d.date);
  const closes = w.daily_candles.map((d) => d.c);
  const highs = w.daily_candles.map((d) => d.h);
  const lows = w.daily_candles.map((d) => d.l);

  if (GT_CHART) GT_CHART.destroy();
  const ctx = document.getElementById("gt-week-chart").getContext("2d");
  GT_CHART = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [
        {label: "close", data: closes, borderColor: "#1976d2", backgroundColor: "transparent", tension: 0.1, pointRadius: 3},
        {label: "high",  data: highs,  borderColor: "#999",   backgroundColor: "transparent", borderDash: [4,4], pointRadius: 0},
        {label: "low",   data: lows,   borderColor: "#999",   backgroundColor: "transparent", borderDash: [4,4], pointRadius: 0},
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {legend: {display: true}},
      scales: {x: {ticks: {maxRotation: 0, minRotation: 0}}, y: {beginAtZero: false}},
    },
  });
}

function gtRowClass(label) {
  if (label === "uptrend") return "gt-row-up";
  if (label === "downtrend") return "gt-row-dn";
  if (label === "range") return "gt-row-rg";
  return "";
}

function gtRenderTable() {
  const tbody = document.querySelector("#gt-table tbody");
  tbody.innerHTML = "";
  for (const w of GT_DATA.weeks) {
    const s = GT_STATE[w.week_start] || {label: "", note: ""};
    const tr = document.createElement("tr");
    tr.dataset.week = w.week_start;
    if (s.label) tr.classList.add(gtRowClass(s.label));

    const checkbox = `<input type="checkbox" class="gt-row-check" data-week="${w.week_start}" ${GT_SELECTED.has(w.week_start) ? "checked" : ""}>`;
    const labelCell = s.label ? `<strong>${s.label}</strong>` : "—";
    const noteCell = s.note ? `<span style="font-size:0.85em;color:#555;">${s.note.replace(/</g, "&lt;")}</span>` : "—";

    tr.innerHTML =
      `<td>${checkbox}</td>` +
      `<td><strong>${w.week_start}</strong></td>` +
      `<td class="num">${w.weekly_candle.o.toFixed(0)}</td>` +
      `<td class="num">${w.weekly_candle.c.toFixed(0)}</td>` +
      `<td class="${classNum(w.return_pct)}">${gtFmtPct(w.return_pct)}</td>` +
      `<td class="num">${w.range_pct.toFixed(2)}%</td>` +
      `<td>${gtCandleColor(w.weekly_candle.o, w.weekly_candle.c)}</td>` +
      `<td class="num">${w.adx_mean !== null ? w.adx_mean.toFixed(1) : "—"}</td>` +
      `<td style="font-size:0.8em;">${gtFormatRegimeDist(w.current_regime_distribution)}</td>` +
      `<td>${labelCell}</td>` +
      `<td>${noteCell}</td>`;
    tbody.appendChild(tr);
  }

  tbody.querySelectorAll(".gt-row-check").forEach((cb) => {
    cb.addEventListener("change", (ev) => {
      ev.stopPropagation();
      const wk = ev.target.dataset.week;
      if (ev.target.checked) GT_SELECTED.add(wk);
      else GT_SELECTED.delete(wk);
      gtUpdateSelectedCount();
    });
  });

  // 行クリックでチャート表示（チェックボックスを除く）
  tbody.querySelectorAll("tr").forEach((tr) => {
    tr.addEventListener("click", (ev) => {
      if (ev.target.tagName === "INPUT") return;
      tbody.querySelectorAll("tr.gt-active-row").forEach((r) => r.classList.remove("gt-active-row"));
      tr.classList.add("gt-active-row");
      gtRenderChart(tr.dataset.week);
    });
  });
}

function gtApplyBulk() {
  if (GT_SELECTED.size === 0) {
    alert("週が1つも選択されていません");
    return;
  }
  const label = document.getElementById("gt-bulk-label").value;
  const note = document.getElementById("gt-bulk-note").value.trim();
  if (!label) {
    alert("判定（uptrend/downtrend/range/クリア）を選んでください");
    return;
  }
  if (label !== "__clear__" && !note) {
    alert("note は必須です（判定根拠を入力してください）");
    return;
  }

  const apply = label === "__clear__" ? "" : label;
  for (const wk of GT_SELECTED) {
    GT_STATE[wk] = {label: apply, note: apply ? note : ""};
  }
  GT_SELECTED.clear();
  document.getElementById("gt-bulk-label").value = "";
  document.getElementById("gt-bulk-note").value = "";
  document.getElementById("gt-check-all").checked = false;
  gtRenderTable();
  gtUpdateSelectedCount();
  gtUpdateCsvOutput();
}

function gtUncheckAll() {
  GT_SELECTED.clear();
  document.getElementById("gt-check-all").checked = false;
  document.querySelectorAll(".gt-row-check").forEach((cb) => { cb.checked = false; });
  gtUpdateSelectedCount();
}

function gtCheckAll(checked) {
  if (checked) {
    for (const w of GT_DATA.weeks) GT_SELECTED.add(w.week_start);
  } else {
    GT_SELECTED.clear();
  }
  document.querySelectorAll(".gt-row-check").forEach((cb) => { cb.checked = checked; });
  gtUpdateSelectedCount();
}

async function renderGroundTruth() {
  GT_DATA = await fetchJSON("data/weekly_summary.json");
  for (const w of GT_DATA.weeks) {
    GT_STATE[w.week_start] = {label: "", note: ""};
  }
  gtRenderTable();
  gtUpdateCsvOutput();
  gtUpdateSelectedCount();

  document.getElementById("gt-apply-btn").addEventListener("click", gtApplyBulk);
  document.getElementById("gt-uncheck-all-btn").addEventListener("click", gtUncheckAll);
  document.getElementById("gt-check-all").addEventListener("change", (ev) => gtCheckAll(ev.target.checked));
}

// ====== ⑤ 日次肉眼判定タブ（DH = Daily Human）======
let DH_DATA = null;
let DH_PRICE_CHART = null;
const DH_STATE = {};  // date -> {label, note}
const DH_SELECTED = new Set();

function dhLabelColor(label) {
  if (label === "uptrend") return "#4caf50";
  if (label === "downtrend") return "#e53935";
  if (label === "range") return "#9e9e9e";
  return "#ffffff";
}

function dhLabelLight(label) {
  if (label === "uptrend") return "rgba(76, 175, 80, 0.22)";
  if (label === "downtrend") return "rgba(229, 57, 53, 0.22)";
  if (label === "range") return "rgba(158, 158, 158, 0.18)";
  return "rgba(255, 255, 255, 0)";
}

function dhDow(dateStr) {
  const d = new Date(dateStr);
  return ["日","月","火","水","木","金","土"][d.getDay()];
}

function dhDailyChangePct(today, prev) {
  if (!prev || prev.close === 0) return null;
  return (today.close - prev.close) / prev.close * 100;
}

function _legacy_tcDominantLabel(m) {
  const cands = [
    ["uptrend", m.uptrend],
    ["downtrend", m.downtrend],
    ["range", m.range],
  ];
  cands.sort((a, b) => b[1] - a[1]);
  if (cands[0][1] === 0) return "—";
  return `${cands[0][0]} (${cands[0][1]}日)`;
}

function tcWeeklyHumanForMonth(month) {
  // month = "2025-04" のように YYYY-MM
  if (!TC_DATA.weekly_human_labels) return "—";
  const items = TC_DATA.weekly_human_labels.filter((w) => w.week_start.startsWith(month));
  if (items.length === 0) return "—";
  const cnt = {uptrend: 0, downtrend: 0, range: 0, blank: 0};
  for (const w of items) {
    if (w.label === "uptrend") cnt.uptrend++;
    else if (w.label === "downtrend") cnt.downtrend++;
    else if (w.label === "range") cnt.range++;
    else cnt.blank++;
  }
  const parts = [];
  if (cnt.uptrend) parts.push(`up:${cnt.uptrend}`);
  if (cnt.downtrend) parts.push(`dn:${cnt.downtrend}`);
  if (cnt.range) parts.push(`rg:${cnt.range}`);
  if (cnt.blank) parts.push(`空:${cnt.blank}`);
  return parts.join(" / ") || "—";
}

function tcRenderSummary() {
  const lc = TC_DATA.label_counts;
  const days = TC_DATA.days;
  const first = days[0]?.date || "—";
  const last = days[days.length - 1]?.date || "—";
  document.getElementById("tc-period").textContent = `${first} 〜 ${last}（${TC_DATA.n_days}日）`;
  document.getElementById("tc-up").textContent = `${lc.uptrend}日`;
  document.getElementById("tc-dn").textContent = `${lc.downtrend}日`;
  document.getElementById("tc-rg").textContent = `${lc.range}日`;
  document.getElementById("tc-wu").textContent = `${lc.warmup}日`;
}

// チャート用のフィルタ済み日付配列を保持（背景色プラグインで参照）
let TC_CHART_DAYS = [];

const tcBackgroundPlugin = {
  id: "tcBackgroundPlugin",
  beforeDatasetsDraw(chart) {
    const {ctx, chartArea, scales} = chart;
    if (!chartArea || !TC_CHART_DAYS.length) return;
    const xScale = scales.x;
    ctx.save();
    for (let i = 0; i < TC_CHART_DAYS.length; i++) {
      const d = TC_CHART_DAYS[i];
      const x0 = xScale.getPixelForValue(i);
      const x1 = (i + 1 < TC_CHART_DAYS.length) ? xScale.getPixelForValue(i + 1) : chartArea.right;
      const left = Math.max(x0, chartArea.left);
      const right = Math.min(x1, chartArea.right);
      if (right <= left) continue;
      ctx.fillStyle = tcLabelLight(d.label);
      ctx.fillRect(left, chartArea.top, right - left, chartArea.bottom - chartArea.top);
    }
    ctx.restore();
  },
};

function tcRenderPriceChart() {
  const monthFilter = document.getElementById("tc-chart-month-filter").value;
  const allDays = TC_DATA.days;
  TC_CHART_DAYS = monthFilter === "all"
    ? allDays.slice()
    : allDays.filter((d) => d.date.startsWith(monthFilter));

  const labels = TC_CHART_DAYS.map((d) => d.date);
  const closes = TC_CHART_DAYS.map((d) => d.close);

  if (TC_PRICE_CHART) TC_PRICE_CHART.destroy();
  const ctx = document.getElementById("tc-price-chart").getContext("2d");
  TC_PRICE_CHART = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "BTC close (日足)",
        data: closes,
        borderColor: "#1976d2",
        backgroundColor: "transparent",
        tension: 0.1,
        pointRadius: monthFilter === "all" ? 0 : 2,
        borderWidth: 1.8,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {mode: "index", intersect: false},
      plugins: {
        legend: {display: false},
        tooltip: {
          callbacks: {
            afterLabel: (item) => {
              const d = TC_CHART_DAYS[item.dataIndex];
              if (!d) return "";
              return `label: ${d.label || "—"} | dir: ${d.direction_score} | 一目: ${d.ichimoku} | ADX: ${d.adx} | BB幅: ${d.bb_width_pct}`;
            },
          },
        },
      },
      scales: {
        x: {ticks: {maxTicksLimit: 14}},
        y: {beginAtZero: false},
      },
    },
    plugins: [tcBackgroundPlugin],
  });
}

function tcRenderMonthlyTable() {
  const tbody = document.querySelector("#tc-monthly-table tbody");
  tbody.innerHTML = "";
  for (const m of TC_DATA.monthly_summary) {
    const tr = document.createElement("tr");
    tr.innerHTML =
      `<td><strong>${m.month}</strong></td>` +
      `<td class="num pos">${m.uptrend}</td>` +
      `<td class="num neg">${m.downtrend}</td>` +
      `<td class="num">${m.range}</td>` +
      `<td class="num">${m.warmup}</td>` +
      `<td>${tcDominantLabel(m)}</td>` +
      `<td style="font-size:0.85em;color:#555;">${tcWeeklyHumanForMonth(m.month)}</td>`;
    tbody.appendChild(tr);
  }
}

function tcRenderDayTable() {
  const monthFilter = document.getElementById("tc-month-filter").value;
  const labelFilter = document.getElementById("tc-label-filter").value;
  const tbody = document.querySelector("#tc-day-table tbody");
  tbody.innerHTML = "";
  let count = 0;
  for (const d of TC_DATA.days) {
    if (monthFilter !== "all" && !d.date.startsWith(monthFilter)) continue;
    const labKey = d.label || "warmup";
    if (labelFilter !== "all" && labelFilter !== labKey) continue;
    count++;
    const tr = document.createElement("tr");
    tr.style.background = tcLabelLight(d.label);
    tr.innerHTML =
      `<td>${d.date}</td>` +
      `<td class="num">${Number(d.close).toFixed(0)}</td>` +
      `<td><strong style="color:${tcLabelColor(d.label)};">${d.label || "warmup"}</strong></td>` +
      `<td class="num">${d.direction_score}</td>` +
      `<td>${d.ichimoku}</td>` +
      `<td class="num">${d.adx}</td>` +
      `<td class="num">${d.bb_width_pct}</td>` +
      `<td class="num">${d.bb_median}</td>` +
      `<td style="font-size:0.85em;">${d.note}</td>`;
    tbody.appendChild(tr);
  }
  document.getElementById("tc-day-count").textContent = `表示中: ${count}日`;
}

function tcPopulateMonthFilter() {
  const months = TC_DATA.monthly_summary.map((m) => m.month);
  const tableSel = document.getElementById("tc-month-filter");
  const chartSel = document.getElementById("tc-chart-month-filter");
  for (const m of months) {
    const opt1 = document.createElement("option");
    opt1.value = m; opt1.textContent = m;
    tableSel.appendChild(opt1);
    const opt2 = document.createElement("option");
    opt2.value = m; opt2.textContent = m;
    chartSel.appendChild(opt2);
  }
}

// ====== DH: 日次肉眼判定 実装 ======
let DH_CHART_DAYS = [];

const dhBackgroundPlugin = {
  id: "dhBackgroundPlugin",
  beforeDatasetsDraw(chart) {
    const {ctx, chartArea, scales} = chart;
    if (!chartArea || !DH_CHART_DAYS.length) return;
    const xScale = scales.x;
    ctx.save();
    for (let i = 0; i < DH_CHART_DAYS.length; i++) {
      const d = DH_CHART_DAYS[i];
      const lab = DH_STATE[d.date]?.label || "";
      const x0 = xScale.getPixelForValue(i);
      const x1 = (i + 1 < DH_CHART_DAYS.length) ? xScale.getPixelForValue(i + 1) : chartArea.right;
      const left = Math.max(x0, chartArea.left);
      const right = Math.min(x1, chartArea.right);
      if (right <= left) continue;
      ctx.fillStyle = dhLabelLight(lab);
      ctx.fillRect(left, chartArea.top, right - left, chartArea.bottom - chartArea.top);
    }
    ctx.restore();
  },
};

function dhUpdateStats() {
  const total = DH_DATA.days.length;
  const counts = {uptrend: 0, downtrend: 0, range: 0, blank: 0};
  for (const d of DH_DATA.days) {
    const l = DH_STATE[d.date]?.label || "";
    if (counts[l] !== undefined) counts[l]++;
    else counts.blank++;
  }
  document.getElementById("dh-stats").textContent =
    `up:${counts.uptrend} / dn:${counts.downtrend} / rg:${counts.range} / 空:${counts.blank} / 計:${total}`;
}

function dhUpdateCsv() {
  const lines = ["date,label,note"];
  for (const d of DH_DATA.days) {
    const s = DH_STATE[d.date] || {label: "", note: ""};
    let note = s.note || "";
    if (note.includes(",") || note.includes('"')) {
      note = '"' + note.replace(/"/g, '""') + '"';
    }
    lines.push(`${d.date},${s.label},${note}`);
  }
  document.getElementById("dh-csv-output").value = lines.join("\n");
}

function dhUpdateSelectedCount() {
  document.getElementById("dh-selected-count").textContent = String(DH_SELECTED.size);
}

function dhRenderPriceChart() {
  const monthFilter = document.getElementById("dh-month-filter").value;
  DH_CHART_DAYS = monthFilter === "all"
    ? DH_DATA.days.slice()
    : DH_DATA.days.filter((d) => d.date.startsWith(monthFilter));

  const labels = DH_CHART_DAYS.map((d) => d.date);
  const closes = DH_CHART_DAYS.map((d) => d.close);

  if (DH_PRICE_CHART) DH_PRICE_CHART.destroy();
  const ctx = document.getElementById("dh-price-chart").getContext("2d");
  DH_PRICE_CHART = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "BTC close",
        data: closes,
        borderColor: "#1976d2",
        backgroundColor: "transparent",
        tension: 0.1,
        pointRadius: monthFilter === "all" ? 0 : 2,
        borderWidth: 1.8,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {mode: "index", intersect: false},
      plugins: {
        legend: {display: false},
        tooltip: {
          callbacks: {
            afterLabel: (item) => {
              const d = DH_CHART_DAYS[item.dataIndex];
              if (!d) return "";
              const lab = DH_STATE[d.date]?.label || "—";
              return `肉眼ラベル: ${lab}`;
            },
          },
        },
      },
      scales: {
        x: {ticks: {maxTicksLimit: 14}},
        y: {beginAtZero: false},
      },
    },
    plugins: [dhBackgroundPlugin],
  });
}

function dhRenderDayTable() {
  const monthFilter = document.getElementById("dh-month-filter").value;
  const tbody = document.querySelector("#dh-day-table tbody");
  tbody.innerHTML = "";
  const filtered = monthFilter === "all"
    ? DH_DATA.days
    : DH_DATA.days.filter((d) => d.date.startsWith(monthFilter));
  let prev = null;
  for (const d of filtered) {
    const s = DH_STATE[d.date] || {label: "", note: ""};
    const tr = document.createElement("tr");
    tr.style.background = dhLabelLight(s.label);
    const change = dhDailyChangePct(d, prev);
    const checkbox = `<input type="checkbox" class="dh-row-check" data-date="${d.date}" ${DH_SELECTED.has(d.date) ? "checked" : ""}>`;
    const labelCell = s.label
      ? `<strong style="color:${dhLabelColor(s.label)};">${s.label}</strong>`
      : "—";
    const noteCell = s.note
      ? `<span style="font-size:0.85em;color:#555;">${s.note.replace(/</g, "&lt;")}</span>`
      : "—";
    tr.innerHTML =
      `<td>${checkbox}</td>` +
      `<td>${d.date}</td>` +
      `<td>${dhDow(d.date)}</td>` +
      `<td class="num">${Number(d.close).toFixed(0)}</td>` +
      `<td class="${change != null && change >= 0 ? 'num pos' : 'num neg'}">${change != null ? change.toFixed(2) + "%" : "—"}</td>` +
      `<td>${labelCell}</td>` +
      `<td>${noteCell}</td>`;
    tbody.appendChild(tr);
    prev = d;
  }
  tbody.querySelectorAll(".dh-row-check").forEach((cb) => {
    cb.addEventListener("change", (ev) => {
      ev.stopPropagation();
      const dt = ev.target.dataset.date;
      if (ev.target.checked) DH_SELECTED.add(dt);
      else DH_SELECTED.delete(dt);
      dhUpdateSelectedCount();
    });
  });
}

function dhApplyBulk() {
  if (DH_SELECTED.size === 0) {
    alert("日が1つも選択されていません");
    return;
  }
  const label = document.getElementById("dh-bulk-label").value;
  const note = document.getElementById("dh-bulk-note").value.trim();
  if (!label) {
    alert("判定（uptrend/downtrend/range/クリア）を選んでください");
    return;
  }
  if (label !== "__clear__" && !note) {
    alert("note は必須です");
    return;
  }
  const apply = label === "__clear__" ? "" : label;
  for (const dt of DH_SELECTED) {
    DH_STATE[dt] = {label: apply, note: apply ? note : ""};
  }
  DH_SELECTED.clear();
  document.getElementById("dh-bulk-label").value = "";
  document.getElementById("dh-bulk-note").value = "";
  document.getElementById("dh-check-all-month").checked = false;
  dhUpdateSelectedCount();
  dhRenderPriceChart();
  dhRenderDayTable();
  dhUpdateStats();
  dhUpdateCsv();
}

function dhUncheckAll() {
  DH_SELECTED.clear();
  document.getElementById("dh-check-all-month").checked = false;
  document.querySelectorAll(".dh-row-check").forEach((cb) => { cb.checked = false; });
  dhUpdateSelectedCount();
}

function dhCheckAllVisible() {
  const checked = document.getElementById("dh-check-all-month").checked;
  const monthFilter = document.getElementById("dh-month-filter").value;
  const visible = monthFilter === "all"
    ? DH_DATA.days
    : DH_DATA.days.filter((d) => d.date.startsWith(monthFilter));
  if (checked) {
    for (const d of visible) DH_SELECTED.add(d.date);
  } else {
    for (const d of visible) DH_SELECTED.delete(d.date);
  }
  document.querySelectorAll(".dh-row-check").forEach((cb) => {
    cb.checked = DH_SELECTED.has(cb.dataset.date);
  });
  dhUpdateSelectedCount();
}

function dhPopulateMonthFilter() {
  const sel = document.getElementById("dh-month-filter");
  const months = Array.from(new Set(DH_DATA.days.map((d) => d.date.slice(0, 7)))).sort();
  for (const m of months) {
    const opt = document.createElement("option");
    opt.value = m; opt.textContent = m;
    sel.appendChild(opt);
  }
}

async function renderTruthCheck() {
  DH_DATA = await fetchJSON("data/regime_truth_daily.json");
  // 初期状態に肉眼日次ラベルを取り込む
  const initial = DH_DATA.daily_human_labels || {};
  for (const d of DH_DATA.days) {
    const init = initial[d.date] || {label: "", note: ""};
    DH_STATE[d.date] = {label: init.label || "", note: init.note || ""};
  }
  dhPopulateMonthFilter();
  dhRenderPriceChart();
  dhRenderDayTable();
  dhUpdateStats();
  dhUpdateCsv();
  dhUpdateSelectedCount();

  document.getElementById("dh-month-filter").addEventListener("change", () => {
    dhRenderPriceChart();
    dhRenderDayTable();
    document.getElementById("dh-check-all-month").checked = false;
  });
  document.getElementById("dh-apply-btn").addEventListener("click", dhApplyBulk);
  document.getElementById("dh-uncheck-all-btn").addEventListener("click", dhUncheckAll);
  document.getElementById("dh-check-all-month").addEventListener("change", dhCheckAllVisible);
}

// ====== ⑥ ML予測検証タブ ======
let ML_DATA = null;
let ML_PRICE_CHART = null;
let ML_CHART_DAYS = [];

function mlLabelLight(label) {
  if (label === "uptrend") return "rgba(76, 175, 80, 0.30)";
  if (label === "downtrend") return "rgba(229, 57, 53, 0.30)";
  if (label === "range") return "rgba(158, 158, 158, 0.25)";
  return "rgba(255, 255, 255, 0)";
}

function mlLabelColor(label) {
  if (label === "uptrend") return "#4caf50";
  if (label === "downtrend") return "#e53935";
  if (label === "range") return "#9e9e9e";
  return "#ccc";
}

const mlBackgroundPlugin = {
  id: "mlBackgroundPlugin",
  beforeDatasetsDraw(chart) {
    const {ctx, chartArea, scales} = chart;
    if (!chartArea || !ML_CHART_DAYS.length) return;
    const xScale = scales.x;
    const model = document.getElementById("ml-model-select").value;
    const predKey = model === "rf" ? "rf_pred" : "gb_pred";
    const midY = (chartArea.top + chartArea.bottom) / 2;
    ctx.save();
    for (let i = 0; i < ML_CHART_DAYS.length; i++) {
      const d = ML_CHART_DAYS[i];
      const x0 = xScale.getPixelForValue(i);
      const x1 = (i + 1 < ML_CHART_DAYS.length) ? xScale.getPixelForValue(i + 1) : chartArea.right;
      const left = Math.max(x0, chartArea.left);
      const right = Math.min(x1, chartArea.right);
      if (right <= left) continue;
      // 上半分: 肉眼正解
      ctx.fillStyle = mlLabelLight(d.true);
      ctx.fillRect(left, chartArea.top, right - left, midY - chartArea.top);
      // 下半分: ML予測
      ctx.fillStyle = mlLabelLight(d[predKey]);
      ctx.fillRect(left, midY, right - left, chartArea.bottom - midY);
    }
    // 中央分割線
    ctx.strokeStyle = "rgba(0,0,0,0.2)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(chartArea.left, midY);
    ctx.lineTo(chartArea.right, midY);
    ctx.stroke();
    ctx.restore();
  },
};

function mlRenderSummary() {
  const rf = ML_DATA.rf_summary;
  const gb = ML_DATA.gb_summary;
  document.getElementById("ml-rf-acc").textContent = rf.accuracy != null
    ? `${(rf.accuracy * 100).toFixed(1)}% (${rf.hit}/${rf.n})` : "—";
  document.getElementById("ml-gb-acc").textContent = gb.accuracy != null
    ? `${(gb.accuracy * 100).toFixed(1)}% (${gb.hit}/${gb.n})` : "—";
  const days = ML_DATA.days;
  if (days.length) {
    document.getElementById("ml-period").textContent = `${days[0].date} 〜 ${days[days.length - 1].date}（${days.length}日）`;
  }
}

function mlDow(dateStr) {
  const d = new Date(dateStr);
  return ["日","月","火","水","木","金","土"][d.getDay()];
}

function mlRenderPriceChart() {
  const monthFilter = document.getElementById("ml-month-filter").value;
  ML_CHART_DAYS = monthFilter === "all"
    ? ML_DATA.days.slice()
    : ML_DATA.days.filter((d) => d.date.startsWith(monthFilter));

  const labels = ML_CHART_DAYS.map((d) => d.date);
  const closes = ML_CHART_DAYS.map((d) => d.close);

  if (ML_PRICE_CHART) ML_PRICE_CHART.destroy();
  const ctx = document.getElementById("ml-price-chart").getContext("2d");
  ML_PRICE_CHART = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "BTC close",
        data: closes,
        borderColor: "#1976d2",
        backgroundColor: "transparent",
        tension: 0.1,
        pointRadius: monthFilter === "all" ? 0 : 2,
        borderWidth: 1.8,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {mode: "index", intersect: false},
      plugins: {
        legend: {display: false},
        tooltip: {
          callbacks: {
            afterLabel: (item) => {
              const d = ML_CHART_DAYS[item.dataIndex];
              if (!d) return "";
              return `肉眼: ${d.true || "—"} / RF: ${d.rf_pred || "—"} ${d.rf_match ? "◯" : "×"} / GB: ${d.gb_pred || "—"} ${d.gb_match ? "◯" : "×"}`;
            },
          },
        },
      },
      scales: {x: {ticks: {maxTicksLimit: 14}}, y: {beginAtZero: false}},
    },
    plugins: [mlBackgroundPlugin],
  });
}

function mlRenderDayTable() {
  const filter = document.getElementById("ml-row-filter").value;
  const tbody = document.querySelector("#ml-day-table tbody");
  tbody.innerHTML = "";
  let count = 0;
  for (const d of ML_DATA.days) {
    if (filter === "mismatch" && d.rf_match && d.gb_match) continue;
    if (filter === "match" && !(d.rf_match && d.gb_match)) continue;
    if (filter === "mismatch" && (d.rf_match === null || d.gb_match === null)) continue;
    count++;
    const tr = document.createElement("tr");
    const tlblHtml = d.true ? `<strong style="color:${mlLabelColor(d.true)};">${d.true}</strong>` : "—";
    const rfHtml = d.rf_pred ? `<strong style="color:${mlLabelColor(d.rf_pred)};">${d.rf_pred}</strong>` : "—";
    const gbHtml = d.gb_pred ? `<strong style="color:${mlLabelColor(d.gb_pred)};">${d.gb_pred}</strong>` : "—";
    const rfMark = d.rf_match === true ? "◯" : (d.rf_match === false ? "×" : "—");
    const gbMark = d.gb_match === true ? "◯" : (d.gb_match === false ? "×" : "—");
    tr.innerHTML =
      `<td>${d.date}</td>` +
      `<td>${mlDow(d.date)}</td>` +
      `<td class="num">${Number(d.close).toFixed(0)}</td>` +
      `<td>${tlblHtml}</td>` +
      `<td>${rfHtml}</td>` +
      `<td>${rfMark}</td>` +
      `<td>${gbHtml}</td>` +
      `<td>${gbMark}</td>`;
    tbody.appendChild(tr);
  }
  document.getElementById("ml-row-count").textContent = `表示中: ${count}日`;
}

function mlRenderFeatTable() {
  const tbody = document.querySelector("#ml-feat-table tbody");
  tbody.innerHTML = "";
  const max = Math.max(...ML_DATA.feature_importances.map((f) => f.importance));
  ML_DATA.feature_importances.forEach((f, i) => {
    const widthPct = (f.importance / max) * 100;
    const tr = document.createElement("tr");
    tr.innerHTML =
      `<td>${i + 1}</td>` +
      `<td>${f.feature}</td>` +
      `<td class="num">${f.importance.toFixed(4)}</td>` +
      `<td><div style="width:${widthPct}%;height:14px;background:#1976d2;"></div></td>`;
    tbody.appendChild(tr);
  });
}

function mlPopulateMonthFilter() {
  const sel = document.getElementById("ml-month-filter");
  const months = Array.from(new Set(ML_DATA.days.map((d) => d.date.slice(0, 7)))).sort();
  for (const m of months) {
    const opt = document.createElement("option");
    opt.value = m; opt.textContent = m;
    sel.appendChild(opt);
  }
}

async function renderMlCheck() {
  ML_DATA = await fetchJSON("data/ml_predictions.json");
  mlRenderSummary();
  mlPopulateMonthFilter();
  mlRenderPriceChart();
  mlRenderDayTable();
  mlRenderFeatTable();
  document.getElementById("ml-month-filter").addEventListener("change", mlRenderPriceChart);
  document.getElementById("ml-model-select").addEventListener("change", mlRenderPriceChart);
  document.getElementById("ml-row-filter").addEventListener("change", mlRenderDayTable);
}

let PH1_DATA = null;

function ph1RenderSummary() {
  document.getElementById("ph1-period").textContent =
    `${PH1_DATA.period.start} 〜 ${PH1_DATA.period.end}`;
  document.getElementById("ph1-days").textContent = PH1_DATA.period.n_days;
  document.getElementById("ph1-fcount").textContent = PH1_DATA.feature_count;
}

function ph1RenderSummaryTable() {
  const tbody = document.querySelector("#ph1-summary-table tbody");
  tbody.innerHTML = "";
  for (const [name, s] of Object.entries(PH1_DATA.features)) {
    const tr = document.createElement("tr");
    const f = (v) => Number(v).toFixed(2);
    tr.innerHTML =
      `<td><strong>${name}</strong></td>` +
      `<td class="num">${f(s.mean)}</td>` +
      `<td class="num">${f(s.std)}</td>` +
      `<td class="num">${f(s.min)}</td>` +
      `<td class="num">${f(s.p5)}</td>` +
      `<td class="num">${f(s.p25)}</td>` +
      `<td class="num">${f(s.p50)}</td>` +
      `<td class="num">${f(s.p75)}</td>` +
      `<td class="num">${f(s.p95)}</td>` +
      `<td class="num">${f(s.max)}</td>`;
    tbody.appendChild(tr);
  }
}

function ph1RenderHistograms() {
  const container = document.getElementById("ph1-histograms");
  container.innerHTML = "";
  for (const [name, h] of Object.entries(PH1_DATA.histograms)) {
    const wrap = document.createElement("div");
    wrap.style.cssText = "border:1px solid #ddd;padding:10px;background:#fff;";
    wrap.innerHTML = `<div style="font-weight:bold;margin-bottom:6px;">${name}</div>` +
      `<div style="height:160px;"><canvas></canvas></div>`;
    container.appendChild(wrap);
    const canvas = wrap.querySelector("canvas");
    const labels = h.bin_edges.slice(0, -1).map((e, i) =>
      `${e.toFixed(1)}〜${h.bin_edges[i + 1].toFixed(1)}`);
    new Chart(canvas, {
      type: "bar",
      data: {
        labels,
        datasets: [{ data: h.counts, backgroundColor: "#1976d2", borderWidth: 0 }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { display: false }, grid: { display: false } },
          y: { beginAtZero: true, ticks: { font: { size: 10 } } },
        },
      },
    });
  }
}

function ph1CorrColor(r) {
  const a = Math.min(Math.abs(r), 1);
  if (r >= 0) return `rgba(211,47,47,${a.toFixed(2)})`;
  return `rgba(25,118,210,${a.toFixed(2)})`;
}

function ph1RenderCorrTable() {
  const { features, matrix } = PH1_DATA.correlation;
  const thead = document.querySelector("#ph1-corr-table thead");
  const tbody = document.querySelector("#ph1-corr-table tbody");
  thead.innerHTML = "";
  tbody.innerHTML = "";

  const trh = document.createElement("tr");
  trh.innerHTML = `<th></th>` + features.map((f) => `<th>${f}</th>`).join("");
  thead.appendChild(trh);

  features.forEach((row, i) => {
    const tr = document.createElement("tr");
    let html = `<th>${row}</th>`;
    matrix[i].forEach((v, j) => {
      const flag = (i !== j && Math.abs(v) >= 0.7) ? " ⚠" : "";
      html += `<td class="num" style="background:${ph1CorrColor(v)};color:${Math.abs(v) > 0.6 ? "#fff" : "#000"};">${v.toFixed(2)}${flag}</td>`;
    });
    tr.innerHTML = html;
    tbody.appendChild(tr);
  });
}

async function renderPhase1Features() {
  PH1_DATA = await fetchJSON("data/phase1_features.json");
  ph1RenderSummary();
  ph1RenderSummaryTable();
  ph1RenderHistograms();
  ph1RenderCorrTable();
}

let PH2_DATA = null;

const PH2_LABEL_COLOR = {
  STRONG_UP:   "#1b5e20",  // 濃緑
  WEAK_UP:     "#66bb6a",  // 中緑
  DRIFT_UP:    "#c8e6c9",  // 薄緑
  NEUTRAL:     "#bdbdbd",  // 灰
  DRIFT_DOWN:  "#ffcdd2",  // 薄赤
  WEAK_DOWN:   "#ef5350",  // 中赤
  STRONG_DOWN: "#b71c1c",  // 濃赤
};

const PH2_LABEL_SHORT = {
  STRONG_UP:   "強UP",
  WEAK_UP:     "弱UP",
  DRIFT_UP:    "微UP",
  NEUTRAL:     "横",
  DRIFT_DOWN:  "微DN",
  WEAK_DOWN:   "弱DN",
  STRONG_DOWN: "強DN",
};

function ph2Color(label) {
  return PH2_LABEL_COLOR[label] || "#bdbdbd";
}

function ph2RenderSummary() {
  const cfg = PH2_DATA.adopted_config;
  const m = PH2_DATA.metrics;
  document.getElementById("ph2-config").textContent =
    `${cfg.candidate_label} / n=${cfg.n_states} / seed=${cfg.random_state}`;
  document.getElementById("ph2-margin").textContent = m.margin.toFixed(3);
  document.getElementById("ph2-logl").textContent = m.logL.toFixed(1);
  const ss = PH2_DATA.search_stats;
  document.getElementById("ph2-passrate").textContent =
    `${ss.n_passed}/${ss.n_combinations_tried} (${ss.pass_rate_pct}%)`;
  document.getElementById("ph2-period").textContent =
    `${PH2_DATA.period.start} 〜 ${PH2_DATA.period.end} (${PH2_DATA.period.n_days}日)`;
}

function ph2RenderPassCheck() {
  const tbody = document.querySelector("#ph2-passcheck-table tbody");
  tbody.innerHTML = "";
  for (const [k, v] of Object.entries(PH2_DATA.pass_check)) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${k}</td><td style="font-weight:bold;color:${v ? "#2e7d32" : "#c62828"}">${v ? "✅ 合格" : "❌ 不合格"}</td>`;
    tbody.appendChild(tr);
  }
}

function ph2RenderStatesTable() {
  const tbody = document.querySelector("#ph2-states-table tbody");
  tbody.innerHTML = "";
  // ラベル順: UPTREND, MID4, MID3, RANGE, MID1, MID2, DOWNTREND（リターン降順）
  const entries = Object.entries(PH2_DATA.state_summary);
  entries.sort((a, b) => b[1].ret_mean_pct - a[1].ret_mean_pct);
  for (const [label, s] of entries) {
    const tr = document.createElement("tr");
    tr.innerHTML =
      `<td><span style="display:inline-block;width:14px;height:14px;background:${ph2Color(label)};margin-right:6px;vertical-align:middle;"></span><strong>${label}</strong></td>` +
      `<td class="num">${s.state_id}</td>` +
      `<td class="num">${s.n_days}</td>` +
      `<td class="num ${s.ret_mean_pct >= 0 ? "pos" : "neg"}">${s.ret_mean_pct.toFixed(3)}</td>` +
      `<td class="num ${s.ret_median_pct >= 0 ? "pos" : "neg"}">${s.ret_median_pct.toFixed(3)}</td>` +
      `<td class="num">${s.duration_median_days}</td>` +
      `<td class="num">${s.p_value}</td>`;
    tbody.appendChild(tr);
  }
}

let PH2_PRICE_CHART = null;

function ph2GetPeriodOptions(mode) {
  if (mode === "all") return ["all"];
  const keys = new Set(PH2_DATA.daily.map((d) => mode === "year" ? d.date.slice(0, 4) : d.date.slice(0, 7)));
  return Array.from(keys).sort();
}

function ph2RepopulatePeriodPicker() {
  const mode = document.getElementById("ph2-period-mode").value;
  const sel = document.getElementById("ph2-period-pick");
  const opts = ph2GetPeriodOptions(mode);
  sel.innerHTML = "";
  for (const v of opts) {
    const o = document.createElement("option");
    o.value = v;
    o.textContent = v === "all" ? "全期間" : (mode === "year" ? v + "年" : v);
    sel.appendChild(o);
  }
  if (mode === "month") sel.value = opts[opts.length - 1];
}

function ph2StepPeriod(delta) {
  const sel = document.getElementById("ph2-period-pick");
  const idx = sel.selectedIndex;
  const next = idx + delta;
  if (next >= 0 && next < sel.options.length) {
    sel.selectedIndex = next;
    ph2RenderPriceChart();
  }
}

function ph2RenderPriceChart() {
  const mode = document.getElementById("ph2-period-mode").value;
  const sel = document.getElementById("ph2-period-pick").value;
  const data = sel === "all"
    ? PH2_DATA.daily
    : PH2_DATA.daily.filter((d) => d.date.startsWith(sel));

  const info = document.getElementById("ph2-period-info");
  if (data.length > 0) {
    const counts = {};
    data.forEach((d) => { counts[d.label] = (counts[d.label] || 0) + 1; });
    const summary = Object.entries(counts).sort((a, b) => b[1] - a[1])
      .map(([k, v]) => `${PH2_LABEL_SHORT[k] || k}=${v}`).join(" / ");
    info.textContent = `${data.length}日 [${summary}]`;
  } else {
    info.textContent = "";
  }

  const ctx = document.getElementById("ph2-price-chart").getContext("2d");
  if (PH2_PRICE_CHART) PH2_PRICE_CHART.destroy();

  // 背景色プラグイン: 状態によって縦帯
  const bgPlugin = {
    id: "ph2RegimeBg",
    beforeDraw(chart) {
      const { ctx, chartArea, scales } = chart;
      if (!chartArea) return;
      ctx.save();
      const xScale = scales.x;
      const total = data.length;
      data.forEach((d, i) => {
        const xStart = xScale.getPixelForValue(i);
        const xEnd = i + 1 < total ? xScale.getPixelForValue(i + 1) : chartArea.right;
        ctx.fillStyle = ph2Color(d.label);
        ctx.globalAlpha = 0.35;
        ctx.fillRect(xStart, chartArea.top, xEnd - xStart, chartArea.bottom - chartArea.top);
      });
      ctx.restore();
    },
  };

  PH2_PRICE_CHART = new Chart(ctx, {
    type: "line",
    data: {
      labels: data.map((d) => d.date),
      datasets: [{
        label: "BTC close",
        data: data.map((d) => d.close),
        borderColor: "#000",
        borderWidth: 1.2,
        pointRadius: 0,
        tension: 0.1,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const d = data[ctx.dataIndex];
              return `${d.date}  $${d.close}  ret=${d.ret_pct >= 0 ? "+" : ""}${d.ret_pct}%  [${d.label}]`;
            },
          },
        },
      },
      scales: {
        x: { ticks: { maxTicksLimit: 12, font: { size: 10 } } },
        y: { ticks: { font: { size: 10 } } },
      },
    },
    plugins: [bgPlugin],
  });
}

function ph2RenderMonthlyStrip() {
  const container = document.getElementById("ph2-monthly-strip");
  container.innerHTML = "";
  const grid = document.createElement("div");
  grid.style.cssText = "display:grid;grid-template-columns:repeat(12,1fr);gap:2px;font-size:0.7em;";
  // 年×月マトリクス
  const byYM = {};
  PH2_DATA.monthly.forEach((m) => { byYM[m.date] = m; });
  const years = Array.from(new Set(PH2_DATA.monthly.map((m) => m.date.slice(0, 4)))).sort();

  // ヘッダー（月）
  const labelHead = document.createElement("div");
  labelHead.style.cssText = "grid-column:1 / -1;display:grid;grid-template-columns:60px repeat(12,1fr);gap:2px;font-weight:bold;text-align:center;margin-bottom:4px;";
  labelHead.innerHTML = `<div></div>` + Array.from({length: 12}, (_, i) => `<div>${i + 1}月</div>`).join("");
  container.appendChild(labelHead);

  for (const y of years) {
    const row = document.createElement("div");
    row.style.cssText = "display:grid;grid-template-columns:60px repeat(12,1fr);gap:2px;margin-bottom:2px;";
    row.innerHTML = `<div style="font-weight:bold;align-self:center;">${y}年</div>`;
    for (let mon = 1; mon <= 12; mon++) {
      const ym = `${y}-${String(mon).padStart(2, "0")}`;
      const m = byYM[ym];
      const cell = document.createElement("div");
      if (m) {
        const color = ph2Color(m.dominant_label);
        cell.style.cssText = `background:${color};color:#fff;padding:6px 4px;text-align:center;cursor:pointer;`;
        cell.textContent = PH2_LABEL_SHORT[m.dominant_label] || m.dominant_label;
        cell.title = `${ym}\n${m.dominant_label} (${(m.label_share[m.dominant_label]*100).toFixed(0)}%)\nmean_ret=${m.mean_ret_pct.toFixed(3)}%`;
      } else {
        cell.style.cssText = "background:#eee;padding:6px 4px;";
      }
      row.appendChild(cell);
    }
    container.appendChild(row);
  }
}

function ph2RenderMonthlyTable() {
  const tbody = document.querySelector("#ph2-monthly-table tbody");
  tbody.innerHTML = "";
  const pct = (v) => ((v || 0) * 100).toFixed(0);
  PH2_DATA.monthly.forEach((m) => {
    const sh = m.label_share;
    const tr = document.createElement("tr");
    tr.innerHTML =
      `<td>${m.date}</td>` +
      `<td class="num">${m.n_days}</td>` +
      `<td class="num ${m.mean_ret_pct >= 0 ? "pos" : "neg"}">${m.mean_ret_pct.toFixed(3)}</td>` +
      `<td><span style="display:inline-block;width:10px;height:10px;background:${ph2Color(m.dominant_label)};margin-right:4px;vertical-align:middle;"></span>${PH2_LABEL_SHORT[m.dominant_label] || m.dominant_label}</td>` +
      `<td class="num">${pct(sh.STRONG_UP)}</td>` +
      `<td class="num">${pct(sh.WEAK_UP)}</td>` +
      `<td class="num">${pct(sh.DRIFT_UP)}</td>` +
      `<td class="num">${pct(sh.NEUTRAL)}</td>` +
      `<td class="num">${pct(sh.DRIFT_DOWN)}</td>` +
      `<td class="num">${pct(sh.WEAK_DOWN)}</td>` +
      `<td class="num">${pct(sh.STRONG_DOWN)}</td>`;
    tbody.appendChild(tr);
  });
}

function ph2RenderHistograms() {
  const container = document.getElementById("ph2-histograms");
  container.innerHTML = "";
  const entries = Object.entries(PH2_DATA.return_histograms_per_state);
  entries.sort((a, b) => b[1].mean - a[1].mean);
  for (const [label, h] of entries) {
    const wrap = document.createElement("div");
    wrap.style.cssText = `border:1px solid ${ph2Color(label)};padding:10px;background:#fff;`;
    wrap.innerHTML =
      `<div style="font-weight:bold;margin-bottom:6px;color:${ph2Color(label)};">${label}` +
      ` <span style="color:#666;font-weight:normal;">n=${h.n} mean=${h.mean.toFixed(3)}% median=${h.median.toFixed(3)}% std=${h.std.toFixed(2)}%</span></div>` +
      `<div style="height:160px;"><canvas></canvas></div>`;
    container.appendChild(wrap);
    const labels = h.bin_edges.slice(0, -1).map((e, i) => `${e.toFixed(1)}〜${h.bin_edges[i+1].toFixed(1)}`);
    new Chart(wrap.querySelector("canvas"), {
      type: "bar",
      data: { labels, datasets: [{ data: h.counts, backgroundColor: ph2Color(label), borderWidth: 0 }] },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { display: false }, grid: { display: false } },
          y: { beginAtZero: true, ticks: { font: { size: 10 } } },
        },
      },
    });
  }
}

function ph2RenderTransition() {
  const t = PH2_DATA.transition;
  const thead = document.querySelector("#ph2-transition-table thead");
  const tbody = document.querySelector("#ph2-transition-table tbody");
  thead.innerHTML = "";
  tbody.innerHTML = "";
  const trh = document.createElement("tr");
  trh.innerHTML = `<th>from \\ to</th>` + t.labels_in_order.map((l) => `<th><span style="background:${ph2Color(l)};color:#fff;padding:2px 4px;">${l}</span></th>`).join("");
  thead.appendChild(trh);
  t.labels_in_order.forEach((label, i) => {
    const tr = document.createElement("tr");
    let html = `<th><span style="background:${ph2Color(label)};color:#fff;padding:2px 4px;">${label}</span></th>`;
    t.matrix[i].forEach((p, j) => {
      const intensity = Math.min(p, 1);
      const bg = `rgba(46,125,50,${intensity.toFixed(2)})`;
      html += `<td class="num" style="background:${bg};color:${intensity > 0.5 ? "#fff" : "#000"};">${(p*100).toFixed(1)}%</td>`;
    });
    tr.innerHTML = html;
    tbody.appendChild(tr);
  });
}

// ============== Phase 3 (HMM 1h K=3) ==============
let PH3_DATA = null;
const PH3_LABEL_COLOR = { UP: "#1b5e20", RANGE: "#bdbdbd", DOWN: "#b71c1c" };
const PH3_LABEL_SHORT = { UP: "UP", RANGE: "RG", DOWN: "DOWN" };
function ph3Color(l) { return PH3_LABEL_COLOR[l] || "#bdbdbd"; }

function ph3RenderSummary() {
  const s = PH3_DATA.summary;
  document.getElementById("ph3-config").textContent =
    `seed=${s.picked_seed} / LL=${s.picked_ll.toFixed(0)}`;
  document.getElementById("ph3-passrate").textContent =
    `${s.n_seeds_passing}/${s.n_seeds_tried} (${(s.passing_rate*100).toFixed(0)}%)`;
  document.getElementById("ph3-ari").textContent =
    s.intra_solution_ari_mean !== null ? s.intra_solution_ari_mean.toFixed(4) : "—";
  document.getElementById("ph3-spread").textContent =
    `${s.spread_daily.toFixed(2)}%  (${s.min_daily_pct.toFixed(2)} / ${s.max_daily_pct.toFixed(2)})`;
  document.getElementById("ph3-period").textContent =
    `${PH3_DATA.period.start.slice(0,10)} 〜 ${PH3_DATA.period.end.slice(0,10)} (${PH3_DATA.period.n_days}日)`;
}

function ph3RenderStatesTable() {
  const tbody = document.querySelector("#ph3-states-table tbody");
  tbody.innerHTML = "";
  const ss = PH3_DATA.summary.state_summary;
  const labelToSid = {};
  for (const [sid, lab] of Object.entries(PH3_DATA.labels_by_sid)) labelToSid[lab] = sid;
  const order = ["UP", "RANGE", "DOWN"];
  for (const label of order) {
    const s = ss[label];
    if (!s) continue;
    const sid = labelToSid[label];
    const tr = document.createElement("tr");
    tr.innerHTML =
      `<td><span style="display:inline-block;width:14px;height:14px;background:${ph3Color(label)};margin-right:6px;vertical-align:middle;"></span><strong>${label}</strong></td>` +
      `<td class="num">${sid}</td>` +
      `<td class="num">${s.n}</td>` +
      `<td class="num">${(s.share*100).toFixed(1)}%</td>` +
      `<td class="num ${s.mean_period_pct >= 0 ? "pos" : "neg"}">${s.mean_period_pct.toFixed(4)}</td>` +
      `<td class="num ${s.daily_pct >= 0 ? "pos" : "neg"}">${s.daily_pct.toFixed(3)}</td>` +
      `<td class="num">${s.std_period_pct.toFixed(3)}</td>`;
    tbody.appendChild(tr);
  }
}

let PH3_PRICE_CHART = null;

function ph3GetPeriodOptions(mode) {
  if (mode === "all") return ["all"];
  const keys = new Set(PH3_DATA.daily.map((d) => mode === "year" ? d.date.slice(0, 4) : d.date.slice(0, 7)));
  return Array.from(keys).sort();
}

function ph3RepopulatePeriodPicker() {
  const mode = document.getElementById("ph3-period-mode").value;
  const sel = document.getElementById("ph3-period-pick");
  const opts = ph3GetPeriodOptions(mode);
  sel.innerHTML = "";
  for (const v of opts) {
    const o = document.createElement("option");
    o.value = v;
    o.textContent = v === "all" ? "全期間" : (mode === "year" ? v + "年" : v);
    sel.appendChild(o);
  }
  if (mode === "month") sel.value = opts[opts.length - 1];
}

function ph3StepPeriod(delta) {
  const sel = document.getElementById("ph3-period-pick");
  const idx = sel.selectedIndex;
  const next = idx + delta;
  if (next >= 0 && next < sel.options.length) {
    sel.selectedIndex = next;
    ph3RenderPriceChart();
  }
}

function ph3RenderPriceChart() {
  const mode = document.getElementById("ph3-period-mode").value;
  const sel = document.getElementById("ph3-period-pick").value;
  const data = sel === "all"
    ? PH3_DATA.daily
    : PH3_DATA.daily.filter((d) => d.date.startsWith(sel));

  const info = document.getElementById("ph3-period-info");
  if (data.length > 0) {
    const counts = {};
    data.forEach((d) => { counts[d.dominant] = (counts[d.dominant] || 0) + 1; });
    const summary = Object.entries(counts).sort((a, b) => b[1] - a[1])
      .map(([k, v]) => `${PH3_LABEL_SHORT[k] || k}=${v}`).join(" / ");
    info.textContent = `${data.length}日 [${summary}]`;
  } else {
    info.textContent = "";
  }

  const ctx = document.getElementById("ph3-price-chart").getContext("2d");
  if (PH3_PRICE_CHART) PH3_PRICE_CHART.destroy();

  const bgPlugin = {
    id: "ph3RegimeBg",
    beforeDraw(chart) {
      const { ctx, chartArea, scales } = chart;
      if (!chartArea) return;
      ctx.save();
      const xScale = scales.x;
      data.forEach((d, i) => {
        const xStart = xScale.getPixelForValue(i);
        const xEnd = i + 1 < data.length ? xScale.getPixelForValue(i + 1) : chartArea.right;
        ctx.fillStyle = ph3Color(d.dominant);
        ctx.globalAlpha = 0.30 + 0.30 * (d.dominant_share || 0);
        ctx.fillRect(xStart, chartArea.top, xEnd - xStart, chartArea.bottom - chartArea.top);
      });
      ctx.restore();
    },
  };

  PH3_PRICE_CHART = new Chart(ctx, {
    type: "line",
    data: {
      labels: data.map((d) => d.date),
      datasets: [{
        label: "BTC close",
        data: data.map((d) => d.close),
        borderColor: "#000",
        borderWidth: 1.2,
        pointRadius: 0,
        tension: 0.1,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (cx) => {
              const d = data[cx.dataIndex];
              const sh = Object.entries(d.share).map(([k,v]) => `${PH3_LABEL_SHORT[k]||k}=${(v*100).toFixed(0)}%`).join("/");
              return `${d.date}  $${d.close}  ret=${d.mean_ret_pct >= 0 ? "+" : ""}${d.mean_ret_pct}%  [${d.dominant} ${(d.dominant_share*100).toFixed(0)}%] (${sh})`;
            },
          },
        },
      },
      scales: {
        x: { ticks: { maxTicksLimit: 12, font: { size: 10 } } },
        y: { ticks: { font: { size: 10 } } },
      },
    },
    plugins: [bgPlugin],
  });
}

function ph3RenderMonthlyStrip() {
  const container = document.getElementById("ph3-monthly-strip");
  container.innerHTML = "";
  const byYM = {};
  PH3_DATA.monthly.forEach((m) => { byYM[m.date] = m; });
  const years = Array.from(new Set(PH3_DATA.monthly.map((m) => m.date.slice(0, 4)))).sort();

  const labelHead = document.createElement("div");
  labelHead.style.cssText = "display:grid;grid-template-columns:60px repeat(12,1fr);gap:2px;font-weight:bold;text-align:center;margin-bottom:4px;font-size:0.7em;";
  labelHead.innerHTML = `<div></div>` + Array.from({length: 12}, (_, i) => `<div>${i + 1}月</div>`).join("");
  container.appendChild(labelHead);

  for (const y of years) {
    const row = document.createElement("div");
    row.style.cssText = "display:grid;grid-template-columns:60px repeat(12,1fr);gap:2px;margin-bottom:2px;font-size:0.7em;";
    row.innerHTML = `<div style="font-weight:bold;align-self:center;">${y}年</div>`;
    for (let mon = 1; mon <= 12; mon++) {
      const ym = `${y}-${String(mon).padStart(2, "0")}`;
      const m = byYM[ym];
      const cell = document.createElement("div");
      if (m) {
        const color = ph3Color(m.dominant);
        cell.style.cssText = `background:${color};color:#fff;padding:6px 4px;text-align:center;`;
        cell.textContent = PH3_LABEL_SHORT[m.dominant] || m.dominant;
        const sh = Object.entries(m.label_share).map(([k,v]) => `${PH3_LABEL_SHORT[k]||k}=${(v*100).toFixed(0)}%`).join(" / ");
        cell.title = `${ym}\n${m.dominant} 支配\n${sh}\nmean_ret/h=${m.mean_ret_pct_per_h.toFixed(4)}%`;
      } else {
        cell.style.cssText = "background:#eee;padding:6px 4px;";
      }
      row.appendChild(cell);
    }
    container.appendChild(row);
  }
}

function ph3RenderMonthlyTable() {
  const tbody = document.querySelector("#ph3-monthly-table tbody");
  tbody.innerHTML = "";
  const pct = (v) => ((v || 0) * 100).toFixed(0);
  PH3_DATA.monthly.forEach((m) => {
    const sh = m.label_share;
    const tr = document.createElement("tr");
    tr.innerHTML =
      `<td>${m.date}</td>` +
      `<td class="num">${m.n_hours}</td>` +
      `<td class="num ${m.mean_ret_pct_per_h >= 0 ? "pos" : "neg"}">${m.mean_ret_pct_per_h.toFixed(4)}</td>` +
      `<td><span style="display:inline-block;width:10px;height:10px;background:${ph3Color(m.dominant)};margin-right:4px;vertical-align:middle;"></span>${PH3_LABEL_SHORT[m.dominant] || m.dominant}</td>` +
      `<td class="num">${pct(sh.UP)}</td>` +
      `<td class="num">${pct(sh.RANGE)}</td>` +
      `<td class="num">${pct(sh.DOWN)}</td>`;
    tbody.appendChild(tr);
  });
}

function ph3RenderHistograms() {
  const container = document.getElementById("ph3-histograms");
  container.innerHTML = "";
  const order = ["UP", "RANGE", "DOWN"];
  for (const label of order) {
    const h = PH3_DATA.return_histograms_per_state[label];
    if (!h) continue;
    const wrap = document.createElement("div");
    wrap.style.cssText = `border:1px solid ${ph3Color(label)};padding:10px;background:#fff;`;
    wrap.innerHTML =
      `<div style="font-weight:bold;margin-bottom:6px;color:${ph3Color(label)};">${label}` +
      ` <span style="color:#666;font-weight:normal;">n=${h.n} mean=${h.mean.toFixed(4)}% std=${h.std.toFixed(3)}%</span></div>` +
      `<div style="height:160px;"><canvas></canvas></div>`;
    container.appendChild(wrap);
    const labels = h.bin_edges.slice(0, -1).map((e, i) => `${e.toFixed(2)}〜${h.bin_edges[i+1].toFixed(2)}`);
    new Chart(wrap.querySelector("canvas"), {
      type: "bar",
      data: { labels, datasets: [{ data: h.counts, backgroundColor: ph3Color(label), borderWidth: 0 }] },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { display: false }, grid: { display: false } },
          y: { beginAtZero: true, ticks: { font: { size: 10 } } },
        },
      },
    });
  }
}

function ph3RenderTransition() {
  const t = PH3_DATA.transition;
  const thead = document.querySelector("#ph3-transition-table thead");
  const tbody = document.querySelector("#ph3-transition-table tbody");
  thead.innerHTML = "";
  tbody.innerHTML = "";
  const trh = document.createElement("tr");
  trh.innerHTML = `<th>from \\ to</th>` + t.labels_in_order.map((l) => `<th><span style="background:${ph3Color(l)};color:#fff;padding:2px 4px;">${l}</span></th>`).join("");
  thead.appendChild(trh);
  t.labels_in_order.forEach((label, i) => {
    const tr = document.createElement("tr");
    let html = `<th><span style="background:${ph3Color(label)};color:#fff;padding:2px 4px;">${label}</span></th>`;
    t.matrix[i].forEach((p) => {
      const intensity = Math.min(p, 1);
      const bg = `rgba(46,125,50,${intensity.toFixed(2)})`;
      html += `<td class="num" style="background:${bg};color:${intensity > 0.5 ? "#fff" : "#000"};">${(p*100).toFixed(1)}%</td>`;
    });
    tr.innerHTML = html;
    tbody.appendChild(tr);
  });
}

async function renderPhase3Hmm() {
  PH3_DATA = await fetchJSON("data/phase3_hmm.json");
  ph3RenderSummary();
  ph3RenderStatesTable();
  ph3RepopulatePeriodPicker();
  ph3RenderPriceChart();
  ph3RenderMonthlyStrip();
  ph3RenderMonthlyTable();
  ph3RenderHistograms();
  ph3RenderTransition();
  document.getElementById("ph3-period-mode").addEventListener("change", () => {
    ph3RepopulatePeriodPicker();
    ph3RenderPriceChart();
  });
  document.getElementById("ph3-period-pick").addEventListener("change", ph3RenderPriceChart);
  document.getElementById("ph3-prev-btn").addEventListener("click", () => ph3StepPeriod(-1));
  document.getElementById("ph3-next-btn").addEventListener("click", () => ph3StepPeriod(1));
}

async function renderPhase2Hmm() {
  PH2_DATA = await fetchJSON("data/phase2_hmm.json");
  ph2RenderSummary();
  ph2RenderPassCheck();
  ph2RenderStatesTable();
  ph2RepopulatePeriodPicker();
  ph2RenderPriceChart();
  ph2RenderMonthlyStrip();
  ph2RenderMonthlyTable();
  ph2RenderHistograms();
  ph2RenderTransition();
  document.getElementById("ph2-period-mode").addEventListener("change", () => {
    ph2RepopulatePeriodPicker();
    ph2RenderPriceChart();
  });
  document.getElementById("ph2-period-pick").addEventListener("change", ph2RenderPriceChart);
  document.getElementById("ph2-prev-btn").addEventListener("click", () => ph2StepPeriod(-1));
  document.getElementById("ph2-next-btn").addEventListener("click", () => ph2StepPeriod(1));
}

(async () => {
  try {
    await renderProgress();
    await renderFires();   // この中で regimeData も取得 → renderRegimeStrip も呼ぶ
    await renderSignals();
    await renderGroundTruth();
    await renderTruthCheck();
    await renderMlCheck();
    await renderPhase1Features();
    await renderPhase2Hmm();
    await renderPhase3Hmm();
  } catch (e) {
    console.error(e);
    document.body.insertAdjacentHTML("afterbegin",
      `<div style="background:#fee;padding:12px;color:#c00;">${e.message}</div>`);
  }
})();
