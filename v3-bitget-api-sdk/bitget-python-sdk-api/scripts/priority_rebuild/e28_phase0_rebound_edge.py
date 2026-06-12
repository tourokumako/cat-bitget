#!/usr/bin/env python3
"""e28_phase0_rebound_edge.py — E28 Phase 0: 下げ相場の反発 LONG の素エッジ測定（eval_engine per-trade・学習期間のみ）

経過:
 round-1（40分スキャル・確認型）= 素エッジなし（対称ノイズ・黒字月1/45・レース率<無エッジ基準）。
 round-2/2b（capitulation+確認・深さ勾配）= 深い21件だけ in-sample で +、1段広げると消失・深い2hフラッシュは悪化。
 → round-3（本版・スイング）: 保有を長く（4h/12h/1日）して capitulation の反発を取れるかを測る（まこさん 2026-06-12）。
   同じ capitulation エントリーで保有を伸ばし、スイング規模の大きな TP/SL（データ較正）で素エッジ
   （コスト＋funding 控除後）を測る。スキャル(40分)では構造的に取れない多時間〜日の反発を見る。

★注記（数字の読み方）:
 - net は eval_engine の per-trade・コスト控除後（連続モード score.py 採点ではない＝Phase 2）。
 - per-trade 独立（建玉が重なる・スイングは重なり大 → total_net は参考外・exp_net と レース率 を見る）。
 - バリア（TP/SL）は学習期間 in-sample 較正＝やや楽観。学習 2021-04〜2024-12 のみ・採点2025 不参照。
 - レース率（利確 vs 損切り）を無ドリフト基準 SL/(TP+SL) と比べ「方向エッジか・バリアの形か」を切り分ける。
V9本体/審判(eval_engine)不変・import のみ。score.py/precheck.py は呼ばない（採点しない）。
"""
from __future__ import annotations
import argparse
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import replay_csv as rc                      # noqa: E402
import gen_p23_candidates as gen             # noqa: E402
import eval_engine as ee                     # noqa: E402
from preload_cache import cached_preload     # noqa: E402

RATCHET = ROOT / "results" / "priority_rebuild" / "ratchet"
TRAIN_END = pd.Timestamp("2025-01-01")   # 学習期間のみ（採点 2025-04〜12 は触らない・H8）
SIZE = 0.024
WARMUP = 50


def build_entry_masks(df):
    """capitulation ベースのエントリー（保有=スイングで取れるかを測る）。
    返り値: [(名前, 発火 bool 配列)]。"""
    close = df.close.to_numpy(float)
    openp = df.open.to_numpy(float)
    ema20 = df.ema_20.to_numpy(float)
    rsi = df.rsi_short.to_numpy(float)

    def shift(a, k):
        return pd.Series(a).shift(k).to_numpy()

    cs = pd.Series(close)
    ret12 = cs.pct_change(12).to_numpy() * 100.0      # 直近1h(12本)の下落%
    rsi_min3 = pd.Series(rsi).rolling(3).min().to_numpy()

    os_rsi = 35.0
    at_lows = close < ema20
    capit = (ret12 < -1.5) & at_lows                   # 急落（1h −1.5%超・安値圏）
    rsi_cross = (rsi > os_rsi) & (shift(rsi, 1) <= os_rsi)   # RSI 上抜け回復
    green = close > openp

    masks = [
        ("capit_cross", capit & rsi_cross),                          # 急落+RSI回復
        ("capit_deep_cross", capit & (rsi_min3 < 25.0) & rsi_cross),  # 急落+深OS+回復（scalp で +だった21件系）
        ("capit_green", capit & green),                              # 急落+陽線（確認ゆるめ・件数多）
    ]
    return [(nm, np.nan_to_num(m, nan=0.0).astype(bool)) for nm, m in masks]


def calibrate(idxs, highs, lows, closes, n, hold):
    """保有 hold 本の前向き MFE/MAE からバリアを導出（スイング規模・上限拡大・手置きグリッドでない）。"""
    mfe, mae = [], []
    for i in idxs:
        j0, j1 = i + 1, min(i + hold, n - 1)
        if j1 <= j0:
            continue
        ref = closes[i]
        mfe.append((highs[j0:j1 + 1].max() - ref) / ref * 100.0)
        mae.append((lows[j0:j1 + 1].min() - ref) / ref * 100.0)
    if not mfe:
        return None
    tp_pct = float(np.clip(np.median(mfe) * 0.65 / 100.0, 0.0015, 0.06))   # スイング規模で上限拡大
    sl_pct = float(np.clip(np.percentile(np.abs(mae), 75) / 100.0, 0.003, 0.08))
    return tp_pct, sl_pct, float(np.median(mfe)), float(np.median(mae))


def measure(conf, hold, idxs, tp_pct, sl_pct, opens, highs, lows, closes, tss, years):
    """各発火 index を eval_engine の intrabar TP-before-SL 前向き sim（per-trade・コスト+funding 控除後）。"""
    nets, filled, wins = [], 0, 0
    gross = fee = 0.0
    reasons, yr_net = {}, {}
    records = []
    for i in idxs:
        tr = ee.simulate_trade(i, ee.LONG, SIZE, opens, highs, lows, closes, tss,
                               tp_pct=tp_pct, sl_pct=sl_pct, max_hold_bars=hold,
                               entry_type="maker")
        if tr is None:
            continue
        filled += 1
        nets.append(tr.net)
        gross += tr.gross
        fee += tr.fee
        wins += int(tr.net > 0)
        reasons[tr.exit_reason] = reasons.get(tr.exit_reason, 0) + 1
        y = int(years[i])
        yr_net[y] = yr_net.get(y, 0.0) + tr.net
        records.append({
            "conf": conf, "hold_bars": hold, "sig_time": tss[i],
            "exit_reason": tr.exit_reason, "net_usd": round(tr.net, 4),
            "gross_usd": round(tr.gross, 4), "fee_usd": round(tr.fee, 4),
            "funding_usd": round(tr.funding_cost, 4), "year": y,
        })
    if filled == 0:
        return None, []
    nets = np.array(nets)
    tp_cnt, sl_cnt = reasons.get("TP", 0), reasons.get("SL", 0)
    tp_race = tp_cnt / (tp_cnt + sl_cnt) if (tp_cnt + sl_cnt) else float("nan")
    rw_bench = sl_pct / (tp_pct + sl_pct)
    return {
        "fires": len(idxs), "filled": filled,
        "exp_net": float(nets.mean()), "total_net": float(nets.sum()),
        "winrate": wins / filled, "tp_race": tp_race, "rw_bench": rw_bench,
        "gross": gross, "fee": fee, "reasons": reasons,
        "yr_net": {k: round(yr_net[k], 0) for k in sorted(yr_net)},
    }, records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    params = rc._load_params()
    df, _ = cached_preload(str(gen.OHLCV_CSV), params)
    ts = pd.to_datetime(df.timestamp_ms, unit="ms")
    assert ts.iloc[-1] >= pd.Timestamp("2026-03-01"), "データ範囲異常"
    opens = df.open.to_numpy(float)
    highs = df.high_raw.to_numpy(float)
    lows = df.low_raw.to_numpy(float)
    closes = df.close.to_numpy(float)
    tss = ts.to_numpy()
    years = pd.DatetimeIndex(ts).year.to_numpy()
    n = len(closes)
    end = int((ts < TRAIN_END).sum())
    step = 50 if args.smoke else 1
    hold_list = [48, 144, 288]   # 4h / 12h / 1日（スイング保有）

    print("=" * 84)
    print("[E28 Phase 0 round-3 スイング] capitulation の反発を保有を伸ばして取れるか（eval_engine per-trade・学習期間）")
    print(f"  計器: maker {ee.MAKER_FEE} / taker {ee.TAKER_FEE} / slip {ee.SLIPPAGE} / funding {ee.FUNDING_RATE_8H}/8h / size {SIZE} BTC")
    print(f"  保有候補: {[f'{h*5//60}h' if h*5>=60 else f'{h*5}m' for h in hold_list]} / entry=指値maker(TTL3) / 学習〜{TRAIN_END.date()}（採点不参照）")
    print(f"  ※ per-trade 独立（重なり大）→ exp_net と レース率 を見る・total は参考外")
    print("=" * 84)

    masks = build_entry_masks(df)
    all_records, results = [], {}
    for hold in hold_list:
        hlabel = f"{hold*5//60}h" if hold * 5 >= 60 else f"{hold*5}m"
        print(f"\n############### 保有 {hlabel}（{hold}本） ###############")
        for name, mask in masks:
            idxs = np.where(mask)[0]
            idxs = idxs[(idxs >= WARMUP) & (idxs < min(end, n - hold - 2))]
            if step > 1:
                idxs = idxs[::step]
            idxs = idxs.tolist()
            if not idxs:
                print(f"\n■ {name} @ {hlabel}: 発火 0 件")
                continue
            cal = calibrate(idxs, highs, lows, closes, n, hold)
            if cal is None:
                continue
            tp_pct, sl_pct, med_mfe, med_mae = cal
            r, recs = measure(name, hold, idxs, tp_pct, sl_pct, opens, highs, lows, closes, tss, years)
            if r is None:
                continue
            results[(name, hold)] = r
            all_records.extend(recs)
            verdict = "✅ 素エッジあり" if r["exp_net"] > 0 else "❌ なし"
            if r["tp_race"] > r["rw_bench"] + 0.005:
                race_v = "方向プラス（無エッジ基準超）"
            elif abs(r["tp_race"] - r["rw_bench"]) <= 0.02:
                race_v = "ほぼ無エッジ（バリアの形）"
            else:
                race_v = "方向マイナス（下落継続気味）"
            print(f"\n■ {name} @ {hlabel}")
            print(f"  発火 {r['fires']} / 約定 {r['filled']} / 前向き MFE中央 {med_mfe:.2f}% MAE中央 {med_mae:.2f}%"
                  f" / 較正 TP {tp_pct*100:.2f}% SL {sl_pct*100:.2f}%")
            print(f"  期待値 net/件 {r['exp_net']:+.3f} USD / 勝率 {r['winrate']:.1%}"
                  f" / レース率 {r['tp_race']:.1%} vs 無エッジ基準 {r['rw_bench']:.1%} → {race_v}  {verdict}")
            print(f"  gross {r['gross']:+.0f} / 手数料 {r['fee']:.0f} / 出口別 {r['reasons']}")
            print(f"  年別 net {r['yr_net']}")

    if all_records and not args.smoke and results:
        rec_df = pd.DataFrame(all_records)
        fcsv = RATCHET / "e28_phase0_swing_trades.csv"
        rec_df.to_csv(fcsv, index=False)
        print(f"\n[保存] per-trade {len(rec_df)}件 → results/priority_rebuild/ratchet/{fcsv.name}")

    print("\n" + "=" * 84)
    print("[総括] (entry, 保有) で 期待値>0 かつ レース率>無エッジ基準 の組:")
    hit = [(k, r) for k, r in results.items()
           if r["exp_net"] > 0 and r["tp_race"] > r["rw_bench"] + 0.005]
    if hit:
        for (name, hold), r in sorted(hit, key=lambda x: -x[1]["exp_net"]):
            hl = f"{hold*5//60}h" if hold * 5 >= 60 else f"{hold*5}m"
            print(f"  ✅ {name} @ {hl}: {r['exp_net']:+.2f}/件・{r['filled']}件・年別 {r['yr_net']}")
        print("  → スイング保有で取れる候補あり。件数・年別の頑健性を見て Phase 1 へ。")
    else:
        print("  なし＝capitulation の反発はスイング保有でもコスト控除後の方向エッジが立たない。")
        print("  → 5m OHLCV の下げ相場 LONG（スキャル/スイング）は exhaustive に negative。")
    print("=" * 84)


if __name__ == "__main__":
    main()
