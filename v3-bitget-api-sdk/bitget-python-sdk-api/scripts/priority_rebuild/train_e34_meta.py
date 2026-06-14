#!/usr/bin/env python3
"""train_e34_meta.py — E34 iteration-3: dwell 候補のメタラベリング（方向二値・LONG・採点なし）

設計書: .claude/ratchet/e34_design.md §11.4（まこさん GO 2026-06-14・実装前プレゼン GO 済）。py3.13 / lightgbm。

6軸ゲート（§11.0）:
  軸4 cascade … 前段=dwell（固定ルール・候補生成＝段1・高recall）→ 後段=LightGBM（段2・賭けるか見送るか）。
  軸6 Meta 同型回避 … primary=dwell(固定ルール)≠secondary(LightGBM)＝異種。secondary に盲点情報=レジサポを入力（--set B）。
  軸1 ボラ逃げ不違反（§11.5 H15）… ラベル=方向（中心TP 先着）／LONG 単独／atr_pct・bb_width は脇役（importance 監視）。

候補（primary・不変＝dwell_max2 と同一）:
  S1' dev_z ≤ 学習q0.05 ゾーン滞在 ∩ S2 taker_ls ≤ 学習q0.25 ∩ S3 ADX14 ≤ 25・学習期間 < 2025-01 のみ。

ラベル（方向・H15・★最重要 reviewer note #1）:
  候補 si から単発前向き sim → 中心TP 先着=1 / SL or 48本時間切れ 先着=0。
  ⚠ exit ロジックは連続モードと同式（e34_range_base.run L216-234）＝
    TP=現バー SMA20（動く中心・armed= smai≥entry×(1+COST_FLOOR) のとき high≥smai）／ SL= entry−1.5×ATR14（low≤sl）／ 48本。
  ★eval_engine.simulate_trade（固定 tp_pct=entry×(1+tp_pct)）はラベルに使わない＝E8b の
    「480分保有に5分σバリア」誤ラベル（AUC0.52・L-252）再演を防ぐ。中心TP は時系列で動くので各バー smai を参照する。
  net 金額をラベルにしない（高ボラほど net 伸びる＝ボラ依存＝H15 違反）。

特徴量（sig_time 確定値・leak-safe・§11.3）:
  --set A（既存分離指標のみ）= dev_z, ret_5, rsi, stoch_k, rsi_slope, bb_width, atr_pct, adx, bb_mid_slope_pct, taker_ls。
  --set B（A＋レジサポ）= A ＋ e34_levels.LEVEL_FEATS（support/resistance/nearest 距離・タッチ回数・volume_at_support）。

θ（§11.4）= 学習 OOF で1度だけ決める単一 a priori（採点窓を見ない＝forbid_fixed_value_tuning）。
  採用率を N0 で報告＝degenerate（near-inaction・E21 全通過/E27 採点7件）でないか確認。

★不正防止（cat_requirements §8.4-2.9・§11.7(3)）:
  ラベル sim は連続モードと同式（eval_engine の固定 tp_pct を使わない）。eval_engine は entry 約定/コスト定数の
  import のみ（改造禁止）。番人 ratchet_guards を import して通す（self_check 用にわざと壊して落ちるかは別途確認済）。
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import e34_range_zscore_taker as e34v1   # noqa: E402  指標/分位/定数の単一ソース（add_indicators/add_taker/分位）
import e34_range_base as base            # noqa: E402  前処理 add_analysis_features ＋ 出口定数（中心TP/SL/48本）
import e34_levels as lv                  # noqa: E402  成分B レジサポ（leak-safe・H6）
import eval_engine as ee                 # noqa: E402  審判（entry 約定/コスト定数・import のみ・改造禁止）
import ratchet_guards as rg              # noqa: E402  leak/期間/vol_share 番人（import のみ・改造禁止）

RAT = e34v1.RATCHET
TRAIN_END = e34v1.TRAIN_END              # 2025-01-01（学習 <2025-01・H8）
SCORE_START = pd.Timestamp("2025-06-01") # 採点始（学習末 < 採点始 を assert_period_split で物理担保）
N_FOLDS = 5
EMBARGO = pd.Timedelta(days=1)           # purged k-fold（候補単位・E27/E28 precedent）

# 成分A（既存・全カラム e34_range_base に記録済／atr_pct はここで算出）
FEATS_A = ["dev_z", "ret_5", "rsi", "stoch_k", "rsi_slope",
           "bb_width", "atr_pct", "adx", "bb_mid_slope_pct", "taker_ls"]
# 成分B（A＋レジサポ）
FEATS_B = FEATS_A + lv.LEVEL_FEATS

# LightGBM 過学習対策（num_leaves 小・min_child 大・L1/L2・class weight）＝train_e28_meta と同流儀
LPARAMS = dict(objective="binary", metric="auc", learning_rate=0.03,
               num_leaves=15, min_child_samples=50, feature_fraction=0.8, bagging_fraction=0.8,
               bagging_freq=1, lambda_l1=1.0, lambda_l2=1.0, seed=42, verbose=-1)


def _log(m):
    print(m, flush=True)


def label_forward_sim(fill_idx, entry_avg, atr_entry, sma_arr, high_arr, low_arr, n):
    """★連続モードと同式の単発前向き sim（e34_range_base.run L216-234 を1ロット想定で再現）。

    Returns: 1(中心TP先着) / 0(SL or 48本時間切れ 先着) / None(末尾でバリア未到達＝学習に使わない)。
    entry_avg = 約定価格（1ロット想定 avg）。SL は entry 基準で固定（連続は add で再計算するが単発は不変）。
    出口判定は約定 bar の「次 bar」以降から（H2・eval_engine fill_idx+1 契約と同じ）。
    """
    sl_price = entry_avg - base.SL_ATR_K * atr_entry           # SL = avg − 1.5×ATR14（連続モードと同式）
    for i in range(fill_idx + 1, n):                           # ★次 bar 以降（H2・未来 bar は順次のみ参照）
        li = low_arr[i]; hi = high_arr[i]; smai = sma_arr[i]
        # ① SL 先着（連続モードは SL を TP より先に判定・L219）
        if li <= sl_price:
            return 0
        # ② TP=現バー SMA20（動く中心）。armed= 中心≥avg×(1+COST_FLOOR) のとき high≥smai（L226-227）
        armed = np.isfinite(smai) and smai >= entry_avg * (1.0 + base.COST_FLOOR)
        if armed and hi >= smai:
            return 1
        # ③ 時間切れ 48本（約定起点＝連続は first_idx=初回entry だが単発は fill が初回・全ロット）
        if (i - fill_idx) >= base.HOLD_5M:
            return 0
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", choices=["A", "B"], required=True,
                    help="A=既存分離指標のみ / B=A＋レジサポ（§7 源泉検証 ablation）")
    ap.add_argument("--smoke", action="store_true", help="末尾候補に制限（配管確認）")
    a = ap.parse_args()
    feats = FEATS_A if a.set == "A" else FEATS_B
    tag = f"E34_meta{a.set}"

    _log("=" * 92)
    _log(f"[{tag}] dwell 候補のメタラベリング（方向二値・中心TP先着=1・LONG単独・採点なし）set={a.set}")

    # ── 番人（leak/期間分割）を物理的に通す（§11.7(3)）──────────────────────────
    rg.assert_no_future_ref(pathlib.Path(__file__).read_text())     # 自分のコードに .shift(-N)/center=True が無い
    rg.assert_no_future_ref(pathlib.Path(lv.__file__).read_text())  # e34_levels も検査
    rg.assert_period_split(TRAIN_END, SCORE_START)                  # 学習末 < 採点始（H8）

    # ── 前処理（e34_range_base と完全同一＝add_indicators+add_taker+add_analysis_features）──
    df = pd.read_csv(e34v1.CSV)
    df["ts"] = pd.to_datetime(df["timestamp"])
    df = df.reset_index(drop=True)
    df = e34v1.add_indicators(df)
    df = e34v1.add_taker(df)
    df = base.add_analysis_features(df)
    df["atr_pct"] = df["atr"] / df["close"] * 100.0                 # §11.3 atr_pct=(atr/close×100)（脇役）
    if a.set == "B":
        df = lv.add_level_features(df)                              # 成分B レジサポ（leak/H6 assert 内蔵）

    # ── 候補（primary・dwell_max2 と同一＝S1' dwell ∩ S2 ∩ S3・学習期間のみ）──────────
    tr = df[df.ts < TRAIN_END]
    z_thr = float(tr.dev_z.quantile(e34v1.Z_Q))                     # 学習 q0.05（覗き見なし・H8）
    taker_thr = float(tr.taker_ls.quantile(e34v1.TAKER_Q))         # 学習 q0.25
    s1 = df.dev_z <= z_thr
    s2 = df.taker_ls <= taker_thr
    s3 = df.adx <= e34v1.ADX_MAX
    cand_mask = (s1 & s2 & s3).fillna(False) & (df.ts < TRAIN_END)
    _log(f"  分位（学習<2025-01）: dev_z≤q{e34v1.Z_Q}={z_thr:+.2f} / taker_ls≤q{e34v1.TAKER_Q}={taker_thr:.3f} / ADX≤{e34v1.ADX_MAX}")
    _log(f"  dwell 候補（学習期間）: {int(cand_mask.sum()):,} 件")

    # ── ラベル付け（★連続モードと同式の単発前向き sim・中心TP先着=方向）─────────────
    sma_arr = df["sma"].to_numpy(float); atr_arr = df["atr"].to_numpy(float)
    high_arr = df["high"].to_numpy(float); low_arr = df["low"].to_numpy(float)
    close_arr = df["close"].to_numpy(float)
    n = len(df)
    cand_idx = np.where(cand_mask.to_numpy())[0]

    rows = []
    skipped = 0
    for si in cand_idx:
        if si < e34v1.SMA_N + 2 or si >= n - base.HOLD_5M - 2:
            skipped += 1
            continue
        atri = atr_arr[si]; smai = sma_arr[si]
        if not (np.isfinite(atri) and atri > 0 and np.isfinite(smai)):
            skipped += 1
            continue
        # entry = 次バー maker 指値 close×(1−offset)・TTL 内約定（連続モードと同じ・1ロット想定）
        sig_close = close_arr[si]
        limit = sig_close * (1.0 - ee.ENTRY_LIMIT_OFFSET)
        fill_idx = None
        for j in range(si + 1, min(si + 1 + ee.DEFAULT_TTL, n)):
            if low_arr[j] <= limit:
                fill_idx = j
                break
        if fill_idx is None:
            skipped += 1                                            # TTL 内不約定＝候補不成立（連続モードと同じ）
            continue
        entry_avg = limit
        atr_fill = atr_arr[fill_idx]
        if not (np.isfinite(atr_fill) and atr_fill > 0):
            atr_fill = atri
        y = label_forward_sim(fill_idx, entry_avg, atr_fill, sma_arr, high_arr, low_arr, n)
        if y is None:
            skipped += 1
            continue
        feat_vals = {c: float(df[c].iloc[si]) for c in feats}       # 特徴は sig_time(si) 確定値（leak-safe）
        if not np.isfinite(list(feat_vals.values())).all():
            skipped += 1
            continue
        row = {"sig_ts": pd.Timestamp(df.ts.iloc[si]), "y": int(y),
               "year": int(pd.Timestamp(df.ts.iloc[si]).year)}
        row.update(feat_vals)
        rows.append(row)

    cd = pd.DataFrame(rows).sort_values("sig_ts").reset_index(drop=True)
    if a.smoke:
        cd = cd.tail(200).reset_index(drop=True)
        _log("[SMOKE] 末尾200候補に制限")
    assert len(cd) > 0, "教師 0 件（候補/分位/データ確認）"
    yv = cd["y"].to_numpy()
    spw = float((yv == 0).sum()) / max(1, int((yv == 1).sum()))    # class weight（中心TP先着が少数派なら重く）
    _log(f"  [教師生成・自己検査] 約定候補 {len(cd):,}件（除外 {skipped:,}）/ ラベル分布 中心TP先着(y=1) {int((yv==1).sum()):,}"
         f" / SL・時間切れ(y=0) {int((yv==0).sum()):,} / base_rate {yv.mean():.3f} / scale_pos_weight {spw:.2f}")
    _log(f"  年別件数: {cd.groupby('year').size().to_dict()}")

    X = cd[feats].to_numpy(dtype=np.float32)

    # ── purged k-fold OOF（候補単位・時系列ブロック・embargo 1day・E27/E28 precedent）────
    oof = np.full(len(cd), np.nan)
    fold_rows = []
    lp = dict(LPARAMS); lp["scale_pos_weight"] = spw
    ts_all = cd["sig_ts"].to_numpy()
    blocks = np.array_split(np.arange(len(cd)), 2 if a.smoke else N_FOLDS)
    min_ti, min_vi = (40, 15) if a.smoke else (120, 30)
    for fi, vi in enumerate(blocks):
        if len(vi) == 0:
            continue
        v0, v1 = cd["sig_ts"].iloc[vi[0]], cd["sig_ts"].iloc[vi[-1]]
        purge = (ts_all >= np.datetime64(v0 - EMBARGO)) & (ts_all <= np.datetime64(v1 + EMBARGO))
        ti = np.where(~purge)[0]
        if len(ti) < min_ti or len(vi) < min_vi or len(np.unique(yv[ti])) < 2:
            continue
        dtr = lgb.Dataset(X[ti], label=yv[ti])
        m = lgb.train(lp, dtr, num_boost_round=300)
        oof[vi] = m.predict(X[vi])
        try:
            auc = roc_auc_score(yv[vi], oof[vi])
        except ValueError:
            auc = float("nan")
        fold_rows.append({"fold": int(fi), "val": f"{v0.date()}〜{v1.date()}", "n": int(len(vi)), "auc": round(float(auc), 3)})
        _log(f"  [fold{fi}] {v0.date()}〜{v1.date()} n={len(vi)} train={len(ti)} AUC={auc:.3f}")
    assert fold_rows, "有効 fold 0"

    mask = ~np.isnan(oof)
    oof_auc = float(roc_auc_score(yv[mask], oof[mask])) if len(np.unique(yv[mask])) > 1 else float("nan")
    _log(f"\n  OOF AUC（中心TP先着を見分けるか）: {oof_auc:.3f} / fold別 {[r['auc'] for r in fold_rows]}")

    # ── θ＝学習 OOF で1度だけ決める単一 a priori（採点窓を見ない・forbid_fixed_value_tuning）──
    #    規則: base_rate（dwell の中心TP先着率）を OOF 上で再現する単一閾値＝(1−base_rate) 分位点。
    #          ＝「学習の自然な合格率に揃える」単一 a priori（採点窓スイープでない・E8a-2 を OOF で踏襲）。
    base_rate = float(yv[mask].mean())
    theta = float(np.quantile(oof[mask], 1.0 - base_rate))
    n0_train = int((oof[mask] >= theta).sum())
    adopt_train = n0_train / int(mask.sum())
    _log(f"  θ（学習OOF・単一a priori・(1−base_rate={1-base_rate:.3f})分位）= {theta:.4f}")
    _log(f"  [N0 採用率・degenerate チェック] 学習OOFで prob≥θ 採用 {n0_train:,}/{int(mask.sum()):,} = {adopt_train:.1%}"
         f"（near-inaction なら採点で 7件型・E27/E21 を疑う）")

    # ── 本学習（全候補）→ feature_importance + vol_share（H15 ボラ脇役 verify・番人）────
    m_full = lgb.train(lp, lgb.Dataset(X, label=yv), num_boost_round=300)
    imp = pd.Series(m_full.feature_importance("gain"), index=feats).sort_values(ascending=False)
    vr = rg.report_vol_importance(dict(zip(feats, m_full.feature_importance("gain"))))
    _log(f"\n  [H15 ボラ寄与] vol_share={vr['vol_share']}（揺れ幅が方向主役でないこと・top5={vr['top']}）")
    _log("  [feature_importance top（gain）]\n" + imp.head(min(15, len(feats))).to_string())

    # ── 出力（モデル ＋ θ ＋ 学習パラメータ JSON）→ ratchet ────────────────────────
    RAT.mkdir(parents=True, exist_ok=True)
    model_path = RAT / f"{tag}_model.txt"
    m_full.save_model(str(model_path))                              # LightGBM Booster（lazy import で e34_range_base が読む）
    meta = {
        "_source": "train_e34_meta.py（E34 iteration-3・dwell メタラベリング・方向二値・採点なし）",
        "set": a.set, "features": feats, "primary": "dwell_max2(S1' dev_z≤q0.05 ∩ S2 taker≤q0.25 ∩ S3 ADX≤25)",
        "label": "中心TP先着=1 / SL・48本時間切れ=0（連続モードと同式・方向・H15）",
        "n_cand": int(len(cd)), "base_rate": round(base_rate, 4),
        "oof_auc": round(oof_auc, 4), "folds": fold_rows,
        "theta": round(theta, 6), "n0_train_adopt": n0_train, "adopt_rate_train": round(adopt_train, 4),
        "vol_share": vr["vol_share"], "vol_top": vr["top"],
        "z_thr": round(z_thr, 4), "taker_thr": round(taker_thr, 4),
        "lparams": {k: (v if not isinstance(v, float) else round(v, 4)) for k, v in lp.items()},
        "feature_importance_gain": {k: round(float(v), 1) for k, v in imp.to_dict().items()},
        "model_path": str(model_path.name),
        "level_N": lv.LEVEL_N, "level_tol": lv.VOL_TOL,
    }
    json_path = RAT / f"{tag}_train.json"
    json.dump(meta, open(json_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    rg.assert_output_exists(str(model_path)); rg.assert_output_exists(str(json_path))
    _log(f"\n  [out] モデル {model_path.name} / メタ {json_path.name}（θ={theta:.4f}）")
    _log(f"  → 次（採点は Workflow 外で1回）:")
    _log(f"     python3 scripts/priority_rebuild/e34_range_base.py --entry dwell --max-adds 2 "
         f"--meta-model {model_path} --theta {theta:.6f} --meta-set {a.set}")
    _log("=" * 92)


if __name__ == "__main__":
    main()
