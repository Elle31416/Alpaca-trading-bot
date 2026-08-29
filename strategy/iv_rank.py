"""
IV Rank and IV Percentile calculation.

IV Rank    = (current_iv - min_iv_over_window) / (max_iv_over_window - min_iv_over_window) * 100
IV Percentile = % of days in the window where IV was BELOW the current level

Both answer "is current IV rich?" but can diverge — IV rank is sensitive to
outlier spikes in the window, IV percentile is not. Screener checks both and
requires agreement (see screener.py) to reduce false positives from a single
historical spike skewing IV rank.

This uses the underlying's historical realized-vol-implied proxy: we track
the ATM implied volatility time series if you have it stored, but for a
lightweight scaffold we approximate using historical close-to-close
volatility as a stand-in when a true historical IV series isn't available.
Swap `historical_iv_series` for a real stored IV series if you have one —
that's the more correct input, and worth building once options-history
storage is wired up.
"""
import numpy as np
import pandas as pd


def iv_rank(current_iv: float, historical_iv_series: pd.Series) -> float:
    lo, hi = historical_iv_series.min(), historical_iv_series.max()
    if hi == lo:
        return 0.0
    return float((current_iv - lo) / (hi - lo) * 100)


def iv_percentile(current_iv: float, historical_iv_series: pd.Series) -> float:
    below = (historical_iv_series < current_iv).sum()
    return float(below / len(historical_iv_series) * 100)


def realized_vol_proxy_series(closes: pd.Series, window: int = 20) -> pd.Series:
    """
    Fallback proxy when a stored historical IV series isn't available yet:
    annualized rolling realized volatility of the underlying. This is NOT
    the same signal as implied volatility (it's backward-looking realized
    vol, not the market's forward-looking price of vol) — treat it as a
    bootstrap for testing the pipeline, and replace with real historical IV
    (e.g. persisted daily snapshots of ATM IV) before trusting live signals.
    """
    log_returns = np.log(closes / closes.shift(1))
    rolling_std = log_returns.rolling(window).std()
    return rolling_std * np.sqrt(252) * 100
