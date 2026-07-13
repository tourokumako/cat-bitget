#!/usr/bin/env python3
"""v22_gate_diag.py — read-only 検証（診断レーン・acceptance 免除・2026-07-14 まこさん承認）

目的: v22 の選定の門（v21_band_consensus）が「本物の利益を殺しているか／過剰適合を弾いたか」を、
      門に却下された候補（特に range_dc/rsi≥55＝学習窓 +$492・(iii)帯悪化だけで却下）を採点窓に通して照合する。
      ＝門は学習窓だけで採否を決める。その採否が採点窓の真実と一致するかを見る（門の監査であって、採点窓で選ぶのではない）。

read-only: 戦略 e37_range_scalp の実関数を import で再利用（セットアップ再実装なし＝ズレ回避）・print のみ・
           売買記録CSVを出さない・score.py を呼ばない。net は run_continuous_v11 が計算した net_usd の窓別合計
           （score.py の公式 net と同一量＝単一戦略で cap 内・実験ではない）。

自己検証（走らせる前の担保）: incumbent（v22 OFF=v21_040 構成）の
   学習窓 net ≈ 既知 -1,575（v22 report 選定 incumbent）／採点窓 net ≈ 既知 -465（v21_040 採点）と一致すれば、
   セットアップは忠実＝以降の却下候補の数字を信用できる。一致しなければ数字を使わない（正直に停止）。
"""
import sys
import pandas as pd

sys.path.insert(0, "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild")
import e37_range_scalp as e37   # noqa: E402
import periods                  # noqa: E402  検証期間の唯一の正本（SSOT・手打ち禁止・ledger E0.5）

BOX_TF = "5m"
TRAIN_END = periods.TRAIN_END
SC_START = periods.SCORE_START
SCORE_END = periods.SEAL_START   # 採点スライスの排他終端＝封印開始（e37 と同一）


def clone(p):
    return {k: (dict(v) if isinstance(v, dict) else v) for k, v in p.items() if k != "cell_fn"} | (
        {"cell_fn": p["cell_fn"]} if "cell_fn" in p else {})


def build_setup():
    """run_e37 の v22 経路（--v11 --v12-open-range --v13-time-maker --v18-tp2-far --v20-rg5 --v22-set）と同一のセットアップを再現。"""
    df = e37._load(0)                       # smoke=0 = 全期間
    df = e37._rsi9_v10(df)
    df = e37._apply_rg5_to_5m(df)           # RG-v5（v20）
    df = e37._attach_v16_bb(df)             # v18 基盤の BB 列
    # ── v18 base（cell_fn fit）＝run_e37 3914-3929 と同一 ──
    dtr18 = df[df["ts"] < TRAIN_END].reset_index(drop=True)
    up20 = df["rg5_uptrend"].to_numpy(bool)
    base18 = {"ladder": None, "sl_far": 1.0, "tmax": 48, "down": None, "ret": {}, "dd": {}, "cell_fn": None,
              "v16": True, "v17": True, "guard": {}, "guard_all": None, "cooldown": e37.V16_COOLDOWN[0], "be_time": {},
              "tmax_map": {}, "down_map": {}, "tp1_f": {}, "tp2_f": {}, "size0": {},
              "break_mode": None, "break_bars": e37.V15_BREAK_BARS}
    base_tr18 = e37.run_continuous_v11(dtr18, BOX_TF, v13_time_maker=True, v14_params=None,
                                       v15_params=clone(base18), v20_uptrend=up20[:len(dtr18)])
    cell_fn18, ncell18, cdesc18 = e37._fit_v15_branch_policy(base_tr18, num_leaves=e37.V16_NUM_LEAVES)
    print(f"  [setup] 場面セル {ncell18} セル: {cdesc18}")
    v15p_base = clone(base18)
    v15p_base.update({"cell_fn": cell_fn18, "dd": dict(e37.V18_FIXED_FROM_V17["dd"]),
                      "down_map": dict(e37.V18_FIXED_FROM_V17["down_map"]), "tp2_far": True,
                      "v21_entry": dict(e37.V22_FIXED_V21_ENTRY), "v21_fold": dict(e37.V22_FIXED_V21_FOLD)})
    df = e37.v22_uptrend_warning(df)        # v22 前兆フラグ
    return df, v15p_base, up20


def run_cfg(df, v15p_base, up20, overrides):
    p = clone(v15p_base)
    for k, v in overrides.items():
        p[k] = (dict(v) if isinstance(v, dict) else v)
    tr = e37.run_continuous_v11(df, BOX_TF, no_add=False, single_tp=False,
                                v11_open_entry=False, v12_open_range=True, v13_time_maker=True,
                                v14_params=None, v15_params=p, v20_uptrend=up20)
    return tr


def window_stats(tr, lo, hi):
    """entry_time が [lo, hi) の玉の net 合計・新規建て玉数（add_count==1）を返す。hi=None なら lo 未満。"""
    net = 0.0
    n_new = 0
    n_all = 0
    for r in tr:
        et = pd.Timestamp(r["entry_time"])
        if hi is None:
            inside = et < lo
        else:
            inside = (lo <= et) and (et < hi)
        if inside:
            net += float(r["net_usd"])
            n_all += 1
            if int(r["add_count"]) == 1:
                n_new += 1
    days = max((hi - lo).total_seconds() / 86400.0, 1.0) if hi is not None else \
        max((pd.Timestamp(lo) - pd.Timestamp("2021-04-01")).total_seconds() / 86400.0, 1.0)
    return net, n_new, n_all, n_new / days


def main():
    print("=" * 100)
    print("v22 選定の門 監査（read-only 診断・門が本物の利益を殺したか／過剰適合を弾いたかを両窓照合）")
    print("=" * 100)
    df, v15p_base, up20 = build_setup()

    # 候補（v22 選定の門に却下された range_dc 入口一般化 ＋ incumbent ＋ 採択された anchor）
    configs = [
        ("incumbent(v22 OFF=v21_040)", {}),
        ("range_dc/rsi--", {"v22_entry": {"rsi_lo": None}}),
        ("range_dc/rsi>=45", {"v22_entry": {"rsi_lo": 45.0}}),
        ("range_dc/rsi>=50", {"v22_entry": {"rsi_lo": 50.0}}),
        ("range_dc/rsi>=55  ★候補04(門却下・学習窓+492)", {"v22_entry": {"rsi_lo": 55.0}}),
        ("adopted anchor cell0/M24(採択)", {"v22_anchor": {0: 24}}),
    ]
    rows = []
    for name, ov in configs:
        tr = run_cfg(df, v15p_base, up20, ov)
        tr_net, tr_new, tr_all, tr_fpd = window_stats(tr, TRAIN_END, None)      # 学習窓（門の視点）
        sc_net, sc_new, sc_all, sc_fpd = window_stats(tr, SC_START, SCORE_END)  # 採点窓（真実）
        rows.append((name, tr_net, tr_new, tr_fpd, sc_net, sc_new, sc_fpd))
        print(f"  走了: {name:<48} 学習窓 net ${tr_net:>9,.0f} / 採点窓 net ${sc_net:>8,.0f}", flush=True)

    print("\n" + "=" * 100)
    print(f"{'候補':<48}{'学習窓net':>12}{'新規/日':>9}{'採点窓net':>12}{'採点新規/日':>11}")
    print("-" * 100)
    inc = rows[0]
    for name, tr_net, tr_new, tr_fpd, sc_net, sc_new, sc_fpd in rows:
        d_tr = tr_net - inc[1]
        d_sc = sc_net - inc[4]
        print(f"{name:<48}{tr_net:>12,.0f}{tr_fpd:>9.2f}{sc_net:>12,.0f}{sc_fpd:>11.2f}"
              f"   （対inc 学習{d_tr:+,.0f}/採点{d_sc:+,.0f}）")

    print("\n[自己検証＝セットアップ忠実性] 既知値と一致するか（一致しなければ以下の結論は無効・正直に破棄）:")
    print(f"  incumbent 学習窓 net = {inc[1]:,.0f}  （既知 ≈ -1,575＝v22 report 選定 incumbent）")
    print(f"  incumbent 採点窓 net = {inc[4]:,.0f}  （既知 ≈ -465＝v21_040 採点）")
    print(f"  candidate04(rsi>=55) 学習窓 net = {rows[4][1]:,.0f}  （既知 ≈ -1,083＝v22 report 候補04）")
    print(f"  adopted anchor cell0/M24 採点窓 net = {rows[5][4]:,.0f}  （既知 ≈ -456＝v22_042 採点）")

    print("\n[判定＝門は本物の利益を殺したか？] 候補04（学習窓で門を +$492 上回るが (iii)帯悪化 で却下）の採点窓:")
    c4_sc = rows[4][4]
    inc_sc = inc[4]
    if c4_sc > inc_sc + 1e-9:
        print(f"  → 候補04 採点窓 ${c4_sc:,.0f} > incumbent ${inc_sc:,.0f}（+${c4_sc - inc_sc:,.0f}）")
        print("  → 門が本物の利益を殺していた疑い濃厚（学習窓でも採点窓でも incumbent 超え＝(iii)各帯非悪化 が厳しすぎ）")
    else:
        print(f"  → 候補04 採点窓 ${c4_sc:,.0f} <= incumbent ${inc_sc:,.0f}（{c4_sc - inc_sc:+,.0f}）")
        print("  → 門は過剰適合を正しく弾いた（学習窓+$492 は採点窓に持ち越さない）＝問題は門でなく上流（教師/greedy）")


if __name__ == "__main__":
    main()
