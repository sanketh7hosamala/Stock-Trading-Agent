from math import isfinite
from typing import Any, Literal
import uuid

from alpaca.data import StockLatestQuoteRequest
from alpaca.data.enums import DataFeed
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderClass, OrderSide, OrderType, TimeInForce
from alpaca.trading.requests import StopLossRequest, TakeProfitRequest
from datetime import datetime, timezone
from alpaca_clients import market_data_client, trading_client
from config import MAX_QUOTE_AGE
from trading.risk import validate_trade
from storage.journal import log_trade


def submit_paper_order(
    symbol: str,
    side: str,
    quantity: int,
    rationale: str,
    user_approved: bool,
    order_mode: Literal["market", "bracket"] = "market",
    stop_loss_price: float | None = None,
    take_profit_price: float | None = None,
) -> dict:
    if not user_approved:
        return {
            "status": "rejected",
            "reason": "User approval is required before order submission",
        }

    symbol = symbol.strip().upper()
    side = side.lower()
    if side not in {"buy", "sell"}:
        return {"status": "rejected", "reason": "side must be 'buy' or 'sell'"}
    if quantity <= 0:
        return {"status": "rejected", "reason": "quantity must be greater than zero"}
    if order_mode not in {"market", "bracket"}:
        return {
            "status": "rejected",
            "reason": "order_mode must be 'market' or 'bracket'",
        }

    if order_mode == "bracket" and (
        stop_loss_price is None or take_profit_price is None
    ):
        return {
            "status": "rejected",
            "reason": "bracket orders require both stop-loss and take-profit prices",
        }
    if order_mode == "market" and (
        stop_loss_price is not None or take_profit_price is not None
    ):
        return {
            "status": "rejected",
            "reason": "stop-loss and take-profit prices apply only to bracket orders",
        }
    if order_mode == "bracket":
        assert stop_loss_price is not None
        assert take_profit_price is not None
        if (
            not isfinite(stop_loss_price)
            or not isfinite(take_profit_price)
            or stop_loss_price <= 0
            or take_profit_price <= 0
        ):
            return {
                "status": "rejected",
                "reason": "stop-loss and take-profit prices must be finite and positive",
            }

    reference_price = get_reference_price(symbol, side)

    if order_mode == "bracket":
        assert stop_loss_price is not None
        assert take_profit_price is not None
        prices_are_valid = (
            stop_loss_price < reference_price < take_profit_price
            if side == "buy"
            else take_profit_price < reference_price < stop_loss_price
        )
        if not prices_are_valid:
            return {
                "status": "rejected",
                "reason": (
                    "For a buy bracket, stop-loss must be below and take-profit above "
                    "the current reference price; for a sell bracket, take-profit must "
                    "be below and stop-loss above it."
                ),
                "reference_price": reference_price,
            }

    risk = validate_trade(symbol, side, quantity, reference_price)
    if not risk["approved"]:
        return {
            "status": "rejected",
            "reason": "Risk validation failed",
            "risk": risk,
        }

    client_order_id = f"mcp-{uuid.uuid4()}"

    request_options: dict[str, Any] = {}
    if order_mode == "bracket":
        assert stop_loss_price is not None
        assert take_profit_price is not None
        request_options = {
            "order_class": OrderClass.BRACKET,
            "take_profit": TakeProfitRequest(limit_price=take_profit_price),
            "stop_loss": StopLossRequest(stop_price=stop_loss_price),
        }

    request = MarketOrderRequest(
        symbol=symbol,
        qty=quantity,
        side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
        type=OrderType.MARKET,
        time_in_force=TimeInForce.DAY,
        client_order_id=client_order_id,
        **request_options,
    )

    order = trading_client.submit_order(request)

    result = {
        "status": "submitted",
        "order_id": str(order.id),
        "client_order_id": client_order_id,
        "symbol": order.symbol,
        "side": order.side.value,
        "quantity": float(order.qty),
        "order_type": "market",
        "order_mode": order_mode,
        "order_class": "bracket" if order_mode == "bracket" else "simple",
        "time_in_force": order.time_in_force.value,
        "submitted_at": order.submitted_at.isoformat(),
        "rationale": rationale,
        "risk": risk,
    }
    if order_mode == "bracket":
        result["stop_loss"] = {"stop_price": stop_loss_price}
        result["take_profit"] = {"limit_price": take_profit_price}
        result["exit_order_note"] = (
            "Bracket exit orders activate when the parent order fills. "
            "Stop orders may execute at a different price."
        )

    log_trade(
        symbol=symbol,
        side=side,
        quantity=quantity,
        rationale=rationale,
        order_id=client_order_id,
        status="submitted",
    )

    return result


def get_reference_price(symbol: str, side: str) -> float:
    symbol = symbol.strip().upper()

    if side not in {"buy", "sell"}:
        raise ValueError("side must be 'buy' or 'sell'")

    request = StockLatestQuoteRequest(
        symbol_or_symbols=symbol,
        feed=DataFeed.IEX,
    )
    quotes = market_data_client.get_stock_latest_quote(request)
    quote = quotes.get(symbol)

    if quote is None:
        raise RuntimeError(f"No latest quote returned for {symbol}")

    age = datetime.now(timezone.utc) - quote.timestamp
    if age > MAX_QUOTE_AGE:
        raise RuntimeError(f"Latest quote for {symbol} is stale")

    price = quote.ask_price if side == "buy" else quote.bid_price
    if price is None or price <= 0:
        raise RuntimeError(f"Quote has no valid {'ask' if side == 'buy' else 'bid'} price")

    return float(price)


def get_order(trading_client, order_id: str) -> dict:
    order = trading_client.get_order_by_id(GetOrdersRequest(order_id=order_id))
    return {
        "order_id": str(order.id),
        "symbol": order.symbol,
        "side": order.side.value,
        "quantity": float(order.qty),
        "filled_quantity": float(order.filled_qty),
        "status": order.status.value,
        "order_class": order.order_class.value if order.order_class else None,
        "legs": [
            {
                "order_id": str(leg.id),
                "side": leg.side.value if leg.side else None,
                "quantity": float(leg.qty) if leg.qty is not None else None,
                "filled_quantity": (
                    float(leg.filled_qty) if leg.filled_qty is not None else None
                ),
                "status": leg.status.value,
                "type": leg.type.value if leg.type else None,
                "stop_price": (
                    float(leg.stop_price) if leg.stop_price is not None else None
                ),
                "limit_price": (
                    float(leg.limit_price) if leg.limit_price is not None else None
                ),
            }
            for leg in (order.legs or [])
        ],
        "submitted_at": order.submitted_at.isoformat(),
    }


def cancel_order(trading_client, order_id: str) -> dict:
    trading_client.cancel_order_by_id(order_id)
    return {"order_id": order_id, "status": "cancel_requested"}
