from datetime import timedelta
import os
from dotenv import load_dotenv
from datetime import timedelta
load_dotenv()

ALPACA_API_KEY = os.environ["ALPACA_API_KEY"]
ALPACA_SECRET_KEY = os.environ["ALPACA_SECRET_KEY"]

MAX_POSITION_NOTIONAL_EUR = float(os.getenv("MAX_POSITION_NOTIONAL_EUR", "500"))
MAX_SINGLE_POSITION_PCT = float(os.getenv("MAX_SINGLE_POSITION_PCT", "0.05"))
MAX_DAILY_TRADES = int(os.getenv("MAX_DAILY_TRADES", "10"))
MAX_QUOTE_AGE = timedelta(seconds=60)