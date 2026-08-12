#!/usr/bin/env python
"""Runs delivery-SMS APScheduler at 09:40 IST (Debian + pymssql/FreeTDS)."""

from __future__ import annotations

import time
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scheduler import start_delivery_sms_scheduler


def main() -> None:
    print("[Skylark] Chicks delivery SMS worker starting (09:40 IST)", flush=True)
    start_delivery_sms_scheduler()
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
