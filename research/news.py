from datetime import datetime, timedelta, timezone
from alpaca.data.requests import NewsRequest

def get_recent_news(news_client, symbol: str, days: int, max_articles: int) -> dict:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)

    request = NewsRequest(
        symbols=symbol,  # This SDK version expects a string here
        start=start,
        end=end,
        limit=max_articles,
        sort="DESC",
        include_content=False,
    )

    response = news_client.get_news(request)

    articles = []
    for item in response.data.get("news", []):
        articles.append(
            {
                "headline": item.headline,
                "summary": getattr(item, "summary", None),
                "url": str(item.url),
                "source": item.source,
                "published_at": item.created_at.isoformat(),
                "symbols": list(item.symbols),
            }
        )

    return {
        "symbol": symbol,
        "period": {"start": start.isoformat(), "end": end.isoformat()},
        "article_count": len(articles),
        "articles": articles,
    }
