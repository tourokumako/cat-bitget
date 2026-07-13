#!/usr/bin/env python3
"""e37_traj_diag.py — read-only 検証（診断レーン・acceptance 免除・2026-07-14 まこさん承認・GO）

目的（まこさん指示）: entry 後の建玉の動きを手抜きせず詳細に観察し、挙動で分岐する。
   ＝Exit 状態機械を「思い込み」でなく実データの経路から設計するための Check（分析）。

観察する2つの経路:
  (1) 実際の経路: エンジンが記録した mfe_usd/mae_usd/net/exit_reason（＝現在の出口で切られた結果）
  (2) 自然な経路: entry から HORIZON バー先まで、現在の出口を無視して 5分足を辿った 含み損益 の推移
      （＝もし管理を変えて持ったら建玉がどう動くかの全挙動空間・状態機械の分岐設計の土台）

read-only: 戦略の実関数を import で再利用・print のみ・売買記録CSV/score.py に不関与（診断レーン）。
   ★因果性: 自然経路の MFE ピーク等は「観察（あたり付け）」専用＝Exit にそのまま使えば leak。
   実装する Exit は「走行ピークからの割戻し」等 その時点で取得可能な因果信号のみ（採否は実エンジン両窓 score.py）。
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild")
from v22_gate_diag import build_setup, run_cfg   # noqa: E402  検証済みセットアップを再利用（再実装しない＝ズレ回避）
import periods                                    # noqa: E402
import eval_engine as ee                          # noqa: E402  手数料の確定値（改造禁止）

TRAIN_END = periods.TRAIN_END
SC_START = periods.SCORE_START
SCORE_END = periods.SEAL_START
HORIZON = 48                                       # 自然経路を辿る本数（4h＝現行 T_MAX）
RT_FEE_PCT = 2 * ee.MAKER_FEE * 100                # maker 往復手数料 %（≈0.028）＝「含み益が費用を超えた」の目安


def main():
    print("=" * 100)
    print("E37 entry 後の建玉 詳細観察（Check・状態機械の分岐設計の土台・read-only 診断）")
    print("=" * 100)
    df, v15p_base, up20 = build_setup()
    trades = run_cfg(df, v15p_base, up20, {})      # incumbent(v22 OFF=v21_040 構成)＝基準地面
    ts = df["ts"].to_numpy()
    close = df["close"].to_numpy(float)
    idx_of = {pd.Timestamp(t).value: i for i, t in enumerate(ts)}

    # 採点窓の玉だけを対象（本番相当・SC_START〜SCORE_END）
    rows = [r for r in trades if SC_START <= pd.Timestamp(r["entry_time"]) < SCORE_END]
    print(f"\n採点窓 玉数 {len(rows)}（incumbent・SHORT のみ）／往復maker費 {RT_FEE_PCT:.3f}%")

    # ── (1) 実際の経路＝記録から粗分岐（含み益ピークが費用を超えたか）──
    recs = []
    for r in rows:
        i0 = idx_of.get(pd.Timestamp(r["entry_time"]).value)
        if i0 is None:
            continue
        ep = float(r["entry_price"]); size = float(r["size_btc"])
        mfe_usd = float(r["mfe_usd"]); mae_usd = float(r["mae_usd"]); net = float(r["net_usd"])
        fee = float(r["fee_usd"])
        # 含み益ピーク % （SHORT: mfe_usd>0 なら価格が下げて益が出た）
        mfe_pct = mfe_usd / (ep * size) * 100 if size > 0 else 0.0
        mae_pct = mae_usd / (ep * size) * 100 if size > 0 else 0.0
        had_profit = mfe_usd > fee                 # 費用を超える含み益が実在した＝利確の機会があった
        # ── (2) 自然な経路＝entry→HORIZON 先まで（現在の出口を無視）──
        j1 = min(i0 + HORIZON, len(close) - 1)
        path = (ep - close[i0:j1 + 1]) / ep * 100.0   # SHORT 含み損益 %（+ が益）
        nat_mfe = float(path.max()); nat_mfe_bar = int(path.argmax())
        nat_mae = float(path.min()); nat_mae_bar = int(path.argmin())
        nat_end = float(path[-1])
        # ピーク後にどれだけ戻したか（ピーク→その後の最悪＝反転の深さ・因果でなく観察）
        after = path[nat_mfe_bar:]
        giveback = nat_mfe - float(after.min()) if len(after) else 0.0
        recs.append(dict(reason=r["exit_reason"], net=net, fee=fee, hold_min=int(r["hold_min"]),
                         mfe_pct=mfe_pct, mae_pct=mae_pct, had_profit=had_profit,
                         nat_mfe=nat_mfe, nat_mfe_bar=nat_mfe_bar, nat_mae=nat_mae, nat_mae_bar=nat_mae_bar,
                         nat_end=nat_end, giveback=giveback,
                         stoch=r.get("stoch_k_at_entry"), adx=r.get("adx_at_entry")))
    d = pd.DataFrame(recs)
    print(f"再構成 {len(d)} 玉（idx マップ欠落 {len(rows)-len(d)}）")

    # ── 粗分岐（net 符号 × 含み益ピークが費用超え）──
    print("\n[粗分岐＝実際の経路] net 符号 × 含み益ピークが費用を超えたか")
    def blk(name, m):
        sub = d[m]
        if len(sub) == 0:
            print(f"  {name:<40} 0 玉"); return
        print(f"  {name:<40} {len(sub):>4}玉 net ${sub.net.sum():>8,.0f} / 平均MFE {sub.mfe_pct.mean():.3f}% / 平均保有 {sub.hold_min.mean():.0f}分")
    blk("勝ち（net>0）", d.net > 0)
    blk("負け・含み益ピーク費用超え(利食い損ね疑い A)", (d.net <= 0) & (d.had_profit))
    blk("負け・含み益ほぼ無し(即逆行=本物上昇 B)", (d.net <= 0) & (~d.had_profit))

    # ── TREND_CONT（出血の本体）を深掘り ──
    tc = d[d.reason == "TREND_CONT"]
    print(f"\n[TREND_CONT 深掘り] {len(tc)}玉 net ${tc.net.sum():,.0f}")
    if len(tc):
        n_prof = int((tc.had_profit).sum())
        print(f"  含み益ピークが費用を超えた玉（＝逃げ場が実在した）: {n_prof}/{len(tc)} = {n_prof/len(tc)*100:.0f}%")
        print(f"  実際の経路 平均MFE {tc.mfe_pct.mean():.3f}% / 平均MAE {tc.mae_pct.mean():.3f}%")
        print(f"  自然経路(entry→{HORIZON}本) 平均: MFE {tc.nat_mfe.mean():.3f}%(ピーク {tc.nat_mfe_bar.mean():.1f}本目) "
              f"/ MAE {tc.nat_mae.mean():.3f}% / {HORIZON}本後 {tc.nat_end.mean():.3f}%")
        print(f"  自然経路で {HORIZON}本後に含み益＞0 に戻る玉: {(tc.nat_end>0).sum()}/{len(tc)} "
              f"= {(tc.nat_end>0).mean()*100:.0f}%（戻る=レンジ往復／戻らない=本物上昇 の内訳）")

    # ── 因果トレーリングのあたり付け（走行ピークからの割戻しで畳む＝leak なし・あたり付け専用）──
    print(f"\n[因果トレーリング あたり付け] 走行ピークから D% 割戻しで maker 決済（その時点情報のみ＝leak なし）")
    print("  ⚠️あたり付け＝設計に焼かない・採否は実エンジン両窓 score.py（下は方向確認）")
    for D in (0.05, 0.10, 0.15, 0.20):
        tot = 0.0
        for r in rows:
            i0 = idx_of.get(pd.Timestamp(r["entry_time"]).value)
            if i0 is None:
                continue
            ep = float(r["entry_price"]); size = float(r["size_btc"])
            j1 = min(i0 + HORIZON, len(close) - 1)
            peak = -1e9; exit_px = None
            for j in range(i0, j1 + 1):
                p = (ep - close[j]) / ep * 100.0
                peak = max(peak, p)
                if peak > 0 and (peak - p) >= D:            # 益が出た後にピークから D% 落ちたら畳む（因果）
                    exit_px = close[j]; break
            if exit_px is None:
                exit_px = close[j1]                          # 未発火は HORIZON 末で clperse（比較用）
            gross = (ep - exit_px) * size
            fee = ep * size * ee.MAKER_FEE + exit_px * size * ee.MAKER_FEE
            tot += gross - fee
        print(f"    D={D:.2f}%  トレーリング net（採点窓・全玉に一律適用の粗試算）≈ ${tot:,.0f}")


if __name__ == "__main__":
    main()
