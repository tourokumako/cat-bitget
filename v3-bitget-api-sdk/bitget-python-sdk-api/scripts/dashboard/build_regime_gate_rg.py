"""build_regime_gate_rg.py — レンジ・レジーム判定 RG 系列（RG-v1）＝仕様自動生成つきの正本計器

背景（まこさん指示 2026-07-12）:
  ダッシュボード v12 は ①まこさんの手動4hラベルを直接教師にしていた（2026-07-03 確定方針
  「手動ラベルを教師に使わない」に違反） ②表示が最大4hの未来値を含む ③判定粒度が4h＝5分足に未対応。
  → レンジのレジーム判定を RG 系列として組み直す。今回の混乱（仕様が手書き・散在で誤解）を防ぐため、
  **仕様ロジックは report §0「使用パラメータ」と同等の内容を実行時の実値から自動生成**し、
  ダッシュボードの仕様欄に表示する（手書き禁止＝必須項目を削ると SystemExit のスキーマ強制つき）。

RG-v1 のロジック＝v17 計器（build_range_gate_dashboard.py・まこさん視認校正済み 2026-07-05）と同一。
  実装は import 再利用（コピーしない＝ロジックの正本は1箇所）。同一であることを labels_v17.csv との
  全期間一致 selftest で毎回機械照合する（E37 の --v11-selftest-zones と同じ方式）。
  ⛔ 教師なし＝幾何ルールのみ。手動レジームラベル（regime_samples_4h*.csv /
     regime_ground_truth_daily_human.csv）は一切読まない。

実行:  python3 scripts/dashboard/build_regime_gate_rg.py
出力:  dashboard/regime_prototype/predictions_rg-v1_{1h,1d}.json / predictions_rg-v1_5m/<月>.json /
       labels_rg-v1.csv / index.json（spec 自動生成・rg-v1 エントリ）
確認:  python3 scripts/dashboard/dashboard_server.py → ⑪ → rg-v1 → 粒度5分 → 月 → 日絞り
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_range_gate_dashboard as v17   # noqa: E402  ロジックの正本（視認校正済み）＝import 再利用・コピー禁止

REPO_ROOT = Path(__file__).resolve().parents[2]
PROTO_DIR = REPO_ROOT / "dashboard" / "regime_prototype"
INDEX_JSON = PROTO_DIR / "index.json"
VERSION = "rg-v1"                          # RG 系列＝戦略の vN（E37 v18/v19…）と衝突しない別名前空間（L-333 混乱対策）
SM_DIR = PROTO_DIR / f"predictions_{VERSION}_5m"

# ── 仕様スキーマ（必須項目を削ると SystemExit＝report §0 と同型の物理強制）──
RG_SPEC_SCHEMA = ("入力データ", "教師", "判定ロジック", "パラメータ（出所つき）", "因果性（未来値ゼロ）",
                  "出力粒度", "selftest", "生成方式")


def _assert_spec_schema(spec: dict) -> None:
    """仕様の必須項目スキーマ検査。欠けたら SystemExit（項目削除・手書き固定文字列化を物理的に禁止）。"""
    for key in RG_SPEC_SCHEMA:
        if key not in spec or not str(spec[key]).strip():
            raise SystemExit(f"[RG 仕様スキーマ強制] 必須項目欠落: {key}（仕様は実値から自動生成・削れない・まこさん 2026-07-12）")


def _selftest_vs_v17(df1h: pd.DataFrame) -> str:
    """RG-v1 の 1h ゾーン出力が視認校正済み labels_v17.csv と全期間一致するか機械照合（ロジック同一の証明）。"""
    lab_path = PROTO_DIR / "labels_v17.csv"
    if not lab_path.exists():
        raise SystemExit(f"ABORT: labels_v17.csv がありません: {lab_path}")
    lab = pd.read_csv(lab_path, parse_dates=["datetime_utc"]).set_index("datetime_utc").sort_index()
    j = df1h.join(lab, how="inner", rsuffix="_lab")
    assert len(j) > 0, "labels_v17.csv と 1h index が重ならない（入力 CSV が違う疑い）"
    ok_mis = int((j["range_ok"].astype(int) != j["range_ok_lab"].astype(int)).sum())
    px_mis = 0
    for col in ("res_lo", "res_hi", "sup_lo", "sup_hi"):
        a = j[col].round(1); b = j[f"{col}_lab"]
        both = a.notna() & b.notna()
        px_mis += int(((a[both] - b[both]).abs() > 0.1).sum())
        px_mis += int((a.isna() != b.isna()).sum())
    assert ok_mis == 0 and px_mis == 0, f"RG-v1 が labels_v17 と不一致（range_ok {ok_mis} / ゾーン価格 {px_mis}）＝移植ミス"
    msg = f"labels_v17.csv と全期間一致（1h {len(j):,}本・range_ok 不一致0・ゾーン価格 不一致0）＝視認校正済み計器と同一ロジックの機械証明"
    print(f"    [selftest] ✅ {msg}")
    return msg


def main() -> int:
    csv_path = v17.CSV
    if not csv_path.exists():
        sys.exit(f"ABORT: missing input CSV: {csv_path}")
    if not INDEX_JSON.exists():
        sys.exit(f"ABORT: missing index.json: {INDEX_JSON}")

    print(f"[1/6] loading 5m CSV: {csv_path.name}")
    md5_head = hashlib.md5(csv_path.read_bytes()).hexdigest()[:12]
    df5 = pd.read_csv(csv_path)
    df5["ts"] = pd.to_datetime(df5["timestamp"])
    df5 = df5.set_index("ts").sort_index()
    print(f"    5m rows: {len(df5):,} / {df5.index[0].date()}〜{df5.index[-1].date()} / md5 {md5_head}")

    print(f"[2/6] ① 1時間 S/Rゾーン局面（v17 ロジック import 再利用）...")
    df1h = v17._zones_1h(v17._resample(df5, "1h"))
    n1 = len(df1h); ok1 = int(df1h["range_ok"].sum())
    print(f"    1h: {n1:,}本 / range局面 {ok1:,}（{ok1/n1*100:.1f}%）")

    print(f"[3/6] ② 5分足 即離脱ガード ＋ selftest（labels_v17 全期間一致）...")
    df5g = v17._apply_5m_guard(df5, df1h)
    n5 = len(df5g); ok5 = int(df5g["range_ok"].sum())
    print(f"    5m: {n5:,}本 / range(執行) {ok5:,}（{ok5/n5*100:.1f}%）")
    selftest_msg = _selftest_vs_v17(df1h)

    print(f"[4/6] writing JSON（1h + 1d + 5m月別）...")
    SM_DIR.mkdir(parents=True, exist_ok=True)
    for old in SM_DIR.glob("*.json"):
        old.unlink()
    (PROTO_DIR / f"predictions_{VERSION}_1h.json").write_text(
        json.dumps({"version": VERSION, "granularity": "1h", "rows": v17._rows(df1h)}, ensure_ascii=False), encoding="utf-8")
    day = pd.DataFrame({"close": df5g["close"].values, "ok": df5g["range_ok"].astype(int).values,
                        "date": df5g.index.normalize()}, index=df5g.index)
    dd = day.groupby("date").agg(close=("close", "last"), ok=("ok", "mean"))
    ts_ms_d = (dd.index.astype("int64") // 10**6).tolist()
    rows_1d = [[int(t), int(round(c)), ("range" if o >= 0.5 else ""), ""]
               for t, c, o in zip(ts_ms_d, dd["close"].tolist(), dd["ok"].tolist())]
    (PROTO_DIR / f"predictions_{VERSION}_1d.json").write_text(
        json.dumps({"version": VERSION, "granularity": "1d", "rows": rows_1d}, ensure_ascii=False), encoding="utf-8")
    edges = pd.date_range(v17.PLOT_START, v17.PLOT_END, freq="MS")
    n_sm = 0
    for lo, hi in zip(edges[:-1], edges[1:]):
        sub = df5g[(df5g.index >= lo) & (df5g.index < hi)]
        if len(sub) < 100:
            continue
        (SM_DIR / f"{lo.strftime('%Y-%m')}.json").write_text(
            json.dumps({"version": VERSION, "granularity": "5m", "rows": v17._rows(sub)}, ensure_ascii=False), encoding="utf-8")
        n_sm += 1
    print(f"    saved 1h/1d ＋ 5m 月別 {n_sm} ファイル → predictions_{VERSION}_5m/")
    pd.DataFrame({"datetime_utc": df1h.index, "close": df1h["close"].round(1),
                  "res_lo": df1h["res_lo"].round(1), "res_hi": df1h["res_hi"].round(1),
                  "sup_lo": df1h["sup_lo"].round(1), "sup_hi": df1h["sup_hi"].round(1),
                  "range_ok": df1h["range_ok"].astype(int)}).to_csv(PROTO_DIR / f"labels_{VERSION}.csv", index=False)
    print(f"    saved labels_{VERSION}.csv（E37 移植時の一致照合の正本）")

    print(f"[5/6] 仕様の自動生成（実値由来・スキーマ強制）...")
    # ★report §0 と同等: 使用データ・教師・ロジックの流れ・全パラメータと出所・因果性・粒度・selftest・生成方式
    #   全て実行時の実値・import した定数から組み立てる（手書き固定文字列の腐りを構造的に防ぐ）。
    spec = {
        "入力データ": (f"{csv_path.name}（5分足 {len(df5):,}本 {df5.index[0].date()}〜{df5.index[-1].date()}・"
                   f"md5 {md5_head}・Binance spot 正本 §8.2.1.1）"),
        "教師": "なし＝幾何ルールのみ（手動レジームラベル regime_samples_4h*.csv / daily_human は一切不読・2026-07-03 方針）",
        "判定ロジック": (f"①1時間足: 確定 fractal スイング（j+2 確定）を過去{v17.ZONE_LOOKBACK}h窓・価格帯{v17.ZONE_TOL*100:.1f}%で束ね、"
                    f"スイング数≥{v17.ZONE_TOUCH}のS/Rゾーンが close の上下に揃い幅≥{v17.ZONE_MIN_W*100:.1f}%＝レンジ局面 "
                    f"②5分足: close がゾーン外（上限上抜け/下限下抜け）＝即離脱。トレンド排除は「ゾーンが立つか否か」が担う"),
        "パラメータ（出所つき）": (f"ZONE_LOOKBACK={v17.ZONE_LOOKBACK}h / ZONE_TOL={v17.ZONE_TOL} / ZONE_TOUCH={v17.ZONE_TOUCH} / "
                         f"ZONE_MIN_W={v17.ZONE_MIN_W}〔全て視認校正（まこさん 2026-07-05 概ね良い）＝v17 と同一値・スイープしない L-267〕"),
        "因果性（未来値ゼロ）": ("1hバーは確定時刻ラベル（label=right/closed=right）＝確定した1hゾーンのみを5分足へ前向き適用（ffill）。"
                        "5分バー i の判定はバー i の確定値まで使用＝売買に使う時の執行はバー i+1 から（v12 の「バー開始から塗る最大4h後出し」を排除）"),
        "出力粒度": "5m（執行・月別）/ 1h（ゾーン局面）/ 1d（俯瞰・日内 range 率≥50%）",
        "selftest": selftest_msg,
        "生成方式": (f"scripts/dashboard/build_regime_gate_rg.py がロジックを build_range_gate_dashboard.py（v17 正本）から import 再利用し、"
                 f"本仕様を実行時の実値から自動生成（必須{len(RG_SPEC_SCHEMA)}項目のスキーマ検査つき＝削ると生成停止）"),
    }
    _assert_spec_schema(spec)
    print(f"    仕様 {len(spec)} 項目 生成・スキーマ検査 ✅")

    print(f"[6/6] updating index.json with {VERSION} ...")
    distribution = {"range": {"count": ok5, "pct": round(ok5 / n5 * 100, 2)},
                    "non_range": {"count": n5 - ok5, "pct": round((n5 - ok5) / n5 * 100, 2)}}
    index_obj = json.loads(INDEX_JSON.read_text(encoding="utf-8"))
    index_obj["prototypes"] = [p for p in index_obj["prototypes"] if p.get("version") != VERSION]
    index_obj["prototypes"].append({
        "version": VERSION,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "spec": spec,
        "distribution": distribution,
    })
    INDEX_JSON.write_text(json.dumps(index_obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"    index.json: {VERSION} 登録（5m range {distribution['range']['pct']}%）")

    print(f"\n[DONE] ダッシュボード → python3 scripts/dashboard/dashboard_server.py → ⑪ → {VERSION} → 粒度5分 → 月 → 日絞り")
    return 0


if __name__ == "__main__":
    sys.exit(main())
