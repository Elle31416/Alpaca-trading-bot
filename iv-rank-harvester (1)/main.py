"""
Orchestration entry point.

    python main.py --dry-run     # screen + propose trades, print only
    python main.py               # screen + propose + actually submit orders

This loop is intentionally linear and easy to read top-to-bottom — the
"multi-agent" framing (Scanner / Strategist / Risk Officer / Execution) in
agents/roles.md maps directly onto the four steps below if you split this
into separate Claude Code subagents for a more visibly agentic demo.
"""
import argparse

import config
from strategy.screener import screen_watchlist
from strategy.spread_builder import build_structure
from execution.order_manager import size_position, portfolio_risk_ok, submit_iron_condor
from logging_util import record_run


def run(dry_run: bool = True):
    from alpaca_client import get_trading_client

    client = get_trading_client()
    account = client.get_account()
    equity = float(account.equity)

    print(f"Account equity: ${equity:,.2f} | dry_run={dry_run}")

    candidates = screen_watchlist()
    print(f"Screened {len(config.WATCHLIST)} symbols -> {len(candidates)} passed IV-rank threshold")

    open_risk = 0.0  # TODO: sum max_loss of currently-open positions via client.get_all_positions()
    trades_placed = 0
    trade_summaries = []

    for candidate in candidates:
        if trades_placed >= config.MAX_CONCURRENT_POSITIONS:
            print("Hit MAX_CONCURRENT_POSITIONS, stopping.")
            break

        structure = build_structure(candidate.symbol)
        if structure is None:
            print(f"[{candidate.symbol}] could not build a valid structure, skipping")
            continue

        qty = size_position(structure, equity)
        if qty <= 0:
            print(f"[{candidate.symbol}] sizing returned 0 contracts, skipping")
            continue

        trade_risk = structure.max_loss * qty
        if not portfolio_risk_ok(open_risk, trade_risk, equity):
            print(f"[{candidate.symbol}] would breach portfolio risk cap, skipping")
            continue

        print(f"[{candidate.symbol}] IV rank {candidate.iv_rank:.1f} -> {structure.summary()}")
        submit_iron_condor(structure, qty, dry_run=dry_run)

        open_risk += trade_risk
        trades_placed += 1
        trade_summaries.append(structure.summary())

    print(f"Done. {trades_placed} structure(s) proposed/placed.")

    record_run(
        equity=equity,
        candidates_count=len(candidates),
        trades_placed=trades_placed,
        trade_summaries=trade_summaries,
        dry_run=dry_run,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Screen and propose trades without submitting orders")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
