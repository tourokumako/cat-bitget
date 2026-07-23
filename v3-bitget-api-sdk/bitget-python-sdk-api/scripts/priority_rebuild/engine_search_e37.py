#!/usr/bin/env python3
"""engine_search_e37.py — 層3エンジン内探索（まこさん GO 2026-07-21・段階B）

疑似シミュを介さず、試行ごとに実エンジン（e37_scalp.run_e37）を回し、審判式 net（score.score・import のみ・H13）で
候補を評価する Optuna 探索。再回転・手数料・約定が全部本物の計算で入る＝L-330 の穴が無い。

- 探索窓＝2024-04-01〜2024-07-31（まこさん決定 2026-07-24「2024-04〜07 にする」＝下の
  SEARCH_START/SEARCH_END が実体。選定方法＝値動きの構造特徴15次元による類似窓抽出＝成績を使わない・
  方法と全順位の正本は .claude/ratchet/window_similarity_ranking.md。選定履歴は SEARCH_START 上のコメント）。
  採点窓 2026-03-01〜2026-06-30（periods.py）と重ならない＝采否の窓の汚染ゼロ。
- 探索対象＝v59 の枝のツマミ（型別のシグナル種・閾値・切る%・待ち・窓・切り方 close/stop）。
  値の差し替えは e37_scalp のモジュール定数 setattr（エンジン本体は無変更・既定値は v59_157 と同一）。
- 試行は CSV を書かない（run_e37 return_trades=True）。全試行のログを残す。
- 最終候補は1つだけ選び、正式にタグ連番の本走→採点窓 score.py→report/analyze 型別4分割で、采否はまこさんが判断。
  採点窓で確認する候補を1つに絞るのは、采否の窓を何度も覗かないため。
- 命名: e3N_ 接頭辞を避けた（実験ではなく選定装置＝売買記録CSVを出さない。score.score を呼ぶ＝pdca_mark の
  審判検知への登録は hook 復帰時にまこさん承認で・pdca_flow §5）。
"""
import argparse
import contextlib
import io
import sys
import time

import numpy as np
import pandas as pd

import e37_scalp as e37
import score as judge          # 審判＝import のみ・無変更（H13）

# 探索窓（まこさん決定 2026-07-24「2024-04〜07 にする」＝値動きの構造特徴15次元による類似窓抽出の2位・
# バランス型［15特徴中13が z差±0.8 以内・極端イベントなし］・方法と全順位の正本＝
# .claude/ratchet/window_similarity_ranking.md。1位 2025-09〜12 は5分リターン尖度の生値が基準の約8倍＝
# 2025-10 急落イベント含みで急騰切りツマミが過適合する懸念から不採用）。
# 選定履歴: 2022-07〜12［成績の近さ1位・2026-07-21］→ v59c_162 実測で反転し廃止（構造では29位相当＝
# 「成績は近いが構造が遠い」）→ 2025-12〜2026-02［walk-forward 形・2026-07-23］→ 構造類似の実測で
# 2024-04〜07 へ（2026-07-24）。periods.py の採点窓 2026-03〜06 とは非重複＝
# 採点窓 SCORE_START/SCORE_END には触れない（採否は最終本走の score.py が periods 正本で行う・汚染ゼロ）。
SEARCH_START = pd.Timestamp("2024-04-01")
SEARCH_END   = pd.Timestamp("2024-08-01")            # 2024-07-31 まで（終端は排他）
WARM_START   = SEARCH_START - pd.Timedelta(days=60)  # 助走60日（e37._load と同じ考え方）

# 土台 longfu_145 の構成（report_trades_e37_range_scalp_longfu_145_score.txt §0 実行引数と同一）＋ v59 ON
BASE_KW = dict(
    v11=True, v12_open_range=True, v13_time_maker=True, v18_tp2_far=True, v20_rg5=True,
    v22_set=True, v24_trend_maker_tp=True, v25_adaptive_band=True,
    v26_down_hours=1.0, v26_gap=0.5, v26_max_age_hours=6.0, v26_split_ceiling=True,
    v27_flatup_lock=True, v31_time_be=True, v35_flatup_range=True, v36_flatup_near=True,
    v37_flatup_climb=True, v38_flatup_clamp=True, v40_down_no_age=True,
    v47_mtf_cut=True, v48_stale_wait=True, v50_trend_wait=True, v53_flatup_fast_cut=True,
    v56_rearm_delay=True, v57_long_support=True, v57_long_flat_up_only=True,
)

# 探索するツマミ（v59 のモジュール定数名 → Optuna の提案）。範囲は分布の裾を広めに覆う固定幅＝
# 特定の net で選んだ範囲ではない（Optuna が範囲内を絞る・L-267 の禁止は採点窓 net を目的関数にした選定）。
# 2026-07-23 まこさんGO（切る系2周目）: シグナル種に di14/kijun26 を追加・待ち 45/60・down 判定窓を追加。
# kijun26 は%スケール（adx/di の 10〜70 と桁が違う）＝閾値レンジは探索窓の分布分位から実行時に決める（CC の手打ち値なし）。
_KIJ_TH_RANGE = None   # (lo, hi) = 探索窓 kijun26 乖離%の (q50, q99.5)。main() が実行時に設定・印字。

_V59_SIGS = ["adx7", "di7", "di14", "kijun26"]


def _kij_range(df):
    kij = (df["high"].rolling(26).max() + df["low"].rolling(26).min()) / 2.0
    dev = ((df["close"] / kij) - 1.0) * 100.0
    return float(dev.quantile(0.50)), float(dev.quantile(0.995))


def _suggest(t):
    ov = {}
    ds = t.suggest_categorical("down_sig", _V59_SIGS)
    ov["V59_DOWN_SIG"] = ds
    ov["V59_DOWN_ADX7_TH"] = (t.suggest_float("down_th_kij", *_KIJ_TH_RANGE) if ds == "kijun26"
                              else t.suggest_float("down_th", 10.0, 70.0))
    ov["V59_DOWN_ADV_PCT"] = t.suggest_float("down_adv", 0.1, 1.0)
    ov["V59_DOWN_WIN_MIN"] = t.suggest_categorical("down_win", [0, 120, 180, 240, 360])
    fs = t.suggest_categorical("flat_sig", _V59_SIGS)
    ov["V59_FLAT_SIG"] = fs
    ov["V59_FLAT_DID7_TH"] = (t.suggest_float("flat_th_kij", *_KIJ_TH_RANGE) if fs == "kijun26"
                              else t.suggest_float("flat_th", 10.0, 70.0))
    ov["V59_FLAT_ADV_PCT"] = t.suggest_float("flat_adv", 0.1, 1.0)
    ov["V59_WAIT_MIN"] = t.suggest_categorical("wait", [0, 5, 10, 15, 20, 30, 45, 60])
    ov["V59_FLAT_WIN_MIN"] = t.suggest_categorical("flat_win", [60, 120, 240, 360])
    ov["V59_CUT_MODE"] = t.suggest_categorical("cut_mode", ["close", "stop"])
    return ov


def _run_engine(df, overrides: dict, v59_on: bool):
    """1試行＝実エンジンを回して探索窓の審判値を返す（CSV を書かない・print は握らず呼び出し側でログへ）。"""
    saved = {k: getattr(e37, k) for k in overrides}
    for k, v in overrides.items():
        setattr(e37, k, v)
    try:
        t = e37.run_e37(df.copy(), "5m", tag=None, v59_adx_cut=v59_on, return_trades=True, **BASE_KW)
    finally:
        for k, v in saved.items():
            setattr(e37, k, v)
    t = t[(pd.to_datetime(t["entry_time"]) >= SEARCH_START)
          & (pd.to_datetime(t["entry_time"]) < SEARCH_END)].reset_index(drop=True)
    if not len(t):
        return {"total": 0.0, "monthly_avg": 0.0, "n_trades": 0}
    res = judge.score(t)                              # 審判式（funding/slippage/maker-taker 込み・H13 無変更）
    days = max((pd.to_datetime(t["exit_time"]).max() - pd.to_datetime(t["entry_time"]).min()).days, 1)
    res["per_day"] = len(t) / days
    return res


def main():
    ap = argparse.ArgumentParser(description=f"層3エンジン内探索（v59 のツマミ・探索窓={SEARCH_START.date()}〜{SEARCH_END.date()} 排他=まこさん決定・SEARCH_START/END 定数が正本）")
    ap.add_argument("--trials", type=int, default=200)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--log", default=None, help="試行ログの出力先（既定=scratchpad 相当のカレント）")
    a = ap.parse_args()
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    print(f"[探索窓] {SEARCH_START.date()} 〜 {SEARCH_END.date()}（排他）＝まこさん決定・採点窓と非重複＝汚染ゼロ")
    t0 = time.time()
    df = e37._load(0, start_override=str(WARM_START.date()))
    df = df[df["ts"] < SEARCH_END].reset_index(drop=True)
    print(f"[共通部分] データ+指標 {len(df):,} バー（{time.time()-t0:.0f}秒・以後の試行はエンジンループのみ）")
    global _KIJ_TH_RANGE
    _KIJ_TH_RANGE = _kij_range(df)
    print(f"[kijun26 閾値レンジ] 探索窓の乖離%分布 (q50, q99.5) = ({_KIJ_TH_RANGE[0]:.4f}, {_KIJ_TH_RANGE[1]:.4f})＝実行時実値（手打ちなし）")

    logf = open(a.log or "engine_search_e37_trials.log", "w", encoding="utf-8")

    def _quiet_run(overrides, v59_on):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            res = _run_engine(df, overrides, v59_on)
        return res

    t1 = time.time()
    base = _quiet_run({}, v59_on=False)
    print(f"[基準] v59 OFF（土台構成）: 探索窓 net ${base['total']:+,.0f} / 月平均 ${base['monthly_avg']:+,.1f}"
          f" / {base['n_trades']}玉 / {base.get('per_day', 0):.2f}件/日（1走 {time.time()-t1:.0f}秒）")
    logf.write(f"BASELINE\t{base['total']:+.1f}\t{base['monthly_avg']:+.2f}\t{base['n_trades']}\n"); logf.flush()

    results = []

    def obj(trial):
        ov = _suggest(trial)
        try:
            res = _quiet_run(ov, v59_on=True)
        except Exception as e:
            logf.write(f"T{trial.number}\tERROR\t{str(e)[:120]}\n"); logf.flush()
            raise optuna.TrialPruned()
        results.append((trial.number, dict(trial.params), res))
        logf.write(f"T{trial.number}\t{res['total']:+.1f}\t{res['n_trades']}\t{res.get('per_day', 0):.2f}\t{trial.params}\n")
        logf.flush()
        if trial.number % 10 == 0:
            el = time.time() - t0
            print(f"  trial {trial.number}: net ${res['total']:+,.0f}（基準 ${base['total']:+,.0f}）"
                  f" / 経過 {el/60:.1f}分", flush=True)
        return res["total"]

    st = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=a.seed))
    st.optimize(obj, n_trials=a.trials, show_progress_bar=False)

    print("\n[上位10（探索窓の審判値・基準との比較つき）]")
    top = sorted(results, key=lambda z: -z[2]["total"])[:10]
    for num, params, res in top:
        print(f"  #{num}: net ${res['total']:+,.0f}（基準比 {res['total']-base['total']:+,.0f}）"
          f" / {res['n_trades']}玉 / {res.get('per_day', 0):.2f}件/日\n"
          f"      {params}")
    print(f"\n[基準] v59 OFF: net ${base['total']:+,.0f} / {base['n_trades']}玉")
    print(f"⚠️ ここは探索窓（{SEARCH_START.date()}〜{SEARCH_END.date()} 排他）の数字＝採否の数字ではない。最終候補1つを正式本走（--tag 連番）で")
    print("   採点窓 score.py＋report/analyze 型別4分割にかけ、採否はまこさんが判断する。")
    logf.close()


if __name__ == "__main__":
    main()
