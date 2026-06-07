#!/usr/bin/env python3
"""
eval_engine.py — 評価基盤 項目A: 約定・コスト計器（自前・replay_csv 準拠 + 楽観3点是正）

位置づけ:
  ml_pipeline_baseline_v1.md §0.8 / §6「評価基盤 詳細設計 A」の実装。
  全工程の Stage 3/4 PnL 評価はこのエンジンで net を測る。
  既存 run_phase4_b.py の compute_pnl（全決済 maker・無条件約定）の不正を置き換える
  「正しい計器」。run_phase4_b は触らず、本モジュールを新規に作る（取り違え防止）。

  ⚠️ 本エンジンは「正直に測る」担保のみ。net が正でも戦略が良いとは限らない（方向エッジは別問題）。

正しさの証明:
  test_eval_engine_known_answers.py の既知答えテスト T1-T5（数学的事実）が全 pass すること。
  まこさんはテスト結果だけ見れば良い（技術不要・L-242）。

確定値の出所（baseline §0.4 / exchange_spec.md audit#19）:
  maker 0.014% (0.00014) / taker 0.042% (0.00042) / slippage 0.005% (成行のみ) /
  funding median +0.0002%/8h (LONG払い・SHORT受取) / TTL 3本 / entry limit = close×(1∓0.0001) /
  ポジション上限 合計 0.12 BTC（§0.5）

仕様（baseline §6 A・1字1句準拠）:
  - Entry 約定: シグナル bar i（close 確定）→ bar i+1 で指値 limit=close_i×(1∓0.0001)。
    bar j (i+1≤j≤i+TTL=3) で LONG:low_j≤limit / SHORT:high_j≥limit で約定（価格=limit・maker）。
    TTL 内未到達 = 取引不成立（記録しない・None を返す）。
  - Exit（replay_csv 楽観3点是正）:
    ① SL を TP より先に判定（同 bar 両到達は不利側=SL 先着）
    ② gap 反映: SL 飛び越えは min(sl,open_j)(LONG) / max(sl,open_j)(SHORT) で約定
    ③ touch でなく保守 fill（exit 判定は entry bar の次 bar から開始）
    TP・SL=指値 maker（placePosTpsl・run_once_v9.py L320-348 executePrice=triggerPrice）/ TIME・能動クローズ=成行 taker + slippage。
  - コスト: entry=maker / exit=maker(TP・SL) or taker(TIME/能動クローズ) / slippage 0.005%(成行のみ) /
    funding=保有中の 8h 境界(00/08/16 UTC)ごとに direction×size×mark×rate。net=gross−全コスト。
  - 0.12 BTC: 任意 t で sum(active)≤0.12 を assert（§0.5・assert_position_cap）。

本番再現性（Prime Directive・§0.3）:
  推論時点 t で取得可能な値のみ使用。exit 判定は entry 約定 bar の次 bar 以降の OHLC のみ参照
  （未来 bar を先読みしない）。MFE/MAE 等の保有期間最大値は判定に使わない。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import numpy as np

# ── 確定値（baseline §0.4・exchange_spec.md audit#19）────────────────────────
MAKER_FEE = 0.00014          # 0.014% 指値 post_only
TAKER_FEE = 0.00042          # 0.042% 成行
SLIPPAGE = 0.00005           # 0.005% 成行のみ
FUNDING_RATE_8H = 0.000002   # +0.0002%/8h median（LONG 払い・SHORT 受取）
ENTRY_LIMIT_OFFSET = 0.0001  # 指値 = close×(1∓0.0001)
DEFAULT_TTL = 3              # 指値 TTL 本数（15分）
POSITION_CAP_BTC = 0.12      # 合計上限（§0.5・H1）
MIN_ORDER_BTC = 0.0001       # 最小注文サイズ（H9・exchange_spec audit#19 contracts API minTradeNum）
MIN_ORDER_USDT = 5.0         # 最小注文額（H9・exchange_spec audit#19 contracts API minTradeUSDT）

LONG = 1
SHORT = -1

# Exit 種別 → 成行か否か（成行なら taker + slippage）
# TP/SL は placePosTpsl 指値（maker）= run_once_v9.py L320-348 で executePrice=triggerPrice 確認済（手動は手数料負け回避で maker 優先）。
# 成行 taker は TIME(時間切れ) と能動クローズ(ACTIVE: トレーリング/MFE_STALE/STOCH_REVERSE 等 close_market) のみ。
_TAKER_REASONS = {"TIME", "ACTIVE"}


@dataclass
class TradeResult:
    """1 トレードの約定・コスト内訳。net = gross − fee − slippage − funding。"""
    direction: int
    size_btc: float
    fill_idx: int          # entry 約定 bar の index
    entry_price: float
    exit_idx: int          # exit 約定 bar の index
    exit_price: float
    exit_reason: str       # "TP" | "SL" | "TIME" | "ACTIVE"
    gross: float           # size×(exit−entry)×dir（コスト前）
    fee: float             # entry fee + exit fee（>0・控除）
    slippage_cost: float   # 成行 exit のみ（>0・控除）
    funding_cost: float    # 8h 境界ごと（LONG 払い=正で控除 / SHORT 受取=負で加算）
    net: float             # gross − fee − slippage_cost − funding_cost


def _funding_boundaries(entry_ts: datetime, exit_ts: datetime) -> list[datetime]:
    """(entry_ts, exit_ts] 内の funding 精算時刻（UTC 00:00 / 08:00 / 16:00）を列挙。"""
    if exit_ts <= entry_ts:
        return []
    # entry の当日 00:00 UTC から 8h 刻みで走査
    start = entry_ts.astimezone(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    boundaries: list[datetime] = []
    t = start
    # exit を超えるまで 8h ずつ進める
    while t <= exit_ts:
        if entry_ts < t <= exit_ts and t.hour in (0, 8, 16):
            boundaries.append(t)
        t = t + timedelta(hours=8)
    return boundaries


def simulate_trade(
    signal_idx: int,
    direction: int,
    size_btc: float,
    opens: np.ndarray,
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    timestamps: np.ndarray,
    tp_pct: float,
    sl_pct: float,
    max_hold_bars: int,
    ttl: int = DEFAULT_TTL,
    maker: float = MAKER_FEE,
    taker: float = TAKER_FEE,
    slippage: float = SLIPPAGE,
    funding_rate_8h: float = FUNDING_RATE_8H,
) -> TradeResult | None:
    """1 トレードを約定・コストモデルでシミュレートし net を返す。

    Returns:
        TradeResult。指値が TTL 内に約定しなければ None（取引不成立・記録しない）。

    本番再現性: signal bar i の close 確定後に発注。exit は約定 bar の「次 bar」以降のみ参照。
    """
    if direction not in (LONG, SHORT):
        raise ValueError(f"direction は {LONG}(LONG) / {SHORT}(SHORT) のみ: {direction}")
    n = len(closes)
    assert len(opens) == len(highs) == len(lows) == len(closes) == len(timestamps) == n

    # ── Entry 約定（指値 maker・TTL 内・未到達は取引不成立）──────────────────
    sig_close = float(closes[signal_idx])
    if direction == LONG:
        limit = sig_close * (1.0 - ENTRY_LIMIT_OFFSET)
    else:
        limit = sig_close * (1.0 + ENTRY_LIMIT_OFFSET)

    fill_idx = None
    for j in range(signal_idx + 1, min(signal_idx + 1 + ttl, n)):
        if direction == LONG and lows[j] <= limit:
            fill_idx = j
            break
        if direction == SHORT and highs[j] >= limit:
            fill_idx = j
            break
    if fill_idx is None:
        return None  # 取引不成立（§6 A: 記録しない）

    entry_price = limit  # 指値約定＝limit 価格（maker）

    # ── TP / SL 価格 ────────────────────────────────────────────────────────
    if direction == LONG:
        tp_price = entry_price * (1.0 + tp_pct)
        sl_price = entry_price * (1.0 - sl_pct)
    else:
        tp_price = entry_price * (1.0 - tp_pct)
        sl_price = entry_price * (1.0 + sl_pct)

    # ── Exit 判定（約定 bar の次 bar から・SL 先着・gap 反映・保守 fill）──────
    exit_idx = None
    exit_price = None
    exit_reason = None
    last_bar = min(fill_idx + max_hold_bars, n - 1)
    for j in range(fill_idx + 1, last_bar + 1):
        # ① SL を TP より先に判定（同 bar 両到達は不利側=SL 先着）
        if direction == LONG:
            if lows[j] <= sl_price:
                # ② gap: open が SL を飛び越えていたら open 約定（不利）
                exit_price = min(sl_price, float(opens[j]))
                exit_idx, exit_reason = j, "SL"
                break
            if highs[j] >= tp_price:
                exit_price = tp_price  # 指値 maker
                exit_idx, exit_reason = j, "TP"
                break
        else:  # SHORT
            if highs[j] >= sl_price:
                exit_price = max(sl_price, float(opens[j]))
                exit_idx, exit_reason = j, "SL"
                break
            if lows[j] <= tp_price:
                exit_price = tp_price
                exit_idx, exit_reason = j, "TP"
                break

    # TP/SL いずれも未発動 → TIME_EXIT（成行 taker・最終 bar の close）
    if exit_idx is None:
        exit_idx = last_bar
        exit_price = float(closes[last_bar])
        exit_reason = "TIME"

    # ── コスト計算 ──────────────────────────────────────────────────────────
    gross = size_btc * (exit_price - entry_price) * direction

    fee_entry = entry_price * size_btc * maker  # entry は常に指値 maker
    exit_is_taker = exit_reason in _TAKER_REASONS
    exit_fee_rate = taker if exit_is_taker else maker
    fee_exit = exit_price * size_btc * exit_fee_rate
    fee = fee_entry + fee_exit

    slippage_cost = (exit_price * size_btc * slippage) if exit_is_taker else 0.0

    # funding: 保有中の 8h 境界ごと direction×size×mark×rate（LONG 払い=控除）
    entry_ts = _to_utc(timestamps[fill_idx])
    exit_ts = _to_utc(timestamps[exit_idx])
    funding_cost = 0.0
    for bts in _funding_boundaries(entry_ts, exit_ts):
        b_idx = int(np.searchsorted(timestamps, np.datetime64(bts.replace(tzinfo=None))))
        b_idx = min(max(b_idx, 0), n - 1)
        mark = float(closes[b_idx])
        funding_cost += direction * size_btc * mark * funding_rate_8h

    net = gross - fee - slippage_cost - funding_cost

    return TradeResult(
        direction=direction, size_btc=size_btc,
        fill_idx=fill_idx, entry_price=entry_price,
        exit_idx=exit_idx, exit_price=exit_price, exit_reason=exit_reason,
        gross=gross, fee=fee, slippage_cost=slippage_cost,
        funding_cost=funding_cost, net=net,
    )


def _to_utc(ts) -> datetime:
    """np.datetime64 / pandas.Timestamp / datetime を UTC aware datetime に正規化。"""
    if isinstance(ts, np.datetime64):
        py = ts.astype("datetime64[ns]").astype("int64") / 1e9
        return datetime.fromtimestamp(py, tz=timezone.utc)
    if isinstance(ts, datetime):
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    # pandas.Timestamp など to_pydatetime を持つ場合
    if hasattr(ts, "to_pydatetime"):
        dt = ts.to_pydatetime()
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    raise TypeError(f"未対応の timestamp 型: {type(ts)}")


def assert_position_cap(active_sizes_btc: list[float], cap: float = POSITION_CAP_BTC) -> float:
    """任意時点 t での保有合計が cap(=0.12 BTC) 以下であることを assert（§0.5）。

    Returns:
        合計 BTC。超過時は AssertionError。
    """
    total = float(sum(active_sizes_btc))
    assert total <= cap + 1e-12, (
        f"ポジション上限違反: sum(active)={total:.6f} BTC > cap={cap} BTC（§0.5・false_positive §0-2 類型H）"
    )
    return total
