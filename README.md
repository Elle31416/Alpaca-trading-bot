# IV-Rank Harvester

**An options-selling agent that only takes trades it can't blow up on.**

## The Problem

When implied volatility is rich, options are expensive to buy and profitable to sell —
but doing that by hand is slow, emotional, and easy to over-size. This agent automates
the disciplined part: find the rich IV, build a defined-risk trade, exit mechanically.

## What It Does

1. **Screens** a watchlist by IV Rank — how rich current IV is vs. *its own* trailing
   range (not vs. other tickers).
2. **Builds** credit spreads or iron condors — max loss is capped the moment the trade
   is placed.
3. **Manages exits** automatically: take profit at a fraction of max gain, stop out at
   a multiple of credit received.
4. **Talks to Claude** — runs through the Alpaca MCP server, so you can ask in plain
   English ("scan my watchlist") and get back real option legs, not just a chart.

## Why This Might Stand Out

- **A real, explainable edge** — IV Rank is a standard vol-selling signal, not a black box.
- **Safety is a design constraint, not an afterthought** — no naked options anywhere in
  the codebase, on purpose.
- **One codebase, two modes** — the same strategy logic drives the backtest *and* the
  live paper trader, so "what we tested" can't drift from "what we run."
- **Agentic, not just automated** — the MCP integration makes this a Claude-native
  trading assistant, not a cron job with an API key.

## Architecture

```
iv-rank-harvester/
├── config.py              # watchlist, thresholds, risk limits
├── alpaca_client.py        # shared Trading + Market Data clients
├── strategy/                # IV rank, screening, spread construction
├── execution/                # order submission, position sizing, risk/exit monitoring
├── data/                       # option chain + greeks
├── backtest/                     # historical replay of the same logic
├── agents/roles.md                 # optional multi-agent split (Scanner/Strategist/Risk/Exec)
├── main.py                           # orchestration loop
└── mcp_config.example.json            # Claude Desktop/Code MCP config
```

## Quickstart (paper trading only)

```bash
cp .env.example .env        # add PAPER API keys — use a fresh, dedicated account
pip install -r requirements.txt
python main.py --dry-run    # prints proposed trades, submits nothing
```

Backtest before trusting live paper results — a few days of live P&L is mostly noise;
months of backtest is where the IV-rank threshold and exit rules actually get validated:

```bash
python backtest/backtest.py
```

## Guardrails, by design

- 🧪 Paper account only
- 🚫 No naked short options — every position is defined-risk
- 📏 Mechanical exits, no discretion — easy to explain and easy to backtest
- ⚠️ Not financial advice; verify Alpaca API field names before ever going live

## What's Real vs. Stubbed

**Real:** IV-rank math, spread construction, position sizing, exit logic.
**Needs a fresh look before going live:** exact Alpaca endpoint/field names (SDKs
shift over time) — flagged in code comments where it matters.
