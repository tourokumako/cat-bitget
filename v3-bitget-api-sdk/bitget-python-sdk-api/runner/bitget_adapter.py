from __future__ import annotations

import json
import time
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bitget.consts import GET, POST
from bitget.v2.mix.order_api import OrderApi


@dataclass(frozen=True)
class Keys:
    api_key: str
    api_secret: str
    passphrase: str


def load_keys(path: Path) -> Keys:
    keys = json.loads(path.read_text(encoding="utf-8"))

    def pick(*cands: str) -> Optional[str]:
        for k in cands:
            v = keys.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()
        return None

    api_key = pick("api_key", "apiKey", "API_KEY", "key")
    sec_key = pick("api_secret", "secret_key", "secretKey", "API_SECRET", "secret")
    passph = pick("passphrase", "api_passphrase", "passPhrase", "API_PASSPHRASE")

    if not (api_key and sec_key and passph):
        raise ValueError("missing api_key/api_secret/passphrase in keys json")
    return Keys(api_key=api_key, api_secret=sec_key, passphrase=passph)


def q_down(x: Decimal, tick: Decimal) -> Decimal:
    return (x / tick).to_integral_value(rounding=ROUND_DOWN) * tick


def q_up(x: Decimal, tick: Decimal) -> Decimal:
    return (x / tick).to_integral_value(rounding=ROUND_UP) * tick


def fmt_price_1dp(x: Decimal) -> str:
    # Bitgetの返り値が "88836.4" のような1桁小数だったログに合わせる
    return f"{x:.1f}"


class BitgetAdapter:
    """
    mix/USDT-FUTURES 専用の薄いアダプタ。
    ここ以外でSDKを叩かない。
    """

    def __init__(self, keys: Keys, paper_trading: bool) -> None:
        self.paper_trading = bool(paper_trading)
        self.api = OrderApi(keys.api_key, keys.api_secret, keys.passphrase)
        self.api.PAPER_TRADING = self.paper_trading

        if not hasattr(self.api, "placePosTpsl"):
            raise AttributeError("SDK OrderApi has no placePosTpsl")
        
        
    # --- PUBLIC helpers ---

    def get_contracts(self, product_type: str) -> Dict[str, Any]:
        r = self.api._request_with_params(
            GET,
            "/api/v2/mix/market/contracts",
            {"productType": product_type},
        )
        if r.get("code") != "00000":
            raise RuntimeError(f"contracts failed: {r}")
        return r

    def get_ticker(self, product_type: str, symbol: str) -> Dict[str, Any]:
        r = self.api._request_with_params(
            GET,
            "/api/v2/mix/market/ticker",
            {"productType": product_type, "symbol": symbol},
        )
        if r.get("code") != "00000":
            raise RuntimeError(f"ticker failed: {r}")
        return r

    def get_symbol_price(self, product_type: str, symbol: str) -> Dict[str, Any]:
        r = self.api._request_with_params(
            GET,
            "/api/v2/mix/market/symbol-price",
            {"productType": product_type, "symbol": symbol},
        )
        if r.get("code") != "00000":
            raise RuntimeError(f"symbol-price failed: {r}")
        return r

    def get_candles(self, product_type: str, symbol: str, granularity: str = "5m", limit: int = 100) -> Dict[str, Any]:
        r = self.api._request_with_params(
            GET,
            "/api/v2/mix/market/candles",
            {"productType": product_type, "symbol": symbol, "granularity": granularity, "limit": str(limit)},
        )
        if r.get("code") != "00000":
            raise RuntimeError(f"candles failed: {r}")
        return r        

    # --- READ-ONLY helpers ---

    def get_positions(self, product_type: str, margin_coin: str) -> List[Dict[str, Any]]:
        r = self.api._request_with_params(
            GET,
            "/api/v2/mix/position/all-position",
            {"productType": product_type, "marginCoin": margin_coin},
        )
        if r.get("code") != "00000":
            raise RuntimeError(f"positions failed: {r}")
        return r.get("data") or []
    
    def get_single_position(self, *, product_type: str, margin_coin: str, symbol: str) -> Optional[Dict[str, Any]]:
        ps = self.get_positions(product_type, margin_coin)
        sym = str(symbol).upper()
        for p in ps:
            try:
                if str(p.get("symbol", "")).upper() == sym:
                    return p
            except Exception:
                continue
        return None


    def pos_count(self, product_type: str, margin_coin: str) -> int:
        return len(self.get_positions(product_type, margin_coin))
    
    def get_pending_profit_loss(self, product_type: str, symbol: str) -> List[Dict[str, Any]]:
        r = self.api.ordersPlanPending(
            {"planType": "profit_loss", "productType": product_type, "symbol": symbol}
        )
        if r.get("code") != "00000":
            raise RuntimeError(f"pending failed: {r}")
        data = r.get("data") or {}
        lst = data.get("entrustedList")
        return [] if lst in (None, []) else list(lst)

    def get_fill_history(self, product_type: str, symbol: str,
                         limit: int = 20, order_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """約定履歴を取得（第一証拠: クローズ約定確認用）"""
        params: Dict[str, Any] = {"productType": product_type, "symbol": symbol, "limit": str(limit)}
        if order_id:
            params["orderId"] = order_id
        r = self.api._request_with_params(
            GET,
            "/api/v2/mix/order/fill-history",
            params,
        )
        if r.get("code") != "00000":
            raise RuntimeError(f"fill-history failed: {r}")
        data = r.get("data") or {}
        return data.get("fillList") or []

    def get_plan_order_history(self, product_type: str, symbol: str, limit: int = 20) -> List[Dict[str, Any]]:
        """plan order履歴を取得（第二証拠: TP/SL filled確認用）"""
        r = self.api._request_with_params(
            GET,
            "/api/v2/mix/order/orders-plan-history",
            {"productType": product_type, "symbol": symbol, "planType": "profit_loss", "limit": str(limit)},
        )
        if r.get("code") != "00000":
            raise RuntimeError(f"orders-plan-history failed: {r}")
        data = r.get("data") or {}
        return data.get("entrustedList") or []

    # --- EXEC helpers (still no retries) ---

    def place_market_order(
        self,
        *,
        symbol: str,
        product_type: str,
        margin_mode: str,
        margin_coin: str,
        size: str,
        side: str,
        trade_side: str,
        client_oid: str,
    ) -> Dict[str, Any]:
        r = self.api._request_with_params(
            POST,
            "/api/v2/mix/order/place-order",
            {
                "symbol": symbol,
                "productType": product_type,
                "marginMode": margin_mode,
                "marginCoin": margin_coin,
                "size": size,
                "side": side,
                "tradeSide": trade_side,
                "orderType": "market",
                "clientOid": client_oid,
            },
        )
        if r.get("code") != "00000":
            raise RuntimeError(f"place-order failed: {r}")
        return r
    
    def close_market_order(
        self,
        *,
        symbol: str,
        product_type: str,
        margin_mode: str,
        margin_coin: str,
        size: str,
        side: str,
        hold_side: str,   # "long" / "short"
        client_oid: str,
    ) -> Dict[str, Any]:
        r = self.api.closePositions({
            "symbol": symbol,
            "productType": product_type,
            "holdSide": hold_side,
        })
        if r.get("code") != "00000":
            raise RuntimeError(f"close-order failed: {r}")
        return r


    def wait_open_price_avg(
        self,
        *,
        product_type: str,
        margin_coin: str,
        max_wait_s: float = 6.0,
        poll_interval_s: float = 0.5,
    ) -> Decimal:
        deadline = time.time() + max_wait_s
        last_seen: Optional[str] = None
        while time.time() < deadline:
            ps = self.get_positions(product_type, margin_coin)
            if ps:
                opa = ps[0].get("openPriceAvg")
                last_seen = str(opa)
                try:
                    d = Decimal(str(opa))
                    if d > 0:
                        return d
                except Exception:
                    pass
            time.sleep(poll_interval_s)
        raise RuntimeError(f"openPriceAvg not ready (last_seen={last_seen})")

    def attach_tpsl_short(
        self,
        *,
        margin_coin: str,
        product_type: str,
        symbol: str,
        hold_side: str,  # "short"
        entry_price: Decimal,
        tp_pct: Decimal,
        sl_pct: Decimal,
        tick: Decimal,
    ) -> Tuple[Decimal, Decimal, Dict[str, Any]]:
        tp = q_down(entry_price * (Decimal("1") - tp_pct), tick)
        sl = q_up(entry_price * (Decimal("1") + sl_pct), tick)
        if not (tp < entry_price < sl):
            raise RuntimeError(f"tp<entry<sl violated: tp={tp} entry={entry_price} sl={sl}")

        r = self.api.placePosTpsl(
            {
                "marginCoin": margin_coin,
                "productType": product_type,
                "symbol": symbol,
                "holdSide": hold_side,
                "stopSurplusTriggerPrice": fmt_price_1dp(tp),
                "stopSurplusTriggerType": "mark_price",
                "stopSurplusExecutePrice": fmt_price_1dp(tp),
                "stopLossTriggerPrice": fmt_price_1dp(sl),
                "stopLossTriggerType": "mark_price",
                "stopLossExecutePrice": fmt_price_1dp(sl),
            }
        )
        if r.get("code") != "00000":
            raise RuntimeError(f"placePosTpsl failed: {r}")
        return tp, sl, r

    def cancel_profit_loss(
        self,
        *,
        symbol: str,
        product_type: str,
        margin_coin: str,
        order_id_list: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        r = self.api.cancelPlanOrder(
            {
                "orderIdList": order_id_list,
                "symbol": symbol,
                "productType": product_type,
                "marginCoin": margin_coin,
                "planType": "profit_loss",
            }
        )
        if r.get("code") != "00000":
            raise RuntimeError(f"cancelPlanOrder failed: {r}")
        return r
