"""
Single place that constructs Alpaca clients so every module shares the same
auth/config. Verify import paths against the installed alpaca-py version —
the SDK has reorganized these modules before.
"""
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("APCA_API_KEY_ID")
API_SECRET = os.environ.get("APCA_API_SECRET_KEY")
PAPER = True  # hard-coded on purpose: this project only ever trades paper


def get_trading_client():
    """Trading client: account info, orders, positions."""
    from alpaca.trading.client import TradingClient
    if not API_KEY or not API_SECRET:
        raise RuntimeError(
            "Missing APCA_API_KEY_ID / APCA_API_SECRET_KEY. Copy .env.example "
            "to .env and fill in your PAPER account credentials."
        )
    return TradingClient(API_KEY, API_SECRET, paper=PAPER)


def get_option_data_client():
    """Market data client scoped to options (chains, quotes, greeks)."""
    from alpaca.data.historical.option import OptionHistoricalDataClient
    return OptionHistoricalDataClient(API_KEY, API_SECRET)


def get_stock_data_client():
    """Market data client for underlying price history (for IV rank calc)."""
    from alpaca.data.historical.stock import StockHistoricalDataClient
    return StockHistoricalDataClient(API_KEY, API_SECRET)
