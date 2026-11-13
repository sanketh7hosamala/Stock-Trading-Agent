from datetime import datetime, timezone

from alpaca_clients import trading_client
from config import (
    MAX_DAILY_TRADES,
    MAX_POSITION_NOTIONAL_EUR,
    MAX_SINGLE_POSITION_PCT,
)


def get_account_summary(trading_client) -> dict:
    account = trading_client.get_account()
    return {
        "account_id": str(account.id),
        "status": account.status.value,
        "currency": account.currency,
        "cash": float(account.cash),
        "equity": float(account.equity),
        "buying_power": float(account.buying_power),
        #"paper_account": str(getattr(account, "_paper", False)),
    }


def get_open_positions(trading_client) -> list[dict]:
    positions = trading_client.get_all_positions()
    return [
        {
            "symbol": position.symbol,
            "quantity": float(position.qty),
            "avg_entry_price": float(position.avg_entry_price),
            "market_value": float(position.market_value),
            "unrealized_pl": float(position.unrealized_pl),
            "unrealized_plpc": float(position.unrealized_plpc),
        }
        for position in positions
    ]


def validate_trade(symbol: str, side: str, quantity: int, price: float) -> dict:
    account = trading_client.get_account()
    equity = float(account.equity)
    cash = float(account.cash)

    notional = quantity * price
    max_notional = min(
        MAX_POSITION_NOTIONAL_EUR,
        equity * MAX_SINGLE_POSITION_PCT,
    )

    errors = []

    if side not in {"buy", "sell"}:
        errors.append("side must be 'buy' or 'sell'")

    if side == "buy" and notional > max_notional:
        errors.append(
            f"Order notional {notional:.2f} exceeds limit {max_notional:.2f}"
        )

    if side == "buy" and notional > cash:
        errors.append("Insufficient paper-account cash")

    if daily_trade_count() >= MAX_DAILY_TRADES:
        errors.append("Daily trade limit reached")

    return {
        "approved": not errors,
        "errors": errors,
        "account_equity": equity,
        "account_cash": cash,
        "reference_price": price,
        "order_notional": notional,
        "max_allowed_notional": max_notional,
    }


def daily_trade_count() -> int:
    return 0
