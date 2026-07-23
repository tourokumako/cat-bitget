#!/usr/bin/env python3
"""e34_range_zscore_taker.py — E34 Phase 0: レンジ逆張り（相対分位 ∩ taker投げ売り枯渇・LONG単発）の素エッジ測定

設計書: .claude/ratchet/e34_design.md（Peterson hypothesis-driven 構成・まこさん GO 2026-06-13）。
仮説（a priori・反証可能）: レンジ下限で「相対的に行き過ぎ ∩ 投げ売りが枯れた」場面は、中心(SMA20)へ
  回帰して利確に到達する（方向・二値）。固定閾値の素朴MR（E33）は no-edge。相対分位＋投げ売り枯渇で
  到達率が無エッジ基準を上回る（E28 が下げ相場LONGで同2道具を per-trade で実証＝+0.29→+1.27/件）。
棄却条件: per-trade レース率 ≤ 無エッジ基準 / exp_net/件 ≤ 0 / 年別で符号バラバラ。

仕様（Indicators → Signals → Rules）:
 Indicators（全 leak-safe・shift(1)/asof backward）: SMA20・std20・dev_z=(close−SMA20)/std20・ATR14・ADX14・taker_ls。
 Signals: S1 行き過ぎ dev_z≤thr_z（学習分位 cross-in）／ S2 投げ売り枯渇 taker_ls≤thr_taker（成行売り過熱）／ S3 非トレンド ADX14≤25。
 Rules: ENTRY=次バー maker指値 LONG size0.024 ／ TP=entry時点SMA20価格に固定指値（tp_pct=(sma20−close)/close）
        ／ SL=entry−1.5×ATR14 ／ 時間切れ48本(4h) ／ 1ポジ単発。

★注記（E28/E33 と同じ規律）:
 - net は per-trade・コスト+funding 控除後（eval_engine・改造禁止・import のみ）。連続モード score.py 採点は Phase 2。
 - 学習 〜2024-12-31 のみ・採点2025 不参照（H8）。日足regimeで絞らない（E33の「レンジ5%しか発火しない」を避け5mで局所の行き過ぎを拾う）。
 - 分位は a priori 単一値（行き過ぎ q0.05・投げ売り q0.25・E28 実績帯）＝学習分布から算出する生値。最良値スイープしない（hook L-267）。
   頑健性は「年別の符号一致」＋「Phase2 連続モード採点」で担保（プロジェクト標準）。分位プラトーはまこさん GO 後に別途。
 - コンポーネント個別評価（S1単独 / S1∩S2 / S1∩S2∩S3）でどの signal が寄与するかを切り分ける（過剰適合防止・値スイープでない）。
 - レース率 vs 無エッジ基準 SL/(TP+SL) で「方向エッジか・形（小TP広SL）か」を切り分ける。
"""
from __future__ import annotations
import argparse
import pathlib
import sys

import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import eval_engine as ee   # noqa: E402  （審判・改造禁止・import のみ）

CSV = ROOT / "data" / "BTCUSDT-5m-2021-04-01_2026-06-30_V9FULL_safe.csv"  # Binance spot 5m（§8.2.1.1 正本・窓の組み替えで2026-06-30版へ・2026-07-23 まこさん確定＝採点窓 2026-03〜06）
OI_CSV = ROOT / "data" / "oi_BTCUSDT_5y.csv"                                # taker_ls（Binance futures metrics・5min）
RATCHET = ROOT / "results" / "priority_rebuild" / "ratchet"
TRAIN_END = pd.Timestamp("2025-01-01")   # 学習 2021-04〜2024-12 のみ（H8・Phase0 は E28/E33 と同窓）

# ── Phase0 前提値（固定・単一・最良値スイープしない）──────────────────────────
SIZE = 0.024
SMA_N = 20          # 中心（移動平均）と std の窓
ATR_N = 14
ADX_N = 14
ADX_MAX = 25.0      # 非トレンド（バンドウォーク回避）
SL_ATR_K = 1.5      # SL = entry − k×ATR14
HOLD_5M = 48        # 時間切れ 4h
COST_FLOOR = 0.0020 # TP がコスト床（maker往復+slip）未満なら不成立
Z_Q = 0.05          # 行き過ぎ下側分位（a priori 単一・学習分布から生値を算出）
TAKER_Q = 0.25      # taker_ls 投げ売り下側分位（a priori 単一・E28 実績帯）


def add_indicators(df):
    """5m 上で SMA20 / std20 / dev_z / ATR14 / ADX14 を計算（全て当該足までで確定＝leak-safe）。"""
    c, h, l = df.close, df.high, df.low
    df["sma"] = c.rolling(SMA_N).mean()
    df["std"] = c.rolling(SMA_N).std()
    df["dev_z"] = (c - df["sma"]) / df["std"]          # 中心からの乖離（標準化・負ほど売られすぎ）
    pc = c.shift(1)
    tr = np.maximum(h - l, np.maximum((h - pc).abs(), (l - pc).abs()))
    df["atr"] = tr.rolling(ATR_N).mean()
    # ADX14（Wilder の rolling-mean 近似・非トレンド判定用フィルタ）
    up = h.diff()
    dn = -l.diff()
    plus_dm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=df.index)
    atr_w = tr.rolling(ADX_N).mean()
    plus_di = 100 * plus_dm.rolling(ADX_N).mean() / atr_w
    minus_di = 100 * minus_dm.rolling(ADX_N).mean() / atr_w
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    df["adx"] = dx.rolling(ADX_N).mean()
    return df


def add_taker(df):
    """taker_ls（taker 買い/売り比・低い＝投げ売り）を asof backward（時刻 t 以前の最後の値＝leak-safe）。"""
    oi = pd.read_csv(OI_CSV)
    oi["time"] = pd.to_datetime(oi["time"])
    oi = oi[oi.taker_ls > 0].sort_values("time").reset_index(drop=True)
    oi_t = oi.time.to_numpy("datetime64[ns]")
    tls_v = oi.taker_ls.to_numpy(float)
    t_now = df.ts.to_numpy("datetime64[ns]")
    idx = np.searchsorted(oi_t, t_now, side="right") - 1     # ≤ t（未来参照なし）
    idx = np.clip(idx, 0, len(tls_v) - 1)
    df["taker_ls"] = tls_v[idx]
    return df


def measure(label, fired, opens, highs, lows, closes, tss, n):
    """発火行 → 5m signal_idx → eval_engine 前向き sim（per-trade・コスト+funding 控除後）。"""
    nets, filled, wins, bench_sum = [], 0, 0, 0.0
    gross = fee = 0.0
    skipped_floor = 0
    reasons, yr_net = {}, {}
    records = []
    for _, r in fired.iterrows():
        si = int(r.pos)
        if si < SMA_N + 2 or si >= n - HOLD_5M - 2:
            continue
        if not (np.isfinite(r.atr) and np.isfinite(r.sma) and r.close > 0 and r.atr > 0):
            continue
        tp_pct = float((r.sma - r.close) / r.close)        # 案A: 中心(SMA20)価格への固定指値（その場のレンジ幅・可変）
        if tp_pct < COST_FLOOR:                            # TP がコスト床未満＝利確がコストを覆えない → 不成立
            skipped_floor += 1
            continue
        sl_pct = float(np.clip(SL_ATR_K * r.atr / r.close, 0.005, 0.08))  # SL = 1.5×ATR14（σ比例）
        tr = ee.simulate_trade(si, ee.LONG, SIZE, opens, highs, lows, closes, tss,
                               tp_pct=tp_pct, sl_pct=sl_pct, max_hold_bars=HOLD_5M, entry_type="maker")
        if tr is None:
            continue
        filled += 1
        nets.append(tr.net)
        gross += tr.gross
        fee += tr.fee
        wins += int(tr.net > 0)
        bench_sum += sl_pct / (tp_pct + sl_pct)
        reasons[tr.exit_reason] = reasons.get(tr.exit_reason, 0) + 1
        y = int(pd.Timestamp(r.ts).year)
        yr_net[y] = yr_net.get(y, 0.0) + tr.net
        records.append({"label": label, "sig_time": r.ts, "exit_reason": tr.exit_reason,
                        "tp_pct": round(tp_pct, 5), "sl_pct": round(sl_pct, 5),
                        "dev_z": round(float(r.dev_z), 3), "taker_ls": round(float(r.taker_ls), 4),
                        "adx": round(float(r.adx), 1) if np.isfinite(r.adx) else None,
                        "net_usd": round(tr.net, 4), "gross_usd": round(tr.gross, 4),
                        "fee_usd": round(tr.fee, 4), "year": y})
    if filled == 0:
        return None, []
    nets = np.array(nets)
    tp_cnt, sl_cnt = reasons.get("TP", 0), reasons.get("SL", 0)
    tp_race = tp_cnt / (tp_cnt + sl_cnt) if (tp_cnt + sl_cnt) else float("nan")
    return {"filled": filled, "exp_net": float(nets.mean()), "total_net": float(nets.sum()),
            "winrate": wins / filled, "tp_race": tp_race, "rw_bench": bench_sum / filled,
            "gross": gross, "fee": fee, "reasons": reasons, "skipped_floor": skipped_floor,
            "yr_net": {k: round(yr_net[k], 0) for k in sorted(yr_net)}}, records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    print("=" * 92)
    print("[E34 Phase 0] レンジ逆張り 相対分位 ∩ taker投げ売り枯渇（LONG単発・eval_engine per-trade・学習期間）")
    df = pd.read_csv(CSV)
    df["ts"] = pd.to_datetime(df["timestamp"])
    df = df.reset_index(drop=True)
    df["pos"] = np.arange(len(df))
    opens = df.open.to_numpy(float); highs = df.high.to_numpy(float)
    lows = df.low.to_numpy(float); closes = df.close.to_numpy(float)
    tss = df.ts.to_numpy(); n = len(df)
    print(f"  価格: {CSV.name}（{n}本・{df.ts.iloc[0].date()}〜{df.ts.iloc[-1].date()}）")
    print(f"  計器: maker {ee.MAKER_FEE} / taker {ee.TAKER_FEE} / slip {ee.SLIPPAGE} / funding {ee.FUNDING_RATE_8H}/8h / size {SIZE}")
    print(f"  入口: dev_z=(close−SMA{SMA_N})/std≤q{Z_Q} / taker_ls≤q{TAKER_Q} / ADX{ADX_N}≤{ADX_MAX} ／ 出口: TP=中心固定 / SL={SL_ATR_K}×ATR{ATR_N} / 時間切れ{HOLD_5M*5//60}h / 学習〜{TRAIN_END.date()}")
    print("=" * 92)

    df = add_indicators(df)
    df = add_taker(df)
    tr_mask = df.ts < TRAIN_END                      # 学習期間のみ（閾値も発火もここから）
    tr = df[tr_mask]

    # ── 閾値（学習分布から算出する生値・a priori 単一分位・覗き見なし）──────────
    z_thr = float(tr.dev_z.quantile(Z_Q))
    taker_thr = float(tr.taker_ls.quantile(TAKER_Q))
    print(f"[閾値（学習分布の分位＝生値）] dev_z q{Z_Q}={z_thr:+.2f} / taker_ls q{TAKER_Q}={taker_thr:.3f}")

    devz = df.dev_z
    s1 = (devz <= z_thr) & (devz.shift(1) > z_thr)   # 行き過ぎ cross-in（下側分位を初めて割った瞬間）
    s2 = df.taker_ls <= taker_thr                    # 投げ売り枯渇（成行売りが過熱）
    s3 = df.adx <= ADX_MAX                           # 非トレンド

    # ── コンポーネント個別評価（§7・signal の組合せ違い＝値スイープでない）──────
    entries = [
        ("S1単独 行き過ぎ", s1),
        ("S1∩S2 +taker枯渇", s1 & s2),
        ("S1∩S2∩S3 +ADX非トレンド [本命]", s1 & s2 & s3),
    ]

    results, all_recs = {}, []
    for label, mask in entries:
        sel = df[mask.fillna(False) & tr_mask]
        if args.smoke:
            sel = sel.iloc[::5]
        r, recs = measure(label, sel, opens, highs, lows, closes, tss, n)
        if r is None:
            print(f"\n■ {label}: 約定 0 件")
            continue
        results[label] = r
        all_recs.extend(recs)
        edge = r["tp_race"] - r["rw_bench"]
        verdict = "✅ 素エッジあり" if (r["exp_net"] > 0 and r["tp_race"] > r["rw_bench"]) else "❌ なし"
        print(f"\n■ {label}: 発火 {int((mask.fillna(False) & tr_mask).sum())} / 約定 {r['filled']}（床棄却 {r['skipped_floor']}）")
        print(f"  期待値 net/件 {r['exp_net']:+.3f} USD / 勝率 {r['winrate']:.1%}"
              f" / レース率 {r['tp_race']:.1%} vs 無エッジ基準 {r['rw_bench']:.1%}（差 {edge:+.1%}）→ {verdict}")
        print(f"  gross {r['gross']:+.0f} / 手数料 {r['fee']:.0f} / 出口別 {r['reasons']}")
        print(f"  年別 net {r['yr_net']}")

    if all_recs and not args.smoke and results:
        rec_df = pd.DataFrame(all_recs)
        fcsv = RATCHET / "e34_range_zscore_taker_trades.csv"
        rec_df.to_csv(fcsv, index=False)
        print(f"\n[保存] per-trade {len(rec_df)}件 → results/priority_rebuild/ratchet/{fcsv.name}")

    print("\n" + "=" * 92)
    print("[総括] 合格基準＝exp_net/件>0 ∩ レース率>無エッジ基準 ∩ 年別で符号一致（§3）:")
    hit = [(k, r) for k, r in results.items()
           if r["exp_net"] > 0 and r["tp_race"] > r["rw_bench"]]
    if hit:
        for k, r in sorted(hit, key=lambda x: -x[1]["exp_net"]):
            yrs = r["yr_net"]
            allpos = all(v > 0 for v in yrs.values())
            print(f"  ✅ {k}: {r['exp_net']:+.3f}/件・{r['filled']}件・年別 {yrs}{'（全年+）' if allpos else ''}")
        print("  → S1単独 vs ∩S2 vs ∩S2∩S3 の寄与差で「効いた部品」を判定（GO 後 Phase 2 連続モード採点）。")
    else:
        print("  なし＝相対分位＋投げ売り枯渇でも 5m レンジ逆張りの素エッジは立たず（→ E28流 refine or 道具差し替え）。")
    print("=" * 92)


if __name__ == "__main__":
    main()
