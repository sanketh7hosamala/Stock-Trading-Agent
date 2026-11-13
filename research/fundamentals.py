import os
from datetime import datetime, timedelta, timezone

import httpx
from alpaca.data.requests import StockBarsRequest
from alpaca.data.enums import DataFeed
from alpaca.data.timeframe import TimeFrame

FMP_API_KEY = os.getenv("FMP_API_KEY")


def get_stock_fundamentals(market_data_client, symbol: str, lookback_days: int) -> dict:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=lookback_days)

    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
        feed=DataFeed.IEX,
    )

    bars = market_data_client.get_stock_bars(request).df.reset_index()

    if bars.empty:
        raise ValueError(
            f"No historical bars returned for {symbol} in the requested period"
        )

    latest = bars.iloc[-1]

    recent_bars = bars.tail(30).to_dict(orient="records")
    for bar in recent_bars:
        timestamp = bar.get("timestamp")
        if hasattr(timestamp, "isoformat"):
            bar["timestamp"] = timestamp.isoformat()

    return {
        "symbol": symbol,
        "as_of": latest["timestamp"].isoformat(),
        "price_snapshot": {
            "close": float(latest["close"]),
            "open": float(latest["open"]),
            "high": float(latest["high"]),
            "low": float(latest["low"]),
            "volume": int(latest["volume"]),
        },
        "recent_bars": recent_bars,
        "fundamentals": fetch_fmp_profile(symbol),
    }


def fetch_fmp_profile(symbol: str) -> dict:
    if not FMP_API_KEY:
        return {"status": "unavailable", "reason": "FMP_API_KEY not configured"}

    url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}"
    try:
        response = httpx.get(url, params={"apikey": FMP_API_KEY}, timeout=15)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return {
            "status": "unavailable",
            "reason": (
                f"Financial Modeling Prep returned HTTP {exc.response.status_code}; "
                "check the API key, subscription, and endpoint access."
            ),
        }
    except httpx.RequestError as exc:
        return {
            "status": "unavailable",
            "reason": f"Financial Modeling Prep request failed ({type(exc).__name__}).",
        }

    try:
        data = response.json()
    except ValueError:
        return {
            "status": "unavailable",
            "reason": "Financial Modeling Prep returned an invalid JSON response.",
        }
    if not data:
        return {"status": "not_found"}

    profile = data[0]
    return {
        "status": "ok",
        "company_name": profile.get("companyName"),
        "sector": profile.get("sector"),
        "industry": profile.get("industry"),
        "description": profile.get("description"),
        "market_cap": profile.get("mktCap"),
        "beta": profile.get("beta"),
        "exchange": profile.get("exchangeShortName"),
    }
