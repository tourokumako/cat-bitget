"""
clustering 廃止後の設計選択肢評価 (選択肢 1/4/5/6/7・既存データ試算)

指示書: .claude/instructions/2026-05-14_clustering_alternatives_eval.md

Steps:
  1: 各選択肢の組合せ数 + train サンプル数 + train→test 変化
  2-A: SHORT q90/q95/q99 一致率 (既存 k=2)
  2-B: SHORT 足のみで k=2 再 fit → train/test share 比較
  2-C: SHORT 単独 k=2,3,4 再選定
  3-A: per-entry Exit 算式定義可否 (テキスト spec)
  3-B: K12 LONG MFE_lift マイナス問題の per-entry 影響
  4: 2025-01/09 暴騰局面の月別集中度
  5: 比較表生成 + CC 推奨
"""

import hashlib
import json
import warnings
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "results" / "priority_rebuild"
NORM_DIR = DATA_DIR / "ml_phase4_a_norm"
OUT_DIR = DATA_DIR / "clustering_alternatives"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_NORM_PATH = NORM_DIR / "predictions_train_normalized.parquet"
TEST_NORM_PATH = NORM_DIR / "predictions_test2025_normalized.parquet"
LABELS_TRAIN = DATA_DIR / "labels_mfe_mae_train_2021_2024.parquet"
LABELS_TEST = DATA_DIR / "labels_mfe_mae_test_2025.parquet"
K2_SCALER = NORM_DIR / "scaler_train_2021_2024.joblib"
K2_KM = NORM_DIR / "kmeans_k2_train_2021_2024.joblib"

LABEL_COLS = [
    f"{side}_{kind}_K{k}"
    for k in (12, 24, 48, 96)
    for side in ("LONG", "SHORT")
    for kind in ("MFE", "MAE")
]
PCT_COLS = [c + "_pct" for c in LABEL_COLS]
SHORT_PCT_COLS = [c for c in PCT_COLS if c.startswith("SHORT")]
LONG_PCT_COLS = [c for c in PCT_COLS if c.startswith("LONG")]
K_WINDOWS = (12, 24, 48, 96)
SIDES = ("LONG", "SHORT")
Q_LEVELS = (0.90, 0.95, 0.99)
RANDOM_STATE = 42
ATR_BUCKETS = 3


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


def main():
    t0 = datetime.now()
    TS = t0.strftime("%Y%m%dT%H%M%SZ")
    LOG_PATH = OUT_DIR / f"alternatives_log_{TS}.txt"

    with open(LOG_PATH, "w") as logf:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")

            log(f"START at {t0.isoformat()}", logf)
            log(f"output: {OUT_DIR}", logf)

            # 物理証跡 1
            train_sha = sha256_file(TRAIN_NORM_PATH)
            test_sha = sha256_file(TEST_NORM_PATH)
            log(f"  train_norm sha256: {train_sha[:12]}", logf)
            log(f"  test_norm  sha256: {test_sha[:12]}", logf)

            log("Load data ...", logf)
            df_train = pd.read_parquet(TRAIN_NORM_PATH).sort_index()
            df_test = pd.read_parquet(TEST_NORM_PATH).sort_index()
            log(f"  train: {len(df_train)} test: {len(df_test)}", logf)
            assert len(df_train) == 394753
            assert len(df_test) == 105120

            # 既存 k=2 cluster (16 列・LONG+SHORT 混在で fit) ロード
            scaler_full = joblib.load(K2_SCALER)
            km_full = joblib.load(K2_KM)
            X_train_full = df_train[PCT_COLS].values
            X_test_full = df_test[PCT_COLS].values
            tr_cluster_full = km_full.predict(scaler_full.transform(X_train_full))
            te_cluster_full = km_full.predict(scaler_full.transform(X_test_full))
            df_train["cluster_full_k2"] = tr_cluster_full
            df_test["cluster_full_k2"] = te_cluster_full

            # ======================================================
            # Step 1: 各選択肢の組合せ + サンプル数 + train→test
            # ======================================================
            log("Step 1: 各選択肢の組合せ + サンプル数 + train→test ...", logf)

            # ratio (MFE/MAE) を K×side ごとに先に計算
            ratios_tr = {}
            ratios_te = {}
            for k in K_WINDOWS:
                for side in SIDES:
                    mfe = f"{side}_MFE_K{k}_pct"
                    mae = f"{side}_MAE_K{k}_pct"
                    ratios_tr[(k, side)] = df_train[mfe] / df_train[mae].clip(lower=1e-9)
                    ratios_te[(k, side)] = df_test[mfe] / df_test[mae].clip(lower=1e-9)

            # ===== 選択肢 4: K × side (8 組合せ・各 q99) =====
            log("  選択肢 4: K × side q99 ...", logf)
            opt4_rows = []
            for k in K_WINDOWS:
                for side in SIDES:
                    r_tr = ratios_tr[(k, side)]
                    r_te = ratios_te[(k, side)]
                    thr_tr = r_tr.quantile(0.99)
                    n_tr = int((r_tr >= thr_tr).sum())
                    n_te = int((r_te >= thr_tr).sum())  # train 閾値を test に
                    n_te_self = int((r_te >= r_te.quantile(0.99)).sum())
                    opt4_rows.append({
                        "option": 4,
                        "combination": f"K{k}_{side}_q99",
                        "n_train_q99": n_tr,
                        "n_test_apply_train_thr": n_te,
                        "n_test_self_q99": n_te_self,
                        "train_judgment": assess_n(n_tr),
                        "test_judgment": assess_n(n_te),
                    })
            df_opt4 = pd.DataFrame(opt4_rows)
            df_opt4.to_csv(OUT_DIR / "option4_K_side_q99.csv", index=False)
            log(f"    saved option4_K_side_q99.csv (8 rows)", logf)
            log(f"    少数組合せ <100: train={int((df_opt4['n_train_q99'] < 100).sum())} / "
                f"test={int((df_opt4['n_test_apply_train_thr'] < 100).sum())}", logf)

            # ===== 選択肢 5: K × side × q-level (24 組合せ) =====
            log("  選択肢 5: K × side × q-level (q90/q95/q99 nested but split into bands) ...", logf)
            # band 定義: q99 = top 1% / q95-q99 = next 4% / q90-q95 = next 5%
            opt5_rows = []
            for k in K_WINDOWS:
                for side in SIDES:
                    r_tr = ratios_tr[(k, side)]
                    r_te = ratios_te[(k, side)]
                    thr_90 = r_tr.quantile(0.90)
                    thr_95 = r_tr.quantile(0.95)
                    thr_99 = r_tr.quantile(0.99)
                    bands = [
                        ("q99", (r_tr >= thr_99), (r_te >= thr_99)),
                        ("q95-q99", (r_tr >= thr_95) & (r_tr < thr_99), (r_te >= thr_95) & (r_te < thr_99)),
                        ("q90-q95", (r_tr >= thr_90) & (r_tr < thr_95), (r_te >= thr_90) & (r_te < thr_95)),
                    ]
                    for band_name, mask_tr, mask_te in bands:
                        n_tr = int(mask_tr.sum())
                        n_te = int(mask_te.sum())
                        opt5_rows.append({
                            "option": 5,
                            "combination": f"K{k}_{side}_{band_name}",
                            "n_train": n_tr,
                            "n_test_apply_train_thr": n_te,
                            "train_judgment": assess_n(n_tr),
                            "test_judgment": assess_n(n_te),
                        })
            df_opt5 = pd.DataFrame(opt5_rows)
            df_opt5.to_csv(OUT_DIR / "option5_K_side_qlevel.csv", index=False)
            log(f"    saved option5_K_side_qlevel.csv (24 rows)", logf)
            log(f"    少数組合せ <100: train={int((df_opt5['n_train'] < 100).sum())} / "
                f"test={int((df_opt5['n_test_apply_train_thr'] < 100).sum())}", logf)

            # ===== 選択肢 6: ATR bucket × K × side =====
            # ATR proxy = (LONG_MFE_K12_pct + LONG_MAE_K12_pct)/2 (volatility approximation)
            log("  選択肢 6: ATR bucket × K × side q99 ...", logf)
            atr_proxy_tr = (df_train["LONG_MFE_K12_pct"] + df_train["LONG_MAE_K12_pct"]) / 2
            atr_proxy_te = (df_test["LONG_MFE_K12_pct"] + df_test["LONG_MAE_K12_pct"]) / 2
            # train tertile thresholds
            atr_thr1 = atr_proxy_tr.quantile(1/3)
            atr_thr2 = atr_proxy_tr.quantile(2/3)
            log(f"    ATR proxy thresholds (train): low<={atr_thr1:.4f} / mid<={atr_thr2:.4f} / high>", logf)

            def atr_bucket(series, thr1, thr2):
                b = pd.Series(index=series.index, dtype=object)
                b.loc[series <= thr1] = "low"
                b.loc[(series > thr1) & (series <= thr2)] = "mid"
                b.loc[series > thr2] = "high"
                return b

            atr_bk_tr = atr_bucket(atr_proxy_tr, atr_thr1, atr_thr2)
            atr_bk_te = atr_bucket(atr_proxy_te, atr_thr1, atr_thr2)
            log(f"    train bucket dist: {atr_bk_tr.value_counts().to_dict()}", logf)
            log(f"    test  bucket dist: {atr_bk_te.value_counts().to_dict()}", logf)

            opt6_rows = []
            for bkt in ("low", "mid", "high"):
                m_tr_bk = atr_bk_tr == bkt
                m_te_bk = atr_bk_te == bkt
                for k in K_WINDOWS:
                    for side in SIDES:
                        r_tr = ratios_tr[(k, side)]
                        r_te = ratios_te[(k, side)]
                        thr = r_tr[m_tr_bk].quantile(0.99) if m_tr_bk.sum() > 0 else np.nan
                        n_tr = int((r_tr[m_tr_bk] >= thr).sum()) if not np.isnan(thr) else 0
                        n_te = int((r_te[m_te_bk] >= thr).sum()) if not np.isnan(thr) else 0
                        opt6_rows.append({
                            "option": 6,
                            "combination": f"ATR_{bkt}_K{k}_{side}_q99",
                            "n_train_in_bucket": int(m_tr_bk.sum()),
                            "n_train_q99_in_bucket": n_tr,
                            "n_test_in_bucket": int(m_te_bk.sum()),
                            "n_test_q99_in_bucket": n_te,
                            "train_judgment": assess_n(n_tr),
                            "test_judgment": assess_n(n_te),
                        })
            df_opt6 = pd.DataFrame(opt6_rows)
            df_opt6.to_csv(OUT_DIR / "option6_ATR_K_side.csv", index=False)
            log(f"    saved option6_ATR_K_side.csv (24 rows)", logf)
            log(f"    少数組合せ <100: train={int((df_opt6['n_train_q99_in_bucket'] < 100).sum())} / "
                f"test={int((df_opt6['n_test_q99_in_bucket'] < 100).sum())}", logf)

            # ===== 選択肢 7: SHORT は cluster (既存 k=2) × K + LONG は per-entry =====
            log("  選択肢 7: SHORT 2 cluster × 4 K + LONG 4 K per-entry ...", logf)
            opt7_rows = []
            for k in K_WINDOWS:
                # SHORT cluster × K
                r_tr = ratios_tr[(k, "SHORT")]
                r_te = ratios_te[(k, "SHORT")]
                thr_tr = r_tr.quantile(0.99)
                m_tr_q99 = r_tr >= thr_tr
                m_te_q99 = r_te >= thr_tr
                for c in (0, 1):
                    n_tr = int((m_tr_q99 & (df_train["cluster_full_k2"] == c)).sum())
                    n_te = int((m_te_q99 & (df_test["cluster_full_k2"] == c)).sum())
                    opt7_rows.append({
                        "option": 7,
                        "combination": f"SHORT_cluster{c}_K{k}_q99",
                        "n_train_q99": n_tr,
                        "n_test_apply_train_thr": n_te,
                        "train_judgment": assess_n(n_tr),
                        "test_judgment": assess_n(n_te),
                    })
                # LONG per-entry per K (no aggregation per cluster・count q99 fires only)
                r_tr_L = ratios_tr[(k, "LONG")]
                r_te_L = ratios_te[(k, "LONG")]
                thr_tr_L = r_tr_L.quantile(0.99)
                n_tr_L = int((r_tr_L >= thr_tr_L).sum())
                n_te_L = int((r_te_L >= thr_tr_L).sum())
                opt7_rows.append({
                    "option": 7,
                    "combination": f"LONG_perentry_K{k}_q99",
                    "n_train_q99": n_tr_L,
                    "n_test_apply_train_thr": n_te_L,
                    "train_judgment": assess_n(n_tr_L),
                    "test_judgment": assess_n(n_te_L),
                })
            df_opt7 = pd.DataFrame(opt7_rows)
            df_opt7.to_csv(OUT_DIR / "option7_short_clu_long_perentry.csv", index=False)
            log(f"    saved option7_short_clu_long_perentry.csv (12 rows)", logf)
            log(f"    少数組合せ <100: train={int((df_opt7['n_train_q99'] < 100).sum())} / "
                f"test={int((df_opt7['n_test_apply_train_thr'] < 100).sum())}", logf)

            # ======================================================
            # Step 2-A: SHORT q90/q95/q99 cluster 一致率 (既存 k=2)
            # ======================================================
            log("Step 2-A: SHORT q90/q95/q99 cluster 一致率 (既存 16-col k=2) ...", logf)
            s2a_rows = []
            for k in K_WINDOWS:
                r_tr = ratios_tr[(k, "SHORT")]
                r_te = ratios_te[(k, "SHORT")]
                for q in Q_LEVELS:
                    thr_tr = r_tr.quantile(q)
                    thr_te = r_te.quantile(q)
                    m_tr = r_tr >= thr_tr
                    m_te = r_te >= thr_te
                    tr_dist = df_train.loc[m_tr, "cluster_full_k2"].value_counts(normalize=True).sort_index()
                    te_dist = df_test.loc[m_te, "cluster_full_k2"].value_counts(normalize=True).sort_index()
                    dom_tr = int(tr_dist.idxmax())
                    dom_te = int(te_dist.idxmax())
                    in_dom_tr = float(te_dist.get(dom_tr, 0.0))
                    s2a_rows.append({
                        "entry": f"K{k}_SHORT_q{int(q*100)}",
                        "train_dom_cluster": dom_tr,
                        "train_dom_share": round(float(tr_dist.max()), 4),
                        "test_dom_cluster": dom_te,
                        "test_dom_share": round(float(te_dist.max()), 4),
                        "test_in_train_dom_share": round(in_dom_tr, 4),
                        "match_flag": "✅" if dom_tr == dom_te else "⚠️",
                    })
            df_s2a = pd.DataFrame(s2a_rows)
            df_s2a.to_csv(OUT_DIR / "step2a_short_match_rates.csv", index=False)
            log(f"  saved step2a_short_match_rates.csv (12 rows)", logf)
            for _, row in df_s2a.iterrows():
                log(f"    {row['entry']}: train_dom={row['train_dom_cluster']} ({row['train_dom_share']:.2f}) / "
                    f"test_dom={row['test_dom_cluster']} ({row['test_dom_share']:.2f}) / "
                    f"in_dom={row['test_in_train_dom_share']:.2f} {row['match_flag']}", logf)

            # ======================================================
            # Step 2-B: SHORT 足 8 列だけで k=2 再 fit → train/test share
            # ======================================================
            log("Step 2-B: SHORT-only k=2 再 fit (SHORT_PCT_COLS 8 列) ...", logf)
            X_tr_s = df_train[SHORT_PCT_COLS].values
            X_te_s = df_test[SHORT_PCT_COLS].values
            scaler_s = StandardScaler()
            X_tr_s_scaled = scaler_s.fit_transform(X_tr_s)
            X_te_s_scaled = scaler_s.transform(X_te_s)
            km_s = KMeans(n_clusters=2, random_state=RANDOM_STATE, n_init=10)
            km_s.fit(X_tr_s_scaled)
            tr_labels_s = km_s.labels_
            te_labels_s = km_s.predict(X_te_s_scaled)
            tr_sh_s = pd.Series(tr_labels_s).value_counts(normalize=True).sort_index().to_dict()
            te_sh_s = pd.Series(te_labels_s).value_counts(normalize=True).sort_index().to_dict()
            sil_s = silhouette_score(X_tr_s_scaled, tr_labels_s, sample_size=20000, random_state=RANDOM_STATE)
            max_diff = max(abs(tr_sh_s.get(c, 0) - te_sh_s.get(c, 0)) for c in set(tr_sh_s) | set(te_sh_s)) * 100
            sum_diff = sum(abs(tr_sh_s.get(c, 0) - te_sh_s.get(c, 0)) for c in set(tr_sh_s) | set(te_sh_s)) * 100
            log(f"  SHORT-only k=2: silhouette={sil_s:.4f} inertia={km_s.inertia_:.2f} n_iter={km_s.n_iter_}", logf)
            log(f"  train shares: {tr_sh_s}", logf)
            log(f"  test  shares: {te_sh_s}", logf)
            log(f"  share_max_diff={max_diff:.2f}pp share_sum_diff={sum_diff:.2f}pp", logf)
            # bit-exact
            km_s_b = KMeans(n_clusters=2, random_state=RANDOM_STATE, n_init=10)
            km_s_b.fit(X_tr_s_scaled)
            bit_exact_s = bool((tr_labels_s == km_s_b.labels_).all())
            log(f"  bit-exact: {bit_exact_s}", logf)

            df_train["cluster_short_k2"] = tr_labels_s
            df_test["cluster_short_k2"] = te_labels_s

            # SHORT q99 match rate (SHORT-only k=2)
            log("  SHORT-only k=2 → q99 match rate ...", logf)
            s2b_rows = []
            for k in K_WINDOWS:
                r_tr = ratios_tr[(k, "SHORT")]
                r_te = ratios_te[(k, "SHORT")]
                thr_tr = r_tr.quantile(0.99)
                thr_te = r_te.quantile(0.99)
                m_tr = r_tr >= thr_tr
                m_te = r_te >= thr_te
                tr_dist = df_train.loc[m_tr, "cluster_short_k2"].value_counts(normalize=True).sort_index()
                te_dist = df_test.loc[m_te, "cluster_short_k2"].value_counts(normalize=True).sort_index()
                dom_tr = int(tr_dist.idxmax())
                dom_te = int(te_dist.idxmax())
                in_dom_tr = float(te_dist.get(dom_tr, 0.0))
                s2b_rows.append({
                    "entry": f"K{k}_SHORT_q99",
                    "train_dom_cluster": dom_tr,
                    "test_dom_cluster": dom_te,
                    "test_in_train_dom_share": round(in_dom_tr, 4),
                    "match_flag": "✅" if dom_tr == dom_te else "⚠️",
                })
            df_s2b = pd.DataFrame(s2b_rows)
            df_s2b.to_csv(OUT_DIR / "step2b_short_only_k2_match.csv", index=False)

            # save SHORT-only k=2 artifacts
            joblib.dump(scaler_s, OUT_DIR / "scaler_short_only_train_2021_2024.joblib")
            joblib.dump(km_s, OUT_DIR / "kmeans_short_only_k2_train_2021_2024.joblib")

            # ======================================================
            # Step 2-C: SHORT 単独 k=2,3,4 再選定
            # ======================================================
            log("Step 2-C: SHORT 単独 k=2,3,4 再選定 ...", logf)
            s2c_rows = []
            for k in (2, 3, 4):
                km_k = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
                km_k.fit(X_tr_s_scaled)
                lbl_tr = km_k.labels_
                lbl_te = km_k.predict(X_te_s_scaled)
                sil = silhouette_score(X_tr_s_scaled, lbl_tr, sample_size=20000, random_state=RANDOM_STATE)
                tr_sh = pd.Series(lbl_tr).value_counts(normalize=True).sort_index().to_dict()
                te_sh = pd.Series(lbl_te).value_counts(normalize=True).sort_index().to_dict()
                mxd = max(abs(tr_sh.get(c, 0) - te_sh.get(c, 0)) for c in set(tr_sh) | set(te_sh)) * 100
                sumd = sum(abs(tr_sh.get(c, 0) - te_sh.get(c, 0)) for c in set(tr_sh) | set(te_sh)) * 100
                if mxd <= 10:
                    v = "✅"
                elif mxd <= 20:
                    v = "⚠️"
                else:
                    v = "❌"
                s2c_rows.append({
                    "k": k,
                    "silhouette": round(sil, 4),
                    "inertia": round(km_k.inertia_, 2),
                    "train_shares": json.dumps({int(c): round(v_, 4) for c, v_ in tr_sh.items()}),
                    "test_shares": json.dumps({int(c): round(v_, 4) for c, v_ in te_sh.items()}),
                    "share_max_diff_pp": round(mxd, 2),
                    "share_sum_diff_pp": round(sumd, 2),
                    "verdict": v,
                })
                log(f"  SHORT-only k={k}: sil={sil:.4f} max_diff={mxd:.2f}pp {v}", logf)
            df_s2c = pd.DataFrame(s2c_rows)
            df_s2c.to_csv(OUT_DIR / "step2c_short_only_k_selection.csv", index=False)

            # ======================================================
            # Step 3-A: per-entry Exit spec (テキスト出力)
            # ======================================================
            log("Step 3-A: per-entry Exit 算式 spec (テキスト出力) ...", logf)
            per_entry_spec = """
per-entry Exit パラメータ算式 (LONG 側・選択肢 1 / 選択肢 7 で共通):

TP 計算:
  TP_PCT(entry) = clip(pred_MFE_K{K_window} × α, TP_MIN, TP_MAX)
  - α = TP scaling factor (default 0.6・実 MFE への到達確度を加味)
  - TP_MIN = 0.001 (0.1%) ・手数料を考慮した最低 TP
  - TP_MAX = 0.03  (3%)   ・1 trade 当たり過剰な目標値の上限
  - pred_MFE_K{K_window} は本 entry の K 窓予測 MFE (%)・正規化前の絶対額に戻す場合は close × pct/100

SL 計算 (選択肢):
  Option A (動的 SL): SL_PCT(entry) = pred_MAE_K{K_window} × β (β = 1.2 で余裕を持たせる)
  Option B (固定 SL): SL_PCT = K 窓別固定 (K12=0.6%, K96=2%)
  → Phase 4-b で A/B 両方を grid 評価

Time Exit:
  N_BARS(entry) = K_window (予測窓と同じ)
  ※ §4b.3 で K×2 禁止のため K //2 か K の 2 候補

Floor 設定:
  if pred_MFE_K{K_window} × α < TP_MIN: → このエントリーを no-trade (発火スキップ)
  → 極小予測 MFE のエントリーは送らない

α・β は train PnL で最適化。entry quality 別の最適化 (q-level 別)は不要 (per-entry 化の利点を活かす)。
"""
            with open(OUT_DIR / "step3a_perentry_spec.md", "w") as f:
                f.write(per_entry_spec)
            log(f"  saved step3a_perentry_spec.md", logf)

            # ======================================================
            # Step 3-B: K12 LONG MFE_lift マイナス問題の per-entry 影響
            # ======================================================
            log("Step 3-B: K12 LONG MFE_lift マイナス問題の per-entry 影響 ...", logf)
            labels_tr = pd.read_parquet(LABELS_TRAIN).sort_index()
            common = df_train.index.intersection(labels_tr.index)
            assert len(common) == len(df_train)
            # K12 LONG q99 entries (train)
            r = ratios_tr[(12, "LONG")]
            m_q99 = r >= r.quantile(0.99)
            real_mfe_q99 = labels_tr.loc[df_train.index[m_q99], "LONG_MFE_K12"].mean()
            real_mfe_all = labels_tr["LONG_MFE_K12"].mean()
            mfe_lift_train = (real_mfe_q99 / real_mfe_all) - 1 if real_mfe_all > 0 else np.nan

            # per-entry α 推奨候補で TP 到達率を推定 (簡易版)
            pred_mfe = df_train.loc[m_q99, "LONG_MFE_K12_pct"]  # already pct
            real_mfe = labels_tr.loc[df_train.index[m_q99], "LONG_MFE_K12"]
            close_at = df_train.loc[m_q99, "close"]
            real_mfe_pct = real_mfe / close_at * 100
            # 比率 (real_pct / pred_pct) 分布
            achieve_ratio = real_mfe_pct / pred_mfe.clip(lower=1e-9)
            log(f"  K12 LONG q99 (train): n={int(m_q99.sum())}", logf)
            log(f"    real MFE mean (q99) = {real_mfe.mean():.2f} USD / all = {real_mfe_all:.2f} USD", logf)
            log(f"    MFE lift (q99 vs all) = {mfe_lift_train:+.4f} ({mfe_lift_train*100:+.2f}%)", logf)
            log(f"    real_pct / pred_pct distribution: "
                f"mean={achieve_ratio.mean():.3f} median={achieve_ratio.median():.3f} "
                f"q25={achieve_ratio.quantile(0.25):.3f} q75={achieve_ratio.quantile(0.75):.3f}", logf)

            s3b_summary = {
                "k12_long_q99_train_n": int(m_q99.sum()),
                "real_mfe_q99_mean_usd": float(real_mfe.mean()),
                "real_mfe_all_mean_usd": float(real_mfe_all),
                "mfe_lift_train": float(mfe_lift_train),
                "achieve_ratio_mean": float(achieve_ratio.mean()),
                "achieve_ratio_median": float(achieve_ratio.median()),
                "achieve_ratio_q25": float(achieve_ratio.quantile(0.25)),
                "achieve_ratio_q75": float(achieve_ratio.quantile(0.75)),
                "interpretation": (
                    "MFE lift がマイナス/小さい場合、q99 entry の実 MFE が全エントリ平均と大差ない。"
                    "per-entry で TP = pred_MFE × α を使う際、α を小さくしても (e.g. 0.3) MFE を超えるリスクは"
                    "achieve_ratio の分位点を見て調整可能。median が 1.0 を下回るなら α < median を推奨。"
                ),
            }
            with open(OUT_DIR / "step3b_k12_long_mfe_lift.json", "w") as f:
                json.dump(s3b_summary, f, indent=2, ensure_ascii=False)
            log(f"  saved step3b_k12_long_mfe_lift.json", logf)

            # ======================================================
            # Step 4: 2025-01/09 暴騰局面の月別集中度
            # ======================================================
            log("Step 4: 2025 月別の K12_LONG_q99 / K96_LONG_q99 cluster 分布 ...", logf)
            df_test_idx = df_test.copy()
            df_test_idx["year_month"] = df_test_idx.index.to_period("M").astype(str)

            # K12_LONG_q99 in test (using train threshold)
            r_te_12L = ratios_te[(12, "LONG")]
            thr_12L = ratios_tr[(12, "LONG")].quantile(0.99)
            m_te_12 = r_te_12L >= thr_12L
            r_te_96L = ratios_te[(96, "LONG")]
            thr_96L = ratios_tr[(96, "LONG")].quantile(0.99)
            m_te_96 = r_te_96L >= thr_96L
            log(f"  K12_LONG_q99 test fires (train thr): {int(m_te_12.sum())}", logf)
            log(f"  K96_LONG_q99 test fires (train thr): {int(m_te_96.sum())}", logf)

            s4_rows = []
            for ym in sorted(df_test_idx["year_month"].unique()):
                m_ym = df_test_idx["year_month"] == ym
                n_total = int(m_ym.sum())
                # K12_LONG_q99 in this month
                m12_ym = m_te_12 & m_ym
                m96_ym = m_te_96 & m_ym
                clu12 = df_test.loc[m12_ym, "cluster_full_k2"].value_counts().sort_index().to_dict()
                clu96 = df_test.loc[m96_ym, "cluster_full_k2"].value_counts().sort_index().to_dict()
                # cluster 1 share (LONG cluster in train・反転先で問題視されている)
                k12_n = int(m12_ym.sum())
                k12_clu0 = int(clu12.get(0, 0))
                k12_clu1 = int(clu12.get(1, 0))
                k96_n = int(m96_ym.sum())
                k96_clu0 = int(clu96.get(0, 0))
                k96_clu1 = int(clu96.get(1, 0))
                s4_rows.append({
                    "year_month": ym,
                    "month_n_rows": n_total,
                    "K12_LONG_q99_n": k12_n,
                    "K12_LONG_q99_clu0": k12_clu0,
                    "K12_LONG_q99_clu1": k12_clu1,
                    "K12_LONG_q99_clu1_share": round(k12_clu1 / k12_n, 4) if k12_n > 0 else 0,
                    "K96_LONG_q99_n": k96_n,
                    "K96_LONG_q99_clu0": k96_clu0,
                    "K96_LONG_q99_clu1": k96_clu1,
                    "K96_LONG_q99_clu1_share": round(k96_clu1 / k96_n, 4) if k96_n > 0 else 0,
                })
            df_s4 = pd.DataFrame(s4_rows)
            df_s4.to_csv(OUT_DIR / "step4_monthly_long_q99_cluster.csv", index=False)
            log(f"  saved step4_monthly_long_q99_cluster.csv ({len(s4_rows)} rows)", logf)
            for _, row in df_s4.iterrows():
                log(f"    {row['year_month']}: K12 fires={row['K12_LONG_q99_n']} "
                    f"(clu0={row['K12_LONG_q99_clu0']} clu1={row['K12_LONG_q99_clu1']}) / "
                    f"K96 fires={row['K96_LONG_q99_n']} "
                    f"(clu0={row['K96_LONG_q99_clu0']} clu1={row['K96_LONG_q99_clu1']})", logf)

            # ======================================================
            # Step 5: 比較表
            # ======================================================
            log("Step 5: 比較表生成 ...", logf)
            n_under100_opt4 = int((df_opt4["n_train_q99"] < 100).sum())
            n_under100_opt5 = int((df_opt5["n_train"] < 100).sum())
            n_under100_opt6 = int((df_opt6["n_train_q99_in_bucket"] < 100).sum())
            n_under100_opt7 = int((df_opt7["n_train_q99"] < 100).sum())

            comparison = [
                {
                    "axis": "組合せ数",
                    "opt1": "1 関数 (per-entry)",
                    "opt4": "8 (K×side)",
                    "opt5": "24 (K×side×qlv)",
                    "opt6": "24 (ATR×K×side)",
                    "opt7": "12 (SHORT 8 + LONG 4)",
                },
                {
                    "axis": "少数組合せ <100 (train)",
                    "opt1": "N/A",
                    "opt4": f"{n_under100_opt4}/8",
                    "opt5": f"{n_under100_opt5}/24",
                    "opt6": f"{n_under100_opt6}/24",
                    "opt7": f"{n_under100_opt7}/12",
                },
                {
                    "axis": "少数組合せ <100 (test apply)",
                    "opt1": "N/A",
                    "opt4": f"{int((df_opt4['n_test_apply_train_thr'] < 100).sum())}/8",
                    "opt5": f"{int((df_opt5['n_test_apply_train_thr'] < 100).sum())}/24",
                    "opt6": f"{int((df_opt6['n_test_q99_in_bucket'] < 100).sum())}/24",
                    "opt7": f"{int((df_opt7['n_test_apply_train_thr'] < 100).sum())}/12",
                },
                {
                    "axis": "SHORT clustering 活用",
                    "opt1": "なし",
                    "opt4": "なし",
                    "opt5": "なし",
                    "opt6": "なし (ATR で代替)",
                    "opt7": "あり (k=2 厳密確認済)",
                },
                {
                    "axis": "LONG cluster 反転問題の回避",
                    "opt1": "✅ clustering 廃止",
                    "opt4": "✅ clustering 廃止",
                    "opt5": "✅ clustering 廃止",
                    "opt6": "? ATR が代替できるか未確認",
                    "opt7": "✅ LONG は per-entry",
                },
                {
                    "axis": "Phase 4-b spec 改訂規模",
                    "opt1": "大 (新規 simulate_predicted_mfe_tp 中心)",
                    "opt4": "中 (cluster ループ削除のみ)",
                    "opt5": "中 (q-level 軸追加)",
                    "opt6": "中 (ATR 計算追加)",
                    "opt7": "中 (SHORT は既存・LONG は新規)",
                },
                {
                    "axis": "Phase 7 運用負荷",
                    "opt1": "中 (per-entry 推論のみ・state なし)",
                    "opt4": "低 (8 個の table lookup)",
                    "opt5": "低 (24 個の table lookup)",
                    "opt6": "中 (ATR リアルタイム計算)",
                    "opt7": "中 (cluster 推論 + per-entry 並走)",
                },
                {
                    "axis": "Phase 5 影響範囲",
                    "opt1": "Phase 5/5-d/5-e 全面書き換え",
                    "opt4": "cluster ループ → group ループ置換",
                    "opt5": "+ q-level 軸",
                    "opt6": "+ ATR 軸",
                    "opt7": "SHORT は既存ロジック・LONG だけ新規",
                },
            ]
            df_cmp = pd.DataFrame(comparison)
            df_cmp.to_csv(OUT_DIR / "step5_comparison.csv", index=False)
            log(f"  saved step5_comparison.csv", logf)

            # ====== summary JSON ======
            t1 = datetime.now()
            summary = {
                "task": "clustering 廃止後の選択肢 1/4/5/6/7 評価",
                "duration_sec": (t1 - t0).total_seconds(),
                "n_under100": {
                    "opt4_train": n_under100_opt4,
                    "opt4_test": int((df_opt4["n_test_apply_train_thr"] < 100).sum()),
                    "opt5_train": n_under100_opt5,
                    "opt5_test": int((df_opt5["n_test_apply_train_thr"] < 100).sum()),
                    "opt6_train": n_under100_opt6,
                    "opt6_test": int((df_opt6["n_test_q99_in_bucket"] < 100).sum()),
                    "opt7_train": n_under100_opt7,
                    "opt7_test": int((df_opt7["n_test_apply_train_thr"] < 100).sum()),
                },
                "short_only_k2": {
                    "silhouette": float(sil_s),
                    "share_max_diff_pp": float(max_diff),
                    "share_sum_diff_pp": float(sum_diff),
                    "bit_exact": bit_exact_s,
                },
                "short_only_k_selection": s2c_rows,
                "k12_long_mfe_lift_train": s3b_summary,
                "train_norm_sha256": train_sha,
                "test_norm_sha256": test_sha,
                "start": t0.isoformat(),
                "end": t1.isoformat(),
            }
            with open(OUT_DIR / "alternatives_summary.json", "w") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
            log(f"saved alternatives_summary.json", logf)

            log(f"END duration={(t1 - t0).total_seconds():.2f}s", logf)
            log(f"Python warnings: {len(caught)}", logf)
            for w in caught:
                log(f"  WARN: {w.category.__name__}: {w.message}", logf)

    print(f"\nLOG: {LOG_PATH}", flush=True)


if __name__ == "__main__":
    main()
