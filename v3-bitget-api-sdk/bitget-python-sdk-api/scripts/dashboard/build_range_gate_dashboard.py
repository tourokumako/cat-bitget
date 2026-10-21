"""build_range_gate_dashboard.py — E37 レンジ判定計器の視認校正用データ＋拡大チャート生成（v17）

目的（improvement_plan.md 2026-07-05・まこさん GO）:
  E37 v10 のレンジ判定には「トレンド排除」が無く（通過率53.1%・ADX40+混入）トレンド中の上限ショートで
  轢かれていた（N11 方向ミス89%）。まこさんのレンジ定義＝「レジスタンス2〜3回タッチのゾーンの間を往復」で
  レンジを計器化し、ダッシュボード⑪タブ（粒度5分）で まこさんが目で校正する（probe でなく視認校正）。

  ★設計（2層・KB §2「上位足でレンジ局面を構築 → 5分足で執行」）:
   ① レンジ局面（1時間足）＝タッチ実績（≥ZONE_TOUCH回・fractal スイングを価格帯で束ね）のある
      レジスタンス／サポートゾーンが close の上下に揃い、その間にいる（往復可能な幅がある）＝レンジ。
      ★トレンド排除は「ゾーンが束なる/立つか」が担う（トレンド中はスイングが同価格帯に集まらず立たない）。
      → BBスクイーズ・傾きは撤廃（低ボラを要求せず、値幅のある往復レンジも取れる・まこさん 2026-2-15 指摘）。
   ② 5分足の即離脱ガード（本番の執行足）＝ゾーンをブレイク（上限上抜け/下限下抜け）or 急騰/急落（急変・緩やか
      トレンド）で即離脱。1時間足だけだと検知が最大1時間遅れ＝スキャルで轢かれる（まこさん 2025-12 指摘）。

  ⛔ 既存の手動レンジラベル（値動きが少ない定義・regime_ground_truth_daily_human.csv）は参考にしない。

入力: data/BTCUSDT-5m-2021-04-01_03-31_1826d_V9FULL_safe.csv（Binance spot 5m 正本・§8.2.1.1）
出力: dashboard/regime_prototype/predictions_v17_{1h,1d}.json / predictions_v17_5m/<月>.json / labels_v17.csv / index.json
      dashboard/regime_prototype/range_charts/range_v17_<月>.png（確認用）
確認: python3 scripts/dashboard/dashboard_server.py → ⑪ → v17 → 粒度5分 → 表示期間で月 → 日絞り
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402
import matplotlib.dates as mdates  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "priority_rebuild"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "regime"))
import structure_features as sf   # noqa: E402  fractal スイング検出（j+2 確定・leak-safe・v10 が使用）

CSV = REPO_ROOT / "data" / "BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv"  # 窓の組み替えで2026-06-30版へ（2026-07-23・既存期間は2026-05-31版と同一・06が追加されるだけ）
PROTO_DIR = REPO_ROOT / "dashboard" / "regime_prototype"
CHART_DIR = PROTO_DIR / "range_charts"
SM_DIR = PROTO_DIR / "predictions_v17_5m"
INDEX_JSON = PROTO_DIR / "index.json"
VERSION = "v17"

# ── ① レンジ局面（1時間足・S/Rゾーン主軸・a-priori・校正で調整・L-267）──
ZONE_LOOKBACK = 168    # ゾーン構築の窓（168時間=7日・上位足で主要ゾーンを構築）
ZONE_TOL = 0.003       # ゾーン束ね幅（0.3%・近いスイングを1つのゾーンに）
ZONE_TOUCH = 2         # タッチ回数（スイング数≥これ＝機能実績・まこさん「2回でもいい」）
ZONE_MIN_W = 0.004     # 上下ゾーン間の最低幅（0.4%・往復して手数料を超える幅）

# ── ② 5分足の即離脱ガード（本番の執行足）──
SPIKE5M_BARS = 3       # 急変本数（15分）
SPIKE5M_MAX = 0.010    # 急変閾値（15分で1%の急騰/急落は即離脱）
TREND5M_BARS = 12      # 短期トレンド本数（1時間）
TREND5M_MAX = 0.008    # 1時間の一方向の累積変化率（緩やかな上昇/下降トレンドの初動で離脱）

PLOT_START = "2024-06-01"
PLOT_END = "2026-06-01"   # 5分ビュー表示窓の上限（採点窓延長で2026-05まで表示・2026-07-15）


def _resample(df5: pd.DataFrame, rule: str, edge: str = "right") -> pd.DataFrame:
    """5分足を rule の足に束ねる。
    ★2026-10-20（工事 m2c15-band-s1-20261020・F-4・監査 CP60 の修正69・まこさん「すべて案どおりでよい」ok_d1_20261004 の③）
      edge="right"（既定・今のまま）＝label=right・closed=right。5分足の時刻はバーの始まりなので、1時間足は 10:05〜11:05 の足を束ねる。
      edge="hour"＝正時で区切る（10:00〜11:00＝始まりが 10:00〜10:55 の足）。束ねた値の時刻は、区切りの最後の5分足の始まり（10:55）に
      置く＝その足が閉じた 11:00 に1時間足が閉じる（未来を見ない・right と同じ「その行が閉じた時に確定済み」）。
      既定は今のままなので、RG-v5・labels_v17 の結果は変わらない。"""
    if edge == "right":
        o = df5["open"].resample(rule, label="right", closed="right").first()
        h = df5["high"].resample(rule, label="right", closed="right").max()
        l = df5["low"].resample(rule, label="right", closed="right").min()
        c = df5["close"].resample(rule, label="right", closed="right").last()
        v = df5["volume"].resample(rule, label="right", closed="right").sum()
        return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": v}).dropna(subset=["close"])
    if edge != "hour":
        raise ValueError(f"_resample の edge は right か hour（{edge}）")
    step = pd.Series(df5.index).diff().median()
    o = df5["open"].resample(rule, label="left", closed="left").first()
    h = df5["high"].resample(rule, label="left", closed="left").max()
    l = df5["low"].resample(rule, label="left", closed="left").min()
    c = df5["close"].resample(rule, label="left", closed="left").last()
    v = df5["volume"].resample(rule, label="left", closed="left").sum()
    out = pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": v}).dropna(subset=["close"])
    out.index = out.index + pd.Timedelta(rule) - step
    return out


def _zones_1h(df: pd.DataFrame) -> pd.DataFrame:
    """① レンジ局面（1時間足）＝タッチ実績のあるS/Rゾーンが close の上下に揃い、その間にいる。
    過去 ZONE_LOOKBACK 本の確定 fractal スイング（j+2 確定＝当該足まで・leak-safe）を価格帯 ZONE_TOL で束ね、
    タッチ（束ねたスイング数）≥ ZONE_TOUCH のゾーンを「機能しているレベル」とする。上下に揃い幅≥ZONE_MIN_W ならレンジ。"""
    is_res, is_sup, piv_h, piv_l = sf._detect_fractals(df)
    n = len(df)
    c = df["close"].to_numpy(float)
    is_res = np.asarray(is_res, bool); is_sup = np.asarray(is_sup, bool)
    piv_h = np.asarray(piv_h, float); piv_l = np.asarray(piv_l, float)
    res_idx = np.flatnonzero(is_res); res_px = piv_h[res_idx]
    sup_idx = np.flatnonzero(is_sup); sup_px = piv_l[sup_idx]
    r_lo = np.full(n, np.nan); r_hi = np.full(n, np.nan)
    s_lo = np.full(n, np.nan); s_hi = np.full(n, np.nan)
    ok = np.zeros(n, bool)

    def best_zone(px_arr, idx_arr, i, lo_w, price, above):
        j0 = int(np.searchsorted(idx_arr, lo_w)); j1 = int(np.searchsorted(idx_arr, i + 1))
        if j1 <= j0:
            return None
        px = px_arr[j0:j1]
        sel = (px > price) if above else (px < price)
        if not sel.any():
            return None
        px = np.sort(px[sel])
        clusters = []; s = 0
        for k in range(1, len(px) + 1):
            if k == len(px) or px[k] - px[k - 1] > px[k - 1] * ZONE_TOL:
                clusters.append(px[s:k]); s = k
        clusters.sort(key=lambda cl: abs(float(np.mean(cl)) - price))   # price に近いゾーンから
        for cpx in clusters:
            if len(cpx) >= ZONE_TOUCH:
                return float(cpx.min()) * (1 - ZONE_TOL / 2), float(cpx.max()) * (1 + ZONE_TOL / 2)
        return None

    start = max(ZONE_LOOKBACK, 25)
    for i in range(start, n):
        lo_w = i - ZONE_LOOKBACK + 1
        rz = best_zone(res_px, res_idx, i, lo_w, c[i], True)
        if rz is None:
            continue
        sz = best_zone(sup_px, sup_idx, i, lo_w, c[i], False)
        if sz is None:
            continue
        if (rz[0] - sz[1]) / c[i] < ZONE_MIN_W:
            continue
        r_lo[i], r_hi[i] = rz; s_lo[i], s_hi[i] = sz; ok[i] = True
    df = df.copy()
    df["res_lo"] = r_lo; df["res_hi"] = r_hi; df["sup_lo"] = s_lo; df["sup_hi"] = s_hi
    df["range_ok"] = ok
    return df


def _apply_5m_guard(df5: pd.DataFrame, df1h: pd.DataFrame) -> pd.DataFrame:
    """② 5分足の即離脱ガード＝直近確定の1時間ゾーン局面 ∩ 5分足でゾーンブレイク/急変していない。"""
    ok1h = df1h["range_ok"].reindex(df5.index, method="ffill").fillna(False).to_numpy(bool)
    res_hi = df1h["res_hi"].reindex(df5.index, method="ffill").to_numpy(float)
    sup_lo = df1h["sup_lo"].reindex(df5.index, method="ffill").to_numpy(float)
    c = df5["close"].to_numpy(float)
    brk = ((c > res_hi) | (c < sup_lo))                                  # 5分足でゾーン外れ（ブレイク＝離脱）
    brk = np.where(np.isfinite(res_hi) & np.isfinite(sup_lo), brk, False)
    # ★ゾーン主軸では離脱は「ゾーンブレイク」が担う。急変ガード(spike/trend)はゾーン内の往復で誤発火し
    #   細切れの原因になるため撤廃（トレンド/急騰は上限ゾーンを明確に上抜け＝brk で捉える）。
    df5 = df5.copy()
    df5["range_ok"] = ok1h & ~brk
    return df5


def _rows(df: pd.DataFrame) -> list:
    ts_ms = (df.index.astype("int64") // 10**6).tolist()
    close_int = df["close"].round().astype(int).tolist()
    labels = ["range" if x else "" for x in df["range_ok"].tolist()]
    return [[int(t), int(c), lab, ""] for t, c, lab in zip(ts_ms, close_int, labels)]


def _write_json(name: str, gran: str, rows: list) -> None:
    (PROTO_DIR / name).write_text(
        json.dumps({"version": VERSION, "granularity": gran, "rows": rows}, ensure_ascii=False),
        encoding="utf-8")
    print(f"    saved {name} ({len(rows):,} rows)")


def _plot_months(df5: pd.DataFrame) -> list:
    """5分足の価格ライン＋range_ok の連続区間を axvspan で塗った拡大チャート（月別・確認用）。"""
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    for old in CHART_DIR.glob("range_v17_*.png"):
        old.unlink()
    edges = pd.date_range(PLOT_START, PLOT_END, freq="MS")
    saved = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        sub = df5[(df5.index >= lo) & (df5.index < hi)]
        if len(sub) < 100:
            continue
        fig, ax = plt.subplots(figsize=(16, 5))
        ax.plot(sub.index, sub["close"], color="#222", linewidth=0.7, zorder=3)
        ok = sub["range_ok"].to_numpy(bool)
        idx = sub.index
        i = 0
        first = True
        while i < len(ok):
            if ok[i]:
                j = i
                while j + 1 < len(ok) and ok[j + 1]:
                    j += 1
                ax.axvspan(idx[i], idx[min(j + 1, len(idx) - 1)], color="#9e9e9e", alpha=0.35,
                           zorder=1, label=("range (zone)" if first else None))
                first = False
                i = j + 1
            else:
                i += 1
        ax.set_title(f"E37 range gate {VERSION}  {lo.strftime('%Y-%m')}  (5m grey=range zone)  "
                     f"range {ok.mean()*100:.0f}%", fontsize=11)
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
        ax.grid(True, alpha=0.2)
        ax.legend(loc="upper left", fontsize=9)
        fig.autofmt_xdate()
        fig.tight_layout()
        out = CHART_DIR / f"range_{VERSION}_{lo.strftime('%Y-%m')}.png"
        fig.savefig(out, dpi=110)
        plt.close(fig)
        saved.append(out)
    print(f"    月別チャート {len(saved)} 枚（{PLOT_START[:7]}〜・5分足）")
    return saved


def main() -> int:
    if not CSV.exists():
        sys.exit(f"ABORT: missing input CSV: {CSV}")
    if not INDEX_JSON.exists():
        sys.exit(f"ABORT: missing index.json: {INDEX_JSON}")

    print(f"[1/6] loading 5m CSV: {CSV.name}")
    df5 = pd.read_csv(CSV)
    df5["ts"] = pd.to_datetime(df5["timestamp"])
    df5 = df5.set_index("ts").sort_index()
    print(f"    5m rows: {len(df5):,} / {df5.index[0].date()}〜{df5.index[-1].date()}")

    print(f"[2/6] ① 1時間 S/Rゾーン局面（タッチ≥{ZONE_TOUCH}の上下ゾーン間）...")
    df1h = _zones_1h(_resample(df5, "1h"))
    n1 = len(df1h); ok1 = int(df1h["range_ok"].sum())
    print(f"    1h: {n1:,}本 / range局面(ゾーン間) {ok1:,}（{ok1/n1*100:.1f}%）")

    print(f"[3/6] ② 5分足 即離脱ガード（ゾーン局面 ∩ ゾーンブレイク/急変なし）...")
    df5g = _apply_5m_guard(df5, df1h)
    n5 = len(df5g); ok5 = int(df5g["range_ok"].sum())
    print(f"    5m: {n5:,}本 / range(執行) {ok5:,}（{ok5/n5*100:.1f}%）")

    print(f"[4/6] writing JSON (1h局面 + 1d + 5m月別=執行) ...")
    PROTO_DIR.mkdir(parents=True, exist_ok=True)
    _write_json(f"predictions_{VERSION}_1h.json", "1h", _rows(df1h))
    day = pd.DataFrame({"close": df5g["close"].values, "ok": df5g["range_ok"].astype(int).values,
                        "date": df5g.index.normalize()}, index=df5g.index)
    dd = day.groupby("date").agg(close=("close", "last"), ok=("ok", "mean"))
    ts_ms_d = (dd.index.astype("int64") // 10**6).tolist()
    rows_1d = [[int(t), int(round(c)), ("range" if o >= 0.5 else ""), ""]
               for t, c, o in zip(ts_ms_d, dd["close"].tolist(), dd["ok"].tolist())]
    _write_json(f"predictions_{VERSION}_1d.json", "1d", rows_1d)
    (PROTO_DIR / f"predictions_{VERSION}_4h.json").unlink(missing_ok=True)
    SM_DIR.mkdir(parents=True, exist_ok=True)
    for old in SM_DIR.glob("*.json"):
        old.unlink()
    edges = pd.date_range(PLOT_START, PLOT_END, freq="MS")
    n_sm = 0
    for lo, hi in zip(edges[:-1], edges[1:]):
        sub = df5g[(df5g.index >= lo) & (df5g.index < hi)]
        if len(sub) < 100:
            continue
        (SM_DIR / f"{lo.strftime('%Y-%m')}.json").write_text(
            json.dumps({"version": VERSION, "granularity": "5m", "rows": _rows(sub)}, ensure_ascii=False),
            encoding="utf-8")
        n_sm += 1
    print(f"    saved 5m 月別 {n_sm} ファイル → predictions_{VERSION}_5m/")
    pd.DataFrame({"datetime_utc": df1h.index, "close": df1h["close"].round(1),
                  "res_lo": df1h["res_lo"].round(1), "res_hi": df1h["res_hi"].round(1),
                  "sup_lo": df1h["sup_lo"].round(1), "sup_hi": df1h["sup_hi"].round(1),
                  "range_ok": df1h["range_ok"].astype(int)}).to_csv(PROTO_DIR / f"labels_{VERSION}.csv", index=False)

    print(f"[5/6] rendering 拡大チャート (5分足・月別・確認用) ...")
    charts = _plot_months(df5g)

    print(f"[6/6] updating index.json with {VERSION} ...")
    distribution = {"range": {"count": ok5, "pct": round(ok5 / n5 * 100, 2)},
                    "non_range": {"count": n5 - ok5, "pct": round((n5 - ok5) / n5 * 100, 2)}}
    index_obj = json.loads(INDEX_JSON.read_text(encoding="utf-8"))
    index_obj["prototypes"] = [p for p in index_obj["prototypes"] if p.get("version") != VERSION]
    index_obj["prototypes"].append({
        "version": VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "spec": {
            "method": "E37 range gate v2 = ①1h S/Rゾーン間(タッチ≥2) ②5m ゾーンブレイク/急変ガード",
            "purpose": "E37 レンジ判定の視認校正（まこさんのレンジ定義=S/Rゾーン往復・improvement_plan 2026-07-05）",
            "layer1_zone_1h": {"lookback_h": ZONE_LOOKBACK, "tol_pct": ZONE_TOL, "touch_min": ZONE_TOUCH,
                               "min_width_pct": ZONE_MIN_W, "note": "トレンド排除はゾーンが立つか否かが担う（BBスクイーズ撤廃）"},
            "layer2_5m_guard": {"break": "close が上限ゾーン上抜け/下限ゾーン下抜け",
                                "spike5m_bars": SPIKE5M_BARS, "spike5m_max_pct": SPIKE5M_MAX,
                                "trend5m_bars": TREND5M_BARS, "trend5m_max_pct": TREND5M_MAX},
            "view": "ダッシュボードは 粒度5分 → 表示期間で月 → 日絞りで拡大",
            "output_granularity": "5m(exec)/1h(zone)",
        },
        "distribution": distribution,
    })
    # available_months（⑪ 月プルダウンの源＝app.js rp-month が読む）＝データの実期間から自動生成。
    # 誰も保守しない静的リストを廃し、期間を延ばすと末尾が自動追従（手当て漏れ防止・2026-07-15 まこさん指示）。
    index_obj["available_months"] = (
        pd.period_range(df5.index.min(), df5.index.max(), freq="M").strftime("%Y-%m").tolist())
    INDEX_JSON.write_text(json.dumps(index_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"    index.json: {VERSION} appended（5m range {distribution['range']['pct']}%）"
          f" / available_months {index_obj['available_months'][0]}〜{index_obj['available_months'][-1]}")

    print(f"\n[DONE] ダッシュボード → python3 scripts/dashboard/dashboard_server.py → ⑪ → {VERSION} → 粒度5分 → 月 → 日絞り")
    print(f"       確認用PNG {len(charts)}枚（5分足）→ dashboard/regime_prototype/range_charts/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
