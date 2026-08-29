"""
Monitors open credit-spread/iron-condor positions and closes them when they
hit the mechanical exit rules from config.py:
  - close at PROFIT_TAKE_PCT_OF_MAX of max profit
  - close at a loss of STOP_LOSS_MULTIPLE_OF_CREDIT x credit received

Keeping exits mechanical (not discretionary) is deliberate: it's what makes
the strategy backtestable and explainable, and it's what stops "let it ride"
thinking from turning a defined-risk trade into a bigger loss than planned
(closing early on a stop still beats holding to max loss).
"""
from dataclasses import dataclass

import config


@dataclass
class OpenPosition:
    underlying: str
    structure_type: str
    net_credit: float      # credit received at entry, per contract
    max_profit: float      # == net_credit * 100 for a condor, informational here
    current_value_to_close: float  # what it would cost to close right now, per contract
    qty: int


def evaluate_exit(position: OpenPosition) -> str | None:
    """
    Returns 'profit_take', 'stop_loss', or None (hold).

    current_value_to_close is the debit required to close the spread now —
    for a credit spread, profit = net_credit - current_value_to_close.
    """
    profit_so_far = position.net_credit - position.current_value_to_close
    profit_take_level = position.net_credit * config.PROFIT_TAKE_PCT_OF_MAX
    stop_loss_level = -position.net_credit * config.STOP_LOSS_MULTIPLE_OF_CREDIT

    if profit_so_far >= profit_take_level:
        return "profit_take"
    if profit_so_far <= stop_loss_level:
        return "stop_loss"
    return None


def close_position(position: OpenPosition, dry_run: bool = True):
    """
    Closes an open multi-leg position by submitting the inverse legs.
    Left as a stub pointing at order_manager patterns — wire this up to
    fetch the position's actual leg symbols from the trading client
    (client.get_all_positions()) rather than reconstructing them, so you
    close exactly what's open rather than what you assumed was open.
    """
    if dry_run:
        print(
            f"[DRY RUN] would close {position.qty}x {position.underlying} "
            f"{position.structure_type}"
        )
        return None
    raise NotImplementedError(
        "Wire this to alpaca_client.get_trading_client().close_position(...) "
        "or an inverse multi-leg order once you're ready to go live."
    )
