#!/usr/bin/env python3
"""compose_p21_sized_E16.py — P21 文脈配分の合成・選定・採点用 CSV 生成（E16）

入力: trades_p21_E16_ground.csv（全玉0.06）/ trades_p21_E16_thick.csv（全玉0.12・失速ゲート$8=pct等価）
自己検査: 両 run の (entry_time, exit_time, exit_reason) 全件完全一致 assert
  → 一致すれば「玉ごとに 0.06版/0.12版 の net を選ぶ」合成が正確な連続モードになる（同時保有なし・タイミング同一）。

帯（entry 時点で取得可能・%のみ・H2/H6 充足）:
  ret4h  = entry_price / close(4h前) − 1（直近4hリターン）
  pos24h = (entry_price − 24h最安) / (24hレンジ幅)（24hレンジ内位置 0-100）

候補（2026-06-11 事前宣言・学習期間 2021-04〜2024-12 のみで1案選定・採点期間不接触）:
  案1: ret4h < −1% → 0.12 / 他 0.06
  案2: ret4h < −1% AND pos24h < 33 → 0.12 / 他 0.06
  案3: ret4h < −2% → 0.12 / 他 0.06
  対照実験: ret4h > +1% → 0.12（逆帯 thick・「文脈に情報がある」なら本命より悪化するはず）

使い方: python3 compose_p21_sized_E16.py            … 学習期間で3案比較（選定用・採点しない）
        python3 compose_p21_sized_E16.py --emit N   … 案N の合成 CSV を全期間で出力（score.py 用）
"""
from __future__ import annotations
import sys
import pathlib
import pandas as pd
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
RAT = ROOT / "results" / "priority_rebuild" / "ratchet"
BASE = RAT / "trades_p21_E16_ground.csv"
THICK = RAT / "trades_p21_E16_thick.csv"
OHLCV = ROOT / "data" / "BTCUSDT-5m-2021-04-01_03-31_1826d_V9FULL_safe.csv"
OUT = RAT / "trades_p21_E16_sized.csv"

TRAIN_END = pd.Timestamp("2024-12-31 23:59:59")


def load():
    b = pd.read_csv(BASE, parse_dates=["entry_time", "exit_time"])
    t = pd.read_csv(THICK, parse_dates=["entry_time", "exit_time"])
    # ---- 自己検査: タイミング完全一致（pct 等価が成立している証明） ----
    assert len(b) == len(t), f"件数不一致 base={len(b)} thick={len(t)}（pct等価が破れた・停止）"
    for col in ("entry_time", "exit_time", "exit_reason"):
        same = (b[col].values == t[col].values).all()
        assert same, f"{col} 不一致（pct等価が破れた・停止）"
    print(f"[自己検査] ✅ base/thick 全 {len(b)} 件で entry_time/exit_time/exit_reason 完全一致")

    px = pd.read_csv(OHLCV)
    ts_col = [c for c in px.columns if "time" in c.lower() or "ts" in c.lower()][0]
    px["dt"] = (pd.to_datetime(px[ts_col], unit="ms")
                if px[ts_col].dtype.kind in "iu" else pd.to_datetime(px[ts_col]))
    close = px.set_index("dt").sort_index()["close"]

    r4, pos24 = [], []
    idx = close.index
    for r in b.itertuples():
        e = r.entry_time
        p24 = close[(idx >= e - pd.Timedelta(hours=24)) & (idx <= e)]
        if len(p24) >= 49:
            r4.append((r.entry_price / p24.iloc[-49] - 1) * 100)
            hi, lo = p24.max(), p24.min()
            pos24.append((r.entry_price - lo) / (hi - lo) * 100 if hi > lo else 50.0)
        else:
            r4.append(np.nan)
            pos24.append(np.nan)
    b["ret4h"], b["pos24h"] = r4, pos24
    return b, t


def masks(b):
    return {
        1: (b.ret4h < -1.0),
        2: (b.ret4h < -1.0) & (b.pos24h < 33),
        3: (b.ret4h < -2.0),
        "ctrl_rev": (b.ret4h > 1.0),   # 対照: 逆帯 thick
    }


def compose_net(b, t, mask):
    """mask=True の玉を thick(0.12) に置換した net 系列"""
    net = b.net_usd.copy()
    net[mask.fillna(False)] = t.net_usd[mask.fillna(False)].values
    return net


def main():
    b, t = load()
    ms = masks(b)
    train = b.entry_time <= TRAIN_END

    if "--emit" in sys.argv:
        n = int(sys.argv[sys.argv.index("--emit") + 1])
        mask = ms[n].fillna(False)
        out = b.drop(columns=["ret4h", "pos24h"]).copy()
        cols_swap = [c for c in ("size_btc", "gross_usd", "fee_usd", "net_usd",
                                 "mfe_usd", "mae_usd", "tp_diff_usd") if c in out.columns]
        out.loc[mask, cols_swap] = t.loc[mask, cols_swap].values
        out.to_csv(OUT, index=False)
        n_thick = int(mask.sum())
        print(f"[emit] 案{n}: thick {n_thick}/{len(out)} 玉 → {OUT}")
        print(f"→ 採点: python3 scripts/priority_rebuild/score.py {OUT} --start 2025-04-01 --end 2025-12-31")
        return

    print(f"\n=== 学習期間（〜2024-12-31・{train.sum()}件）での候補比較（採点期間 不接触） ===")
    base_net = b.net_usd[train].sum()
    print(f"base(全玉0.06): ${base_net:.0f}")
    for k, mask in ms.items():
        comp = compose_net(b, t, mask)
        tr_net = comp[train].sum()
        n_thick = int((mask & train).fillna(False).sum())
        yearly = (comp[train].groupby(b.entry_time[train].dt.year).sum()
                  - b.net_usd[train].groupby(b.entry_time[train].dt.year).sum()).round(0)
        print(f"案{k}: 合成net ${tr_net:.0f}（差分 {tr_net-base_net:+.0f}・thick {n_thick}玉）年別差分 {dict(yearly)}")


if __name__ == "__main__":
    main()
