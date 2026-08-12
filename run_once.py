"""Run the delivery-reminder job once (manual / Task Scheduler / cron)."""

from __future__ import annotations

import argparse
import sys
import traceback

import config
from job import run_delivery_reminders


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send chicks delivery reminder SMS once")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Send even if today's lock already exists",
    )
    args = parser.parse_args()
    if args.force:
        config.FORCE_SEND = True

    try:
        run_delivery_reminders()
    except Exception:
        print("[fatal] Delivery reminder job crashed:", flush=True)
        traceback.print_exc()
        sys.exit(1)
