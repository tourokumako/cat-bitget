"""e35_early_separation_probe.py — E35 iter6 計測2（保有「前半」で 伸びる玉/死ぬ玉 を見分けられるか）

計測1（時間プロファイル）で「含み益は保有前半で尽き・後半に建値で締める余地は薄い／取れる層は前半」と両窓判明。
前半で締めると勝ち玉も早逃げ（E14）。→ 「保有前半の1スナップで hold-ML が 伸びる玉(EDGE_TP/CENTER) と
死ぬ玉(TIME) を分けられるか」を両窓で測る。これが iter6（早期建値撤退）の前提。

★戦略は変えない・score.py は通さない・ratchet に trades を増やさない計測。教師＝建値撤退OFF(iter3基底)。
材料＝hold-ML が使う指標一式（_hold_feat_vec・全て t 時点＝leak-safe）。判定＝分離スコア AUC（両窓）＋お金の翻訳。
合格ライン（事前固定）: 両窓 AUC≥0.55 ∧ お金の翻訳 両窓プラス ∧ 取りこぼす勝ち<救う損。
"""
from __future__ import annotations
import sys, pathlib
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
import lightgbm as lgb   # python3.13 のみ

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import e35_range_oscillation as e35o
import eval_engine as ee

UNIT = e35o.UNIT
MAKER = ee.MAKER_FEE
RT_MAKER = 2 * MAKER
TRAIN_END = e35o.TRAIN_END
BOX_TF = "5m"                     # iter5a と同じ（main 既定）
WIN = {"TP_FILLED", "EDGE_TP", "CENTER_LOCK"}
OFFSETS = [2, 3, 4, 6, 8, 12]    # 保有 10〜60 分（5m×bars）
SCORE_S, SCORE_E = pd.Timestamp("2025-06-01"), pd.Timestamp("2025-12-31 23:59")

# leak grep（自分のソースに未来参照リテラルが無いこと）
_src = pathlib.Path(__file__).read_text(encoding="utf-8")
assert ("shift(" + "-") not in _src and ("center" + "=True") not in _src, "leak 疑い（未来参照）"


def build_base_and_snaps():
    """教師＝建値撤退OFF(iter3基底)の玉 → 各オフセットで1スナップ（特徴＋結末ラベル＋お金）。"""
    df = e35o._load(0)
    e35o._attach_entry_cols(df, BOX_TF)
    A = e35o._hold_arrays(df, BOX_TF)
    idx_of = {x: i for i, x in enumerate(df["ts"].tolist())}

    saved = e35o.BE_ARM_BARS
    e35o.BE_ARM_BARS = 10 ** 9                 # OFF＝iter3 基底（建値撤退なし）
    base_trades, _ = e35o.run_continuous(df, BOX_TF, e35o.MAX_ADDS)
    e35o.BE_ARM_BARS = saved
    bt = pd.DataFrame(base_trades)
    bt["entry_time"] = pd.to_datetime(bt["entry_time"]); bt["exit_time"] = pd.to_datetime(bt["exit_time"])
    print(f"  教師(iter3基底) {bt['position_id'].nunique()} 玉 / 出口 {dict(bt['exit_reason'].value_counts())}")

    rows = []
    for pid, g in bt.groupby("position_id"):
        g = g.sort_values("entry_time")
        lot_idx = [idx_of[x] for x in g["entry_time"]]; lot_px = g["entry_price"].astype(float).tolist()
        exit_idx = idx_of[g["exit_time"].iloc[0]]
        sdir = 1 if g["side"].iloc[0] == "LONG" else -1
        reason = g["exit_reason"].iloc[0]
        label = 1 if reason in WIN else (0 if reason == "TIME_EXIT" else -1)   # win=1 / die=0 / その他(SL/EOD)=-1
        pos_net = float(g["net_usd"].sum())                                    # 玉の実 net（全レグ合算）
        first_idx = lot_idx[0]; et = g["entry_time"].iloc[0]
        for off in OFFSETS:
            i = first_idx + off
            if i >= exit_idx:                          # オフセット時点で既に決済済＝対象外
                continue
            if not (np.isfinite(A["Cc"][i]) and np.isfinite(A["atr"][i])):
                continue
            filled = [(li, lp) for li, lp in zip(lot_idx, lot_px) if li <= i]
            if not filled:
                continue
            nlot = len(filled); avg_i = sum(lp for _, lp in filled) / nlot
            feats = e35o._hold_feat_vec(A, sdir, avg_i, first_idx, nlot, i)
            # お金の翻訳: その時点で maker 建値撤退したら（funding 近似無視）
            cl = A["close"][i]
            modeled = (cl - avg_i) * nlot * UNIT * sdir - (avg_i + cl) * nlot * UNIT * MAKER
            rows.append([et, off, label, reason, pos_net, modeled] + feats)
    cols = ["entry_time", "off", "label", "reason", "pos_net", "modeled_net"] + e35o._HOLD_FEATS
    return pd.DataFrame(rows, columns=cols)


def auc_and_money(snaps):
    params = dict(n_estimators=300, num_leaves=15, min_child_samples=200, reg_alpha=1.0, reg_lambda=1.0,
                  learning_rate=0.03, random_state=42, verbose=-1)
    FE = e35o._HOLD_FEATS
    print("\n  ── 分離スコア(AUC: 伸びる1 vs 死ぬ0) と お金の翻訳（両窓・オフセット別）──")
    print("  off(分)  学習OOF_AUC  採点OOS_AUC | θ*  救う損$  取りこぼし$  純改善$(採点) | 学習玉 採点玉")
    for off in OFFSETS:
        s = snaps[snaps.off == off]
        wd = s[s.label >= 0]                            # win/die のみ（AUC 用）
        tr = wd[wd.entry_time < TRAIN_END]
        sc = wd[(wd.entry_time >= SCORE_S) & (wd.entry_time <= SCORE_E)]
        if len(tr) < 50 or len(sc) < 20 or tr.label.nunique() < 2 or sc.label.nunique() < 2:
            print(f"   {off*5:>3d}    サンプル不足（学習{len(tr)}/採点{len(sc)}）"); continue
        # 学習窓 OOF AUC（玉ごと1行＝玉内leakなし・5-fold）
        Xtr, ytr = tr[FE].to_numpy(), tr.label.to_numpy()
        oof = np.zeros(len(tr))
        for tri, vai in StratifiedKFold(5, shuffle=True, random_state=42).split(Xtr, ytr):
            m = lgb.LGBMClassifier(**params); m.fit(Xtr[tri], ytr[tri])
            oof[vai] = m.predict_proba(Xtr[vai])[:, 1]
        auc_tr = roc_auc_score(ytr, oof)
        # 採点窓 OOS AUC（全学習窓で fit → 採点窓 予測）
        full = lgb.LGBMClassifier(**params); full.fit(Xtr, ytr)
        psc = full.predict_proba(sc[FE].to_numpy())[:, 1]
        auc_sc = roc_auc_score(sc.label.to_numpy(), psc)
        # お金の翻訳: θ を学習窓 OOF で「純改善(救う損−取りこぼし)」最大に選び、採点窓へ適用
        #   救う損=die玉を建値撤退した改善(modeled−actual>0想定) / 取りこぼし=win玉を切った悪化(<0)
        s_tr = s[s.entry_time < TRAIN_END]; s_sc = s[(s.entry_time >= SCORE_S) & (s.entry_time <= SCORE_E)]
        full_all = lgb.LGBMClassifier(**params); full_all.fit(tr[FE].to_numpy(), tr.label.to_numpy())
        ptr_all = full_all.predict_proba(s_tr[FE].to_numpy())[:, 1] if len(s_tr) else np.array([])
        psc_all = full_all.predict_proba(s_sc[FE].to_numpy())[:, 1] if len(s_sc) else np.array([])
        best_th, best_gain = 0.5, -1e18
        for th in [0.3, 0.4, 0.5, 0.6, 0.7]:
            cut = s_tr[ptr_all < th]
            gain = float((cut.modeled_net - cut.pos_net).sum())
            if gain > best_gain:
                best_gain, best_th = gain, th
        cut_sc = s_sc[psc_all < best_th]
        delta = cut_sc.modeled_net - cut_sc.pos_net
        saved = float(delta[cut_sc.label == 0].sum())        # die 玉で救った損
        forfeit = float(delta[cut_sc.label == 1].sum())      # win 玉で取りこぼし（負）
        net_imp = float(delta.sum())
        print(f"   {off*5:>3d}     {auc_tr:.3f}       {auc_sc:.3f}    | {best_th}  {saved:>+7.0f}   {forfeit:>+7.0f}    {net_imp:>+7.0f}      | {len(tr):>4d} {len(sc):>4d}")
    print("\n  読み方: 両窓 AUC≥0.55 ∧ 純改善(採点)が＋ ∧ |取りこぼし|<救う損 を満たすオフセットがあれば iter6設計へ。")
    print("          満たさなければ A 見送り→B(全玉こまめ薄利確) を議論。OOF=学習窓の正直な分離力 / OOS=採点窓(未学習)。")


def main():
    print("=" * 90)
    print("E35 iter6 計測2: 保有前半で 伸びる玉/死ぬ玉 を見分けられるか（両窓・教師=iter3基底・score不使用）")
    print(f"box={BOX_TF} / offsets(分)={[o*5 for o in OFFSETS]} / UNIT={UNIT} / 往復maker率={RT_MAKER}")
    snaps = build_base_and_snaps()
    # 自己検査: H15 ボラ逃げ（atr_pct が前半で上位独占でないか）を 1 モデルで確認
    s12 = snaps[(snaps.off == 6) & (snaps.label >= 0) & (snaps.entry_time < TRAIN_END)]
    if len(s12) > 100:
        m = lgb.LGBMClassifier(n_estimators=300, num_leaves=15, min_child_samples=200,
                               reg_alpha=1.0, reg_lambda=1.0, learning_rate=0.03, random_state=42, verbose=-1)
        m.fit(s12[e35o._HOLD_FEATS].to_numpy(), s12.label.to_numpy())
        fi = pd.Series(m.feature_importances_, index=e35o._HOLD_FEATS).sort_values(ascending=False)
        rank = list(fi.index).index("atr_pct") + 1
        print(f"  [H15] off=30分モデル feature importance top6:\n{fi.head(6).to_string()}")
        print(f"  [H15] atr_pct 順位 {rank}/{len(e35o._HOLD_FEATS)}（上位独占でなければ OK）")
    auc_and_money(snaps)
    print("=" * 90)


if __name__ == "__main__":
    main()
