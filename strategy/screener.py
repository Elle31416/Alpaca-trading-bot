"""
Screen the configured watchlist and return candidates whose IV looks rich
enough to sell premium against, ranked best-first.
"""
from dataclasses import dataclass

import pandas as pd

import config
from strategy.iv_rank import iv_rank, iv_percentile, realized_vol_proxy_series


@dataclass
class Candidate:
    symbol: str
    current_iv: float
    iv_rank: float
    iv_percentile: float

    def passes_threshold(self) -> bool:
        # Require agreement between rank and percentile to reduce the chance
        # a single historical spike is skewing IV rank on its own.
        return (
            self.iv_rank >= config.IV_RANK_ENTRY_THRESHOLD
            and self.iv_percentile >= config.IV_RANK_ENTRY_THRESHOLD
        )


def _fetch_close_history(symbol: str, lookback_days: int) -> pd.Series:
    from datetime import datetime, timedelta
    from alpaca_client import get_stock_data_client
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame

    client = get_stock_data_client()
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=datetime.utcnow() - timedelta(days=int(lookback_days * 1.6)),  # padding for weekends/holidays
    )
    bars = client.get_stock_bars(request).df
    return bars["close"].droplevel(0) if isinstance(bars.index, pd.MultiIndex) else bars["close"]


def _current_atm_iv(symbol: str) -> float:
    """Approximate current IV as the average IV of near-ATM contracts."""
    from data.option_chain import fetch_chain

    contracts = fetch_chain(symbol, config.MIN_DAYS_TO_EXPIRATION, config.MAX_DAYS_TO_EXPIRATION)
    ivs = [c.implied_volatility for c in contracts if c.implied_volatility]
    if not ivs:
        raise ValueError(f"No IV data returned for {symbol}; check chain fetch / market hours.")
    return sum(ivs) / len(ivs)


def screen_watchlist() -> list[Candidate]:
    candidates = []
    for symbol in config.WATCHLIST:
        try:
            closes = _fetch_close_history(symbol, config.IV_LOOKBACK_DAYS)
            proxy_series = realized_vol_proxy_series(closes).dropna()
            current_iv = _current_atm_iv(symbol)

            candidates.append(
                Candidate(
                    symbol=symbol,
                    current_iv=current_iv,
                    iv_rank=iv_rank(current_iv, proxy_series),
                    iv_percentile=iv_percentile(current_iv, proxy_series),
                )
            )
        except Exception as exc:  # noqa: BLE001 — screening one bad symbol shouldn't kill the run
            print(f"[screener] skipping {symbol}: {exc}")

    passing = [c for c in candidates if c.passes_threshold()]
    return sorted(passing, key=lambda c: c.iv_rank, reverse=True)
