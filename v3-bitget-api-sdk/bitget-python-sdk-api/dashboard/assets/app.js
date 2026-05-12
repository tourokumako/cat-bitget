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

async function dhSaveLabels() {
  const btn = document.getElementById("dh-save-btn");
  const status = document.getElementById("dh-save-status");
  btn.disabled = true;
  status.textContent = "保存中…";
  status.style.color = "#555";
  const labels = DH_DATA.days.map((d) => {
    const s = DH_STATE[d.date] || {label: "", note: ""};
    return {date: d.date, label: s.label || "", note: s.note || ""};
  });
  try {
    const res = await fetch("/api/save_daily_labels", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({labels}),
    });
    const j = await res.json();
    if (!res.ok || !j.ok) {
      status.textContent = `保存失敗: ${j.error || res.status}`;
      status.style.color = "#c62828";
    } else {
      const ts = new Date().toLocaleTimeString("ja-JP");
      status.textContent = `✓ ${j.rows}行保存 (${ts}・backup: ${j.backup})`;
      status.style.color = "#2e7d32";
    }
  } catch (e) {
    status.textContent = `保存失敗: ${e.message}`;
    status.style.color = "#c62828";
  } finally {
    btn.disabled = false;
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
  document.getElementById("dh-save-btn").addEventListener("click", dhSaveLabels);
}

// ====== ⑫ 4h 肉眼判定（年選択・サンプルラベル付け） ======
let S4_DATA = null;
let S4_PRICE_CHART = null;
let S4_YAXIS_CHART = null;
const S4_STATE = {};  // timestamp_utc -> label
const S4_SELECTED = new Set();
let S4_CHART_ITEMS = [];  // {key, close, label, intensity}
const S4_Y_STEP = 2000;
let S4_Y_GLOBAL_MIN = 0;
let S4_Y_GLOBAL_MAX = 0;
let S4_YEAR = "2025";

function s4LabelColor(label) {
  if (label === "uptrend") return "#4caf50";
  if (label === "downtrend") return "#e53935";
  if (label === "range") return "#9e9e9e";
  return "#ffffff";
}

function s4LabelLight(label, intensity) {
  // intensity = "strong" (default) | "weak" (1d 混在用・強度半分)
  const w = intensity === "weak";
  if (label === "uptrend")   return w ? "rgba(76, 175, 80, 0.11)" : "rgba(76, 175, 80, 0.22)";
  if (label === "downtrend") return w ? "rgba(229, 57, 53, 0.11)" : "rgba(229, 57, 53, 0.22)";
  if (label === "range")     return w ? "rgba(158, 158, 158, 0.09)" : "rgba(158, 158, 158, 0.18)";
  return "rgba(255, 255, 255, 0)";
}

function s4BarChangePct(bar) {
  if (!bar || bar.open === 0) return null;
  return (bar.close - bar.open) / bar.open * 100;
}

const s4BackgroundPlugin = {
  id: "s4BackgroundPlugin",
  beforeDatasetsDraw(chart) {
    const {ctx, chartArea, scales} = chart;
    if (!chartArea || !S4_CHART_ITEMS.length) return;
    const xScale = scales.x;
    ctx.save();
    for (let i = 0; i < S4_CHART_ITEMS.length; i++) {
      const it = S4_CHART_ITEMS[i];
      const x0 = xScale.getPixelForValue(i);
      const x1 = (i + 1 < S4_CHART_ITEMS.length) ? xScale.getPixelForValue(i + 1) : chartArea.right;
      const left = Math.max(x0, chartArea.left);
      const right = Math.min(x1, chartArea.right);
      if (right <= left) continue;
      ctx.fillStyle = s4LabelLight(it.label, it.intensity);
      ctx.fillRect(left, chartArea.top, right - left, chartArea.bottom - chartArea.top);
    }
    ctx.restore();
  },
};

function s4UpdateStats() {
  const total = S4_DATA.bars.length;
  const counts = {uptrend: 0, downtrend: 0, range: 0, blank: 0};
  for (const b of S4_DATA.bars) {
    const l = S4_STATE[b.timestamp_utc] || "";
    if (counts[l] !== undefined) counts[l]++;
    else counts.blank++;
  }
  document.getElementById("s4-stats").textContent =
    `up:${counts.uptrend} / dn:${counts.downtrend} / rg:${counts.range} / 空:${counts.blank} / 計:${total}`;
}

function s4UpdateSelectedCount() {
  document.getElementById("s4-selected-count").textContent = String(S4_SELECTED.size);
}

function s4AggregateDaily(bars) {
  // bars (4h) を日単位に集約。背景色 intensity 判定込み。
  const byDay = new Map();
  for (const b of bars) {
    const day = b.timestamp_utc.slice(0, 10);
    if (!byDay.has(day)) byDay.set(day, []);
    byDay.get(day).push(b);
  }
  const items = [];
  for (const [day, list] of byDay) {
    list.sort((a, b) => a.timestamp_utc.localeCompare(b.timestamp_utc));
    const labels = list.map((b) => S4_STATE[b.timestamp_utc] || "");
    const counts = {uptrend: 0, downtrend: 0, range: 0};
    let blanks = 0;
    for (const l of labels) {
      if (counts[l] !== undefined) counts[l]++;
      else blanks++;
    }
    const totalLabeled = labels.length - blanks;
    let label = "";
    let intensity = "strong";
    if (totalLabeled === 0) {
      label = "";
    } else {
      const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
      label = top[0];
      const allSame = (top[1] === labels.length);
      intensity = allSame ? "strong" : "weak";
    }
    items.push({
      key: day,
      close: list[list.length - 1].close,
      label,
      intensity,
    });
  }
  items.sort((a, b) => a.key.localeCompare(b.key));
  return items;
}

function s4RenderPriceChart() {
  const monthFilter = document.getElementById("s4-month-filter").value;
  const granularity = document.getElementById("s4-granularity").value;
  const filteredBars = monthFilter === "all"
    ? S4_DATA.bars.slice()
    : S4_DATA.bars.filter((b) => b.timestamp_utc.startsWith(monthFilter));

  if (granularity === "1d") {
    S4_CHART_ITEMS = s4AggregateDaily(filteredBars);
  } else {
    S4_CHART_ITEMS = filteredBars.map((b) => ({
      key: b.timestamp_utc,
      close: b.close,
      label: S4_STATE[b.timestamp_utc] || "",
      intensity: "strong",
    }));
  }

  const labels = S4_CHART_ITEMS.map((it) => {
    if (granularity === "1d") return it.key;  // YYYY-MM-DD
    return it.key.slice(5, 16).replace("T", " ");  // MM-DD HH:MM
  });
  const closes = S4_CHART_ITEMS.map((it) => it.close);

  // Y軸: 表示中データの min/max + 上下 3% パディング（対数軸前提）
  const dataMin = closes.length ? Math.min(...closes) : 1;
  const dataMax = closes.length ? Math.max(...closes) : 1;
  const yMin = dataMin * 0.97;
  const yMax = dataMax * 1.03;

  if (S4_PRICE_CHART) S4_PRICE_CHART.destroy();
  const ctx = document.getElementById("s4-price-chart").getContext("2d");
  S4_PRICE_CHART = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: granularity === "1d" ? "BTC close (1d)" : "BTC close (4h)",
        data: closes,
        borderColor: "#1976d2",
        backgroundColor: "transparent",
        tension: 0.1,
        pointRadius: monthFilter === "all" ? 0 : 1.5,
        borderWidth: 1.5,
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
              const it = S4_CHART_ITEMS[item.dataIndex];
              if (!it) return "";
              if (granularity === "1d") {
                const labText = it.label || "—";
                const mix = it.label && it.intensity === "weak" ? "（混在）" : "";
                return `日支配ラベル: ${labText}${mix}`;
              }
              return `肉眼ラベル: ${it.label || "—"}`;
            },
          },
        },
      },
      scales: {
        x: {ticks: {maxTicksLimit: 24}},
        y: {
          display: false,
          type: "logarithmic",
          min: yMin,
          max: yMax,
        },
      },
      layout: {padding: {left: 0, right: 0}},
    },
    plugins: [s4BackgroundPlugin],
  });

  // Y軸専用チャート（左固定・本体と同じ min/max/stepSize）
  if (S4_YAXIS_CHART) S4_YAXIS_CHART.destroy();
  const yaxisCtx = document.getElementById("s4-yaxis-chart").getContext("2d");
  S4_YAXIS_CHART = new Chart(yaxisCtx, {
    type: "line",
    data: {
      labels: [""],
      datasets: [{data: [yMin], borderColor: "transparent", pointRadius: 0}],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      layout: {padding: {left: 20, right: 0, top: 0, bottom: 0}},
      plugins: {legend: {display: false}, tooltip: {enabled: false}},
      scales: {
        x: {display: false, offset: false},
        y: {
          type: "logarithmic",
          min: yMin,
          max: yMax,
          ticks: {
            callback: (v) => {
              // 対数軸では Chart.js が自動で目盛り選択。
              // 5桁・6桁の整数を「k」表記に圧縮（例: 90,000 → 90k）して幅を抑える
              const n = Number(v);
              if (n >= 1000) return (n / 1000).toFixed(0) + "k";
              return n.toLocaleString();
            },
            padding: 0,
            maxTicksLimit: 12,
          },
          grid: {display: false},
          border: {display: false},
          position: "right",
        },
      },
    },
  });
}

function s4RenderBarTable() {
  const monthFilter = document.getElementById("s4-month-filter").value;
  const tbody = document.querySelector("#s4-bar-table tbody");
  tbody.innerHTML = "";
  const filtered = monthFilter === "all"
    ? S4_DATA.bars
    : S4_DATA.bars.filter((b) => b.timestamp_utc.startsWith(monthFilter));
  for (const b of filtered) {
    const lab = S4_STATE[b.timestamp_utc] || "";
    const tr = document.createElement("tr");
    tr.style.background = s4LabelLight(lab);
    const change = s4BarChangePct(b);
    const checkbox = `<input type="checkbox" class="s4-row-check" data-ts="${b.timestamp_utc}" ${S4_SELECTED.has(b.timestamp_utc) ? "checked" : ""}>`;
    const labelCell = lab
      ? `<strong style="color:${s4LabelColor(lab)};">${lab}</strong>`
      : "—";
    const tsDisplay = b.timestamp_utc.slice(0, 16).replace("T", " ");
    tr.innerHTML =
      `<td>${checkbox}</td>` +
      `<td>${tsDisplay}</td>` +
      `<td class="num">${Number(b.open).toFixed(0)}</td>` +
      `<td class="num">${Number(b.close).toFixed(0)}</td>` +
      `<td class="${change != null && change >= 0 ? 'num pos' : 'num neg'}">${change != null ? change.toFixed(2) + "%" : "—"}</td>` +
      `<td>${labelCell}</td>`;
    tbody.appendChild(tr);
  }
  tbody.querySelectorAll(".s4-row-check").forEach((cb) => {
    cb.addEventListener("change", (ev) => {
      ev.stopPropagation();
      const ts = ev.target.dataset.ts;
      if (ev.target.checked) S4_SELECTED.add(ts);
      else S4_SELECTED.delete(ts);
      s4UpdateSelectedCount();
    });
  });
}

function s4ApplyBulk() {
  if (S4_SELECTED.size === 0) {
    alert("4hバーが1つも選択されていません");
    return;
  }
  const label = document.getElementById("s4-bulk-label").value;
  if (!label) {
    alert("判定（uptrend/downtrend/range/クリア）を選んでください");
    return;
  }
  const apply = label === "__clear__" ? "" : label;
  for (const ts of S4_SELECTED) {
    S4_STATE[ts] = apply;
  }
  S4_SELECTED.clear();
  document.getElementById("s4-bulk-label").value = "";
  document.getElementById("s4-check-all-month").checked = false;
  s4UpdateSelectedCount();
  s4RenderPriceChart();
  s4RenderBarTable();
  s4UpdateStats();
}

function s4UncheckAll() {
  S4_SELECTED.clear();
  document.getElementById("s4-check-all-month").checked = false;
  document.querySelectorAll(".s4-row-check").forEach((cb) => { cb.checked = false; });
  s4UpdateSelectedCount();
}

function s4CheckAllVisible() {
  const checked = document.getElementById("s4-check-all-month").checked;
  const monthFilter = document.getElementById("s4-month-filter").value;
  const visible = monthFilter === "all"
    ? S4_DATA.bars
    : S4_DATA.bars.filter((b) => b.timestamp_utc.startsWith(monthFilter));
  if (checked) {
    for (const b of visible) S4_SELECTED.add(b.timestamp_utc);
  } else {
    for (const b of visible) S4_SELECTED.delete(b.timestamp_utc);
  }
  document.querySelectorAll(".s4-row-check").forEach((cb) => {
    cb.checked = S4_SELECTED.has(cb.dataset.ts);
  });
  s4UpdateSelectedCount();
}

function s4PopulateMonthFilter() {
  const sel = document.getElementById("s4-month-filter");
  const months = Array.from(new Set(S4_DATA.bars.map((b) => b.timestamp_utc.slice(0, 7)))).sort();
  for (const m of months) {
    const opt = document.createElement("option");
    opt.value = m; opt.textContent = m;
    sel.appendChild(opt);
  }
}

async function s4SaveLabels() {
  const btn = document.getElementById("s4-save-btn");
  const status = document.getElementById("s4-save-status");
  btn.disabled = true;
  status.textContent = "保存中…";
  status.style.color = "#555";
  const labels = S4_DATA.bars.map((b) => ({
    timestamp_utc: b.timestamp_utc,
    label: S4_STATE[b.timestamp_utc] || "",
  }));
  try {
    const res = await fetch("/api/save_4h_labels", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({labels, year: parseInt(S4_YEAR, 10)}),
    });
    const j = await res.json();
    if (!res.ok || !j.ok) {
      status.textContent = `保存失敗: ${j.error || res.status}`;
      status.style.color = "#c62828";
    } else {
      const ts = new Date().toLocaleTimeString("ja-JP");
      status.textContent = `✓ ${j.rows}行保存 (${ts}・backup: ${j.backup})`;
      status.style.color = "#2e7d32";
    }
  } catch (e) {
    status.textContent = `保存失敗: ${e.message}`;
    status.style.color = "#c62828";
  } finally {
    btn.disabled = false;
  }
}

function s4JsonPath(year) {
  return year === "2025" ? "data/regime_samples_4h.json" : `data/regime_samples_4h_${year}.json`;
}

async function s4AutoSave() {
  if (!S4_DATA) return;
  const labels = S4_DATA.bars.map((b) => ({
    timestamp_utc: b.timestamp_utc,
    label: S4_STATE[b.timestamp_utc] || "",
  }));
  try {
    await fetch("/api/save_4h_labels", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({labels, year: parseInt(S4_YEAR, 10)}),
    });
  } catch (_) { /* 失敗しても年切替は続行 */ }
}

async function s4LoadYear(year) {
  // 年切替前に現在の入力を自動保存
  await s4AutoSave();

  S4_YEAR = year;
  // 状態リセット
  for (const k of Object.keys(S4_STATE)) delete S4_STATE[k];
  S4_SELECTED.clear();

  S4_DATA = await fetchJSON(s4JsonPath(year));
  const initial = S4_DATA.labels || {};
  for (const b of S4_DATA.bars) {
    S4_STATE[b.timestamp_utc] = initial[b.timestamp_utc] || "";
  }
  const allCloses = S4_DATA.bars.map((b) => b.close);
  S4_Y_GLOBAL_MIN = Math.floor(Math.min(...allCloses) / S4_Y_STEP) * S4_Y_STEP;
  S4_Y_GLOBAL_MAX = Math.ceil(Math.max(...allCloses) / S4_Y_STEP) * S4_Y_STEP;

  // 月フィルタ再構築（"全期間" オプションのみ残す）
  const sel = document.getElementById("s4-month-filter");
  while (sel.options.length > 1) sel.remove(1);
  s4PopulateMonthFilter();
  sel.value = "all";

  s4UpdateSelectedCount();
  s4RenderPriceChart();
  s4RenderBarTable();
  s4UpdateStats();
}

async function renderSamples4h() {
  await s4LoadYear(S4_YEAR);

  document.getElementById("s4-year-select").addEventListener("change", async (ev) => {
    await s4LoadYear(ev.target.value);
    document.getElementById("s4-check-all-month").checked = false;
  });
  document.getElementById("s4-month-filter").addEventListener("change", () => {
    s4RenderPriceChart();
    s4RenderBarTable();
    document.getElementById("s4-check-all-month").checked = false;
  });
  document.getElementById("s4-granularity").addEventListener("change", s4RenderPriceChart);
  document.getElementById("s4-apply-btn").addEventListener("click", s4ApplyBulk);
  document.getElementById("s4-uncheck-all-btn").addEventListener("click", s4UncheckAll);
  document.getElementById("s4-check-all-month").addEventListener("change", s4CheckAllVisible);
  document.getElementById("s4-save-btn").addEventListener("click", s4SaveLabels);
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

let RC_DATA = null;
let RC_CURRENT_RECIPE = null;
let RC_CHART_DAYS = [];
let RC_CHART = null;

const rcBackgroundPlugin = {
  id: "rcBackgroundPlugin",
  beforeDatasetsDraw(chart) {
    const {ctx, chartArea, scales} = chart;
    if (!chartArea || !RC_CHART_DAYS.length) return;
    const xScale = scales.x;
    const midY = (chartArea.top + chartArea.bottom) / 2;
    ctx.save();
    for (let i = 0; i < RC_CHART_DAYS.length; i++) {
      const d = RC_CHART_DAYS[i];
      const x0 = xScale.getPixelForValue(i);
      const x1 = (i + 1 < RC_CHART_DAYS.length) ? xScale.getPixelForValue(i + 1) : chartArea.right;
      const left = Math.max(x0, chartArea.left);
      const right = Math.min(x1, chartArea.right);
      if (right <= left) continue;
      ctx.fillStyle = mlLabelLight(d.true);
      ctx.fillRect(left, chartArea.top, right - left, midY - chartArea.top);
      ctx.fillStyle = mlLabelLight(d.pred);
      ctx.fillRect(left, midY, right - left, chartArea.bottom - midY);
    }
    ctx.strokeStyle = "rgba(0,0,0,0.2)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(chartArea.left, midY);
    ctx.lineTo(chartArea.right, midY);
    ctx.stroke();
    ctx.restore();
  },
};

function rcRenderPriceChart(rid) {
  const monthFilter = document.getElementById("rc-chart-month-filter").value;
  const days = rcRecipeDays(rid);
  RC_CHART_DAYS = monthFilter === "all" ? days.slice() : days.filter((d) => d.date.startsWith(monthFilter));
  const canvas = document.getElementById("rc-price-chart");
  if (RC_CHART) RC_CHART.destroy();
  RC_CHART = new Chart(canvas, {
    type: "line",
    data: {
      labels: RC_CHART_DAYS.map((d) => d.date),
      datasets: [{
        label: "close",
        data: RC_CHART_DAYS.map((d) => d.close),
        borderColor: "#1a1a1a",
        backgroundColor: "rgba(0,0,0,0)",
        borderWidth: 1.4,
        pointRadius: 0,
        tension: 0,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: {
        legend: {display: false},
        tooltip: {
          callbacks: {
            afterBody(items) {
              const idx = items[0].dataIndex;
              const d = RC_CHART_DAYS[idx];
              const mark = d.match === true ? "◯一致" : (d.match === false ? "✗ミス" : "—");
              return `肉眼: ${d.true || "—"} / 予測: ${d.pred || "—"} ${mark}`;
            },
          },
        },
      },
      scales: {x: {ticks: {maxTicksLimit: 14}}, y: {beginAtZero: false}},
    },
    plugins: [rcBackgroundPlugin],
  });
}

function rcMonthMode(labels) {
  const counts = {};
  for (const l of labels) {
    if (!l) continue;
    counts[l] = (counts[l] || 0) + 1;
  }
  let best = null, bn = -1;
  for (const k in counts) {
    if (counts[k] > bn) { best = k; bn = counts[k]; }
  }
  return best;
}

function rcRecipeDays(rid) {
  return RC_DATA.days.map((d) => ({
    date: d.date,
    close: d.close,
    true: d.true,
    pred: d.predicts[rid] || null,
    match: d.matches[rid] === undefined ? null : d.matches[rid],
  }));
}

function rcRenderRecipeDetail(rid) {
  const r = RC_DATA.recipes.find((x) => x.id === rid);
  if (!r) return "";
  const tfs = r.timeframes.join(", ");
  const inds = r.indicators.map((i) => `${i.tf}=${i.name}${i.period ? "(" + i.period + ")" : ""}`).join(" / ");
  return `${r.label} | TF: ${tfs} | IND: ${inds} | AGG: intra=${r.aggregation_intra}, cross=${r.aggregation_cross}`;
}

function rcRenderSummary(rid) {
  const r = RC_DATA.recipes.find((x) => x.id === rid);
  if (!r) return;
  document.getElementById("rc-monthly-acc").textContent =
    r.monthly_acc != null ? `${(r.monthly_acc * 100).toFixed(1)}%` : "—";
  document.getElementById("rc-daily-acc").textContent =
    r.daily_acc != null ? `${(r.daily_acc * 100).toFixed(1)}%` : "—";
  const days = rcRecipeDays(rid);
  const mismatch = days.filter((d) => d.match === false).length;
  document.getElementById("rc-mismatch-count").textContent = `${mismatch} / ${days.length}日`;
  document.getElementById("rc-cb-pass").textContent = r.candidate_b_pass ? "✅" : "❌";
  document.getElementById("rc-period").textContent =
    `${RC_DATA.period.start} 〜 ${RC_DATA.period.end}`;
  document.getElementById("rc-recipe-detail").textContent = rcRenderRecipeDetail(rid);
}

function rcRenderDistTable(rid) {
  const days = rcRecipeDays(rid);
  const trueDist = {downtrend: 0, range: 0, uptrend: 0};
  const predDist = {downtrend: 0, range: 0, uptrend: 0};
  for (const d of days) {
    if (d.true && trueDist[d.true] !== undefined) trueDist[d.true]++;
    if (d.pred && predDist[d.pred] !== undefined) predDist[d.pred]++;
  }
  const tbody = document.querySelector("#rc-dist-table tbody");
  tbody.innerHTML = "";
  for (const reg of ["downtrend", "range", "uptrend"]) {
    const tr = document.createElement("tr");
    const diff = predDist[reg] - trueDist[reg];
    const diffStr = diff >= 0 ? `+${diff}` : `${diff}`;
    tr.innerHTML =
      `<td><strong style="color:${mlLabelColor(reg)};">${reg}</strong></td>` +
      `<td class="num">${trueDist[reg]}</td>` +
      `<td class="num">${predDist[reg]}</td>` +
      `<td class="num">${diffStr}</td>`;
    tbody.appendChild(tr);
  }
}

function rcRenderMonthlyStrip(rid) {
  const days = rcRecipeDays(rid);
  const byMonth = {};
  for (const d of days) {
    const m = d.date.slice(0, 7);
    if (!byMonth[m]) byMonth[m] = {trues: [], preds: []};
    byMonth[m].trues.push(d.true);
    byMonth[m].preds.push(d.pred);
  }
  const wrap = document.getElementById("rc-monthly-strip");
  wrap.innerHTML = "";
  const months = Object.keys(byMonth).sort();
  for (const m of months) {
    const trueLab = rcMonthMode(byMonth[m].trues);
    const predLab = rcMonthMode(byMonth[m].preds);
    const cell = document.createElement("div");
    cell.style.cssText = "min-width:62px;text-align:center;border:1px solid #ccc;cursor:pointer;font-size:0.78em;";
    cell.title = `${m}\n肉眼: ${trueLab || "—"}\n予測: ${predLab || "—"}\n${trueLab === predLab ? "✓ 一致" : "✗ 不一致"}`;
    cell.innerHTML =
      `<div style="background:${mlLabelColor(trueLab)}40;padding:3px 4px;color:#000;border-bottom:1px solid #999;">${m.slice(2)}<br>${(trueLab || "").slice(0, 4)}</div>` +
      `<div style="background:${mlLabelColor(predLab)}40;padding:3px 4px;color:#000;">${(predLab || "").slice(0, 4)}</div>`;
    cell.addEventListener("click", () => {
      document.getElementById("rc-month-filter").value = m;
      rcRenderDayTable(rid);
    });
    wrap.appendChild(cell);
  }
}

function rcRenderDayTable(rid) {
  const filter = document.getElementById("rc-row-filter").value;
  const monthFilter = document.getElementById("rc-month-filter").value;
  const days = rcRecipeDays(rid);
  const tbody = document.querySelector("#rc-day-table tbody");
  tbody.innerHTML = "";
  let count = 0;
  for (const d of days) {
    if (monthFilter !== "all" && !d.date.startsWith(monthFilter)) continue;
    if (filter === "mismatch" && d.match !== false) continue;
    if (filter === "match" && d.match !== true) continue;
    count++;
    const tlbl = d.true ? `<strong style="color:${mlLabelColor(d.true)};">${d.true}</strong>` : "—";
    const plbl = d.pred ? `<strong style="color:${mlLabelColor(d.pred)};">${d.pred}</strong>` : "—";
    const mark = d.match === true ? "◯" : (d.match === false ? "✗" : "—");
    const tr = document.createElement("tr");
    tr.innerHTML =
      `<td>${d.date}</td>` +
      `<td>${mlDow(d.date)}</td>` +
      `<td class="num">${d.close != null ? Number(d.close).toFixed(0) : "—"}</td>` +
      `<td>${tlbl}</td>` +
      `<td>${plbl}</td>` +
      `<td>${mark}</td>`;
    tbody.appendChild(tr);
  }
  document.getElementById("rc-row-count").textContent = `表示中: ${count}日`;
}

function rcRenderRankTable() {
  const tbody = document.querySelector("#rc-rank-table tbody");
  tbody.innerHTML = "";
  const sorted = RC_DATA.recipes.slice().sort((a, b) => {
    const am = a.monthly_acc ?? -1, bm = b.monthly_acc ?? -1;
    if (bm !== am) return bm - am;
    const ad = a.daily_acc ?? -1, bd = b.daily_acc ?? -1;
    return bd - ad;
  });
  sorted.forEach((r, i) => {
    const tr = document.createElement("tr");
    tr.style.cursor = "pointer";
    if (r.id === RC_CURRENT_RECIPE) tr.style.background = "#fffbe0";
    tr.innerHTML =
      `<td class="num">${i + 1}</td>` +
      `<td><strong>${r.id}</strong></td>` +
      `<td>${r.label}</td>` +
      `<td class="num">${r.monthly_acc != null ? (r.monthly_acc * 100).toFixed(1) + "%" : "—"}</td>` +
      `<td class="num">${r.daily_acc != null ? (r.daily_acc * 100).toFixed(1) + "%" : "—"}</td>` +
      `<td>${r.candidate_b_pass ? "✅" : "❌"}</td>` +
      `<td class="num">${r.mode_run_len ?? "—"}</td>`;
    tr.addEventListener("click", () => {
      document.getElementById("rc-recipe-select").value = r.id;
      rcSwitchRecipe(r.id);
    });
    tbody.appendChild(tr);
  });
}

function rcSwitchRecipe(rid) {
  RC_CURRENT_RECIPE = rid;
  rcRenderSummary(rid);
  rcRenderDistTable(rid);
  rcRenderMonthlyStrip(rid);
  rcRenderDayTable(rid);
  rcRenderRankTable();
  rcRenderPriceChart(rid);
}

function rcPopulateMonthFilter() {
  const months = Array.from(new Set(RC_DATA.days.map((d) => d.date.slice(0, 7)))).sort();
  for (const selId of ["rc-month-filter", "rc-chart-month-filter"]) {
    const sel = document.getElementById(selId);
    sel.innerHTML = '<option value="all">全期間</option>';
    for (const m of months) {
      const opt = document.createElement("option");
      opt.value = m; opt.textContent = m;
      sel.appendChild(opt);
    }
  }
}

function rcPopulateRecipeSelect() {
  const sel = document.getElementById("rc-recipe-select");
  sel.innerHTML = "";
  const sorted = RC_DATA.recipes.slice().sort((a, b) => {
    const am = a.monthly_acc ?? -1, bm = b.monthly_acc ?? -1;
    if (bm !== am) return bm - am;
    return (b.daily_acc ?? -1) - (a.daily_acc ?? -1);
  });
  for (const r of sorted) {
    const opt = document.createElement("option");
    opt.value = r.id;
    const monthly = r.monthly_acc != null ? (r.monthly_acc * 100).toFixed(0) + "%" : "—";
    const daily = r.daily_acc != null ? (r.daily_acc * 100).toFixed(0) + "%" : "—";
    opt.textContent = `${r.id}  M=${monthly} D=${daily}  ${r.label}`;
    sel.appendChild(opt);
  }
}

async function renderRecipeCheck() {
  RC_DATA = await fetchJSON("data/recipe_predictions.json");
  rcPopulateRecipeSelect();
  rcPopulateMonthFilter();
  const initial = document.getElementById("rc-recipe-select").value;
  rcSwitchRecipe(initial);
  document.getElementById("rc-recipe-select").addEventListener("change", (e) => rcSwitchRecipe(e.target.value));
  document.getElementById("rc-row-filter").addEventListener("change", () => rcRenderDayTable(RC_CURRENT_RECIPE));
  document.getElementById("rc-month-filter").addEventListener("change", () => rcRenderDayTable(RC_CURRENT_RECIPE));
  document.getElementById("rc-chart-month-filter").addEventListener("change", () => rcRenderPriceChart(RC_CURRENT_RECIPE));
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

// ====== ⑪ レジーム試作 ======
let RP_INDEX = null;
const RP_DATA = {};
let RP_CHART = null;
let RP_CHART_ROWS = [];

const rpBackgroundPlugin = {
  id: "rpBackgroundPlugin",
  beforeDatasetsDraw(chart) {
    const {ctx, chartArea, scales} = chart;
    if (!chartArea || !RP_CHART_ROWS.length) return;
    const xScale = scales.x;
    const midY = (chartArea.top + chartArea.bottom) / 2;
    ctx.save();
    for (let i = 0; i < RP_CHART_ROWS.length; i++) {
      const r = RP_CHART_ROWS[i];
      const x0 = xScale.getPixelForValue(i);
      const x1 = (i + 1 < RP_CHART_ROWS.length) ? xScale.getPixelForValue(i + 1) : chartArea.right;
      const left  = Math.max(x0, chartArea.left);
      const right = Math.min(x1, chartArea.right);
      if (right <= left) continue;
      ctx.fillStyle = mlLabelLight(r[3]);  // human (top)
      ctx.fillRect(left, chartArea.top, right - left, midY - chartArea.top);
      ctx.fillStyle = mlLabelLight(r[2]);  // pred  (bottom)
      ctx.fillRect(left, midY, right - left, chartArea.bottom - midY);
    }
    ctx.strokeStyle = "rgba(0,0,0,0.2)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(chartArea.left, midY);
    ctx.lineTo(chartArea.right, midY);
    ctx.stroke();
    ctx.restore();
  },
};

function rpAggregateTo4h(rows1h) {
  // group every 4 hourly rows by 4h boundary (UTC). use first row's ts and last row's close;
  // pred/human are mode (most common label) within the bucket.
  const buckets = new Map();
  for (const r of rows1h) {
    const bucketTs = Math.floor(r[0] / (4 * 3600 * 1000)) * (4 * 3600 * 1000);
    let b = buckets.get(bucketTs);
    if (!b) { b = {ts: bucketTs, lastClose: r[1], pred: {}, human: {}}; buckets.set(bucketTs, b); }
    b.lastClose = r[1];
    if (r[2]) b.pred[r[2]]   = (b.pred[r[2]]   || 0) + 1;
    if (r[3]) b.human[r[3]] = (b.human[r[3]] || 0) + 1;
  }
  const mode = (m) => {
    let bestK = "", bestV = 0;
    for (const k in m) if (m[k] > bestV) { bestV = m[k]; bestK = k; }
    return bestK;
  };
  return Array.from(buckets.values()).sort((a, b) => a.ts - b.ts)
    .map(b => [b.ts, b.lastClose, mode(b.pred), mode(b.human)]);
}

async function rpFetchData(version, granularity, yearMonth) {
  RP_DATA[version] = RP_DATA[version] || {};
  if (granularity === "5m") {
    RP_DATA[version]["5m"] = RP_DATA[version]["5m"] || {};
    if (!RP_DATA[version]["5m"][yearMonth]) {
      const data = await fetchJSON(`regime_prototype/predictions_${version}_5m/${yearMonth}.json`);
      RP_DATA[version]["5m"][yearMonth] = data.rows;
    }
    return RP_DATA[version]["5m"][yearMonth];
  }
  if (granularity === "4h") {
    if (!RP_DATA[version]["4h"]) {
      const rows1h = await rpFetchData(version, "1h");
      RP_DATA[version]["4h"] = rpAggregateTo4h(rows1h);
    }
    return RP_DATA[version]["4h"];
  }
  if (!RP_DATA[version][granularity]) {
    const data = await fetchJSON(`regime_prototype/predictions_${version}_${granularity}.json`);
    RP_DATA[version][granularity] = data.rows;
  }
  return RP_DATA[version][granularity];
}

function rpFilterByMonth(rows, yearMonth) {
  if (yearMonth === "all") return rows;
  const [y, m] = yearMonth.split("-").map(Number);
  const start = Date.UTC(y, m - 1, 1);
  const end   = Date.UTC(y, m, 1);
  return rows.filter(r => r[0] >= start && r[0] < end);
}

function rpFmtTs(tsMs, granularity) {
  const d = new Date(tsMs);
  const iso = d.toISOString();
  if (granularity === "1d") return iso.slice(0, 10);
  return iso.slice(0, 16).replace("T", " ");
}

async function rpRenderChart() {
  const version = document.getElementById("rp-version").value;
  const gran    = document.getElementById("rp-granularity").value;
  const ym      = document.getElementById("rp-month").value;
  const loading = document.getElementById("rp-loading");
  loading.textContent = "読み込み中...";

  let rows;
  if (gran === "5m") {
    if (ym === "all") {
      loading.textContent = "5分粒度では月を選択してください（全期間は重すぎます）";
      return;
    }
    rows = await rpFetchData(version, "5m", ym);
  } else {
    const all = await rpFetchData(version, gran);
    rows = rpFilterByMonth(all, ym);
  }
  loading.textContent = `${rows.length.toLocaleString()} 行`;

  RP_CHART_ROWS = rows;
  const labels = rows.map(r => rpFmtTs(r[0], gran));
  const closes = rows.map(r => r[1]);

  if (RP_CHART) RP_CHART.destroy();
  const ctx = document.getElementById("rp-chart").getContext("2d");
  RP_CHART = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "BTC close",
        data: closes,
        borderColor: "#1976d2",
        backgroundColor: "transparent",
        tension: 0.1,
        pointRadius: 0,
        borderWidth: 1.4,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      interaction: {mode: "index", intersect: false},
      plugins: {
        legend: {display: false},
        tooltip: {
          callbacks: {
            afterLabel: (item) => {
              const r = RP_CHART_ROWS[item.dataIndex];
              if (!r) return "";
              return `肉眼: ${r[3] || "—"} / 予測: ${r[2] || "—"}`;
            },
          },
        },
      },
      scales: {x: {ticks: {maxTicksLimit: 14}}, y: {beginAtZero: false}},
    },
    plugins: [rpBackgroundPlugin],
  });
}

function rpRenderSummary() {
  const version = document.getElementById("rp-version").value;
  const proto = RP_INDEX.prototypes.find(p => p.version === version);
  if (!proto) return;
  document.getElementById("rp-spec").innerHTML =
    `<strong>仕様（${version}）</strong>` +
    `<ul style="margin:6px 0;line-height:1.7;">` +
    `<li>上位: ${proto.spec.upper}</li>` +
    `<li>中位: ${proto.spec.middle}</li>` +
    `<li>下位: ${proto.spec.lower}</li>` +
    `<li>統合: ${proto.spec.integration}</li>` +
    `<li>ヒステリシス: ${proto.spec.hysteresis_hours} 時間</li>` +
    `<li>出力粒度: ${proto.spec.output_granularity}</li>` +
    `</ul>` +
    `<small style="color:#666;">生成: ${proto.generated_utc}</small>`;
  const a1h = proto.accuracy["1h"];
  const a1d = proto.accuracy["1d"];
  document.getElementById("rp-acc-1h").textContent = a1h && a1h.accuracy != null
    ? `${(a1h.accuracy * 100).toFixed(1)}% (${a1h.hit.toLocaleString()}/${a1h.n.toLocaleString()})` : "—";
  document.getElementById("rp-acc-1d").textContent = a1d && a1d.accuracy != null
    ? `${(a1d.accuracy * 100).toFixed(1)}% (${a1d.hit.toLocaleString()}/${a1d.n.toLocaleString()})` : "—";
  const dist = proto.distribution || {};
  const pctOf = (k) => dist[k] ? `${dist[k].pct}%` : "0%";
  document.getElementById("rp-dist").textContent =
    `up ${pctOf("uptrend")} / dn ${pctOf("downtrend")} / rg ${pctOf("range")}`;
}

async function rpRenderDayTable() {
  const version = document.getElementById("rp-version").value;
  const filter  = document.getElementById("rp-day-filter").value;
  const rowsHourly = await rpFetchData(version, "1h");
  const rowsDaily  = await rpFetchData(version, "1d");
  const dailyBreak = {};
  for (const r of rowsHourly) {
    const d = new Date(r[0]).toISOString().slice(0, 10);
    dailyBreak[d] = dailyBreak[d] || {uptrend: 0, downtrend: 0, range: 0};
    if (r[2] && dailyBreak[d][r[2]] !== undefined) dailyBreak[d][r[2]]++;
  }
  const tbody = document.querySelector("#rp-day-table tbody");
  tbody.innerHTML = "";
  let count = 0;
  for (const r of rowsDaily) {
    const date = new Date(r[0]).toISOString().slice(0, 10);
    const close = r[1], pred = r[2], hu = r[3];
    const valid = pred && hu;
    const match = valid && pred === hu;
    if (filter === "mismatch" && (!valid || match)) continue;
    if (filter === "match" && !match) continue;
    count++;
    const br = dailyBreak[date] || {uptrend: 0, downtrend: 0, range: 0};
    const tr = document.createElement("tr");
    tr.innerHTML =
      `<td>${date}</td>` +
      `<td class="num">${Number(close).toLocaleString()}</td>` +
      `<td><strong style="color:${mlLabelColor(hu)};">${hu || "—"}</strong></td>` +
      `<td><strong style="color:${mlLabelColor(pred)};">${pred || "—"}</strong></td>` +
      `<td>${valid ? (match ? "◯" : "×") : "—"}</td>` +
      `<td class="num">${br.uptrend}</td>` +
      `<td class="num">${br.range}</td>` +
      `<td class="num">${br.downtrend}</td>`;
    tbody.appendChild(tr);
  }
  document.getElementById("rp-day-count").textContent = `表示中: ${count}日`;
}

async function renderRegimeProto() {
  RP_INDEX = await fetchJSON("regime_prototype/index.json");
  if (!RP_INDEX.prototypes || !RP_INDEX.prototypes.length) return;

  const vs = document.getElementById("rp-version");
  vs.innerHTML = "";
  for (const p of RP_INDEX.prototypes) {
    const opt = document.createElement("option");
    opt.value = p.version; opt.textContent = p.version;
    vs.appendChild(opt);
  }
  vs.value = RP_INDEX.prototypes[RP_INDEX.prototypes.length - 1].version;

  const ms = document.getElementById("rp-month");
  ms.innerHTML = '<option value="all" selected>全期間</option>';
  for (const ym of (RP_INDEX.available_months || [])) {
    const opt = document.createElement("option");
    opt.value = ym; opt.textContent = ym;
    ms.appendChild(opt);
  }

  document.getElementById("rp-version").addEventListener("change", async () => {
    rpRenderSummary(); await rpRenderChart(); await rpRenderDayTable();
  });
  document.getElementById("rp-granularity").addEventListener("change", rpRenderChart);
  document.getElementById("rp-month").addEventListener("change", rpRenderChart);
  document.getElementById("rp-day-filter").addEventListener("change", rpRenderDayTable);

  rpRenderSummary();
  await rpRenderChart();
  await rpRenderDayTable();
}

// ============================================================
// ⑬ レジーム持続分布（連続区間長 run-length）
// ============================================================
let RL_DATA = null;
let RL_CHART_A = null;
let RL_CHART_B = null;

function rlFmtH(x) {
  if (x === null || x === undefined || isNaN(x)) return "—";
  if (x >= 24) return `${x.toFixed(1)}h (${(x/24).toFixed(1)}d)`;
  return `${x.toFixed(1)}h`;
}

function rlRenderTable() {
  if (!RL_DATA) return;
  const filter = document.getElementById("rl-label-filter").value;
  const tbody = document.querySelector("#rl-stats-table tbody");
  tbody.innerHTML = "";

  const sources = [
    { tag: "A. 4h 教師", data: RL_DATA.source_a },
    { tag: "B. v14 1h", data: RL_DATA.source_b },
  ];
  const labelsToShow = filter === "ALL"
    ? ["ALL", "uptrend", "downtrend", "range"]
    : [filter];

  for (const src of sources) {
    for (const lab of labelsToShow) {
      const s = src.data.stats[lab];
      if (!s || !s.n) {
        tbody.insertAdjacentHTML("beforeend",
          `<tr><td>${src.tag}</td><td>${lab}</td><td>0</td><td colspan="8">—</td></tr>`);
        continue;
      }
      tbody.insertAdjacentHTML("beforeend", `<tr>
        <td>${src.tag}</td><td>${lab}</td><td>${s.n}</td>
        <td>${rlFmtH(s.median_h)}</td><td>${rlFmtH(s.mean_h)}</td>
        <td>${rlFmtH(s.p25_h)}</td><td>${rlFmtH(s.p75_h)}</td>
        <td>${rlFmtH(s.p90_h)}</td><td>${rlFmtH(s.p99_h)}</td>
        <td>${rlFmtH(s.max_h)}</td><td>${rlFmtH(s.min_h)}</td>
      </tr>`);
    }
  }
}

function rlBuildChartConfig(histogram, label, sourceLabel) {
  const bins = histogram.bin_labels;
  const data = histogram[label];
  return {
    type: "bar",
    data: {
      labels: bins,
      datasets: [{
        label: `${sourceLabel} ${label}`,
        data: data,
        backgroundColor: label === "uptrend" ? "rgba(46,160,67,0.7)"
          : label === "downtrend" ? "rgba(207,34,46,0.7)"
          : label === "range" ? "rgba(132,141,153,0.7)"
          : "rgba(58,118,200,0.7)",
        borderColor: "#333",
        borderWidth: 1,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: true } },
      scales: {
        x: { title: { display: true, text: "持続時間 bin" } },
        y: { title: { display: true, text: "run 数" }, beginAtZero: true },
      },
    },
  };
}

function rlRenderCharts() {
  if (!RL_DATA) return;
  const filter = document.getElementById("rl-label-filter").value;
  if (RL_CHART_A) RL_CHART_A.destroy();
  if (RL_CHART_B) RL_CHART_B.destroy();
  const ctxA = document.getElementById("rl-chart-a");
  const ctxB = document.getElementById("rl-chart-b");
  RL_CHART_A = new Chart(ctxA, rlBuildChartConfig(RL_DATA.source_a.histogram, filter, "A: 4h教師"));
  RL_CHART_B = new Chart(ctxB, rlBuildChartConfig(RL_DATA.source_b.histogram, filter, "B: v14 1h"));
  document.getElementById("rl-chart-a-title").textContent =
    `A. ${RL_DATA.source_a.name} (ラベル付き ${RL_DATA.source_a.n_bars_labeled}/${RL_DATA.source_a.n_bars_total})`;
  document.getElementById("rl-chart-b-title").textContent =
    `B. ${RL_DATA.source_b.name} (ラベル付き ${RL_DATA.source_b.n_bars_labeled}/${RL_DATA.source_b.n_bars_total})`;
}

async function renderRunLength() {
  RL_DATA = await fetchJSON("data/regime_label_run_length.json");
  document.getElementById("rl-label-filter").addEventListener("change", () => {
    rlRenderTable();
    rlRenderCharts();
  });
  rlRenderTable();
  // Chart.js は display:none のタブで dimension=0 となり空描画する。
  // タブが active になった瞬間に再描画する。
  const rlBtn = document.querySelector('header nav button[data-tab="run_length"]');
  if (rlBtn) {
    rlBtn.addEventListener("click", () => {
      // クリック後 display:block になってから次フレームで描画
      requestAnimationFrame(() => rlRenderCharts());
    });
  }
  // 初回も試行（既に表示されていれば描画される）
  rlRenderCharts();
}

// ============================================================
// ⑭ trade × regime 境界 整合性検証
// ============================================================
let TC_DATA = null;
let TC_CHART_NET = null;
let TC_CHART_PRI = null;

function tcFmtUsd(x) {
  if (x === null || x === undefined || isNaN(x)) return "—";
  const sign = x >= 0 ? "+" : "−";
  return `${sign}$${Math.abs(x).toFixed(2)}`;
}

function tcFmtPct(x) {
  if (x === null || x === undefined || isNaN(x)) return "—";
  return `${x.toFixed(1)}%`;
}

function tcRenderTables() {
  if (!TC_DATA) return;
  const oi = TC_DATA.overall_implied;
  const os = TC_DATA.overall_strict;
  const oTbody = document.querySelector("#tc-overall-table tbody");
  oTbody.innerHTML = `
    <tr>
      <td>IMPLIED（主軸）</td><td>${oi.n_total}</td><td>${oi.n_decided}</td>
      <td>${oi.n_crossing}</td><td>${oi.n_non_crossing}</td>
      <td><strong>${tcFmtPct(oi.non_crossing_pct)}</strong></td>
      <td>${oi.n_undetermined}</td>
    </tr>
    <tr>
      <td>STRICT（参考）</td><td>${os.n_total}</td><td>${os.n_decided}</td>
      <td>${os.n_crossing}</td><td>${os.n_non_crossing}</td>
      <td>${tcFmtPct(os.non_crossing_pct)}</td>
      <td>${os.n_unlabeled}</td>
    </tr>`;

  const netTbody = document.querySelector("#tc-net-table tbody");
  netTbody.innerHTML = "";
  for (const status of ["IMPLIED_CROSSING", "IMPLIED_NON_CROSSING", "IMPLIED_UNDETERMINED"]) {
    const d = TC_DATA.net_dist_implied[status];
    if (!d || !d.n) {
      netTbody.insertAdjacentHTML("beforeend",
        `<tr><td>${status}</td><td>0</td><td colspan="6">—</td></tr>`);
      continue;
    }
    netTbody.insertAdjacentHTML("beforeend", `<tr>
      <td>${status}</td><td>${d.n}</td>
      <td>${tcFmtUsd(d.sum)}</td><td>${tcFmtUsd(d.mean)}</td>
      <td>${tcFmtUsd(d.median)}</td><td>${tcFmtUsd(d.p25)}</td><td>${tcFmtUsd(d.p75)}</td>
      <td>${tcFmtPct(d.win_rate * 100)}</td>
    </tr>`);
  }

  const priTbody = document.querySelector("#tc-priority-table tbody");
  priTbody.innerHTML = "";
  for (const r of TC_DATA.by_priority) {
    priTbody.insertAdjacentHTML("beforeend", `<tr>
      <td>P${r.key}</td><td>${r.n_trades}</td><td>${r.n_decided}</td>
      <td>${r.n_crossing}</td><td>${r.n_non_crossing}</td>
      <td>${tcFmtPct(r.non_crossing_pct)}</td>
      <td>${tcFmtUsd(r.net_crossing)}</td><td>${tcFmtUsd(r.net_non_crossing)}</td>
    </tr>`);
  }

  const holdTbody = document.querySelector("#tc-hold-table tbody");
  holdTbody.innerHTML = "";
  for (const r of TC_DATA.by_hold_bucket) {
    if (r.n === 0) {
      holdTbody.insertAdjacentHTML("beforeend",
        `<tr><td>${r.bucket}</td><td>0</td><td colspan="4">—</td></tr>`);
      continue;
    }
    holdTbody.insertAdjacentHTML("beforeend", `<tr>
      <td>${r.bucket}</td><td>${r.n}</td><td>${r.n_decided ?? 0}</td>
      <td>${r.n_crossing ?? 0}</td><td>${tcFmtPct(r.crossing_pct)}</td>
      <td>${tcFmtUsd(r.net_total)}</td>
    </tr>`);
  }
}

function tcRenderCharts() {
  if (!TC_DATA) return;
  if (TC_CHART_NET) TC_CHART_NET.destroy();
  if (TC_CHART_PRI) TC_CHART_PRI.destroy();

  const nd = TC_DATA.net_dist_implied;
  const ctxNet = document.getElementById("tc-net-chart");
  TC_CHART_NET = new Chart(ctxNet, {
    type: "bar",
    data: {
      labels: ["CROSSING", "NON_CROSSING", "UNDETERMINED"],
      datasets: [
        {
          label: "mean ($)",
          data: [nd.IMPLIED_CROSSING.mean ?? 0, nd.IMPLIED_NON_CROSSING.mean ?? 0, nd.IMPLIED_UNDETERMINED.mean ?? 0],
          backgroundColor: "rgba(58,118,200,0.7)",
        },
        {
          label: "median ($)",
          data: [nd.IMPLIED_CROSSING.median ?? 0, nd.IMPLIED_NON_CROSSING.median ?? 0, nd.IMPLIED_UNDETERMINED.median ?? 0],
          backgroundColor: "rgba(46,160,67,0.7)",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { y: { title: { display: true, text: "net_usd" } } },
    },
  });

  const ctxPri = document.getElementById("tc-pri-chart");
  const labels = TC_DATA.by_priority.map(r => `P${r.key}`);
  const nonPct = TC_DATA.by_priority.map(r => r.non_crossing_pct ?? 0);
  const crossPct = TC_DATA.by_priority.map(r => r.crossing_pct ?? 0);
  TC_CHART_PRI = new Chart(ctxPri, {
    type: "bar",
    data: {
      labels,
      datasets: [
        { label: "non_crossing %", data: nonPct, backgroundColor: "rgba(46,160,67,0.7)" },
        { label: "crossing %", data: crossPct, backgroundColor: "rgba(207,34,46,0.7)" },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { beginAtZero: true, max: 100, title: { display: true, text: "% of decided" } },
        x: { stacked: false },
      },
    },
  });
}

async function renderTradeCrossing() {
  TC_DATA = await fetchJSON("data/trade_regime_crossing.json");
  const tcBtn = document.querySelector('header nav button[data-tab="trade_crossing"]');
  if (tcBtn) {
    tcBtn.addEventListener("click", () => {
      requestAnimationFrame(() => tcRenderCharts());
    });
  }
  tcRenderTables();
  tcRenderCharts();
}

// ============================================================
// ⑮ 頭打ち原因分析
// ============================================================
let HR_DATA = null;
const HR_CHARTS = {};

function hrUsd(x) {
  if (x === null || x === undefined || isNaN(x)) return "—";
  return (x >= 0 ? "+$" : "−$") + Math.abs(x).toFixed(2);
}
function hrPct(x) {
  if (x === null || x === undefined || isNaN(x)) return "—";
  return (x * 100).toFixed(3) + "%";
}

function hrRenderMeta() {
  const m = HR_DATA.meta;
  document.getElementById("hr-meta").innerHTML = `
    生成: ${m.generated_at} / replay: <code>${m.replay_csv}</code> ${m.replay_start.slice(0,10)} → ${m.replay_end.slice(0,10)} / trade=${m.replay_n} / NET=${hrUsd(m.replay_net)} / 月次平均=${hrUsd(m.replay_monthly_avg)}<br>
    parquet マッチ: ${m.matched_n} / ${m.replay_n} (${m.matched_pct}%) — 2026-Q1 (${m.replay_n - m.matched_n} trade) は parquet 未生成のため除外。合格ライン: 月次 ≥ $${m.pass_line_month}.
  `;
}

function hrRenderVerdict() {
  const v = HR_DATA.verdict;
  const yn = (b) => b ? "<span style='color:#1a7f37;font-weight:bold;'>YES</span>" : "<span style='color:#cf222e;font-weight:bold;'>NO</span>";
  document.querySelector("#hr-verdict-table tbody").innerHTML = `
    <tr><td>Entry 質 random より良い？</td><td>p_mfe_median=${v.p_mfe_vs_random_median}</td><td>${yn(v.entry_quality_ok)}</td></tr>
    <tr><td>完璧 K=96 Exit で全月 $1,900 達成？</td><td>worst_month=${hrUsd(v.perfect_k96_worst_month)}</td><td>${yn(v.perfect_k96_all_12mo_pass)}</td></tr>
    <tr><td>いずれかの仮想 Exit で全月 $1,900 達成？</td><td>${v.n_patterns_all_pass} / ${v.n_patterns_total} パターン</td><td>${yn(v.any_pattern_all_12mo_pass)}</td></tr>
  `;
  const banner = document.getElementById("hr-verdict-banner");
  banner.textContent = "暫定判定: " + v.verdict_label;
  banner.style.background = v.perfect_k96_all_12mo_pass ? "#dafbe1" : "#ffebe9";
  banner.style.color = v.perfect_k96_all_12mo_pass ? "#1a7f37" : "#cf222e";
  document.getElementById("hr-verdict-detail").textContent = v.verdict_detail +
    "（注: 本仕様 §5 マトリクスの機械的マッピング。最終判定は Web Claude/まこさんがダッシュボード視認のうえで決定）";
}

function hrRenderExit() {
  const rows = HR_DATA.step1.exit_reason.slice().sort((a, b) => b.net_usd_sum - a.net_usd_sum);
  document.querySelector("#hr-exit-table tbody").innerHTML = rows.map(r =>
    `<tr><td>${r.bucket}</td><td>${r.n_trades}</td><td class="${classNum(r.net_usd_sum)}">${hrUsd(r.net_usd_sum)}</td><td>${hrUsd(r.net_usd_median)}</td><td>${hrUsd(r.mfe_minus_net_median)}</td></tr>`
  ).join("");
  if (HR_CHARTS.exit) HR_CHARTS.exit.destroy();
  HR_CHARTS.exit = new Chart(document.getElementById("hr-exit-chart"), {
    type: "bar",
    data: {
      labels: rows.map(r => r.bucket),
      datasets: [{
        label: "net_usd_sum ($)",
        data: rows.map(r => r.net_usd_sum),
        backgroundColor: rows.map(r => r.net_usd_sum >= 0 ? "rgba(46,160,67,0.7)" : "rgba(207,34,46,0.7)"),
      }],
    },
    options: { responsive: true, maintainAspectRatio: false, indexAxis: "y",
      scales: { x: { title: { display: true, text: "NET USD" } } } },
  });
}

function hrRenderLoss() {
  const allBuckets = [];
  for (const axis of ["exit_reason", "side", "regime", "priority"]) {
    for (const r of HR_DATA.step1[axis]) {
      allBuckets.push({ axis, bucket: r.bucket, n: r.n_trades, loss: r.mfe_minus_net_median });
    }
  }
  allBuckets.sort((a, b) => b.loss - a.loss);
  if (HR_CHARTS.loss) HR_CHARTS.loss.destroy();
  HR_CHARTS.loss = new Chart(document.getElementById("hr-loss-chart"), {
    type: "bar",
    data: {
      labels: allBuckets.map(r => `${r.axis}: ${r.bucket}`),
      datasets: [{
        label: "MFE − net 取りこぼし中央値 ($)",
        data: allBuckets.map(r => r.loss),
        backgroundColor: "rgba(208,135,0,0.7)",
      }],
    },
    options: { responsive: true, maintainAspectRatio: false,
      scales: { y: { title: { display: true, text: "USD" } } } },
  });
}

function hrRenderEntry() {
  const rows = HR_DATA.step2.filter(r => r.K === 24);
  document.querySelector("#hr-entry-table tbody").innerHTML = rows.map(r =>
    `<tr><td>${r.K}</td><td>${r.side}</td><td>${r.group}</td><td>${hrPct(r.mfe_pct_median)}</td><td>${hrPct(r.mae_pct_median)}</td><td>${r.ratio_mfe_over_mae ?? "—"}</td><td>${r.n}</td><td>${r.mw_u_pvalue_mfe_vs_random ?? "—"}</td></tr>`
  ).join("");
  const groups = ["old_p1_p24", "random_baseline", "all_bar", "top5pct_mfe", "top10pct_mfe", "top20pct_mfe"];
  const longRow = (g) => rows.find(r => r.side === "LONG" && r.group === g)?.mfe_pct_median ?? 0;
  const shortRow = (g) => rows.find(r => r.side === "SHORT" && r.group === g)?.mfe_pct_median ?? 0;
  if (HR_CHARTS.entry) HR_CHARTS.entry.destroy();
  HR_CHARTS.entry = new Chart(document.getElementById("hr-entry-chart"), {
    type: "bar",
    data: {
      labels: groups,
      datasets: [
        { label: "LONG mfe_pct median", data: groups.map(longRow), backgroundColor: "rgba(58,118,200,0.7)" },
        { label: "SHORT mfe_pct median", data: groups.map(shortRow), backgroundColor: "rgba(207,34,46,0.7)" },
      ],
    },
    options: { responsive: true, maintainAspectRatio: false,
      scales: { y: { title: { display: true, text: "MFE pct (=median)" } } } },
  });
}

function hrRenderPos() {
  const tbody = document.querySelector("#hr-pos-table tbody");
  const rows = [];
  for (const r of HR_DATA.step3.trades_per_day) rows.push({ axis: "trades/day", bucket: r.bucket, n: r.n_obs, median: r.median, max: r.max, min: r.min });
  for (const r of HR_DATA.step3.concurrent_positions) rows.push({ axis: "concurrent (all)", bucket: r.bucket, n: r.n_obs, median: r.median, max: r.max, min: r.min });
  for (const r of HR_DATA.step3.concurrent_positions_by_side) rows.push({ axis: "concurrent side", bucket: r.bucket, n: r.n_obs, median: r.median, max: r.max, min: r.min });
  tbody.innerHTML = rows.map(r =>
    `<tr><td>${r.axis}</td><td>${r.bucket}</td><td>${r.n}</td><td>${r.median}</td><td>${r.max}</td><td>${r.min}</td></tr>`
  ).join("");
  const alloc = HR_DATA.step3.priority_x_side_alloc;
  if (HR_CHARTS.pri) HR_CHARTS.pri.destroy();
  HR_CHARTS.pri = new Chart(document.getElementById("hr-pri-chart"), {
    type: "bar",
    data: {
      labels: alloc.map(r => r.bucket),
      datasets: [
        { label: "net_usd_sum", data: alloc.map(r => r.net_usd_sum), backgroundColor: "rgba(46,160,67,0.7)", yAxisID: "y" },
        { label: "n_trades", data: alloc.map(r => r.n_trades), backgroundColor: "rgba(58,118,200,0.4)", yAxisID: "y1", type: "line" },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: {
        y: { position: "left", title: { display: true, text: "NET USD" } },
        y1: { position: "right", title: { display: true, text: "n_trades" }, grid: { drawOnChartArea: false } },
      },
    },
  });
}

function hrRenderMonthly() {
  const series = HR_DATA.step4.monthly_series;
  const passLine = HR_DATA.meta.pass_line_month;
  // Use union of months across selected patterns
  const months = new Set();
  const selected = ["baseline_actual", "perfect_exit_K12", "perfect_exit_K24", "perfect_exit_K48", "perfect_exit_K96"];
  for (const k of selected) {
    if (!series[k]) continue;
    for (const m of Object.keys(series[k])) months.add(m);
  }
  const monthLabels = Array.from(months).sort();
  const colors = {
    baseline_actual: "rgba(120,120,120,0.9)",
    perfect_exit_K12: "rgba(58,118,200,0.9)",
    perfect_exit_K24: "rgba(46,160,67,0.9)",
    perfect_exit_K48: "rgba(208,135,0,0.9)",
    perfect_exit_K96: "rgba(207,34,46,0.9)",
  };
  const datasets = selected.map(k => ({
    label: k,
    data: monthLabels.map(m => series[k] ? (series[k][m] ?? null) : null),
    borderColor: colors[k],
    backgroundColor: colors[k],
    spanGaps: true,
    tension: 0.15,
    fill: false,
  }));
  datasets.push({
    label: `合格ライン $${passLine}`,
    data: monthLabels.map(() => passLine),
    borderColor: "rgba(207,34,46,0.6)",
    borderDash: [6, 4],
    pointRadius: 0,
    fill: false,
  });
  if (HR_CHARTS.monthly) HR_CHARTS.monthly.destroy();
  HR_CHARTS.monthly = new Chart(document.getElementById("hr-monthly-chart"), {
    type: "line",
    data: { labels: monthLabels, datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: { y: { title: { display: true, text: "Monthly NET USD" } } },
    },
  });

  // Step4 table: show baseline + perfect + time_exit + top-3 monthly_avg patterns
  const allRows = HR_DATA.step4.rows;
  const ranked = allRows.slice().sort((a, b) => b.monthly_avg - a.monthly_avg);
  const topMonthlyIds = new Set();
  for (let i = 0, n = 0; i < ranked.length && n < 3; i++) {
    if (!ranked[i].pattern_id.startsWith("baseline_") && !ranked[i].pattern_id.startsWith("perfect_") && !ranked[i].pattern_id.startsWith("time_exit_")) {
      topMonthlyIds.add(ranked[i].pattern_id);
      n++;
    }
  }
  const show = allRows.filter(r =>
    r.pattern_id.startsWith("baseline_") ||
    r.pattern_id.startsWith("perfect_exit") ||
    r.pattern_id.startsWith("time_exit") ||
    topMonthlyIds.has(r.pattern_id)
  );
  document.querySelector("#hr-step4-table tbody").innerHTML = show.map(r =>
    `<tr>
      <td>${r.pattern_id}</td>
      <td>${hrUsd(r.net_sum_total)}</td>
      <td>${hrUsd(r.monthly_avg)}</td>
      <td>${hrUsd(r.worst_month_net)}</td>
      <td>${hrUsd(r.best_month_net)}</td>
      <td>${r.n_months_above_1900} / ${r.n_months}</td>
      <td>${r.all_12mo_pass_1900 ? "✅" : "❌"}</td>
      <td>${r.n_trades_used}</td>
    </tr>`
  ).join("");
}

async function renderHeadroom() {
  HR_DATA = await fetchJSON("data/headroom_analysis.json");
  hrRenderMeta();
  hrRenderVerdict();
  const renderCharts = () => {
    hrRenderExit();
    hrRenderLoss();
    hrRenderEntry();
    hrRenderPos();
    hrRenderMonthly();
  };
  const hrBtn = document.querySelector('header nav button[data-tab="headroom"]');
  if (hrBtn) {
    hrBtn.addEventListener("click", () => {
      requestAnimationFrame(renderCharts);
    });
  }
  renderCharts();
}

(async () => {
  // 各 render を独立 try/catch でラップ。1 つ落ちても他は走る。
  const renders = [
    ["progress", renderProgress],
    ["fires", renderFires],
    ["signals", renderSignals],
    ["groundTruth", renderGroundTruth],
    ["truthCheck", renderTruthCheck],
    ["mlCheck", renderMlCheck],
    ["phase1Features", renderPhase1Features],
    ["phase2Hmm", renderPhase2Hmm],
    ["phase3Hmm", renderPhase3Hmm],
    ["recipeCheck", renderRecipeCheck],
    ["regimeProto", renderRegimeProto],
    ["samples4h", renderSamples4h],
    ["runLength", renderRunLength],
    ["tradeCrossing", renderTradeCrossing],
    ["headroom", renderHeadroom],
  ];
  const failures = [];
  for (const [name, fn] of renders) {
    try {
      await fn();
    } catch (e) {
      console.error(`[render:${name}]`, e);
      failures.push(`${name}: ${e.message}`);
    }
  }
  if (failures.length > 0) {
    document.body.insertAdjacentHTML("afterbegin",
      `<div style="background:#fee;padding:12px;color:#c00;font-size:0.85em;">` +
      `<strong>render warnings (${failures.length}):</strong> ` + failures.join(" / ") + `</div>`);
  }
})();
