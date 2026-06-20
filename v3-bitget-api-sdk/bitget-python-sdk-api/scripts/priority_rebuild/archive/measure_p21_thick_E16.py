#!/usr/bin/env python3
"""measure_p21_thick_E16.py — P21 単独「全玉 0.12・USD ゲート pct 等価」版の replay（E16 配分レバー用）

狙い: P21 でサイズが entry/exit タイミングに影響する経路は P21_MFE_STALE_GATE_USD($4) のみ
（trail=%・TP/SL=%・TIME=分・RSI=指標・STAG=STAG_MIN_M 9999 で無効・PROFIT_LOCK 等は P21 非該当）。
サイズ 0.06→0.12 と同時にゲート $4→$8 にすれば pct 等価＝全玉のタイミングが地面 run と完全一致するはず。
→ 玉ごとに 0.06版 / 0.12版 の net を選ぶだけで「文脈帯配分」の正確な連続モード合成ができる。
自己検査（合成スクリプト側）: 地面 CSV と (entry_time, exit_time, exit_reason) 全件完全一致 assert。
V9 本体不変（import のみ）。
"""
from __future__ import annotations
import sys
import pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import replay_csv as rc                                       # noqa: E402
import gen_p23_candidates as gen                              # noqa: E402

OUT = ROOT / "results" / "priority_rebuild" / "ratchet" / "trades_p21_E16_thick.csv"


def main():
    params = rc._load_params()
    p21 = dict(params)
    for k in list(p21):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            p21[k] = (k == "ENABLE_P21_SHORT")
    p21["P21_POSITION_SIZE_BTC"] = 0.12
    p21["P21_MFE_STALE_GATE_USD"] = 8.0   # $4 × (0.12/0.06) = pct 等価
    print(f"[params] P21 only / size=0.12 / stale_gate=$8 (pct等価)")

    trades = rc.run(str(gen.OHLCV_CSV), p21, regime_switch=False)
    assert trades, "トレード 0 件（想定外・停止）"
    d = pd.DataFrame(trades)
    assert set(d["priority"].astype(int)) == {21} and set(d["side"]) == {"SHORT"}
    mx = d["size_btc"].astype(float).max()
    assert mx <= 0.12 + 1e-9, f"size max {mx} > 0.12"
    print(f"[自己検査] ✅ 全 {len(d)} 件 priority=21 / SHORT / size max={mx}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    d.to_csv(OUT, index=False)
    print(f"[出力] {OUT} / net合計（全期間）${d.net_usd.astype(float).sum():.1f}")


if __name__ == "__main__":
    main()
