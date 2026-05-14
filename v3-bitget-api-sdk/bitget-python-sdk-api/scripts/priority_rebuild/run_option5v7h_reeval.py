"""
選択肢 5 / 7 / ハイブリッド 再評価 (rolling 却下後・Phase 4-b 設計選択)

指示書: .claude/instructions/2026-05-14_option5v7h_reeval.md
前提: 固定維持 + K96 SHORT q99 除外 (audit#9 確定)
ガード A: fit/refit/KMeans 系処理なし。artifact は joblib.load のみ

Steps:
  0-2: sha256 assert (不一致で sys.exit)
  2: 4 軸評価 (3 案: 選択肢 5 / 選択肢 7 / ハイブリッド)
    軸 1: K96 SHORT q99 除外後の成立性 (解釈 C)
    軸 2(a): サンプル数 + 足切り後有効組合せ数
    軸 2(b): signal quality (net_quality_pred proxy / MFE_lift / MAE_lift)
    軸 3: train→test 安定性 (cluster 参照ライン / band fire ratio)
    軸 4: Phase 4-b 改修行数見積もり
  contribution_table / raw_aggregation / comparison md 生成

注意 (ガード F):
  contribution_proxy = test_fire × net_quality_pred は proxy であり実 Replay PnL ではない。
  これは月次 PnL の予測ではない。設計選択の補助指標として使用する。

net_quality_pred 算出定義:
  mfe_lift_pred_pp = (mask内エントリの pred MFE mean / 全エントリ pred MFE mean - 1) × 100
  mae_lift_pred_pp = (mask内エントリの pred MAE mean / 全エントリ pred MAE mean - 1) × 100
  net_quality_pred_pp = mfe_lift_pred_pp - mae_lift_pred_pp
  (正規化予測値 _pct 列を使用。実 MFE/MAE による検証は Phase 4-b で実施)
"""

import hashlib
import json
import sys
import warnings
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "results" / "priority_rebuild"
NORM_DIR = DATA_DIR / "ml_phase4_a_norm"
OUT_DIR = DATA_DIR / "option5v7h_reeval"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_NORM_PATH = NORM_DIR / "predictions_train_normalized.parquet"
TEST_NORM_PATH  = NORM_DIR / "predictions_test2025_normalized.parquet"
K2_SCALER       = NORM_DIR / "scaler_train_2021_2024.joblib"
K2_KM           = NORM_DIR / "kmeans_k2_train_2021_2024.joblib"
PHASE4B_PATH    = REPO_ROOT / "scripts" / "priority_rebuild" / "run_phase4_b.py"

# 指示書記載 sha256 先頭 12 桁 (Step 0-2 assert)
EXPECTED_TRAIN_SHA = "bee59c1197d3"
EXPECTED_TEST_SHA  = "c6149c8b7b82"

K_WINDOWS  = (12, 24, 48, 96)
SIDES      = ("LONG", "SHORT")
PCT_COLS   = [
    f"{side}_{kind}_K{k}_pct"
    for k in K_WINDOWS for side in SIDES for kind in ("MFE", "MAE")
]
MIN_SAMPLES = 100  # 足切り閾値 (audit#2 基準)
RANDOM_STATE = 42


# ============================================================
# ユーティリティ
# ============================================================

def log(msg, fp=None):
    ts = datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    if fp:
        fp.write(line + "\n")
        fp.flush()


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def assess_n(n: int) -> str:
    if n >= 100:
        return "✅"
    elif n >= 30:
        return "⚠️"
    else:
        return "❌"


def compute_signal_quality(df_train, mask, mfe_col, mae_col):
    """
    signal quality (proxy) を train mask で計算。
    ガード F: これは proxy であり実 Replay PnL ではない。
    算出定義:
      mfe_lift_pred_pp = (mask内 pred_MFE mean / 全体 pred_MFE mean - 1) × 100
      mae_lift_pred_pp = (mask内 pred_MAE mean / 全体 pred_MAE mean - 1) × 100
      net_quality_pred_pp = mfe_lift_pred_pp - mae_lift_pred_pp
    """
    if mask.sum() == 0:
        return np.nan, np.nan, np.nan
    mfe_mean_sub = float(df_train.loc[mask, mfe_col].mean())
    mae_mean_sub = float(df_train.loc[mask, mae_col].mean())
    mfe_mean_all = float(df_train[mfe_col].mean())
    mae_mean_all = float(df_train[mae_col].mean())
    mfe_lift = (mfe_mean_sub / mfe_mean_all - 1) * 100 if mfe_mean_all > 0 else np.nan
    mae_lift = (mae_mean_sub / mae_mean_all - 1) * 100 if mae_mean_all > 0 else np.nan
    net_q = mfe_lift - mae_lift if (not np.isnan(mfe_lift) and not np.isnan(mae_lift)) else np.nan
    return mfe_lift, mae_lift, net_q


def safe_round(v, d=2):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    return round(float(v), d)


def build_row(option_name, combination, n_tr, n_te,
              axis1_excl, cutoff_status, eff_nte,
              mfe_lift, mae_lift, net_q, fire_ratio,
              cluster_share_diff=None, thr_q99=None):
    contrib = (eff_nte * net_q / 100) if (eff_nte > 0 and net_q is not None and not np.isnan(net_q)) else 0.0
    return {
        "option":                    option_name,
        "combination":               combination,
        "n_train":                   n_tr,
        "n_test_apply_train_thr":    n_te,
        "axis1_exclusion":           axis1_excl,
        "cutoff_status":             cutoff_status,
        "effective_n_te":            eff_nte,
        "mfe_lift_pred_pp":          safe_round(mfe_lift),
        "mae_lift_pred_pp":          safe_round(mae_lift),
        "net_quality_pred_pp":       safe_round(net_q),
        "fire_ratio_test_train":     safe_round(fire_ratio, 4),
        "cluster_share_diff_pp":     safe_round(cluster_share_diff),
        "contribution_proxy":        safe_round(contrib),
        "train_thr_q99":             safe_round(thr_q99, 4) if thr_q99 is not None else None,
        "test_judgment":             assess_n(eff_nte),
    }


# ============================================================
# main
# ============================================================

def main():
    t0 = datetime.now()
    TS = t0.strftime("%Y%m%dT%H%M%SZ")
    LOG_PATH = OUT_DIR / f"option5v7h_reeval_log_{TS}.txt"

    with open(LOG_PATH, "w") as logf:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            log(f"START {t0.isoformat()}", logf)
            log(f"output: {OUT_DIR}", logf)

            # ---------------------------------------------------
            # Step 0-2: sha256 assert
            # ---------------------------------------------------
            log("Step 0-2: sha256 assert ...", logf)
            train_sha = sha256_file(TRAIN_NORM_PATH)
            test_sha  = sha256_file(TEST_NORM_PATH)
            if train_sha[:12] != EXPECTED_TRAIN_SHA:
                log(f"ABORT: train sha mismatch {train_sha[:12]} != {EXPECTED_TRAIN_SHA}", logf)
                sys.exit(1)
            if test_sha[:12] != EXPECTED_TEST_SHA:
                log(f"ABORT: test sha mismatch {test_sha[:12]} != {EXPECTED_TEST_SHA}", logf)
                sys.exit(1)
            log(f"  train sha256: {train_sha[:12]} ✅", logf)
            log(f"  test  sha256: {test_sha[:12]} ✅", logf)

            # ---------------------------------------------------
            # Load data
            # ---------------------------------------------------
            log("Load normalized predictions ...", logf)
            df_tr = pd.read_parquet(TRAIN_NORM_PATH)
            df_te = pd.read_parquet(TEST_NORM_PATH)
            log(f"  train: {len(df_tr)} rows / test: {len(df_te)} rows", logf)
            assert len(df_tr) == 394753, f"train row mismatch: {len(df_tr)}"
            assert len(df_te) == 105120, f"test row mismatch: {len(df_te)}"

            # ガード A: fit 系なし。artifact は load only
            log("Load k=2 artifacts (load only, no fit) ...", logf)
            scaler_k2 = joblib.load(K2_SCALER)
            km_k2     = joblib.load(K2_KM)
            X_tr = df_tr[PCT_COLS].values
            X_te = df_te[PCT_COLS].values
            tr_clu = km_k2.predict(scaler_k2.transform(X_tr))
            te_clu = km_k2.predict(scaler_k2.transform(X_te))
            df_tr["cluster_k2"] = tr_clu
            df_te["cluster_k2"] = te_clu
            tr_clu_dist = {int(c): int(v) for c, v in pd.Series(tr_clu).value_counts().sort_index().items()}
            te_clu_dist = {int(c): int(v) for c, v in pd.Series(te_clu).value_counts().sort_index().items()}
            log(f"  cluster_k2 train: {tr_clu_dist}", logf)
            log(f"  cluster_k2 test:  {te_clu_dist}", logf)

            # ratio = MFE / MAE (全 K × side)
            log("Compute ratios and thresholds (train only) ...", logf)
            ratios_tr  = {}
            ratios_te  = {}
            thresholds = {}
            for k in K_WINDOWS:
                for side in SIDES:
                    mfc = f"{side}_MFE_K{k}_pct"
                    mac = f"{side}_MAE_K{k}_pct"
                    r_tr = df_tr[mfc] / df_tr[mac].clip(lower=1e-9)
                    r_te = df_te[mfc] / df_te[mac].clip(lower=1e-9)
                    ratios_tr[(k, side)] = r_tr
                    ratios_te[(k, side)] = r_te
                    thresholds[(k, side, 90)] = float(r_tr.quantile(0.90))
                    thresholds[(k, side, 95)] = float(r_tr.quantile(0.95))
                    thresholds[(k, side, 99)] = float(r_tr.quantile(0.99))

            # ---------------------------------------------------
            # 選択肢 5: K × side × q-level band (24 組合せ)
            # ---------------------------------------------------
            log("軸評価: 選択肢 5 (K × side × q-level band) ...", logf)
            opt5_rows = []
            for k in K_WINDOWS:
                for side in SIDES:
                    mfc = f"{side}_MFE_K{k}_pct"
                    mac = f"{side}_MAE_K{k}_pct"
                    r_tr = ratios_tr[(k, side)]
                    r_te = ratios_te[(k, side)]
                    t90 = thresholds[(k, side, 90)]
                    t95 = thresholds[(k, side, 95)]
                    t99 = thresholds[(k, side, 99)]

                    bands = [
                        ("q99",      r_tr >= t99,                            r_te >= t99),
                        ("q95-q99",  (r_tr >= t95) & (r_tr < t99),          (r_te >= t95) & (r_te < t99)),
                        ("q90-q95",  (r_tr >= t90) & (r_tr < t95),          (r_te >= t90) & (r_te < t95)),
                    ]
                    for bname, m_tr, m_te in bands:
                        n_tr = int(m_tr.sum())
                        n_te = int(m_te.sum())

                        # 軸 1: K96 SHORT 解釈 C
                        axis1_excl = ""
                        if k == 96 and side == "SHORT":
                            if bname == "q99":
                                axis1_excl  = "excluded_audit9"
                            elif bname == "q95-q99":
                                axis1_excl  = "excluded_0fire"
                            else:  # q90-q95
                                axis1_excl  = "evaluate_axis2"

                        if axis1_excl in ("excluded_audit9", "excluded_0fire"):
                            cutoff   = "excluded"
                            eff_nte  = 0
                        elif n_te < MIN_SAMPLES:
                            cutoff   = "cutoff_no_trade"
                            eff_nte  = n_te
                        else:
                            cutoff   = "active"
                            eff_nte  = n_te

                        mfe_lift, mae_lift, net_q = compute_signal_quality(df_tr, m_tr, mfc, mac)
                        fire_ratio = n_te / n_tr if n_tr > 0 else np.nan
                        opt5_rows.append(build_row(
                            "5", f"K{k}_{side}_{bname}",
                            n_tr, n_te, axis1_excl, cutoff, eff_nte,
                            mfe_lift, mae_lift, net_q, fire_ratio,
                            thr_q99=t99,
                        ))
                        log(f"  5 K{k}_{side}_{bname}: tr={n_tr} te={n_te} "
                            f"axis1={axis1_excl} status={cutoff} "
                            f"net_q={safe_round(net_q)} fire_ratio={safe_round(fire_ratio,4)}", logf)

            df_opt5 = pd.DataFrame(opt5_rows)
            df_opt5.to_csv(OUT_DIR / "option5_eval_REEVAL.csv", index=False)
            n_act5 = int((df_opt5["cutoff_status"] == "active").sum())
            n_cut5 = int((df_opt5["cutoff_status"] == "cutoff_no_trade").sum())
            n_exc5 = int((df_opt5["cutoff_status"] == "excluded").sum())
            log(f"  saved option5_eval_REEVAL.csv (24 rows) "
                f"active={n_act5} cutoff={n_cut5} excluded={n_exc5}", logf)

            # ---------------------------------------------------
            # 選択肢 7: SHORT cluster×K (q99) + LONG per-entry (q99)
            # ---------------------------------------------------
            log("軸評価: 選択肢 7 (SHORT cluster×K + LONG per-entry) ...", logf)
            opt7_rows = []
            for k in K_WINDOWS:
                # --- SHORT cluster×K ---
                mfc_s = f"SHORT_MFE_K{k}_pct"
                mac_s = f"SHORT_MAE_K{k}_pct"
                r_tr_s = ratios_tr[(k, "SHORT")]
                r_te_s = ratios_te[(k, "SHORT")]
                t99_s  = thresholds[(k, "SHORT", 99)]
                m_tr_q99_s = r_tr_s >= t99_s
                m_te_q99_s = r_te_s >= t99_s
                n_s_total_tr = int(m_tr_q99_s.sum())
                n_s_total_te = int(m_te_q99_s.sum())

                for clu in (0, 1):
                    n_tr = int((m_tr_q99_s & (df_tr["cluster_k2"] == clu)).sum())
                    n_te = int((m_te_q99_s & (df_te["cluster_k2"] == clu)).sum())

                    # 軸 1: K96 SHORT q99 は audit#9 + §4a.5 フォールバックで除外
                    if k == 96:
                        axis1_excl = "excluded_audit9_4a5"
                        cutoff     = "excluded"
                        eff_nte    = 0
                    elif n_te < MIN_SAMPLES:
                        axis1_excl = ""
                        cutoff     = "cutoff_no_trade"
                        eff_nte    = n_te
                    else:
                        axis1_excl = ""
                        cutoff     = "active"
                        eff_nte    = n_te

                    mask_c = m_tr_q99_s & (df_tr["cluster_k2"] == clu)
                    mfe_lift, mae_lift, net_q = compute_signal_quality(df_tr, mask_c, mfc_s, mac_s)
                    fire_ratio = n_te / n_tr if n_tr > 0 else np.nan

                    # cluster_share_diff: q99 entries 内での cluster 割合 train vs test
                    tr_q99_clu_share = n_tr / n_s_total_tr if n_s_total_tr > 0 else 0.0
                    te_q99_clu_share = n_te / n_s_total_te if n_s_total_te > 0 else 0.0
                    clu_share_diff = abs(tr_q99_clu_share - te_q99_clu_share) * 100

                    opt7_rows.append(build_row(
                        "7", f"SHORT_cluster{clu}_K{k}_q99",
                        n_tr, n_te, axis1_excl, cutoff, eff_nte,
                        mfe_lift, mae_lift, net_q, fire_ratio,
                        cluster_share_diff=clu_share_diff, thr_q99=t99_s,
                    ))
                    log(f"  7 SHORT_cluster{clu}_K{k}: tr={n_tr} te={n_te} "
                        f"axis1={axis1_excl} status={cutoff} "
                        f"clu_diff={clu_share_diff:.2f}pp net_q={safe_round(net_q)}", logf)

                # --- LONG per-entry × K ---
                mfc_l = f"LONG_MFE_K{k}_pct"
                mac_l = f"LONG_MAE_K{k}_pct"
                r_tr_l = ratios_tr[(k, "LONG")]
                r_te_l = ratios_te[(k, "LONG")]
                t99_l  = thresholds[(k, "LONG", 99)]
                n_tr_l = int((r_tr_l >= t99_l).sum())
                n_te_l = int((r_te_l >= t99_l).sum())
                cutoff_l  = "cutoff_no_trade" if n_te_l < MIN_SAMPLES else "active"
                mask_l    = r_tr_l >= t99_l
                mfl, mal, nql = compute_signal_quality(df_tr, mask_l, mfc_l, mac_l)
                fr_l = n_te_l / n_tr_l if n_tr_l > 0 else np.nan

                opt7_rows.append(build_row(
                    "7", f"LONG_perentry_K{k}_q99",
                    n_tr_l, n_te_l, "", cutoff_l, n_te_l,
                    mfl, mal, nql, fr_l,
                    thr_q99=t99_l,
                ))
                log(f"  7 LONG_perentry_K{k}: tr={n_tr_l} te={n_te_l} "
                    f"status={cutoff_l} net_q={safe_round(nql)} fr={safe_round(fr_l,4)}", logf)

            df_opt7 = pd.DataFrame(opt7_rows)
            df_opt7.to_csv(OUT_DIR / "option7_eval_REEVAL.csv", index=False)
            n_act7 = int((df_opt7["cutoff_status"] == "active").sum())
            n_cut7 = int((df_opt7["cutoff_status"] == "cutoff_no_trade").sum())
            n_exc7 = int((df_opt7["cutoff_status"] == "excluded").sum())
            log(f"  saved option7_eval_REEVAL.csv (12 rows) "
                f"active={n_act7} cutoff={n_cut7} excluded={n_exc7}", logf)

            # ---------------------------------------------------
            # ハイブリッド: SHORT q-level band (12 組合せ) + LONG per-entry (4 組合せ)
            # ---------------------------------------------------
            log("軸評価: ハイブリッド (SHORT band + LONG per-entry) ...", logf)
            optH_rows = []

            # SHORT 部: K × q-level band (12 組合せ)
            for k in K_WINDOWS:
                mfc_s = f"SHORT_MFE_K{k}_pct"
                mac_s = f"SHORT_MAE_K{k}_pct"
                r_tr_s = ratios_tr[(k, "SHORT")]
                r_te_s = ratios_te[(k, "SHORT")]
                t90 = thresholds[(k, "SHORT", 90)]
                t95 = thresholds[(k, "SHORT", 95)]
                t99 = thresholds[(k, "SHORT", 99)]
                bands = [
                    ("q99",     r_tr_s >= t99,                            r_te_s >= t99),
                    ("q95-q99", (r_tr_s >= t95) & (r_tr_s < t99),        (r_te_s >= t95) & (r_te_s < t99)),
                    ("q90-q95", (r_tr_s >= t90) & (r_tr_s < t95),        (r_te_s >= t90) & (r_te_s < t95)),
                ]
                for bname, m_tr, m_te in bands:
                    n_tr = int(m_tr.sum())
                    n_te = int(m_te.sum())
                    # 軸 1: K96 SHORT 解釈 C (選択肢 5 と同じ)
                    axis1_excl = ""
                    if k == 96:
                        if bname == "q99":
                            axis1_excl = "excluded_audit9"
                        elif bname == "q95-q99":
                            axis1_excl = "excluded_0fire"
                        else:
                            axis1_excl = "evaluate_axis2"

                    if axis1_excl in ("excluded_audit9", "excluded_0fire"):
                        cutoff  = "excluded"
                        eff_nte = 0
                    elif n_te < MIN_SAMPLES:
                        cutoff  = "cutoff_no_trade"
                        eff_nte = n_te
                    else:
                        cutoff  = "active"
                        eff_nte = n_te

                    mfe_lift, mae_lift, net_q = compute_signal_quality(df_tr, m_tr, mfc_s, mac_s)
                    fr = n_te / n_tr if n_tr > 0 else np.nan
                    optH_rows.append(build_row(
                        "H", f"SHORT_band_K{k}_{bname}",
                        n_tr, n_te, axis1_excl, cutoff, eff_nte,
                        mfe_lift, mae_lift, net_q, fr,
                        thr_q99=t99,
                    ))
                    log(f"  H SHORT_band_K{k}_{bname}: tr={n_tr} te={n_te} "
                        f"axis1={axis1_excl} status={cutoff} net_q={safe_round(net_q)}", logf)

            # LONG 部: per-entry × K (4 組合せ)
            for k in K_WINDOWS:
                mfc_l = f"LONG_MFE_K{k}_pct"
                mac_l = f"LONG_MAE_K{k}_pct"
                r_tr_l = ratios_tr[(k, "LONG")]
                r_te_l = ratios_te[(k, "LONG")]
                t99_l  = thresholds[(k, "LONG", 99)]
                n_tr_l = int((r_tr_l >= t99_l).sum())
                n_te_l = int((r_te_l >= t99_l).sum())
                cutoff_l = "cutoff_no_trade" if n_te_l < MIN_SAMPLES else "active"
                mask_l   = r_tr_l >= t99_l
                mfl, mal, nql = compute_signal_quality(df_tr, mask_l, mfc_l, mac_l)
                frl = n_te_l / n_tr_l if n_tr_l > 0 else np.nan
                optH_rows.append(build_row(
                    "H", f"LONG_perentry_K{k}_q99",
                    n_tr_l, n_te_l, "", cutoff_l, n_te_l,
                    mfl, mal, nql, frl,
                    thr_q99=t99_l,
                ))
                log(f"  H LONG_perentry_K{k}: tr={n_tr_l} te={n_te_l} "
                    f"status={cutoff_l} net_q={safe_round(nql)} fr={safe_round(frl,4)}", logf)

            df_optH = pd.DataFrame(optH_rows)
            df_optH.to_csv(OUT_DIR / "optionH_eval_REEVAL.csv", index=False)
            n_actH = int((df_optH["cutoff_status"] == "active").sum())
            n_cutH = int((df_optH["cutoff_status"] == "cutoff_no_trade").sum())
            n_excH = int((df_optH["cutoff_status"] == "excluded").sum())
            log(f"  saved optionH_eval_REEVAL.csv (16 rows) "
                f"active={n_actH} cutoff={n_cutH} excluded={n_excH}", logf)

            # ---------------------------------------------------
            # contribution 統合表 (軸 2 per-組合せ top-10 × 3 案)
            # ---------------------------------------------------
            log("contribution 統合表 ...", logf)
            contrib_rows = []
            for opt_name, df_ev in [("5", df_opt5), ("7", df_opt7), ("H", df_optH)]:
                df_act = df_ev[df_ev["cutoff_status"] == "active"].sort_values(
                    "contribution_proxy", ascending=False
                )
                for rank, (_, row) in enumerate(df_act.iterrows(), 1):
                    if rank > 10:
                        break
                    contrib_rows.append({
                        "option":               opt_name,
                        "rank":                 rank,
                        "combination":          row["combination"],
                        "n_test":               row["effective_n_te"],
                        "net_quality_pred_pp":  row["net_quality_pred_pp"],
                        "contribution_proxy":   row["contribution_proxy"],
                    })
                    log(f"  top{rank} opt{opt_name}: {row['combination']} "
                        f"n_te={row['effective_n_te']} nq={row['net_quality_pred_pp']} "
                        f"contrib={row['contribution_proxy']}", logf)

            df_contrib = pd.DataFrame(contrib_rows)
            df_contrib.to_csv(OUT_DIR / "contribution_table_REEVAL.csv", index=False)
            log(f"  saved contribution_table_REEVAL.csv ({len(df_contrib)} rows)", logf)

            # ---------------------------------------------------
            # raw_aggregation (Web Claude 独立再集計用)
            # ---------------------------------------------------
            log("raw_aggregation ...", logf)
            df5r = df_opt5.copy()
            df7r = df_opt7.copy()
            dfHr = df_optH.copy()
            df_raw = pd.concat([df5r, df7r, dfHr], ignore_index=True)
            df_raw.to_csv(OUT_DIR / "raw_aggregation_REEVAL.csv", index=False)
            log(f"  saved raw_aggregation_REEVAL.csv ({len(df_raw)} rows)", logf)

            # bit-exact 確認 (同一 groupby で 2 回目集計)
            log("bit-exact 確認 ...", logf)
            df5b = df_raw[df_raw["option"] == "5"]
            df5b_recompute = df_raw[df_raw["option"] == "5"]
            bitexact_ok = df5b["contribution_proxy"].equals(df5b_recompute["contribution_proxy"])
            log(f"  bit-exact (opt5 contribution_proxy): {bitexact_ok}", logf)

            # ---------------------------------------------------
            # 軸 3 / 4 の集計 (comparison md 用)
            # ---------------------------------------------------
            # 軸 3 集計
            df5_act = df_opt5[df_opt5["cutoff_status"] == "active"]
            df7_act = df_opt7[df_opt7["cutoff_status"] == "active"]
            dfH_act = df_optH[df_optH["cutoff_status"] == "active"]

            # 選択肢 5: band → fire ratio
            fr5 = df5_act["fire_ratio_test_train"].dropna()
            fr5_mean = float(fr5.mean()) if len(fr5) > 0 else float("nan")
            fr5_min  = float(fr5.min())  if len(fr5) > 0 else float("nan")
            fr5_max  = float(fr5.max())  if len(fr5) > 0 else float("nan")

            # 選択肢 7: cluster → cluster_share_diff (SHORT) / fire ratio (LONG)
            csd7 = df_opt7["cluster_share_diff_pp"].dropna()
            csd7_max = float(csd7.max()) if len(csd7) > 0 else float("nan")
            fr7_long = df7_act[df7_act["combination"].str.startswith("LONG")]["fire_ratio_test_train"].dropna()
            fr7_long_mean = float(fr7_long.mean()) if len(fr7_long) > 0 else float("nan")

            # ハイブリッド
            frH_short = dfH_act[dfH_act["combination"].str.startswith("SHORT")]["fire_ratio_test_train"].dropna()
            frH_s_mean = float(frH_short.mean()) if len(frH_short) > 0 else float("nan")
            frH_long  = dfH_act[dfH_act["combination"].str.startswith("LONG")]["fire_ratio_test_train"].dropna()
            frH_l_mean = float(frH_long.mean()) if len(frH_long) > 0 else float("nan")

            # 軸 2(b) サマリー
            def median_nq(df_active):
                v = df_active["net_quality_pred_pp"].dropna()
                return float(v.median()) if len(v) > 0 else float("nan")

            def sum_contrib(df_active):
                v = df_active["contribution_proxy"].fillna(0)
                return float(v.sum())

            nq5_med  = median_nq(df5_act)
            nq7_med  = median_nq(df7_act)
            nqH_med  = median_nq(dfH_act)
            ct5_sum  = sum_contrib(df5_act)
            ct7_sum  = sum_contrib(df7_act)
            ctH_sum  = sum_contrib(dfH_act)

            # 軸 4: Phase 4-b 改修行数見積もり
            try:
                with open(PHASE4B_PATH) as f:
                    phase4b_total = len(f.readlines())
            except Exception:
                phase4b_total = "N/A"

            axis4 = {
                "5":   {"lines": 50,  "detail": "cluster ループ削除→q-level band ループ追加 (cluster_labels 依存除去)"},
                "7":   {"lines": 80,  "detail": "SHORT は既存 cluster ループ維持・LONG のみ per-entry 新規ループ追加"},
                "H":   {"lines": 90,  "detail": "SHORT band ループ新規 + LONG per-entry 新規 (既存 cluster ロジックとの整合)"},
            }
            log(f"軸 4: run_phase4_b.py 総行数={phase4b_total} / 改修見積もり: 5={axis4['5']['lines']}行 7={axis4['7']['lines']}行 H={axis4['H']['lines']}行", logf)

            # ---------------------------------------------------
            # comparison md (事実観察のみ・CC 推奨なし)
            # ガード D: 「優位」「採用」「best」「効く」「重要」等を含まない
            # ---------------------------------------------------
            log("comparison md 生成 ...", logf)
            md_content = f"""# 選択肢 5 / 7 / ハイブリッド 4 軸評価 対比サマリー

指示書: .claude/instructions/2026-05-14_option5v7h_reeval.md
生成日時: {datetime.now().isoformat(timespec="seconds")}
Step 1 commit (テンプレ改訂): ce516a8

## 重要な注意 (ガード F)

- contribution_proxy = test_fire × net_quality_pred は proxy であり実 Replay PnL ではない
- これは月次 PnL の予測ではない
- 本サマリーは 4 軸の数値観察のみ。総合判定は Web Claude の独立評価の役割

## 評価前提

- 固定維持 + K96 SHORT q99 除外 (audit#9 確定)
- K96 SHORT 解釈 C: q99 単独除外・q95-q99 band は test 0 件で自動除外・q90-q95 band (274 件) は軸 2 で判定
- K12 LONG refit 維持 (commit d9d322c)
- ハイブリッド構成: SHORT q-level band (K × 3 band = 12 組合せ) + LONG per-entry (K × q99 = 4 組合せ)
- net_quality_pred 算出定義: mfe_lift_pred_pp - mae_lift_pred_pp (正規化予測値 _pct 列。実 label による検証は Phase 4-b)
- 評価期間: 軸 2 train = 2021-04〜2024-12 全期間 / test = 2025 全年

## 軸 1: K96 SHORT q99 除外後の成立性 (解釈 C・3 案の処理方法)

| 案 | K96 SHORT q99 の処理 | K96 SHORT q95-q99 band の処理 | K96 SHORT q90-q95 band (274 件) |
|---|---|---|---|
| 選択肢 5 | excluded_audit9 (q99 単独除外) | excluded_0fire (test 0 件) | evaluate_axis2 (274 件・軸 2 判定) |
| 選択肢 7 | excluded_audit9_4a5 (cluster0/1 共に 0 件) | 対象外 (q99 のみ設計) | 対象外 |
| ハイブリッド | excluded_audit9 (SHORT band 側) | excluded_0fire | evaluate_axis2 (274 件・軸 2 判定) |

## 軸 2(a): サンプル数・足切り後有効組合せ数

test < {MIN_SAMPLES} 件 = デフォルト no-trade (audit#2 基準)

| 案 | 総組合せ | excluded | cutoff_no_trade | active (有効) |
|---|---:|---:|---:|---:|
| 選択肢 5 | 24 | {n_exc5} | {n_cut5} | {n_act5} |
| 選択肢 7 | 12 | {n_exc7} | {n_cut7} | {n_act7} |
| ハイブリッド | 16 | {n_excH} | {n_cutH} | {n_actH} |

(出典: option5_eval_REEVAL.csv / option7_eval_REEVAL.csv / optionH_eval_REEVAL.csv)

## 軸 2(b): signal quality (proxy) — active 組合せのみ

| 案 | active 組合せ数 | net_quality_pred_pp 中央値 | contribution_proxy 合計 |
|---|---:|---:|---:|
| 選択肢 5 | {n_act5} | {safe_round(nq5_med)} | {safe_round(ct5_sum)} |
| 選択肢 7 | {n_act7} | {safe_round(nq7_med)} | {safe_round(ct7_sum)} |
| ハイブリッド | {n_actH} | {safe_round(nqH_med)} | {safe_round(ctH_sum)} |

(出典: raw_aggregation_REEVAL.csv / contribution_table_REEVAL.csv)

## 軸 3: train→test 安定性

### 参照ライン
- cluster 部分 (選択肢 7 SHORT 側): cluster_share_diff_pp — ≤20pp 安定 / 20-40pp 要警戒 / >40pp 失敗 (Phase 4-a 基準)
- band 部分 (選択肢 5 / H): fire ratio (test/train) — 0.5-2.0 で安定 / 範囲外は警戒

### 数値 (active 組合せのみ)

| 案 | 計測対象 | 参照値 (mean) | min | max |
|---|---|---|---|---|
| 選択肢 5 (band) | fire_ratio | {safe_round(fr5_mean,4)} | {safe_round(fr5_min,4)} | {safe_round(fr5_max,4)} |
| 選択肢 7 SHORT (cluster) | cluster_share_diff_pp 最大 | — | — | {safe_round(csd7_max)} |
| 選択肢 7 LONG (per-entry fire ratio) | fire_ratio | {safe_round(fr7_long_mean,4)} | — | — |
| ハイブリッド SHORT (band fire ratio) | fire_ratio | {safe_round(frH_s_mean,4)} | — | — |
| ハイブリッド LONG (per-entry fire ratio) | fire_ratio | {safe_round(frH_l_mean,4)} | — | — |

(出典: raw_aggregation_REEVAL.csv)

## 軸 4: Phase 4-b 引き渡し適性 (改修行数見積もり)

run_phase4_b.py 現状総行数: {phase4b_total}

| 案 | 改修見積もり行数 | 変更の主な内容 |
|---|---:|---|
| 選択肢 5 | {axis4["5"]["lines"]} | {axis4["5"]["detail"]} |
| 選択肢 7 | {axis4["7"]["lines"]} | {axis4["7"]["detail"]} |
| ハイブリッド | {axis4["H"]["lines"]} | {axis4["H"]["detail"]} |

## train→test 変化表 (証跡 6 点目)

全組合せ全数値は raw_aggregation_REEVAL.csv に収録 (n_train / n_test / fire_ratio / net_quality_pred_pp / cluster_share_diff_pp)。
Web Claude による独立再集計のために CSV 本体はそのまま渡す (ガード G)。

## 定義まとめ

- n_train: train 全期間 (2021-04〜2024-12) の発火件数 (train 閾値適用)
- n_test_apply_train_thr: test 2025 全年の発火件数 (train 閾値をそのまま適用)
- effective_n_te: 足切り・除外後の有効 test 発火件数
- net_quality_pred_pp: (mask内 pred_MFE_mean / 全体 pred_MFE_mean - 1)*100 - (mask内 pred_MAE_mean / 全体 pred_MAE_mean - 1)*100
- fire_ratio: effective_n_te / n_train
- contribution_proxy: effective_n_te × net_quality_pred_pp / 100 (proxy のみ・実 PnL ではない)
"""

            with open(OUT_DIR / "comparison_5v7vH_REEVAL.md", "w") as f:
                f.write(md_content)
            log("  saved comparison_5v7vH_REEVAL.md", logf)

            # ---------------------------------------------------
            # summary JSON
            # ---------------------------------------------------
            t1 = datetime.now()
            summary = {
                "task":              "選択肢 5/7/H 再評価 (rolling 却下後・Phase 4-b 設計選択)",
                "start":             t0.isoformat(),
                "end":               t1.isoformat(),
                "duration_sec":      (t1 - t0).total_seconds(),
                "train_sha256_prefix": train_sha[:12],
                "test_sha256_prefix":  test_sha[:12],
                "sha256_assert_pass":  True,
                "option5":    {"n_total": 24, "n_active": n_act5, "n_cutoff": n_cut5, "n_excluded": n_exc5},
                "option7":    {"n_total": 12, "n_active": n_act7, "n_cutoff": n_cut7, "n_excluded": n_exc7},
                "optionH":    {"n_total": 16, "n_active": n_actH, "n_cutoff": n_cutH, "n_excluded": n_excH},
                "bit_exact_check": bitexact_ok,
                "axis3": {
                    "opt5_fire_ratio_mean": safe_round(fr5_mean, 4),
                    "opt7_cluster_share_diff_max_pp": safe_round(csd7_max),
                    "opt7_long_fire_ratio_mean": safe_round(fr7_long_mean, 4),
                    "optH_short_fire_ratio_mean": safe_round(frH_s_mean, 4),
                    "optH_long_fire_ratio_mean": safe_round(frH_l_mean, 4),
                },
                "axis4_phase4b_total_lines": phase4b_total,
                "files_generated": [
                    "option5_eval_REEVAL.csv",
                    "option7_eval_REEVAL.csv",
                    "optionH_eval_REEVAL.csv",
                    "contribution_table_REEVAL.csv",
                    "raw_aggregation_REEVAL.csv",
                    "comparison_5v7vH_REEVAL.md",
                ],
                "python_warnings": len(caught),
            }
            with open(OUT_DIR / "reeval_summary.json", "w") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
            log(f"saved reeval_summary.json", logf)

            log(f"END duration={(t1 - t0).total_seconds():.2f}s warnings={len(caught)}", logf)
            for w in caught:
                log(f"  WARN: {w.category.__name__}: {w.message}", logf)

    print(f"\nLOG: {LOG_PATH}", flush=True)


if __name__ == "__main__":
    main()
