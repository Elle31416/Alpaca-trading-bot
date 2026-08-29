"""
Central knobs for the strategy. Keep everything tunable here rather than
scattered through the codebase — makes the backtest/live parity easier to
reason about and easier to defend to judges ("here is every parameter").
"""

# --- Universe -----------------------------------------------------------
# Liquid, optionable names with reliably tight bid/ask spreads. Keep this
# list small while iterating; wide/illiquid chains will produce garbage
# fills and make the backtest lie to you.
WATCHLIST = ["SPY", "QQQ", "AAPL", "MSFT", "AMZN", "NVDA", "META"]

# --- IV Rank screening ----------------------------------------------------
IV_LOOKBACK_DAYS = 252          # trailing window for IV rank/percentile
IV_RANK_ENTRY_THRESHOLD = 50.0  # only consider names with IV rank >= this
MIN_DAYS_TO_EXPIRATION = 25
MAX_DAYS_TO_EXPIRATION = 45     # ~30-45 DTE is the standard theta-decay sweet spot

# --- Structure selection --------------------------------------------------
# "iron_condor" (defined risk both sides) or "credit_spread" (defined risk,
# one side — direction chosen by short-term trend filter in spread_builder).
STRUCTURE = "iron_condor"

SHORT_STRIKE_DELTA = 0.16       # ~1 std dev short strikes, standard for
                                 # premium-selling (roughly 84% OTM probability)
WING_WIDTH_DOLLARS = 5.0        # distance between short and long strike

# --- Risk management -------------------------------------------------------
PROFIT_TAKE_PCT_OF_MAX = 0.50   # close when 50% of max credit is captured
STOP_LOSS_MULTIPLE_OF_CREDIT = 2.0  # close if loss reaches 2x credit received
MAX_CONCURRENT_POSITIONS = 5
MAX_RISK_PER_TRADE_PCT_OF_EQUITY = 0.02  # 2% of account equity, max loss basis
MAX_PORTFOLIO_RISK_PCT_OF_EQUITY = 0.10  # sum of all open max-loss, as % of equity

# --- Execution ---------------------------------------------------------
ORDER_TIME_IN_FORCE = "day"
DEFAULT_QTY = 1  # contracts per structure; position sizing overrides this
                  # via execution/order_manager.size_position()
