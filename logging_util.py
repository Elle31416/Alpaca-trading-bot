"""
Writes run results into docs/data/*.json — plain JSON files served directly
by GitHub Pages (no backend needed). Every scheduled run appends one status
snapshot and, if trades were placed, one or more trade log entries.

Kept dependency-free (stdlib only) since this runs inside the same GitHub
Actions job as the trading logic and shouldn't be a reason for that job to
fail.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "docs" / "data"
STATUS_FILE = DATA_DIR / "status.json"
EQUITY_FILE = DATA_DIR / "equity_curve.json"
TRADES_FILE = DATA_DIR / "trades.json"

MAX_EQUITY_POINTS = 2000  # keep the dashboard file bounded


def _load(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return default


def _save(path: Path, data) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


def record_run(
    equity: float,
    candidates_count: int,
    trades_placed: int,
    trade_summaries: list[str],
    dry_run: bool,
) -> None:
    now = datetime.now(timezone.utc).isoformat()

    _save(
        STATUS_FILE,
        {
            "last_run_utc": now,
            "equity": equity,
            "candidates_screened_pass": candidates_count,
            "trades_placed_this_run": trades_placed,
            "dry_run": dry_run,
        },
    )

    equity_curve = _load(EQUITY_FILE, [])
    equity_curve.append({"timestamp": now, "equity": equity})
    _save(EQUITY_FILE, equity_curve[-MAX_EQUITY_POINTS:])

    if trade_summaries:
        trades = _load(TRADES_FILE, [])
        for summary in trade_summaries:
            trades.append({"timestamp": now, "summary": summary, "dry_run": dry_run})
        _save(TRADES_FILE, trades)
