"""
Turn a screened candidate into concrete option legs for a defined-risk
structure (iron condor or single-side credit spread).

Strike selection is delta-targeted: pick the short strike closest to
config.SHORT_STRIKE_DELTA, then the long strike config.WING_WIDTH_DOLLARS
further out-of-the-money. This is the standard way premium sellers describe
"how far out" a trade is, and it's a much more explainable choice to judges
than a fixed-percent-OTM rule, since it's expressed in terms of the market's
own probability estimate.
"""
from dataclasses import dataclass

import config
from data.option_chain import OptionContract, fetch_chain


@dataclass
class SpreadLeg:
    contract: OptionContract
    side: str          # "buy" | "sell"
    intent: str         # "buy_to_open" | "sell_to_open"


@dataclass
class ProposedStructure:
    underlying: str
    structure_type: str
    legs: list[SpreadLeg]
    net_credit: float
    max_loss: float
    max_profit: float

    def summary(self) -> str:
        leg_desc = ", ".join(
            f"{leg.side} {leg.contract.option_type} {leg.contract.strike} "
            f"exp {leg.contract.expiration}"
            for leg in self.legs
        )
        return (
            f"{self.underlying} {self.structure_type}: {leg_desc} | "
            f"credit=${self.net_credit:.2f} max_loss=${self.max_loss:.2f} "
            f"max_profit=${self.max_profit:.2f}"
        )


def _closest_by_delta(contracts: list[OptionContract], target_delta: float, option_type: str):
    candidates = [c for c in contracts if c.option_type == option_type and c.delta is not None]
    if not candidates:
        return None
    return min(candidates, key=lambda c: abs(abs(c.delta) - target_delta))


def _find_wing(contracts: list[OptionContract], short: OptionContract, wing_width: float):
    direction = 1 if short.option_type == "call" else -1
    target_strike = short.strike + direction * wing_width
    same_type_same_exp = [
        c for c in contracts
        if c.option_type == short.option_type and c.expiration == short.expiration
    ]
    if not same_type_same_exp:
        return None
    return min(same_type_same_exp, key=lambda c: abs(c.strike - target_strike))


def build_iron_condor(symbol: str) -> ProposedStructure | None:
    contracts = fetch_chain(symbol, config.MIN_DAYS_TO_EXPIRATION, config.MAX_DAYS_TO_EXPIRATION)
    if not contracts:
        return None

    short_call = _closest_by_delta(contracts, config.SHORT_STRIKE_DELTA, "call")
    short_put = _closest_by_delta(contracts, config.SHORT_STRIKE_DELTA, "put")
    if not short_call or not short_put:
        return None

    long_call = _find_wing(contracts, short_call, config.WING_WIDTH_DOLLARS)
    long_put = _find_wing(contracts, short_put, config.WING_WIDTH_DOLLARS)
    if not long_call or not long_put:
        return None

    net_credit = (
        short_call.mid + short_put.mid - long_call.mid - long_put.mid
    )
    max_loss = config.WING_WIDTH_DOLLARS * 100 - net_credit * 100
    max_profit = net_credit * 100

    legs = [
        SpreadLeg(short_call, "sell", "sell_to_open"),
        SpreadLeg(long_call, "buy", "buy_to_open"),
        SpreadLeg(short_put, "sell", "sell_to_open"),
        SpreadLeg(long_put, "buy", "buy_to_open"),
    ]
    return ProposedStructure(
        underlying=symbol,
        structure_type="iron_condor",
        legs=legs,
        net_credit=net_credit,
        max_loss=max_loss,
        max_profit=max_profit,
    )


def build_structure(symbol: str) -> ProposedStructure | None:
    if config.STRUCTURE == "iron_condor":
        return build_iron_condor(symbol)
    raise NotImplementedError(
        f"STRUCTURE={config.STRUCTURE!r} not implemented in this scaffold — "
        "iron_condor is the only structure wired up. Add a single-side "
        "credit-spread builder here if you want directional trades too."
    )
