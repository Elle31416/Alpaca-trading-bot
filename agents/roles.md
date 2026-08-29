# Optional: splitting `main.py` into subagents

`main.py` runs the whole loop as one linear script, which is the fastest way
to get something working end-to-end. If you want to more visibly demonstrate
multi-agent orchestration for the "AI trading agent(s)" framing, the same
four steps map cleanly onto separate Claude Code subagents / skills:

| Role | Reads from | Does | Writes to |
|---|---|---|---|
| **Scanner** | `strategy/screener.py` | Screens the watchlist, returns ranked candidates | a shared "candidates" queue/file |
| **Strategist** | `strategy/spread_builder.py` | Turns one candidate into a concrete structure + credit/max-loss numbers | a "proposed trades" queue |
| **Risk Officer** | `execution/order_manager.py`, `config.py` | Vetoes trades that breach per-trade or portfolio risk caps; this is the safety gate — it should be able to say no | an "approved trades" queue, or a rejection log |
| **Execution** | `execution/order_manager.py` | Submits approved trades via the MCP server or `alpaca-py`, logs fills | order/fill log |

Each role can be a separate Claude Code skill/subagent with its own narrow
system prompt and only the tools it needs (Scanner and Strategist need
market-data read access; only Execution needs order-submission access). That
separation is itself a demonstrable safety property worth calling out in a
pitch: the agent that decides "is this a good trade" is not the same agent
that has permission to place it, and the Risk Officer sits in between with
veto power over both.

For a hackathon demo, even a lightweight version of this — four clearly
labeled functions with printed "Scanner says... / Strategist proposes...
/ Risk Officer approves|rejects... / Execution submits..." output — reads as
meaningfully more "agentic" than one script doing everything silently.
