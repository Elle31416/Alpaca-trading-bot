# IV-Rank Premium Harvester

An options-selling agent that screens a watchlist for elevated implied volatility
(relative to its own recent range), then sells **defined-risk** credit spreads or
iron condors against it, with mechanical profit-take / stop-loss exits.

Built against Alpaca's Trading API + Market Data API, designed to run through
either the **Alpaca MCP server** (natural-language / Claude Code driven) or the
**Alpaca CLI** (scheduled/cron-style), with `alpaca-py` doing the heavy lifting
for multi-leg option orders.

> ⚠️ This scaffold targets a **paper trading account only**. Nothing here is
> financial advice, and none of it should be pointed at a live account without
> its own independent review — options selling carries real risk even when
> "defined risk," and IV-rank alone is not a robust edge without further
> validation.

## Why this strategy shape

- **IV Rank / IV Percentile**: how rich current implied volatility is relative
  to its own trailing range (not relative to other names) — a standard,
  explainable vol-selling signal.
- **Defined risk only**: credit spreads and iron condors cap max loss at
  entry. No naked short options anywhere in this codebase, on purpose — a
  single bad naked print during a judging window (or in real life) can wipe
  out a strategy that otherwise looks fine.
- **Mechanical exits**: close at a fraction of max profit, or at a multiple of
  credit received as a stop — removes discretion and emotion from exits,
  which is also what makes the strategy easy to explain and backtest.

## Architecture

```
iv-rank-harvester/
├── config.py                 # watchlist, thresholds, risk limits
├── alpaca_client.py          # shared Trading + Market Data clients
├── strategy/
│   ├── iv_rank.py             # IV rank / percentile calculation
│   ├── screener.py            # scan watchlist, rank candidates
│   └── spread_builder.py      # turn a candidate into concrete option legs
├── execution/
│   ├── order_manager.py       # submit multi-leg orders, position sizing
│   └── risk_manager.py        # monitor open positions, enforce exits
├── data/
│   └── option_chain.py        # fetch & normalize option chain / greeks
├── backtest/
│   └── backtest.py            # historical replay of the same logic
├── agents/
│   └── roles.md               # optional: split this into Scanner / Strategist
│                               #   / Risk Officer / Execution subagents
├── mcp_config.example.json    # example Claude Desktop/Code MCP config
├── main.py                    # orchestration loop
├── requirements.txt
└── .env.example
```

## Setup

1. Create a **new, dedicated** Alpaca paper account — don't reuse an old one.
2. Copy `.env.example` to `.env` and fill in your paper API key/secret.
3. `pip install -r requirements.txt`
4. Sanity-check connectivity:
   ```bash
   python -c "from alpaca_client import get_trading_client; print(get_trading_client().get_account())"
   ```
5. (Optional, for the agent/MCP path) install and point the Alpaca MCP server
   at the same paper credentials — see `mcp_config.example.json`.
6. Run a dry pass:
   ```bash
   python main.py --dry-run
   ```
   This screens the watchlist and prints proposed trades without submitting
   anything. Drop `--dry-run` once you've eyeballed the output.

## Sequencing note

Backtest first (`backtest/backtest.py`) against months of history before
trusting a handful of live paper days — five trading days of live P&L is
mostly noise on its own. Use the backtest to sanity-check the IV-rank
threshold and exit rules; use the live paper run to prove the pipeline
actually executes end-to-end (auth, order routing, fills, exit monitoring).

## What's stubbed vs. what's real

This scaffold implements real logic for IV-rank calculation, spread
construction, position sizing, and exit rules. The Alpaca client calls follow
the documented `alpaca-py` and Market Data API shapes as of this writing —
**verify field names and endpoints against current Alpaca docs before running
live**, since SDK surfaces do shift. Anywhere this matters, there's a comment
flagging it.
