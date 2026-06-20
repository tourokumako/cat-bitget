#!/usr/bin/env python3.13
"""e35_timeexit_separation_probe — iter8 前提検証（採点なし・測定専用・net 不介入）

問い: 順行した玉（保有中 mfe>$2）の中で、最後に「中心C到達(利確)」する玉 と
      「届かず時間切れ(取り逃し=TIME_EXIT)」になる玉 を、保有中その時点で分かる材料で見分けられるか。

やること:
  ① 教師 = 基底 run_continuous（partial/be_gate なし＝玉の自然な結末）を学習窓のみで走らせる。
     ※ be_gate/partial は学習済 booster を要し循環するため、玉の自然な分離力を測る基底を使う
       （取り逃し玉は be_gate=含み損限定 の対象外・partial の介入前＝母集団が最も完全）。
  ② 順行玉だけに 2 クラスを付ける: 中心到達{EDGE_TP,CENTER_LOCK}=0 / 取り逃し{TIME_EXIT & mfe>$2}=1。
  ③ 保有中の各バーのスナップショット = _hold_feat_vec(19列) + time_left_ratio。全て t 時点（leak-safe）。
  ④ 玉単位の前向き OOF（未来玉を学習に入れない）で roc_auc を測る。time_left あり/なし の ablation。
  ⑤ feature importance（atr/ボラが支配でないか・H15）。

判定: AUC≈0.5=材料で区別不可→iter8 不成立 / 0.65〜0.75=分けられる→iter8 GO（time_left の寄与を ablation で確認）/ >0.9=leak 疑い。
判定は score でなく分離力の数字（採点しない・売買記録を judge に出さない・H13 不介入）。
"""
import argparse
import pathlib
import numpy as np
import pandas as pd

import e35_range_oscillation as E   # run_continuous / _hold_arrays / _hold_feat_vec / _HOLD_FEATS / _load / _attach_entry_cols / TRAIN_END / HOLD_5M

WIN = {"EDGE_TP", "CENTER_LOCK"}     # 中心C到達系（届いた＝利確）
MFE_FLOOR = 2.0                      # 順行の定義（玉単位 mfe_usd>$2・iter7 深掘りと同基準）
FEATS_BASE = list(E._HOLD_FEATS)
FEATS_T8 = FEATS_BASE + ["time_left_ratio"]


def _build_snaps(df: pd.DataFrame, box_tf: str) -> pd.DataFrame:
    """基底の玉 → 順行玉(中心到達/取り逃し)の保有中スナップ（学習窓のみ・特徴は t 時点）。"""
    A = E._hold_arrays(df, box_tf)
    idx_of = {x: i for i, x in enumerate(df["ts"].tolist())}
    base_trades, _ = E.run_continuous(df, box_tf, E.MAX_ADDS)        # 基底（partial/be_gate なし）
    bt = pd.DataFrame(base_trades)
    bt["entry_time"] = pd.to_datetime(bt["entry_time"]); bt["exit_time"] = pd.to_datetime(bt["exit_time"])
    print(f"  教師＝基底 {bt['position_id'].nunique()} 玉 / 出口 {dict(bt['exit_reason'].value_counts())}")

    rows = []
    n_center = n_miss = n_drop = 0
    HOLD = float(E.HOLD_5M)
    for pid, g in bt.groupby("position_id"):
        g = g.sort_values("entry_time")
        reason = g["exit_reason"].iloc[0]
        mfe = float(g["mfe_usd"].iloc[0])
        if reason in WIN:
            label = 0; n_center += 1                                  # 中心到達（順行は自明＝届いた）
        elif reason == "TIME_EXIT" and mfe > MFE_FLOOR:
            label = 1; n_miss += 1                                    # 取り逃し（順行したのに時間切れ）
        else:
            n_drop += 1; continue                                     # 母集団外（mfe≤$2 死に玉・箱ブレイク 等）
        lot_idx = [idx_of[x] for x in g["entry_time"]]; lot_px = g["entry_price"].astype(float).tolist()
        exit_idx = idx_of[g["exit_time"].iloc[0]]
        sdir = 1 if g["side"].iloc[0] == "LONG" else -1
        first_idx = lot_idx[0]
        for i in range(first_idx + 1, exit_idx):
            filled = [(li, lp) for li, lp in zip(lot_idx, lot_px) if li <= i]
            if not filled or not (np.isfinite(A["Cc"][i]) and np.isfinite(A["atr"][i])):
                continue
            avg_i = sum(lp for _, lp in filled) / len(filled)
            vec = E._hold_feat_vec(A, sdir, avg_i, first_idx, len(filled), i)
            time_left = (HOLD - float(i - first_idx)) / HOLD          # 残り時間比（t 時点で確定・無次元・H6）
            rows.append([pid, g["entry_time"].iloc[0], label] + vec + [time_left])
    snaps = pd.DataFrame(rows, columns=["position_id", "entry_time", "label"] + FEATS_T8)
    snaps = snaps[snaps.entry_time < E.TRAIN_END].reset_index(drop=True)   # H8 学習窓のみ
    print(f"  母集団（順行玉）: 中心到達 {n_center} 玉 / 取り逃し {n_miss} 玉 / 母集団外 {n_drop} 玉（除外）")
    print(f"  学習窓スナップ {len(snaps):,} 行（玉 {snaps.position_id.nunique()}）/ 取り逃し率 {snaps.label.mean():.3f}")
    return snaps


def _oof_auc(snaps: pd.DataFrame, feats: list, n_blocks: int = 5):
    """玉単位の前向き OOF（未来玉を学習に入れない）で roc_auc。スナップは同玉が複数行＝玉でブロック分割。"""
    import lightgbm as lgb
    from sklearn.metrics import roc_auc_score
    params = dict(n_estimators=300, num_leaves=15, min_child_samples=200, reg_alpha=1.0, reg_lambda=1.0,
                  learning_rate=0.03, random_state=42, verbose=-1)
    # 玉を entry_time 順に並べ n_blocks の時間ブロックへ（同玉は同ブロック＝行分割しない）
    pid_order = (snaps.groupby("position_id")["entry_time"].min().sort_values().index.tolist())
    block_of = {pid: min(int(k * n_blocks / len(pid_order)), n_blocks - 1) for k, pid in enumerate(pid_order)}
    snaps = snaps.assign(_blk=snaps.position_id.map(block_of))
    oof_y, oof_p = [], []
    for b in range(1, n_blocks):                                      # b=0 は学習履歴なし＝テスト不可（前向き）
        tr = snaps[snaps._blk < b]; te = snaps[snaps._blk == b]
        if len(te) == 0 or tr.label.nunique() < 2:
            continue
        m = lgb.LGBMClassifier(**params); m.fit(tr[feats], tr["label"].to_numpy())
        oof_p.extend(m.predict_proba(te[feats])[:, 1].tolist()); oof_y.extend(te["label"].tolist())
    auc = roc_auc_score(oof_y, oof_p) if len(set(oof_y)) == 2 else float("nan")
    return auc, len(oof_y)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--box-tf", choices=E.TFS, default="5m")
    ap.add_argument("--smoke", type=int, default=0)
    a = ap.parse_args()

    # leak 自己検査（自分のソースに未来参照リテラルが無い・動的構築で誤検出回避）
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    _p1 = "shift(" + "-"; _p2 = "center" + "=True"
    assert _p1 not in src and _p2 not in src, "leak 疑い（未来参照 shift/center）"

    print("=" * 100)
    print("[E35 iter8 前提 probe] 順行玉: 取り逃し(時間切れ) vs 中心到達 を保有中材料で分けられるか（採点なし・測定）")
    df = E._load(a.smoke)
    E._attach_entry_cols(df, a.box_tf)
    print(f"  価格 {E.e34v1.CSV.name}（{len(df):,}本）/ 学習窓境界 < {E.TRAIN_END.date()}（採点窓・封印窓は不参照）")

    snaps = _build_snaps(df, a.box_tf)
    if snaps.label.nunique() < 2 or len(snaps) < 200:
        print("  ⛔ 母集団が小さすぎ/片寄り＝AUC 測定不能。"); print("=" * 100); return

    auc_base, n_base = _oof_auc(snaps, FEATS_BASE)
    auc_t8, n_t8 = _oof_auc(snaps, FEATS_T8)
    print(f"\n  ── OOF AUC（玉単位 前向き・採点窓不参照・全保有バー）──")
    print(f"   time_left なし（19特徴）: AUC {auc_base:.3f}（OOF {n_base} 行）")
    print(f"   time_left あり（20特徴）: AUC {auc_t8:.3f}（OOF {n_t8} 行）/ ablation 差 {auc_t8 - auc_base:+.3f}")

    # ★早期に分かるか（部分利確で取れるかは「保有前半で取り逃しと判別できるか」次第）
    #   全バー AUC は保有後半の near-outcome スナップで水増しされる＝早期スライスで測り直す（決定に直結）。
    print(f"\n  ── 早期分離力（保有経過バー帯別 OOF AUC・time_left なし=19特徴）──")
    HOLD = float(E.HOLD_5M)
    for lo, hi, lab in [(0, 6, "0-6本(30分)"), (6, 12, "6-12本(60分)"), (12, 24, "12-24本(2h)"), (24, 48, "24-48本(後半)")]:
        sl = snaps[(snaps.bars_held >= lo) & (snaps.bars_held < hi)]
        if len(sl) < 200 or sl.label.nunique() < 2:
            print(f"   {lab}: 行 {len(sl)}（測定不能・小）"); continue
        a_e, n_e = _oof_auc(sl, FEATS_BASE)
        print(f"   {lab}: AUC {a_e:.3f}（OOF {n_e} 行・取り逃し率 {sl.label.mean():.3f}）")

    # feature importance（学習窓 full fit・atr/ボラ支配でないか＝H15）
    import lightgbm as lgb
    params = dict(n_estimators=300, num_leaves=15, min_child_samples=200, reg_alpha=1.0, reg_lambda=1.0,
                  learning_rate=0.03, random_state=42, verbose=-1)
    m = lgb.LGBMClassifier(**params); m.fit(snaps[FEATS_T8], snaps["label"].to_numpy())
    fi = pd.Series(m.feature_importances_, index=FEATS_T8).sort_values(ascending=False)
    tl_rank = list(fi.index).index("time_left_ratio") + 1
    atr_rank = list(fi.index).index("atr_pct") + 1
    print(f"\n  feature importance top8:\n{fi.head(8).to_string()}")
    print(f"  time_left_ratio 順位 {tl_rank}/{len(FEATS_T8)} / atr_pct 順位 {atr_rank}/{len(FEATS_T8)}（atr 上位独占でなければ H15 OK）")

    print("\n  ── 判定の目安 ──")
    print("   AUC≈0.5 → 材料で区別不可＝iter8 不成立（設計見直し）")
    print("   AUC 0.65〜0.75 → 分けられる＝iter8 GO（time_left の ablation 寄与を確認）")
    print("   AUC>0.9 → leak 疑い（材料に未来混入）→ 調査")
    print("=" * 100)


if __name__ == "__main__":
    main()
