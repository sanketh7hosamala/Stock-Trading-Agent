from research.news import get_recent_news
from research.fundamentals import get_stock_fundamentals


def generate_recommendation(
    symbol: str,
    risk_profile: str,
    news_client,
    market_data_client,
) -> dict:
    news = get_recent_news(
        news_client=news_client,
        symbol=symbol,
        days=7,
        max_articles=10,
    )

    fundamentals = get_stock_fundamentals(
        market_data_client=market_data_client,
        symbol=symbol,
        lookback_days=90,
    )

    closes = [float(bar["close"]) for bar in fundamentals["recent_bars"]]
    momentum = (closes[-1] / closes[-20] - 1) if len(closes) >= 20 else 0.0
    volatility = simple_volatility(closes)

    news_score = news_sentiment_placeholder(news["articles"])
    fundamental_score = fundamental_score_placeholder(fundamentals["fundamentals"])

    composite_score = (
        0.35 * normalize(momentum, -0.10, 0.10)
        + 0.25 * news_score
        + 0.25 * fundamental_score
        - 0.15 * normalize(volatility, 0.0, 0.05)
    )

    if composite_score >= 0.35:
        recommendation = "buy"
    elif composite_score <= -0.35:
        recommendation = "sell"
    elif abs(composite_score) < 0.10:
        recommendation = "hold"
    else:
        recommendation = "don't_buy"

    return {
        "symbol": symbol,
        "recommendation": recommendation,
        "confidence": round(abs(composite_score), 3),
        "composite_score": round(composite_score, 3),
        "inputs": {
            "momentum_20d": round(momentum, 4),
            "volatility": round(volatility, 4),
            "news_score": round(news_score, 3),
            "fundamental_score": round(fundamental_score, 3),
        },
        "risk_profile": risk_profile,
        "reasoning": [
            f"20-day momentum is {momentum:.2%}.",
            f"News score is {news_score:.2f}.",
            f"Fundamental score is {fundamental_score:.2f}.",
            "Recommendation is rule-based and is not financial advice.",
        ],
        "required_before_trade": [
            "User approval",
            "Risk-limit validation",
            "Current position and cash check",
        ],
    }


def normalize(value: float, low: float, high: float) -> float:
    if high == low:
        return 0.0
    return max(0.0, min(1.0, (value - low) / (high - low)))


def simple_volatility(closes: list[float]) -> float:
    if len(closes) < 2:
        return 0.0

    returns = [(closes[i] / closes[i - 1]) - 1 for i in range(1, len(closes))]
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / len(returns)
    return variance ** 0.5


def news_sentiment_placeholder(articles: list[dict]) -> float:
    return 0.5


def fundamental_score_placeholder(fundamentals: dict) -> float:
    return 0.5
