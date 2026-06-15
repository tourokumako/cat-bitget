#!/usr/bin/env python3
"""score.py — 味見の機械（審判）: 売買記録 → 手数料込み net を月いくらで返す

役割（選手と審判の分離）:
  これは「審判」。戦略（ML / 手動）が出した売買記録を受け取り、正しいコストで
  「1 ヶ月いくら net で儲けたか」を **数字 1 つ**で返すだけ。戦略のロジックは一切含まない。
  どんな戦略でも、同じこの審判に通して比較する（＝固定した1つのスコアボード）。

入力 CSV に必要な列:
  entry_time, exit_time, side(LONG/SHORT), size_btc, entry_price, exit_price, exit_reason

コスト（eval_engine の確定値を流用・exchange_spec.md audit#19）:
  entry = 指値 maker / exit = TP_FILLED は maker・それ以外は成行 taker + slippage /
  funding = 保有中の 8h 境界(00/08/16 UTC)ごと dir×size×mark×rate（LONG 払い・SHORT 受取）。
  net = gross − entry_fee − exit_fee − slippage − funding。

正しさの担保:
  コスト定数と funding 境界計算は eval_engine（既知答えテスト T1-T5 pass 済）から import。
  実行時に「再計算した gross/fee が CSV の値と一致するか」を自己検算で出す（審判がデータを
  正しく読めている証拠）→ そのうえで CSV に欠けている slippage+funding を足した分が地面の差。
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eval_engine as ee  # noqa: E402  確定コスト定数 + funding 境界計算（検証済み計器）

# TP_FILLED と SL_FILLED は placePosTpsl 指値（maker）= run_once_v9.py L320-348 で executePrice=triggerPrice 確認済
# （手動は手数料負け回避で entry/exit とも maker 優先）。成行 taker は TIME / MFE_STALE_CUT /
# STOCH_REVERSE 等の能動クローズ（close_market_order）のみ。
# TRAIL_EXIT（P1/P21 トレーリング）は 2026-06-12 まこさん決定で maker に変更:
#   本番執行 = SL と同じ placePosTpsl（triggerPrice=executePrice の指値）を trail 水準でバーごとに更新する方式。
#   live エンジン（run_once_v9.py）に trail は未実装（grep 0件・P21 未稼働）で、taker 計上は replay 側の仮定だった。
#   live の損益 CSV も fee=maker×2 計上（run_once_v9.py L130-131）。すり抜けリスクの扱いは SL maker（E0.1 承認）と同前提。
MAKER_EXIT_REASONS = {"TP_FILLED", "SL_FILLED", "TRAIL_EXIT", "EDGE_TP"}  # 指値(resting limit)約定=maker。EDGE_TP=逆側端の利確指値(2026-06-15 追加・H13・既知答えテスト再pass)
# 成行/トリガ撤退=taker（現在 taker 扱いの全理由を明示＝既存分類を維持）
TAKER_EXIT_REASONS = {"TIME_EXIT", "MFE_STALE_CUT", "STOCH_REVERSE_EXIT", "PROFIT_LOCK",
                      "RSI_REVERSE_EXIT", "MAE_CUT", "FORCE_CLOSE_EOD", "CENTER_LOCK",
                      "ML_STANCH", "BOX_BREAK_SL"}
# 採点 CSV に現れる全 exit_reason（実データ列挙済）。未登録は assert_hard_constraints で STOP（黙って taker 計上しない・§2.9）
KNOWN_EXIT_REASONS = MAKER_EXIT_REASONS | TAKER_EXIT_REASONS


def _funding_for_trade(entry_ts: pd.Timestamp, exit_ts: pd.Timestamp,
                       direction: int, size: float, mark: float) -> float:
    """保有期間中の funding 合計（LONG 払い=正で控除 / SHORT 受取=負で加算）。
    mark は近似として entry_price を使用（funding は極小・$2000 ポジ×0.0002%/8h≒$0.004/回）。"""
    from datetime import timezone
    e = entry_ts.to_pydatetime().replace(tzinfo=timezone.utc)
    x = exit_ts.to_pydatetime().replace(tzinfo=timezone.utc)
    cost = 0.0
    for _ in ee._funding_boundaries(e, x):
        cost += direction * size * mark * ee.FUNDING_RATE_8H
    return cost


def assert_position_cap(df: pd.DataFrame, cap_btc: float = ee.POSITION_CAP_BTC) -> None:
    """【物理強制・false_positive §0-2 / 類型 H】同時保有の合計サイズが cap を超えたら採点を拒否して停止。

    本番で発注不可能（合計 0.12 BTC 超）な楽観記録を、審判が二度と net 化しないための関所。
    事案8(2026-05-15・合計2.28BTC) / 2026-06-07(地面 独立評価0.6BTC) の再演を物理的に封じる。
    1 ポジあたりでなく「保有中の全ポジションの合計」を時系列で見る（§0-2 の定義）。
    """
    d = df.copy()
    et = pd.to_datetime(d["entry_time"]).tolist()
    xt = pd.to_datetime(d["exit_time"]).tolist()
    sz = d["size_btc"].astype(float).tolist()
    events = [(et[i], sz[i]) for i in range(len(d))] + [(xt[i], -sz[i]) for i in range(len(d))]
    events.sort(key=lambda x: (x[0], x[1]))  # 同時刻は exit(マイナス) を先に処理
    cur = mx = 0.0
    mxt = None
    for t, s in events:
        cur = round(cur + s, 9)
        if cur > mx:
            mx = cur
            mxt = t
    if mx > cap_btc + 1e-9:
        sys.exit(
            f"[STOP・false_positive §0-2 違反] 同時保有の合計サイズ {mx:.4f} BTC > 上限 {cap_btc} BTC"
            f"（最初の超過 {mxt}）。\n"
            f"この売買記録は本番で発注不可能な楽観値です（1 ポジでなく合計上限）。\n"
            f"同時保有合計を {cap_btc} BTC 以内に収めた記録で出し直してください。採点を拒否します。"
        )


def assert_min_order(df: pd.DataFrame) -> None:
    """【物理強制・H9 / exchange_spec audit#19】最小注文 0.0001 BTC かつ 5 USDT 未満の発注が無いか。
    記録上の size_btc で下限を見る（per-add 下限は学習側で別途）。"""
    sz = df["size_btc"].astype(float)
    ep = df["entry_price"].astype(float)
    n_btc = int((sz < ee.MIN_ORDER_BTC - 1e-12).sum())
    if n_btc:
        sys.exit(f"[STOP・H9 違反] size_btc < {ee.MIN_ORDER_BTC} BTC（最小注文サイズ）が {n_btc} 件。本番で発注不可。")
    n_usd = int((sz * ep < ee.MIN_ORDER_USDT - 1e-9).sum())
    if n_usd:
        sys.exit(f"[STOP・H9 違反] 注文額 size×price < {ee.MIN_ORDER_USDT} USDT（最小注文額）が {n_usd} 件。本番で発注不可。")


def assert_hard_constraints(df: pd.DataFrame) -> None:
    """【物理強制・boundary validation】審判の入口で、売買記録から検証できるハード制約(invariant)を
    fail-fast で一括チェック。金融システムの作法: 違反は graceful recovery せず即停止
    （FIA/MiFID II pre-trade risk checks・defensive programming の invariant・state 不明での継続は禁止）。
    売買記録に現れない H2(leak)/H6(価格非依存)/H8(train末<採点始) は学習スクリプト側で assert（boundary 違い）。"""
    assert_position_cap(df)   # H1: 同時保有合計 ≤ 0.12 BTC
    assert_min_order(df)      # H9: 最小注文 0.0001 BTC / 5 USDT
    # 未登録 exit_reason STOP（物理対策・§2.9・2026-06-15）: maker/taker 未分類を黙って taker 計上しない＝
    # 戦略が新出口理由を足したのに審判が知らない食い違い(EDGE_TP 事案)を採点前に物理検出して止める。
    if "exit_reason" in df.columns:
        unknown = sorted(set(df["exit_reason"].astype(str)) - KNOWN_EXIT_REASONS)
        if unknown:
            sys.exit(
                f"[STOP・§2.9 未登録 exit_reason] {unknown} は maker/taker 未分類です。"
                f"黙って taker 計上せず採点を拒否します。\n"
                f"score.py の MAKER_EXIT_REASONS / TAKER_EXIT_REASONS に正しく登録してください"
                f"（指値約定=maker / 成行・トリガ=taker）。")


def score(df: pd.DataFrame) -> dict:
    df = df.copy()
    df["entry_time"] = pd.to_datetime(df["entry_time"])
    df["exit_time"] = pd.to_datetime(df["exit_time"])
    assert_hard_constraints(df)  # ★ 採点前に全ハード制約ゲートを通す（boundary・fail-fast・H13 審判の正しさの一部）
    df["dir"] = np.where(df["side"].str.upper() == "LONG", 1, -1)

    recomputed = []
    for _, r in df.iterrows():
        size = float(r["size_btc"]); ep = float(r["entry_price"]); xp = float(r["exit_price"])
        d = int(r["dir"]); reason = str(r["exit_reason"])
        gross = size * (xp - ep) * d
        entry_fee = ep * size * ee.MAKER_FEE                       # entry は常に指値 maker
        is_taker = reason not in MAKER_EXIT_REASONS
        exit_fee = xp * size * (ee.TAKER_FEE if is_taker else ee.MAKER_FEE)
        slippage = (xp * size * ee.SLIPPAGE) if is_taker else 0.0  # 成行のみ
        funding = _funding_for_trade(r["entry_time"], r["exit_time"], d, size, ep)
        net = gross - entry_fee - exit_fee - slippage - funding
        recomputed.append((gross, entry_fee + exit_fee, slippage, funding, net))

    rc = pd.DataFrame(recomputed, columns=["gross", "fee", "slippage", "funding", "net"])
    df = pd.concat([df.reset_index(drop=True), rc], axis=1)
    df["month"] = df["entry_time"].dt.strftime("%Y-%m")

    monthly = df.groupby("month")["net"].agg(["sum", "count"]).rename(
        columns={"sum": "net_usd", "count": "n"})
    n_months = len(monthly)
    total = float(df["net"].sum())

    # 自己検算: 再計算 gross/fee が CSV の既存列と一致するか（審判が正しく読めている証拠）
    selfcheck = {}
    if "gross_usd" in df.columns:
        selfcheck["gross_diff_max"] = float((df["gross"] - df["gross_usd"]).abs().max())
    if "fee_usd" in df.columns:
        selfcheck["fee_diff_max"] = float((df["fee"] - df["fee_usd"]).abs().max())
    if "net_usd" in df.columns:
        selfcheck["csv_net_total"] = float(df["net_usd"].sum())  # CSV(slippage/funding 抜き)の net

    # 異常値スメル（H12・false_positive §5 関所A）: 該当したら main で「異常値・要調査」を強制表示し「合格」と書かせない
    win_rate = float((df["net"] > 0).mean()) if len(df) else 0.0
    max_monthly = float(monthly["net_usd"].max()) if len(monthly) else 0.0
    eq = df.sort_values("exit_time")["net"].cumsum()
    max_dd = float((eq.cummax() - eq).max()) if len(df) else 0.0
    anomaly = []
    if win_rate > 0.70:
        anomaly.append(f"勝率 {win_rate*100:.1f}% > 70%")
    if max_monthly > 3800:
        anomaly.append(f"月次 net 最大 ${max_monthly:.0f} > $3,800（合格ライン $1,900 の2倍）")
    if total > 0 and max_dd < total * 0.05:
        anomaly.append(f"最大DD ${max_dd:.0f} < 合計 net の5%（出来すぎ・DD ほぼ無し）")
    # 注: IS/OOS Sharpe 比（§5 関所A③）は採点期間のみの score 単体では算出不可 → 学習側で別途検証

    return {"monthly": monthly, "n_months": n_months, "total": total,
            "monthly_avg": total / n_months if n_months else 0.0,
            "n_trades": len(df), "selfcheck": selfcheck, "anomaly": anomaly,
            "slippage_total": float(df["slippage"].sum()),
            "funding_total": float(df["funding"].sum())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trades_csv", help="売買記録 CSV（entry/exit/side/size/price/exit_reason 列）")
    ap.add_argument("--start", default=None, help="採点開始日 YYYY-MM-DD（entry_time で絞る・含む）")
    ap.add_argument("--end", default=None, help="採点終了日 YYYY-MM-DD（含む）")
    a = ap.parse_args()

    df = pd.read_csv(a.trades_csv)
    if a.start or a.end:
        et = pd.to_datetime(df["entry_time"])
        if a.start:
            df = df[et >= pd.Timestamp(a.start)]
        if a.end:
            df = df[pd.to_datetime(df["entry_time"]) < pd.Timestamp(a.end) + pd.Timedelta(days=1)]
        df = df.reset_index(drop=True)
        print(f"[期間フィルタ] {a.start or '最初'} 〜 {a.end or '最後'} → {len(df)} trades")
    res = score(df)

    print("=" * 64)
    print(f"審判（味見の機械）: {Path(a.trades_csv).name}")
    print(f"取引数 {res['n_trades']} / 期間 {res['n_months']} ヶ月")
    print("=" * 64)
    print(res["monthly"].to_string())
    print("-" * 64)
    print(f"★ 月平均 net = ${res['monthly_avg']:.2f}/月   （合計 ${res['total']:.2f}）")
    print("-" * 64)
    if res.get("anomaly"):
        print("⚠️ 異常値・要調査（H12・false_positive §5 関所A）:")
        for _a in res["anomaly"]:
            print(f"   - {_a}")
        print("   → 「合格」と書かず原因調査（leak / 過剰適合 / 集計ミスの疑い）。")
        print("-" * 64)
    sc = res["selfcheck"]
    if "csv_net_total" in sc:
        print(f"[自己検算] gross 最大差 ${sc.get('gross_diff_max', float('nan')):.4f} / "
              f"fee 最大差 ${sc.get('fee_diff_max', float('nan')):.4f}  (≒0 なら審判は CSV を正しく読めている)")
        print(f"[地面の差] CSV net 合計 ${sc['csv_net_total']:.2f}  →  審判 net 合計 ${res['total']:.2f}  "
              f"(差 = 追加した slippage ${res['slippage_total']:.2f} + funding ${res['funding_total']:.2f})")


if __name__ == "__main__":
    main()
