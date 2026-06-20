"""measure_e35_time_profile.py — E35 iter6 計測（TIME_EXIT 玉の含み益 時間プロファイル）

目的: TIME_EXIT レグが「保有中いつ建値/含み益に居たか」を両窓で出し、
      候補(b)時間依存収縮 / (c)2段ゲート のどちらが取れる層を持つか判定する。
      ★戦略は触らない・保有 sim を再実行しない計測（close 基準でパス復元＝バー確定の実行可能視点）。

入力: trades_e35_oscillation_5m_iter5a_{score,train}.csv（TIME レグ）＋ 5m 正本 close。
復元: unreal_t = (close_t - entry_price) * UNIT * sdir（eval_engine.gross と同式・LONG+1/SHORT-1）。
建値撤退コスト: 往復 maker（eval_engine: TP/SL/BE_EXIT=maker）＝RT_MAKER。funding は近似無視（modeled net はやや楽観・両窓で符号一致を見る）。
自己検査: 復元パスの最大 ≤ 記録 mfe_usd（intrabar 高安・eval_engine は close でなく h/l で max_fav 更新）。
判定: 後半区間でも建値/fee 以上に触れる層が厚い→(b)で取れる。前半だけ→(b)限定。両窓 符号一致しなければ「効く」と言わない。
"""
from __future__ import annotations
import sys, pathlib
import numpy as np
import pandas as pd

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import e34_range_zscore_taker as e34v1   # CSV / SIZE
import eval_engine as ee                 # MAKER（import のみ・改造なし）

RATCHET = HERE.parent.parent / "results" / "priority_rebuild" / "ratchet"
UNIT = e34v1.SIZE
MAKER = ee.MAKER_FEE
RT_MAKER = 2 * MAKER                      # 建値撤退=往復 maker の手数料率（eval_engine TP/SL/BE_EXIT=maker）

# ── 価格 close マップ ──
px = pd.read_csv(e34v1.CSV)
px["ts"] = pd.to_datetime(px["timestamp"])
TS = px["ts"].to_numpy("datetime64[ns]")
CLOSE = px["close"].to_numpy(float)
ts_to_i = {t: i for i, t in enumerate(TS)}


def leg_path(entry_time, exit_time, entry_price, sdir):
    """entry..exit の各バー close から含み損益(USD)パスを復元。返り値 = np.array（先頭=entry バー）。"""
    ei = ts_to_i.get(np.datetime64(pd.Timestamp(entry_time)))
    xi = ts_to_i.get(np.datetime64(pd.Timestamp(exit_time)))
    if ei is None or xi is None or xi < ei:
        return None
    cl = CLOSE[ei:xi + 1]
    return (cl - entry_price) * UNIT * sdir


def analyze(path_csv, label):
    df = pd.read_csv(path_csv)
    df = df[df.exit_reason == "TIME_EXIT"].reset_index(drop=True)
    n = len(df)
    print(f"\n{'='*70}\n  {label}  TIME_EXIT {n}件  ({path_csv.name})\n{'='*70}")
    if n == 0:
        print("  該当なし"); return

    NB = 5  # 保有を5区間に等分
    occ_be = np.zeros(NB); occ_fee = np.zeros(NB); occ_cnt = np.zeros(NB)
    peak_frac = []; last_touch_fee = []; closemax_le_mfe = 0; valid = 0
    fgrid = [0.0, 0.5, 0.6, 0.7, 0.8]
    delta = {f: 0.0 for f in fgrid}; fired = {f: 0 for f in fgrid}

    for _, r in df.iterrows():
        sdir = 1 if r.side == "LONG" else -1
        p = leg_path(r.entry_time, r.exit_time, r.entry_price, sdir)
        if p is None or len(p) < 3:
            continue
        valid += 1
        m = len(p)
        fee_thr = r.entry_price * UNIT * RT_MAKER          # 建値撤退で覆える含み益（USD）
        if p.max() <= r.mfe_usd + 1e-6:
            closemax_le_mfe += 1
        bins = np.minimum((np.arange(m) / m * NB).astype(int), NB - 1)
        for b in range(NB):
            mask = bins == b
            if mask.any():
                occ_cnt[b] += 1
                occ_be[b] += (p[mask] >= 0).any()
                occ_fee[b] += (p[mask] >= fee_thr).any()
        peak_frac.append(p.argmax() / m)
        idx_fee = np.where(p >= fee_thr)[0]
        last_touch_fee.append((idx_fee.max() / m) if len(idx_fee) else -1.0)
        for f in fgrid:
            start = int(np.ceil(f * m))
            seg = np.where(p[start:] >= fee_thr)[0]
            if len(seg):
                j = start + seg[0]
                modeled = p[j] - fee_thr                    # 建値撤退 net（unreal − 往復maker手数料）
                delta[f] += (modeled - r.net_usd); fired[f] += 1

    print(f"  有効レグ {valid}/{n}  ・自己検査(close基準max ≤ 記録mfe): {closemax_le_mfe}/{valid} "
          f"({100*closemax_le_mfe/max(valid,1):.0f}% ✅期待100%)")

    print("\n  B. 区間別 占有率（保有を5等分・各区間で建値/fee以上に「触れた」レグ割合）")
    print("     区間       建値以上%   fee以上%   (n)")
    labels = ["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"]
    for b in range(NB):
        c = occ_cnt[b]
        print(f"     {labels[b]:8s}   {100*occ_be[b]/max(c,1):6.1f}     {100*occ_fee[b]/max(c,1):6.1f}    ({int(c)})")

    pf = np.array(peak_frac); lt = np.array(last_touch_fee)
    print(f"\n  C. 含み益ピーク位置（保有割合）: 中央 {np.median(pf):.2f} / 前半(<0.5) {100*(pf<0.5).mean():.0f}% / 後半(≥0.5) {100*(pf>=0.5).mean():.0f}%")
    has = lt >= 0
    print(f"  D. 最後に fee 以上に触れた位置（保有割合・到達レグ {has.sum()}/{valid}）: "
          f"中央 {np.median(lt[has]) if has.any() else float('nan'):.2f} / "
          f"後半(≥0.5)で最後に触れた {100*((lt>=0.5).sum()/max(has.sum(),1)):.0f}%")

    print("\n  E. 時間ゲート建値撤退の擬似ルール（f 以降で初めて含み益≥fee→maker撤退・funding近似無視＝やや楽観）")
    print("     f(保有割合) 発火件数  net改善(approx$)   1件平均$")
    base_net = df.net_usd.sum()
    for f in fgrid:
        tag = "（=iter4型・即arm）" if f == 0.0 else ""
        print(f"     {f:>4.1f}        {fired[f]:>4d}/{valid}     {delta[f]:>+8.0f}        {delta[f]/max(fired[f],1):>+6.2f}  {tag}")
    print(f"     （TIME 実 net 合計 = {base_net:+.0f}・改善はこの赤字をどれだけ埋めるか）")


def main():
    score = RATCHET / "trades_e35_oscillation_5m_iter5a_score.csv"
    train = RATCHET / "trades_e35_oscillation_5m_iter5a_train.csv"
    print("E35 iter6 計測: TIME_EXIT 玉の含み益 時間プロファイル（両窓・close 基準・保有 sim 非再実行）")
    print(f"UNIT={UNIT} / MAKER={MAKER} / 往復maker率={RT_MAKER}")
    analyze(train, "学習窓 (entry < 2025-01)")
    analyze(score, "採点窓 (2025-06〜12)")
    print("\n判定の読み方: 区間Bの『80-100%でも fee以上%が厚い』＋『Dで後半に最後に触れる割合が高い』なら "
          "(b)時間依存収縮で取れる層が厚い。Eの net改善が両窓で同符号・近い大きさなら過剰適合でない。")


if __name__ == "__main__":
    main()
