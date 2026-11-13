from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient, NewsClient
#from alpaca.data.news import NewsClient

from config import ALPACA_API_KEY, ALPACA_SECRET_KEY

trading_client = TradingClient(
    api_key=ALPACA_API_KEY,
    secret_key=ALPACA_SECRET_KEY,
    paper=True,
)

market_data_client = StockHistoricalDataClient(
    api_key=ALPACA_API_KEY,
    secret_key=ALPACA_SECRET_KEY,
)

news_client = NewsClient(
    api_key=ALPACA_API_KEY,
    secret_key=ALPACA_SECRET_KEY,
)
