"""
Scheduled entry point. Two ways to use it:

  One-shot (GitHub Actions cron target, or a plain server cron job):
      python scripts/run_scheduled.py               # live paper trades
      python scripts/run_scheduled.py --dry-run      # log only, no orders

  Persistent worker (Railway/Fly.io/Render "worker" process, if you'd rather
  run one long-lived process than a periodic cron):
      python scripts/run_scheduled.py --loop --interval 900

Checks Alpaca's own market clock before doing anything — more reliable than
hardcoding market hours in a cron expression, since it accounts for holidays
and early closes automatically.
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from main import run  # noqa: E402


def market_is_open() -> bool:
    from alpaca_client import get_trading_client

    clock = get_trading_client().get_clock()
    return bool(clock.is_open)


def run_once(dry_run: bool) -> None:
    if not market_is_open():
        print("Market closed — skipping this run.")
        return
    run(dry_run=dry_run)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--loop", action="store_true", help="Run continuously (for a persistent worker) instead of once")
    parser.add_argument("--interval", type=int, default=900, help="Seconds between checks when --loop is set")
    args = parser.parse_args()

    if not args.loop:
        run_once(args.dry_run)
        return

    while True:
        try:
            run_once(args.dry_run)
        except Exception as exc:  # noqa: BLE001 — a single bad cycle shouldn't kill a persistent worker
            print(f"[run_scheduled] error: {exc}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
