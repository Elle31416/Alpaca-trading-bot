"""
Lightweight historical backtest for the IV-rank premium-harvesting logic.

This is deliberately simple — a daily-bar replay, not a full options-pricing
simulation — because the goal for a hackathon submission is to demonstrate
"this logic has a real edge over months, not just five noisy days," not to
build a production-grade options backtester in a week.

Real historical option prices/IV are the expensive part to get right; this
harness is structured so you can swap in a real historical options data
source (Alpaca's historical options data, or a vendor like ORATS/CBOE) behind
the same interface without touching the strategy logic.

Run:
    python backtest/backtest.py
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

import config
from strategy.iv_rank import iv_rank, iv_percentile, realized_vol_proxy_series


@dataclass
class BacktestTrade:
    date: pd.Timestamp
    symbol: str
    iv_rank_at_entry: float
    simulated_pnl: float


@dataclass
class BacktestResult:
    trades: list[BacktestTrade] = field(default_factory=list)

    @property
    def total_pnl(self) -> float:
        return sum(t.simulated_pnl for t in self.trades)

    @property
    def win_rate(self) -> float:
        if not self.trades:
            return 0.0
        wins = sum(1 for t in self.trades if t.simulated_pnl > 0)
        return wins / len(self.trades) * 100

    def equity_curve(self) -> pd.Series:
        df = pd.DataFrame([(t.date, t.simulated_pnl) for t in self.trades], columns=["date", "pnl"])
        df = df.sort_values("date")
        return df.set_index("date")["pnl"].cumsum()


def simulate_iron_condor_pnl(realized_move_pct: float, credit_pct_of_width: float) -> float:
    """
    Extremely simplified payoff model: if the underlying's realized move
    over the trade's life stays within the short strikes (approximated here
    as +/- the credit-implied breakeven band), the trade wins close to max
    profit; otherwise it loses proportionally, capped at max loss.

    This is a stand-in for real options pricing — good enough to validate
    "does the IV-rank filter select trades that would have worked," not
    good enough to be your only evidence. Replace with actual historical
    option pricing before trusting this number in a pitch deck.
    """
    breakeven_band = credit_pct_of_width  # crude proxy: bigger credit -> wider cushion
    if abs(realized_move_pct) <= breakeven_band:
        return credit_pct_of_width  # ~max profit, normalized
    overshoot = abs(realized_move_pct) - breakeven_band
    loss = min(1.0, overshoot / (1 - breakeven_band))  # normalized 0..1 of max loss
    return credit_pct_of_width - loss * (1 + credit_pct_of_width)


def run_backtest(symbol: str, closes: pd.Series, holding_period_days: int = 35) -> BacktestResult:
    result = BacktestResult()
    proxy_iv = realized_vol_proxy_series(closes).dropna()

    for i in range(config.IV_LOOKBACK_DAYS, len(closes) - holding_period_days, holding_period_days):
        window = proxy_iv.iloc[max(0, i - config.IV_LOOKBACK_DAYS):i]
        if window.empty:
            continue
        current_iv = proxy_iv.iloc[i]
        rank = iv_rank(current_iv, window)
        pct = iv_percentile(current_iv, window)

        if rank < config.IV_RANK_ENTRY_THRESHOLD or pct < config.IV_RANK_ENTRY_THRESHOLD:
            continue

        entry_price = closes.iloc[i]
        exit_price = closes.iloc[i + holding_period_days]
        realized_move_pct = (exit_price - entry_price) / entry_price

        # Assume credit ~ a fixed fraction of wing width as a rough estimate;
        # replace with real historical credit once you have option pricing.
        assumed_credit_pct_of_width = 0.30
        normalized_pnl = simulate_iron_condor_pnl(realized_move_pct, assumed_credit_pct_of_width)

        result.trades.append(
            BacktestTrade(
                date=closes.index[i],
                symbol=symbol,
                iv_rank_at_entry=rank,
                simulated_pnl=normalized_pnl,
            )
        )
    return result


if __name__ == "__main__":
    # Example: load your own historical closes CSV (date index, 'close' column)
    # for each watchlist symbol and run the backtest. Left as a manual step
    # since data source/format is very setup-dependent.
    print(
        "Load historical close-price CSVs per symbol and call run_backtest(). "
        "See docstring for the simplifying assumptions before trusting the output."
    )
