"""
Fetch and normalize option chain data for a single underlying.

NOTE: Alpaca's option chain / snapshot endpoints and field names have moved
around across alpaca-py releases. Treat the request construction below as a
template — confirm the exact request class name (e.g. OptionChainRequest vs
OptionSnapshotRequest) and returned field names (implied_volatility, greeks
sub-object, etc.) against the version pinned in requirements.txt before
running live.
"""
from datetime import date, timedelta
from dataclasses import dataclass
from typing import Optional


@dataclass
class OptionContract:
    symbol: str
    underlying: str
    expiration: date
    strike: float
    option_type: str  # "call" | "put"
    bid: float
    ask: float
    implied_volatility: Optional[float]
    delta: Optional[float]

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2 if self.bid and self.ask else 0.0


def fetch_chain(underlying: str, min_dte: int, max_dte: int) -> list[OptionContract]:
    """
    Return normalized option contracts for `underlying` expiring between
    min_dte and max_dte days from today.
    """
    from alpaca_client import get_option_data_client
    from alpaca.data.requests import OptionChainRequest

    client = get_option_data_client()
    today = date.today()
    exp_gte = today + timedelta(days=min_dte)
    exp_lte = today + timedelta(days=max_dte)

    request = OptionChainRequest(
        underlying_symbol=underlying,
        expiration_date_gte=exp_gte,
        expiration_date_lte=exp_lte,
    )
    raw = client.get_option_chain(request)

    contracts = []
    for symbol, snapshot in raw.items():
        quote = getattr(snapshot, "latest_quote", None)
        greeks = getattr(snapshot, "greeks", None)
        contracts.append(
            OptionContract(
                symbol=symbol,
                underlying=underlying,
                expiration=_parse_expiration(symbol),
                strike=_parse_strike(symbol),
                option_type=_parse_type(symbol),
                bid=getattr(quote, "bid_price", 0.0) if quote else 0.0,
                ask=getattr(quote, "ask_price", 0.0) if quote else 0.0,
                implied_volatility=getattr(snapshot, "implied_volatility", None),
                delta=getattr(greeks, "delta", None) if greeks else None,
            )
        )
    return contracts


def _parse_expiration(occ_symbol: str) -> date:
    """OCC symbols embed YYMMDD right after the root ticker."""
    digits = "".join(ch for ch in occ_symbol if ch.isdigit())
    yy, mm, dd = digits[0:2], digits[2:4], digits[4:6]
    return date(2000 + int(yy), int(mm), int(dd))


def _parse_strike(occ_symbol: str) -> float:
    # Last 8 digits of an OCC symbol are strike * 1000.
    return int(occ_symbol[-8:]) / 1000.0


def _parse_type(occ_symbol: str) -> str:
    flag = occ_symbol[-9]
    return "call" if flag == "C" else "put"
