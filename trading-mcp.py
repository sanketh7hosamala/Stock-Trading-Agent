#import config
from mcp.server.mcpserver import MCPServer
from pydantic import Field
from typing import Literal

from alpaca_clients import news_client, market_data_client, trading_client
from research.news import get_recent_news
from research.fundamentals import get_stock_fundamentals
from analysis.recommendation import generate_recommendation
from trading.orders import submit_paper_order, get_order, cancel_order
from trading.risk import get_account_summary, get_open_positions


mcp = MCPServer("AlpacaPaperTradingMCP")


@mcp.tool(
    title="Get stock and company news",
    description="Fetch recent news for a stock symbol.",
)
def get_stock_news(
    symbol: str = Field(description="Stock ticker, e.g. AAPL"),
    days: int = Field(default=7, ge=1, le=30),
    max_articles: int = Field(default=10, ge=1, le=50),
) -> dict:
    return get_recent_news(
        news_client=news_client,
        symbol=symbol.upper(),
        days=days,
        max_articles=max_articles,
    )


@mcp.tool(
    title="Get stock fundamentals and market snapshot",
    description="Return a current quote, recent daily bars, and company fundamentals.",
)
def get_stock_financials(
    symbol: str = Field(description="Stock ticker, e.g. AAPL"),
    lookback_days: int = Field(default=90, ge=20, le=730),
) -> dict:
    return get_stock_fundamentals(
        market_data_client=market_data_client,
        symbol=symbol.upper(),
        lookback_days=lookback_days,
    )


@mcp.tool(
    title="Generate trading recommendation",
    description=(
        "Generate a structured buy / don't_buy / hold / sell recommendation "
        "from price action, news, fundamentals, and current exposure."
    ),
)
def get_trade_recommendation(
    symbol: str = Field(description="Stock ticker, e.g. AAPL"),
    risk_profile: str = Field(
        default="balanced",
        description="One of: conservative, balanced, aggressive",
    ),
) -> dict:
    return generate_recommendation(
        symbol=symbol.upper(),
        risk_profile=risk_profile,
        news_client=news_client,
        market_data_client=market_data_client,
    )


@mcp.tool(
    title="Execute paper trade",
    description=(
        "Submit an Alpaca paper market order, optionally as a bracket with "
        "stop-loss and take-profit exits. Requires explicit user approval."
    ),
)
def execute_trade(
    symbol: str = Field(description="Stock ticker, e.g. AAPL"),
    side: str = Field(description="Must be 'buy' or 'sell'"),
    quantity: int = Field(gt=0, description="Number of shares"),
    rationale: str = Field(description="Why this trade is being placed"),
    user_approved: bool = Field(
        description="Must be true; confirms user approval for this exact trade"
    ),
    order_mode: Literal["market", "bracket"] = Field(
        default="market",
        description=(
            "'market' submits a plain market order without exits; 'bracket' "
            "submits a market entry with stop-loss and take-profit exits."
        ),
    ),
    stop_loss_price: float | None = Field(
        default=None,
        gt=0,
        description="Required for bracket mode; omit for market mode",
    ),
    take_profit_price: float | None = Field(
        default=None,
        gt=0,
        description="Required for bracket mode; omit for market mode",
    ),
) -> dict:
    return submit_paper_order(
        symbol=symbol.upper(),
        side=side.lower(),
        quantity=quantity,
        rationale=rationale,
        order_mode=order_mode,
        stop_loss_price=stop_loss_price,
        take_profit_price=take_profit_price,
        user_approved=user_approved,
    )


@mcp.tool(title="Get account summary")
def get_account() -> dict:
    return get_account_summary(trading_client)


@mcp.tool(title="Get open positions")
def get_positions() -> list[dict]:
    return get_open_positions(trading_client)


@mcp.tool(title="Get order status")
def get_order_status(order_id: str = Field(description="Alpaca order ID")) -> dict:
    return get_order(trading_client, order_id)


@mcp.tool(title="Cancel order")
def cancel_paper_order(order_id: str = Field(description="Alpaca order ID")) -> dict:
    return cancel_order(trading_client, order_id)


if __name__ == "__main__":
    mcp.run()
