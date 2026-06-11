#!/usr/bin/env python3
"""precheck.py — 採点前ゲート（手数料負け・環境ドリフトの事前検査・PASS しないと score.py が走らない）

なぜあるか（2026-06-12 まこさん命令「手数料負けするような設計を事前に止めろ・すべての抜け穴を塞げ」）:
  E21 は学習期間 +79% を見て採点に進み −$1,288 で破棄 = 採点 1 回を浪費した。だが失格サインは
  採点前に学習期間のデータだけで出せた:
    ① 追加した玉の平均 gross $1.14 < 往復コスト $2.08（breakeven 0.55）= 勝率に関係なく手数料負け確定
    ② 型バーの ATR%<0.15 帯が学習 35% → 採点候補 61%（ドリフト 26pt）= 学習成績が当てにならない
  L-40（TP_PCT 提案前の手数料計算義務）を TP 以外の全出口・入口選別の変更にも拡張し、hook で物理強制する。

使い方:
  python3 precheck.py <学習期間トレードCSV> [--vs <ベースライン学習期間CSV>] [--target <採点候補CSV>]
                      [--authorize <採点CSV名>] [--already-scored]

  --vs        : ベースライン（地面）の学習期間トレード。限界分解（追加/削った玉の breakeven）を出す
  --target    : 採点期間の候補CSV。**特徴量列だけ**読む（PnL 列は読み込み時に物理 drop・答え見ない）
  --authorize : PASS 時に許可マーカーを書く採点CSV名（既定 = 学習CSV名から _train を除いた名前）
  --already-scored : 既採点アーティファクトの再採点・レポート再生成用（検査は表示・マーカーは無条件）

判定（機械的・固定ゲート値はチューニング対象でない）:
  FAIL = ①全体または追加玉の breakeven < 1.0（≥50件）= 手数料負け確定
         ②利益確定系出口（TP/トレール）の breakeven < 1.0（≥30件）
         ③ドリフト最大帯シフト ≥ 20pt（E21 実測 26pt がこれで止まる）
  WARN = breakeven 1.0〜1.5（危険域）／ドリフト 10〜20pt
  PASS → .claude/state/precheck_pass_<採点CSV名> を書く（hook require_precheck_before_score.sh が照合）
  FAIL → マーカーなし・exit 1（= score.py 実行が hook でブロックされたまま）
"""
from __future__ import annotations
import argparse, os, sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import report                                     # _judge_cols（審判式コスト・正本1箇所）
import eval_engine as ee

STATE_DIR = Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state")
PROFIT_EXITS = {"TP_FILLED", "TRAIL_EXIT"}        # 利益確定系（breakeven<1 を FAIL にする出口）
PNL_COLS = ["gross_usd", "fee_usd", "net_usd", "mfe_usd", "mae_usd", "tp_diff_usd", "exit_price", "hold_min"]
BANDS = {  # ドリフト検査の帯（report.py G 節と同一）
    "ATR%":   ("atr_pct",      [0, 0.15, 0.2, 0.3, 0.4, 9e9]),
    "ADX":    ("adx_at_entry", [0, 20, 25, 30, 40, 9e9]),
    "bb傾き":  ("bb_mid_slope_at_entry", [-9e9, -30, -10, 0, 9e9]),
}


def _roundtrip_cost(t):
    """審判式の 1 件あたり往復コスト（手数料+slip・_judge_cols 通過後の列を使う）。"""
    return t["_fee"] + t["_slip"]


def _breakeven(t, label, min_n, fails, warns, fail_below=1.0):
    """集団の breakeven 倍率 = 平均gross ÷ 往復コスト/件。<1 は勝率に関係なく手数料負け確定。"""
    n = len(t)
    if n == 0:
        print(f"   {label}: 0件（検査対象なし）")
        return
    g, c = t["_gross"].mean(), _roundtrip_cost(t).mean()
    be = g / c if c > 0 else float("inf")
    mark = ""
    if n >= min_n:
        if be < fail_below:
            fails.append(f"{label} breakeven {be:.2f} < 1.0（平均gross ${g:.2f} < 往復コスト ${c:.2f}・手数料負け確定）")
            mark = " ❌FAIL"
        elif be < 1.5:
            warns.append(f"{label} breakeven {be:.2f}（1.5未満の危険域）")
            mark = " ⚠️WARN"
    print(f"   {label}: {n}件 / 平均gross ${g:.2f} / 往復コスト ${c:.2f}/件 / breakeven {be:.2f}{mark}")


def _band_share(d, col, edges):
    s = pd.cut(d[col], bins=edges, right=False)
    return s.value_counts(normalize=True).sort_index() * 100


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("train_csv")
    ap.add_argument("--vs", help="ベースライン学習期間CSV（限界分解）")
    ap.add_argument("--target", help="採点候補CSV（特徴量のみ・PnL列は物理drop）")
    ap.add_argument("--authorize", help="許可マーカーを書く採点CSV名")
    ap.add_argument("--already-scored", action="store_true")
    a = ap.parse_args()

    d = pd.read_csv(a.train_csv)
    d["entry_time"] = pd.to_datetime(d["entry_time"])
    d = report._judge_cols(d)
    d["atr_pct"] = d["atr_14"] / d["entry_price"] * 100
    name = Path(a.train_csv).name
    auth = a.authorize or name.replace("_train", "")
    out_path = Path(a.train_csv).with_name(f"precheck_{Path(a.train_csv).stem}.txt")
    _rf = open(out_path, "w", encoding="utf-8")
    sys.stdout = report._Tee(sys.__stdout__, _rf)

    fails, warns = [], []
    print("=" * 70)
    print(f"  採点前ゲート: {name}   期間 {d['entry_time'].min().date()}〜{d['entry_time'].max().date()}")
    print("=" * 70)

    # ===== P0. 実験条件一覧（まこさん30秒チェック用・テスト前に全条件を見える化）=====
    print("\n  P0. 実験条件一覧")
    print(f"   件数 {len(d)} / priority {sorted(d['priority'].unique())} / side {sorted(d['side'].unique())}")
    print(f"   size分布 {dict(d['size_btc'].round(3).value_counts())} / add最大 {int(d['add_count'].max())}")
    print(f"   出口構成: " + " / ".join(f"{k} {v}件" for k, v in d["exit_reason"].value_counts().items()))
    print(f"   コスト定数(審判): MAKER {ee.MAKER_FEE} / TAKER {ee.TAKER_FEE} / SLIP {ee.SLIPPAGE}")

    # ===== P1. 出口別コスト整合（L-40 を全出口に拡張）=====
    print("\n  P1. 出口別コスト整合（利益確定系の breakeven<1.0 は FAIL・損切り系は表示のみ）")
    for er, t in d.groupby("exit_reason"):
        if er in PROFIT_EXITS:
            _breakeven(t, f"[{er}]", min_n=30, fails=fails, warns=warns)
        else:
            g, c = t["_gross"].mean(), _roundtrip_cost(t).mean()
            print(f"   [{er}]: {len(t)}件 / 平均gross ${g:.2f} / 往復コスト ${c:.2f}/件（損切り/防御系・参考表示）")

    # ===== P2. 全体・限界分解 breakeven（E21 の致命傷 0.55 を採点前に出す）=====
    print("\n  P2. 全体・限界分解 breakeven")
    _breakeven(d, "全体", min_n=50, fails=fails, warns=warns)
    if a.vs:
        v = pd.read_csv(a.vs)
        v["entry_time"] = pd.to_datetime(v["entry_time"])
        v = report._judge_cols(v)
        key = lambda t: set(zip(t["entry_time"], t["side"]))
        kd, kv = key(d), key(v)
        added = d[[(e, s) in (kd - kv) for e, s in zip(d["entry_time"], d["side"])]]
        removed = v[[(e, s) in (kv - kd) for e, s in zip(v["entry_time"], v["side"])]]
        _breakeven(added, "追加した玉(vs ベースライン)", min_n=50, fails=fails, warns=warns)
        _breakeven(removed, "削った玉(参考)", min_n=10**9, fails=fails, warns=warns)  # 表示のみ

    # ===== P3. 分布ドリフト（学習 vs 採点候補・特徴量のみ・答えは見ない）=====
    if a.target:
        tgt = pd.read_csv(a.target)
        tgt = tgt.drop(columns=[c for c in PNL_COLS if c in tgt.columns])  # PnL 列を物理 drop（類型C防止）
        tgt["atr_pct"] = tgt["atr_14"] / tgt["entry_price"] * 100
        print(f"\n  P3. 分布ドリフト 学習 vs 採点候補（{Path(a.target).name}・特徴量のみ読込・PnL列drop済）")
        worst = 0.0
        for label, (col, edges) in BANDS.items():
            if col not in tgt.columns:
                continue
            tr, te = _band_share(d, col, edges), _band_share(tgt, col, edges)
            diff = (te - tr).abs().max()
            worst = max(worst, diff)
            tab = pd.DataFrame({"学習%": tr.round(1), "採点候補%": te.round(1), "差pt": (te - tr).round(1)})
            print(f"   [{label}] 最大シフト {diff:.1f}pt")
            print("   " + tab.to_string().replace("\n", "\n   "))
        if worst >= 20:
            fails.append(f"ドリフト最大 {worst:.1f}pt ≥ 20pt（学習と採点で環境が別物・学習成績は当てにならない）")
        elif worst >= 10:
            warns.append(f"ドリフト最大 {worst:.1f}pt（10pt超・月別の頑健性を学習期間内で確認してから）")

    # ===== 判定 =====
    print("\n  判定:")
    for w in warns:
        print(f"   ⚠️ WARN: {w}")
    for f in fails:
        print(f"   ❌ FAIL: {f}")
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    marker = STATE_DIR / f"precheck_pass_{auth}"
    if fails and not a.already_scored:
        print(f"   → 不合格。採点（score.py）に進めない（マーカー {marker.name} を書かない）。")
        print("     手数料の壁/環境ドリフトを設計で解消してから再検査する。採点1回をここで温存した。")
        sys.exit(1)
    note = "grandfathered(既採点)" if (fails and a.already_scored) else "PASS"
    marker.write_text(f"{note} {name} -> {auth}\n")
    print(f"   → {note}。マーカー {marker.name} 作成（score.py 実行可）。")


if __name__ == "__main__":
    main()
