# Alpaca Paper-Trading MCP Server

A Model Context Protocol (MCP) server exposing tools for stock research, rule-based recommendations, and Alpaca paper-trading execution.

## Tools

- `get_stock_news`: recent news for a symbol
- `get_stock_financials`: quote, recent bars, and company fundamentals
- `get_trade_recommendation`: buy / don't_buy / hold / sell recommendation
- `execute_trade`: validated market order on the Alpaca paper account
- `get_account_summary`: account equity, cash, and buying power
- `get_open_positions`: current paper-account positions
- `get_order_status`: retrieve an order by ID
- `cancel_order`: cancel an open order

## Setup

```bash
uv sync
cp .env.example .env
# Add your Alpaca PAPER API credentials and optional FMP API key
uv run trading-mcp.py # to run MCP
python interactive-agent.py # to run interactive claude Agent
```

## Safety

- The server is hard-coded to Alpaca paper trading.
- `execute_trade` requires `user_approved=true`.
- Risk limits are enforced before order submission.
- Every submitted order is recorded in `data/trades.db`.

This software is for research and education only. It is not financial advice.
